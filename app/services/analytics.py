import pandas as pd
from app.models.claim import Claim,ClaimStatusHistory
from app.models.appeal import Appeal
from app.models.insurance import InsurancePlan
from app.schemas.analytics import AnalyticsSummary,DenialByPayer
def build_summary(db):
 claims=db.query(Claim).all();plans={p.id:p.payer_id for p in db.query(InsurancePlan).all()};df=pd.DataFrame([{'payer_id':plans.get(c.plan_id,'UNKNOWN'),'status':c.status,'denial_reason_code':c.denial_reason_code} for c in claims]);out=[];reasons={}
 if not df.empty:
  for payer,g in df.groupby('payer_id'):
   total=len(g);denied=int(g.status.isin(['denied','rejected']).sum());out.append(DenialByPayer(payer_id=payer,total=total,denied=denied,denial_rate=round(denied/total,3)))
  reasons={str(k):int(v) for k,v in df.denial_reason_code.dropna().value_counts().head(5).to_dict().items()}
 resolved=[x for x in db.query(Appeal).all() if x.outcome in ('approved','upheld')];rate=round(sum(x.outcome=='approved' for x in resolved)/len(resolved),3) if resolved else 0.0
 return AnalyticsSummary(denial_rate_by_payer=out,top_denial_reasons=reasons,appeal_success_rate=rate,avg_days_to_payment=None)
