from datetime import datetime
from fastapi import HTTPException
from app.models.claim import Claim,ClaimStatusHistory
ALLOWED_TRANSITIONS={"draft":{"submitted"},"submitted":{"paid","denied","rejected"},"denied":{"appeal_pending"},"appeal_pending":{"paid","closed"},"rejected":{"submitted"},"paid":set(),"closed":set()}
def transition(db,claim,to_status,reason_code=None):
 if to_status not in ALLOWED_TRANSITIONS.get(claim.status,set()):raise HTTPException(409,f"Illegal transition {claim.status} -> {to_status}")
 db.add(ClaimStatusHistory(claim_id=claim.id,from_status=claim.status,to_status=to_status,reason_code=reason_code,created_at=datetime.utcnow()));claim.status=to_status
 if reason_code and to_status in {'denied','rejected'}:claim.denial_reason_code=reason_code
 db.commit();db.refresh(claim);return claim
