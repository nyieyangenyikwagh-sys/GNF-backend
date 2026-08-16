from pydantic import BaseModel, EmailStr
class UserCreate(BaseModel): email: EmailStr; password: str; role: str="biller"
class UserOut(BaseModel):
    id:int; email:EmailStr; role:str
    model_config={"from_attributes":True}
class Token(BaseModel): access_token:str; token_type:str="bearer"
