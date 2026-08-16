from datetime import datetime
from pydantic import BaseModel
class EligibilityRequest(BaseModel): patient_insurance_id:int
class Copay(BaseModel): primary:float; specialist:float; er:float
class Deductible(BaseModel): individual:float; family:float; met:float
class EligibilityResponse(BaseModel):
    eligible:bool; reason:str|None=None; member_id:str; payer_id:str; plan_name:str; plan_type:str; copay:Copay; deductible:Deductible; coinsurance:float; out_of_pocket_max:float; prior_auth_required:list[str]=[]; verified_at:datetime; response_latency_ms:int
