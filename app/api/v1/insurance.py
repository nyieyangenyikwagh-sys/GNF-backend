from fastapi import APIRouter,Depends
from app.api.deps import get_current_user
from app.core.database import get_db
from app.schemas.insurance import EligibilityRequest,EligibilityResponse
from app.services.eligibility import verify_eligibility,reverify_eligibility
router=APIRouter(prefix='/insurance',tags=['insurance'])
@router.post('/verify',response_model=EligibilityResponse)
def verify(x:EligibilityRequest,db=Depends(get_db),user=Depends(get_current_user)):return verify_eligibility(db,x.patient_insurance_id)
@router.post('/reverify',response_model=EligibilityResponse)
def reverify(x:EligibilityRequest,db=Depends(get_db),user=Depends(get_current_user)):return reverify_eligibility(db,x.patient_insurance_id)
