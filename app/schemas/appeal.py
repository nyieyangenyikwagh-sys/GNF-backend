from pydantic import BaseModel
class AppealCreate(BaseModel): claim_id:int; note:str|None=None; supporting_doc_url:str|None=None
class AppealOut(BaseModel):
    id:int; claim_id:int; outcome:str
    model_config={"from_attributes":True}
