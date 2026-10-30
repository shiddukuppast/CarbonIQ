from typing import Any
from fastapi import APIRouter, Depends
from app.api.dependencies import get_current_workspace_id, get_db_dep
from app.schemas.dashboard import DashboardSummaryResponse, DashboardTrendsResponse
from app.services.dashboard_service import get_dashboard_summary, get_dashboard_trends

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/summary", response_model=DashboardSummaryResponse)
async def summary(
    workspace_id: str = Depends(get_current_workspace_id),
    db: Any = Depends(get_db_dep),
) -> DashboardSummaryResponse:
    """Calculates overall emissions, module metrics, and breakdown from workspace records."""
    return await get_dashboard_summary(workspace_id, db)


@router.get("/trends", response_model=DashboardTrendsResponse)
async def trends(
    workspace_id: str = Depends(get_current_workspace_id),
    db: Any = Depends(get_db_dep),
) -> DashboardTrendsResponse:
    """Returns combined monthly emissions and cost progression trends."""
    return await get_dashboard_trends(workspace_id, db)
