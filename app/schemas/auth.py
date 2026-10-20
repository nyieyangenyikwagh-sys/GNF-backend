from typing import Literal

from pydantic import BaseModel, EmailStr, Field

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role: Literal["claimant"] = "claimant"
class UserOut(BaseModel):
    id:int; email:EmailStr; role:str
    model_config={"from_attributes":True}
class Token(BaseModel): access_token:str; token_type:str="bearer"
