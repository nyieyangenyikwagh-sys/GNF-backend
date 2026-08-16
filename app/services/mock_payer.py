import random,time
from datetime import datetime,timezone
from app.schemas.insurance import EligibilityResponse,Copay,Deductible
SCENARIOS={"TERM":"COVERAGE_TERMINATED","OON":"OUT_OF_NETWORK","PEND":"COVERAGE_PENDING","INACT":"INACTIVE_PLAN"}
def check_eligibility(member_id,payer_id,plan_name,plan_type):
 start=time.perf_counter(); time.sleep(random.uniform(.2,.6)); reason=next((v for k,v in SCENARIOS.items() if member_id.upper().startswith(k)),None); base=dict(member_id=member_id,payer_id=payer_id,plan_name=plan_name if not reason else "N/A",plan_type=plan_type if not reason else "N/A",copay=Copay(primary=25 if not reason else 0,specialist=50 if not reason else 0,er=250 if not reason else 0),deductible=Deductible(individual=500 if not reason else 0,family=1500 if not reason else 0,met=120 if not reason else 0),coinsurance=.2 if not reason else 0,out_of_pocket_max=3000 if not reason else 0,verified_at=datetime.now(timezone.utc),response_latency_ms=0)
 resp=EligibilityResponse(eligible=not bool(reason),reason=reason,prior_auth_required=["MRI","27447"] if not reason else [],**base);resp.response_latency_ms=int((time.perf_counter()-start)*1000);return resp
