from pydantic import BaseModel
class PaymentCreate(BaseModel): claim_id:int; era_number:str; eob_reference:str|None=None; paid_amount:float; remittance:str|None=None
class PaymentOut(BaseModel):
    id:int; claim_id:int; paid_amount:float; underpaid:bool
    model_config={"from_attributes":True}
