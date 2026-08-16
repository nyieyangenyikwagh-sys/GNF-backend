from datetime import datetime,timedelta,timezone
from fastapi import HTTPException
from app.models.insurance import PatientInsurance,InsurancePlan
from app.services.cache import cache
from app.services.mock_payer import check_eligibility
VERIFY_TTL=3600;GUARD_MAX_AGE_HOURS=24
def _cache_key(i):return f"eligibility:{i}"
def verify_eligibility(db,insurance_id):
 ins=db.get(PatientInsurance,insurance_id)
 if not ins:raise HTTPException(404,"Patient insurance not found")
 cached=cache.get(_cache_key(insurance_id))
 if cached:return __import__('app.schemas.insurance',fromlist=['EligibilityResponse']).EligibilityResponse(**cached)
 plan=db.get(InsurancePlan,ins.plan_id);resp=check_eligibility(ins.member_id,plan.payer_id,plan.name,plan.plan_type or "N/A");ins.last_verified_at=resp.verified_at;ins.last_eligibility=resp.model_dump(mode="json");db.commit();cache.set(_cache_key(insurance_id),resp.model_dump(mode="json"),VERIFY_TTL);return resp
def reverify_eligibility(db,insurance_id):cache.delete(_cache_key(insurance_id));return verify_eligibility(db,insurance_id)
def assert_eligible(db,patient_id,plan_id):
 ins=db.query(PatientInsurance).filter(PatientInsurance.patient_id==patient_id,PatientInsurance.plan_id==plan_id).first()
 if not ins or not ins.last_verified_at or not ins.last_eligibility:raise HTTPException(422,"No verified coverage for this patient/plan")
 at=ins.last_verified_at.replace(tzinfo=timezone.utc) if ins.last_verified_at.tzinfo is None else ins.last_verified_at
 if at<datetime.now(timezone.utc)-timedelta(hours=GUARD_MAX_AGE_HOURS):raise HTTPException(422,"Coverage verification is stale - re-verify")
 if not ins.last_eligibility.get("eligible"):raise HTTPException(422,"Patient is not eligible - claim blocked")
 return ins.last_eligibility
