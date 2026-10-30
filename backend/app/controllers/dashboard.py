"""Controller HTTP: dashboard."""
from fastapi import APIRouter, Depends
from ..database import db_session
from ..core.security import current
from ..repositories.sql_repository import dashboard_summary
router = APIRouter(tags=["Indicadores"])

@router.get('/dashboard/resumo')
def dashboard(u=Depends(current), db=Depends(db_session)):
    return dashboard_summary(db, u)
