from datetime import datetime
from fastapi import APIRouter,Depends,HTTPException
from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.appeal import Appeal
from app.models.claim import Claim
from app.schemas.appeal import AppealCreate,AppealOut
from app.services.claim_status import transition
router=APIRouter(prefix='/appeals',tags=['appeals'])
@router.post('',response_model=AppealOut,status_code=201)
def file_appeal(p:AppealCreate,db=Depends(get_db),user=Depends(get_current_user)):
 c=db.get(Claim,p.claim_id)
 if not c:raise HTTPException(404,'Claim not found')
 if c.status!='denied':raise HTTPException(409,'Only denied claims can be appealed')
 a=Appeal(claim_id=c.id,denial_reason_code=c.denial_reason_code or 'UNKNOWN',note=p.note,supporting_doc_url=p.supporting_doc_url,outcome='pending');db.add(a);transition(db,c,'appeal_pending',c.denial_reason_code);db.commit();db.refresh(a);return a
@router.post('/{appeal_id}/resolve',response_model=AppealOut)
def resolve_appeal(appeal_id:int,approve:bool,db=Depends(get_db),user=Depends(get_current_user)):
 a=db.get(Appeal,appeal_id)
 if not a:raise HTTPException(404,'Appeal not found')
 a.outcome='approved' if approve else 'upheld';a.resolved_at=datetime.utcnow();transition(db,db.get(Claim,a.claim_id),'paid' if approve else 'closed',None if approve else 'APPEAL_UPHELD');db.add(a);db.commit();db.refresh(a);return a
