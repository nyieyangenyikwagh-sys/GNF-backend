import hashlib
import json
from datetime import datetime

from fastapi import APIRouter, Depends, Header, HTTPException, Response
from sqlalchemy.exc import IntegrityError

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.request_context import correlation_id
from app.models.audit import AuditLog
from app.models.claim import Claim, ClaimLine, ClaimStatusHistory
from app.models.insurance import PatientInsurance
from app.models.patient import Patient
from app.schemas.claim import AuditEventOut, ClaimCreate, ClaimOut, ClaimUpdate, StatusChange
from app.services.claim_status import ALLOWED_TRANSITIONS, record_audit, transition
from app.services.claim_workflow import assess_claim
from app.services.eligibility import assert_eligible


router = APIRouter(prefix="/claims", tags=["claims"])
STAFF_READ_ROLES = {"adjuster", "supervisor", "auditor", "admin", "service"}
WRITE_ROLES = {"claimant", "biller", "adjuster", "supervisor", "admin", "service"}
MANUAL_ROLES = {"adjuster", "supervisor", "admin"}


def _can_read(claim: Claim, user) -> bool:
    return user.role in STAFF_READ_ROLES or claim.owner_user_id == user.id


def _get_visible_claim(db, claim_id: int, user, *, lock: bool = False) -> Claim:
    query = db.query(Claim).filter(Claim.id == claim_id)
    if lock:
        query = query.with_for_update()
    claim = query.first()
    if not claim or not _can_read(claim, user):
        # Deliberately conceal existence from callers without ownership.
        raise HTTPException(404, "Claim not found")
    return claim


