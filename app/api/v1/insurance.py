from fastapi import APIRouter,Depends,HTTPException
from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.insurance import PatientInsurance
from app.schemas.insurance import EligibilityRequest,EligibilityResponse
from app.services.eligibility import verify_eligibility,reverify_eligibility
router=APIRouter(prefix='/insurance',tags=['insurance'])
def _authorize(db,insurance_id,user):
 if user.role in {'auditor','analyst'}:raise HTTPException(403,'Read-only role cannot verify insurance')
 ins=db.get(PatientInsurance,insurance_id)
 if not ins or (user.role not in {'adjuster','supervisor','admin','service'} and ins.patient.owner_user_id!=user.id):raise HTTPException(404,'Patient insurance not found')
@router.post('/verify',response_model=EligibilityResponse)
def verify(x:EligibilityRequest,db=Depends(get_db),user=Depends(get_current_user)):_authorize(db,x.patient_insurance_id,user);return verify_eligibility(db,x.patient_insurance_id)
@router.post('/reverify',response_model=EligibilityResponse)
def reverify(x:EligibilityRequest,db=Depends(get_db),user=Depends(get_current_user)):_authorize(db,x.patient_insurance_id,user);return reverify_eligibility(db,x.patient_insurance_id)
