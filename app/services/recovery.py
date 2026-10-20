import logging
from datetime import datetime

from app.core.database import SessionLocal
from app.models.claim import Claim
from app.models.patient import Patient
from app.services.claim_workflow import assess_claim
from app.services.claim_status import transition
from app.core.config import settings


logger = logging.getLogger(__name__)


def recover_pending_claims(limit: int = 100) -> int:
    """Resume durable workflow checkpoints. Safe to call repeatedly."""
    db = SessionLocal()
    recovered = 0
    try:
        claims = db.query(Claim).filter(
            (Claim.status.in_(["PENDING_RULES", "PENDING_FRAUD"])) |
            ((Claim.status == "FAILED_ASSESSMENT") & (Claim.assessment_attempts < settings.RECOVERY_MAX_ATTEMPTS) & (Claim.next_retry_at <= datetime.utcnow()))
        ).order_by(Claim.id).limit(limit).all()
        for claim in claims:
            try:
                if claim.status == "FAILED_ASSESSMENT":
                    transition(db, claim, "PENDING_RULES", "SCHEDULED_RETRY")
                assess_claim(db, claim, db.get(Patient, claim.patient_id))
                recovered += 1
            except Exception:
                db.rollback()
                logger.exception("claim_recovery_failed", extra={"claim_id": claim.id})
        return recovered
    finally:
        db.close()
