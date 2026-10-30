from typing import Any
from fastapi import APIRouter, Depends, Query
from app.api.dependencies import get_current_workspace_id, get_db_dep
from app.schemas.reports import EmissionsReportResponse
from app.services.report_service import generate_emissions_report

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("/emissions", response_model=EmissionsReportResponse)
async def get_emissions_report(
    period: str = Query("2026-YTD", description="Reporting period filter"),
    workspace_id: str = Depends(get_current_workspace_id),
    db: Any = Depends(get_db_dep),
) -> EmissionsReportResponse:
    """Generates an audit-ready emissions summary report calculated from workspace records."""
    return await generate_emissions_report(workspace_id, db, period=period)
