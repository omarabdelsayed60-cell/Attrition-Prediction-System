from typing import List, Dict, Any
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from src.api.schemas import DashboardSummaryResponse
from src.database.connection import get_db
from src.services.dashboard_service import DashboardService
from src.utils.logger import logger

router = APIRouter(prefix="/api/v1", tags=["Analytics & History"])

@router.get(
    "/dashboard",
    response_model=DashboardSummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Executive Dashboard Summary",
    description="Returns aggregate KPI metrics, total employee count, overall attrition rate, risk counts, and department breakdown."
)
def get_dashboard_summary(db: Session = Depends(get_db)):
    """Handles executive dashboard statistics query."""
    service = DashboardService(db)
    return service.get_dashboard_metrics()

@router.get(
    "/history",
    response_model=List[Dict[str, Any]],
    status_code=status.HTTP_200_OK,
    summary="Get Prediction Audit Logs",
    description="Fetches historical prediction records joined with SHAP factors and generated HR recommendations."
)
def get_prediction_history(
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db)
):
    """Handles historical predictions query."""
    service = DashboardService(db)
    return service.get_prediction_history(limit=limit, offset=offset)

@router.get(
    "/employees",
    response_model=List[Dict[str, Any]],
    status_code=status.HTTP_200_OK,
    summary="Get Employees Master List",
    description="Fetches employee records from database master table."
)
def get_employees_list(
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db)
):
    """Handles employee master database query."""
    service = DashboardService(db)
    return service.get_employees(limit=limit, offset=offset)