def _payload_hash(payload: ClaimCreate) -> str:
    canonical = json.dumps(payload.model_dump(mode="json"), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


@router.post("", response_model=ClaimOut, status_code=201)
def create_claim(
    payload: ClaimCreate,
    response: Response,
    idempotency_key: str = Header(..., alias="Idempotency-Key", min_length=8, max_length=128),
    db=Depends(get_db),
    user=Depends(get_current_user),
):
    if user.role not in WRITE_ROLES:
        raise HTTPException(403, "Role cannot create claims")
    digest = _payload_hash(payload)
    existing = db.query(Claim).filter(
        Claim.owner_user_id == user.id, Claim.idempotency_key == idempotency_key,
    ).first()
    if existing:
        if existing.request_hash != digest:
            raise HTTPException(409, {"code": "IDEMPOTENCY_CONFLICT", "message": "Key was already used with a different request"})
        response.status_code = 200
        response.headers["Idempotent-Replay"] = "true"
        return existing

    patient = db.get(Patient, payload.patient_id)
    if not patient:
        raise HTTPException(404, "Patient not found")
    if user.role == "claimant" and patient.owner_user_id != user.id:
        raise HTTPException(404, "Patient not found")
    insurance = db.query(PatientInsurance).filter(
        PatientInsurance.patient_id == payload.patient_id,
        PatientInsurance.plan_id == payload.plan_id,
    ).first()
    if not insurance:
        raise HTTPException(422, {"code": "UNKNOWN_POLICY", "message": "Policy does not exist for this patient"})
    if payload.service_date < insurance.effective_date or (
        insurance.termination_date and payload.service_date > insurance.termination_date
    ):
        raise HTTPException(422, {"code": "SERVICE_DATE_OUTSIDE_POLICY", "message": "Service date is outside the policy period"})
    snapshot = assert_eligible(db, payload.patient_id, payload.plan_id)
    claim = Claim(
        patient_id=payload.patient_id,
        plan_id=payload.plan_id,
        owner_user_id=user.id,
        idempotency_key=idempotency_key,
        request_hash=digest,
        correlation_id=correlation_id(),
        province=payload.province,
        provider_billing_number=payload.provider_billing_number,
        service_date=payload.service_date,
        billed_amount=sum(line.amount * line.units for line in payload.lines),
        coverage_snapshot=snapshot,
        status="PENDING_RULES",
        version=1,
    )
    db.add(claim)
    try:
        db.flush()
        for line in payload.lines:
            db.add(ClaimLine(claim_id=claim.id, **line.model_dump()))
        db.add(ClaimStatusHistory(
            claim_id=claim.id,
            from_status=None,
            to_status="PENDING_RULES",
            reason_code=None,
            actor_user_id=user.id,
            correlation_id=correlation_id(),
            claim_version=claim.version,
            created_at=datetime.utcnow(),
        ))
        record_audit(db, claim, "claim.created", user.id, {"initial_status": "PENDING_RULES"})
        db.commit()
        db.refresh(claim)
    except IntegrityError:
        db.rollback()
        winner = db.query(Claim).filter(
            Claim.owner_user_id == user.id, Claim.idempotency_key == idempotency_key,
        ).first()
        if winner and winner.request_hash == digest:
            response.status_code = 200
            response.headers["Idempotent-Replay"] = "true"
            return winner
        raise HTTPException(409, {"code": "IDEMPOTENCY_CONFLICT", "message": "Concurrent request used this key"})
    return assess_claim(db, claim, patient, user.id)


@router.get("", response_model=list[ClaimOut])
def list_claims(db=Depends(get_db), user=Depends(get_current_user)):
    query = db.query(Claim)
    if user.role not in STAFF_READ_ROLES:
        query = query.filter(Claim.owner_user_id == user.id)
    return query.order_by(Claim.id).all()


@router.get("/{claim_id}", response_model=ClaimOut)
def get_claim(claim_id: int, db=Depends(get_db), user=Depends(get_current_user)):
    return _get_visible_claim(db, claim_id, user)


@router.patch("/{claim_id}", response_model=ClaimOut)
def update_claim(
    claim_id: int,
    payload: ClaimUpdate,
    expected_version: int = Header(..., alias="If-Match", ge=1),
    db=Depends(get_db),
    user=Depends(get_current_user),
):
    if user.role not in WRITE_ROLES:
        raise HTTPException(403, "Role cannot edit claims")
    claim = _get_visible_claim(db, claim_id, user, lock=True)
    if claim.version != expected_version:
        db.rollback()
        raise HTTPException(409, {"code": "VERSION_CONFLICT", "message": "Claim was changed by another request"})
    if claim.status in {"APPROVED", "DENIED", "PAID", "CLOSED"}:
        raise HTTPException(409, "Finalized claims cannot be edited")
    previous_status = claim.status
    values = payload.model_dump(exclude_unset=True)
    if "provider_billing_number" in values:
        claim.provider_billing_number = values["provider_billing_number"]
    if "service_date" in values:
        claim.service_date = values["service_date"]
    if "lines" in values:
        claim.lines.clear()
        for line in payload.lines or []:
            claim.lines.append(ClaimLine(**line.model_dump()))
        claim.billed_amount = sum(line.amount * line.units for line in payload.lines or [])
    claim.version += 1
    claim.status = "PENDING_RULES"
    claim.rules_result = None
    claim.fraud_result = None
    claim.assessment_claim_version = None
    claim.assessment_attempts = 0
    claim.next_retry_at = None
    db.add(ClaimStatusHistory(
        claim_id=claim.id, from_status=previous_status, to_status="PENDING_RULES",
        reason_code="CLAIM_EDITED", actor_user_id=user.id, correlation_id=correlation_id(),
        claim_version=claim.version, created_at=datetime.utcnow(),
    ))
    record_audit(db, claim, "claim.edited_assessment_stale", user.id, {"changed_fields": sorted(values)})
    db.commit()
    db.refresh(claim)
    patient = db.get(Patient, claim.patient_id)
    return assess_claim(db, claim, patient, user.id)


@router.post("/{claim_id}/retry-assessment", response_model=ClaimOut)
def retry_assessment(claim_id: int, db=Depends(get_db), user=Depends(get_current_user)):
    if user.role not in {"adjuster", "supervisor", "admin", "service"}:
        raise HTTPException(403, "Role cannot retry assessments")
    claim = _get_visible_claim(db, claim_id, user, lock=True)
    if claim.status != "FAILED_ASSESSMENT":
        raise HTTPException(409, "Only failed assessments can be retried")
    transition(db, claim, "PENDING_RULES", "RETRY", user.id)
    return assess_claim(db, claim, db.get(Patient, claim.patient_id), user.id)


@router.post("/{claim_id}/status", response_model=ClaimOut)
def change_status(claim_id: int, payload: StatusChange, db=Depends(get_db), user=Depends(get_current_user)):
    if user.role not in MANUAL_ROLES:
        raise HTTPException(403, "Manual review action requires adjuster or supervisor role")
    claim = _get_visible_claim(db, claim_id, user, lock=True)
    if payload.to_status == "APPROVED" and user.role not in {"supervisor", "admin"}:
        raise HTTPException(403, "Approval requires supervisor role")
    if payload.to_status not in ALLOWED_TRANSITIONS.get(claim.status, set()):
        raise HTTPException(409, f"Illegal transition {claim.status} -> {payload.to_status}")
    return transition(db, claim, payload.to_status, payload.reason_code, user.id)


@router.get("/{claim_id}/audit", response_model=list[AuditEventOut])
def claim_audit(claim_id: int, db=Depends(get_db), user=Depends(get_current_user)):
    if user.role not in STAFF_READ_ROLES:
        raise HTTPException(403, "Audit trail requires a staff read role")
    _get_visible_claim(db, claim_id, user)
    return db.query(AuditLog).filter(AuditLog.claim_id == claim_id).order_by(AuditLog.id).all()
