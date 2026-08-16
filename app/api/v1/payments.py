from fastapi import APIRouter,Depends,HTTPException
from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.claim import Claim
from app.models.payment import Payment
from app.schemas.payment import PaymentCreate,PaymentOut
from app.services.reconciliation import is_underpaid
from app.services.claim_status import transition
router=APIRouter(prefix='/payments',tags=['payments'])
@router.post('',response_model=PaymentOut,status_code=201)
def post_payment(p:PaymentCreate,db=Depends(get_db),user=Depends(get_current_user)):
 c=db.get(Claim,p.claim_id)
 if not c:raise HTTPException(404,'Claim not found')
 x=Payment(**p.model_dump(),underpaid=is_underpaid(c,p.paid_amount));db.add(x)
 if c.status=='submitted':transition(db,c,'paid')
 db.commit();db.refresh(x);return x
