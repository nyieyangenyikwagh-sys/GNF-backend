from fastapi import APIRouter,Depends,HTTPException
from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.claim import Claim,ClaimLine
from app.models.patient import Patient
from app.models.insurance import PatientInsurance
from app.schemas.claim import ClaimCreate,ClaimOut,StatusChange
from app.services.eligibility import assert_eligible
from app.services.rule_engine import ClaimContext,run_rules
from app.services.claim_status import transition
from app.services.provincial.registry import get_engine
router=APIRouter(prefix='/claims',tags=['claims'])
@router.post('',response_model=ClaimOut,status_code=201)
def create_claim(p:ClaimCreate,db=Depends(get_db),user=Depends(get_current_user)):
 patient=db.get(Patient,p.patient_id)
 if not patient:raise HTTPException(404,'Patient not found')
 snapshot=assert_eligible(db,p.patient_id,p.plan_id);ins=db.query(PatientInsurance).filter(PatientInsurance.patient_id==p.patient_id,PatientInsurance.plan_id==p.plan_id).first();claim=Claim(patient_id=p.patient_id,plan_id=p.plan_id,province=p.province,provider_billing_number=p.provider_billing_number,service_date=p.service_date,billed_amount=sum(x.amount*x.units for x in p.lines),coverage_snapshot=snapshot,status='draft');db.add(claim);db.flush()
 for x in p.lines:db.add(ClaimLine(claim_id=claim.id,**x.model_dump()))
 db.commit();db.refresh(claim);errors=run_rules(ClaimContext(p.province,p.provider_billing_number,p.service_date,ins.health_card_number if ins else None,patient.province,[x.model_dump() for x in p.lines]))
 if errors:transition(db,claim,'submitted');transition(db,claim,'rejected',errors[0].code);raise HTTPException(422,{'message':'Claim rejected by rule engine','errors':[x.__dict__ for x in errors],'claim_id':claim.id})
 get_engine(p.province).format_submission(claim);return transition(db,claim,'submitted')
@router.get('/{claim_id}',response_model=ClaimOut)
def get_claim(claim_id:int,db=Depends(get_db),user=Depends(get_current_user)):
 c=db.get(Claim,claim_id)
 if not c:raise HTTPException(404,'Claim not found')
 return c
@router.post('/{claim_id}/status',response_model=ClaimOut)
def change_status(claim_id:int,x:StatusChange,db=Depends(get_db),user=Depends(get_current_user)):return transition(db,db.get(Claim,claim_id),x.to_status,x.reason_code)
