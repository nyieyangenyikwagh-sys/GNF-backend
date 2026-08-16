from datetime import date
from pydantic import BaseModel, EmailStr, Field
class InsuranceIn(BaseModel): payer_id:str; member_id:str; health_card_number:str|None=None; group_number:str|None=None; effective_date:date; termination_date:date|None=None; priority:str="primary"
class PatientCreate(BaseModel):
    first_name:str=Field(min_length=2); last_name:str=Field(min_length=2); dob:date; gender:str; province:str="AB"; phone:str|None=None; email:EmailStr|None=None; address_line1:str|None=None; city:str|None=None; postal_code:str|None=None; insurance:InsuranceIn
class PatientOut(BaseModel):
    id:int; first_name:str; last_name:str; province:str
    model_config={"from_attributes":True}
