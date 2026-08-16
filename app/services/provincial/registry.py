from fastapi import HTTPException
from app.services.provincial.ahs import AHSEngine
from app.services.provincial.greenshield import GreenShieldEngine
_ENGINES={"AB":AHSEngine(),"GREENSHIELD":GreenShieldEngine()}
def get_engine(province):
 if province not in _ENGINES:raise HTTPException(400,f"No billing engine for {province}")
 return _ENGINES[province]
