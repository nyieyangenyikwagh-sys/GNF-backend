from datetime import datetime
from fastapi import HTTPException
from app.models.claim import Claim,ClaimStatusHistory
from app.models.audit import AuditLog
from app.core.request_context import correlation_id


ALLOWED_TRANSITIONS = {
    "PENDING_RULES": {"PENDING_FRAUD", "REVIEW", "FAILED_ASSESSMENT"},
    "PENDING_FRAUD": {"SUBMITTED", "REVIEW", "FAILED_ASSESSMENT"},
    "FAILED_ASSESSMENT": {"PENDING_RULES"},
    "REVIEW": {"HUMAN_REVIEW", "SUBMITTED", "DENIED"},
    "HUMAN_REVIEW": {"SUBMITTED", "APPROVED", "DENIED"},
    "SUBMITTED": {"APPROVED", "DENIED", "PAID"},
    "APPROVED": {"PAID"},
    "DENIED": {"HUMAN_REVIEW", "CLOSED"},
    "PAID": {"CLOSED"},
    "CLOSED": set(),
}


def record_audit(db, claim, action, actor_user_id=None, details=None):
    db.add(AuditLog(
        user_id=actor_user_id,
        claim_id=claim.id,
        action=action,
        resource=f"claim:{claim.id}",
        correlation_id=correlation_id(),
        claim_version=claim.version,
        details=details or {},
    ))


def transition(db, claim, to_status, reason_code=None, actor_user_id=None, commit=True):
    if claim is None:
        raise HTTPException(404, "Claim not found")
    if to_status not in ALLOWED_TRANSITIONS.get(claim.status, set()):
        raise HTTPException(409, f"Illegal transition {claim.status} -> {to_status}")
    previous = claim.status
    claim.status = to_status
    claim.version += 1
    if reason_code and to_status in {"DENIED", "REVIEW"}:
        claim.denial_reason_code = reason_code
    db.add(ClaimStatusHistory(
        claim_id=claim.id,
        from_status=previous,
        to_status=to_status,
        reason_code=reason_code,
        actor_user_id=actor_user_id,
        correlation_id=correlation_id(),
        claim_version=claim.version,
        created_at=datetime.utcnow(),
    ))
    record_audit(db, claim, "claim.status_changed", actor_user_id, {
        "from_status": previous, "to_status": to_status, "reason_code": reason_code,
    })
    if commit:
        db.commit()
        db.refresh(claim)
    return claim
