from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from fastapi.security import OAuth2PasswordRequestForm
from app.core.database import get_db
from app.core.security import hash_password,verify_password,create_access_token
from app.models.user import User
from app.schemas.auth import UserCreate,UserOut,Token
router=APIRouter(prefix="/auth",tags=["auth"])
@router.post("/register",response_model=UserOut,status_code=201)
def register(payload:UserCreate,db=Depends(get_db)):
 if db.query(User).filter(User.email==payload.email).first():raise HTTPException(409,"Email already registered")
 u=User(email=payload.email,hashed_password=hash_password(payload.password),role=payload.role);db.add(u)
 try:
  db.commit()
 except IntegrityError:
  db.rollback()
  raise HTTPException(409,"Email already registered")
 db.refresh(u);return u
@router.post("/login",response_model=Token)
def login(form:OAuth2PasswordRequestForm=Depends(),db=Depends(get_db)):
 u=db.query(User).filter(User.email==form.username).first()
 if not u or not verify_password(form.password,u.hashed_password):raise HTTPException(status.HTTP_401_UNAUTHORIZED,"Bad credentials")
 return Token(access_token=create_access_token(u.email,u.role))
