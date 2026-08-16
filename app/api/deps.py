from fastapi import Depends,HTTPException,status
from fastapi.security import OAuth2PasswordBearer
from app.core.database import get_db
from app.core.security import decode_token
from app.models.user import User
oauth2_scheme=OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")
def get_current_user(token=Depends(oauth2_scheme),db=Depends(get_db)):
 payload=decode_token(token);user=db.query(User).filter(User.email==payload.get('sub')).first() if payload else None
 if not user or not user.is_active:raise HTTPException(status.HTTP_401_UNAUTHORIZED,"Invalid or expired token")
 return user
def require_role(*roles):
 def checker(user=Depends(get_current_user)):
  if user.role not in roles:raise HTTPException(status.HTTP_403_FORBIDDEN,"Insufficient role")
  return user
 return checker
