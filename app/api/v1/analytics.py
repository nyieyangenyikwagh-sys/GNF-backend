from fastapi import APIRouter,Depends
from app.api.deps import require_role
from app.core.database import get_db
from app.schemas.analytics import AnalyticsSummary
from app.services.analytics import build_summary
router=APIRouter(prefix='/analytics',tags=['analytics'])
@router.get('/summary',response_model=AnalyticsSummary)
def summary(db=Depends(get_db),user=Depends(require_role('admin','analyst'))):return build_summary(db)
