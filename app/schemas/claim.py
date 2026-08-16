from datetime import date
from pydantic import BaseModel
class ClaimLineIn(BaseModel): service_code:str; diagnosis_code:str; units:int=1; amount:float
class ClaimCreate(BaseModel): patient_id:int; plan_id:int; province:str="AB"; provider_billing_number:str; service_date:date; lines:list[ClaimLineIn]
class ClaimLineOut(ClaimLineIn):
    id:int
    model_config={"from_attributes":True}
class ClaimOut(BaseModel):
    id:int; status:str; province:str; billed_amount:float; denial_reason_code:str|None; lines:list[ClaimLineOut]
    model_config={"from_attributes":True}
class StatusChange(BaseModel): to_status:str; reason_code:str|None=None
