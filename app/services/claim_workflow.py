from datetime import datetime, timedelta

from app.models.insurance import PatientInsurance
from app.services.assessment_clients import AssessmentUnavailable, assess_fraud, assess_rules
from app.services.claim_status import record_audit, transition


def assess_claim(db, claim, patient, actor_user_id=None):
    insurance = db.query(PatientInsurance).filter(
        PatientInsurance.patient_id == claim.patient_id,
        PatientInsurance.plan_id == claim.plan_id,
    ).first()
    if claim.status == "PENDING_RULES":
        try:
            rules = assess_rules(claim, patient, insurance)
        except AssessmentUnavailable as exc:
            transition(db, claim, "FAILED_ASSESSMENT", "RULES_UNAVAILABLE", actor_user_id, commit=False)
            claim.assessment_attempts += 1
            claim.next_retry_at = datetime.utcnow() + timedelta(seconds=min(2 ** claim.assessment_attempts, 300))
            record_audit(db, claim, "rules.failed", actor_user_id, {"error_type": str(exc)})
            db.commit()
            db.refresh(claim)
            return claim

        rules_version = claim.version
        claim.rules_result = {**rules.model_dump(mode="json"), "claim_version": rules_version}
        record_audit(db, claim, "rules.completed", actor_user_id, {
            "outcome": rules.outcome, "reason_codes": rules.reason_codes, "rules_version": rules.rules_version,
        })
        if rules.outcome == "FAIL":
            transition(db, claim, "REVIEW", rules.reason_codes[0] if rules.reason_codes else "RULE_FAILED", actor_user_id, commit=False)
            claim.assessment_claim_version = rules_version
            claim.assessment_attempts = 0
            claim.next_retry_at = None
            db.commit()
            db.refresh(claim)
            return claim

        transition(db, claim, "PENDING_FRAUD", actor_user_id=actor_user_id, commit=False)
        db.commit()
        db.refresh(claim)

    try:
        fraud = assess_fraud(claim)
    except AssessmentUnavailable as exc:
        transition(db, claim, "FAILED_ASSESSMENT", "FRAUD_UNAVAILABLE", actor_user_id, commit=False)
        claim.assessment_attempts += 1
        claim.next_retry_at = datetime.utcnow() + timedelta(seconds=min(2 ** claim.assessment_attempts, 300))
        record_audit(db, claim, "fraud.failed", actor_user_id, {"error_type": str(exc)})
        db.commit()
        db.refresh(claim)
        return claim

    fraud_claim_version = claim.version
    claim.fraud_result = {**fraud.model_dump(mode="json"), "claim_version": fraud_claim_version}
    record_audit(db, claim, "fraud.completed", actor_user_id, {
        "risk": fraud.risk, "model_version": fraud.model_version,
    })
    next_status = "REVIEW" if fraud.risk == "HIGH" else "SUBMITTED"
    transition(db, claim, next_status, "HIGH_FRAUD_RISK" if fraud.risk == "HIGH" else None, actor_user_id, commit=False)
    claim.assessment_claim_version = fraud_claim_version
    claim.assessment_attempts = 0
    claim.next_retry_at = None
    db.commit()
    db.refresh(claim)
    return claim
