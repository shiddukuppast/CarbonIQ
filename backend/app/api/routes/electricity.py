from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Query, status
from app.api.dependencies import get_current_user, get_current_workspace_id, get_db_dep
from app.schemas.electricity import (
    ElectricityCreateRequest,
    ElectricityRecordResponse,
    ElectricitySummaryResponse,
    ElectricityUpdateRequest,
)
from app.services.electricity_service import (
    create_electricity_record,
    delete_electricity_record,
    get_electricity_record,
    get_electricity_summary,
    list_electricity_records,
    update_electricity_record,
)

router = APIRouter(prefix="/electricity", tags=["Electricity Management"])


@router.get("", response_model=List[ElectricityRecordResponse])
async def get_records(
    month: Optional[str] = Query(None, description="Filter by reporting month YYYY-MM"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    workspace_id: str = Depends(get_current_workspace_id),
    db: Any = Depends(get_db_dep),
) -> List[ElectricityRecordResponse]:
    """Retrieves all electricity records belonging to the authenticated user's workspace."""
    return await list_electricity_records(workspace_id, db, month=month, skip=skip, limit=limit)


@router.post("", response_model=ElectricityRecordResponse, status_code=status.HTTP_201_CREATED)
async def create_record(
    req: ElectricityCreateRequest,
    workspace_id: str = Depends(get_current_workspace_id),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Any = Depends(get_db_dep),
) -> ElectricityRecordResponse:
    """Creates a new electricity consumption record and calculates verified emissions."""
    return await create_electricity_record(req, workspace_id, current_user["id"], db)


@router.get("/summary", response_model=ElectricitySummaryResponse)
async def get_summary(
    workspace_id: str = Depends(get_current_workspace_id),
    db: Any = Depends(get_db_dep),
) -> ElectricitySummaryResponse:
    """Calculates aggregate electricity consumption, bills, emissions, and trends."""
    return await get_electricity_summary(workspace_id, db)


@router.get("/{record_id}", response_model=ElectricityRecordResponse)
async def get_record(
    record_id: str,
    workspace_id: str = Depends(get_current_workspace_id),
    db: Any = Depends(get_db_dep),
) -> ElectricityRecordResponse:
    """Retrieves a single electricity record by ID."""
    return await get_electricity_record(record_id, workspace_id, db)


@router.put("/{record_id}", response_model=ElectricityRecordResponse)
async def update_record(
    record_id: str,
    req: ElectricityUpdateRequest,
    workspace_id: str = Depends(get_current_workspace_id),
    db: Any = Depends(get_db_dep),
) -> ElectricityRecordResponse:
    """Updates an existing electricity record and recalculates emissions."""
    return await update_electricity_record(record_id, req, workspace_id, db)


@router.delete("/{record_id}", status_code=status.HTTP_200_OK)
async def delete_record(
    record_id: str,
    workspace_id: str = Depends(get_current_workspace_id),
    db: Any = Depends(get_db_dep),
) -> Dict[str, bool]:
    """Deletes an electricity record belonging to the authorized workspace."""
    await delete_electricity_record(record_id, workspace_id, db)
    return {"success": True}
