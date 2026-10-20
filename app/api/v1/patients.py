from fastapi import APIRouter,Depends,HTTPException
from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.patient import Patient
from app.models.insurance import InsurancePlan,PatientInsurance
from app.schemas.patient import PatientCreate,PatientOut
from app.services.eligibility import verify_eligibility
router=APIRouter(prefix="/patients",tags=["patients"])
@router.post("",status_code=201)
def create_patient(p:PatientCreate,db=Depends(get_db),user=Depends(get_current_user)):
 if user.role not in {'claimant','biller','adjuster','supervisor','admin','service'}:raise HTTPException(403,'Role cannot create patients')
 plan=db.query(InsurancePlan).filter(InsurancePlan.payer_id==p.insurance.payer_id).first()
 if not plan:raise HTTPException(400,f"Unknown payer {p.insurance.payer_id}")
 patient=Patient(owner_user_id=user.id,**p.model_dump(exclude={'insurance'}));db.add(patient);db.flush();ins=PatientInsurance(patient_id=patient.id,plan_id=plan.id,**p.insurance.model_dump());db.add(ins);db.commit();db.refresh(ins);return {"patient_id":patient.id,"patient_insurance_id":ins.id,"eligibility":verify_eligibility(db,ins.id).model_dump()}
@router.get('/{patient_id}',response_model=PatientOut)
def get_patient(patient_id:int,db=Depends(get_db),user=Depends(get_current_user)):
 p=db.get(Patient,patient_id)
 if not p or (user.role not in {'adjuster','supervisor','auditor','admin','service'} and p.owner_user_id!=user.id):raise HTTPException(404,'Patient not found')
 return p
