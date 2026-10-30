from typing import Any, Dict, List
from fastapi import APIRouter, Depends, Query, status
from app.api.dependencies import get_current_user, get_current_workspace_id, get_db_dep
from app.schemas.waste import (
    WasteCreateRequest,
    WasteRecordResponse,
    WasteSummaryResponse,
    WasteUpdateRequest,
)
from app.services.waste_service import (
    create_waste_record,
    delete_waste_record,
    get_waste_record,
    get_waste_summary,
    list_waste_records,
    update_waste_record,
)

router = APIRouter(prefix="/waste", tags=["Waste Management"])


@router.get("", response_model=List[WasteRecordResponse])
async def get_records(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    workspace_id: str = Depends(get_current_workspace_id),
    db: Any = Depends(get_db_dep),
) -> List[WasteRecordResponse]:
    """Retrieves waste management records for the authenticated workspace."""
    return await list_waste_records(workspace_id, db, skip=skip, limit=limit)


@router.post("", response_model=WasteRecordResponse, status_code=status.HTTP_201_CREATED)
async def create_record(
    req: WasteCreateRequest,
    workspace_id: str = Depends(get_current_workspace_id),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Any = Depends(get_db_dep),
) -> WasteRecordResponse:
    """Logs a new waste record and calculates net emissions or recycling credits."""
    return await create_waste_record(req, workspace_id, current_user["id"], db)


@router.get("/summary", response_model=WasteSummaryResponse)
async def get_summary(
    workspace_id: str = Depends(get_current_workspace_id),
    db: Any = Depends(get_db_dep),
) -> WasteSummaryResponse:
    """Calculates total waste, recycling recovery rate, category breakdown, and net emissions."""
    return await get_waste_summary(workspace_id, db)


@router.get("/{record_id}", response_model=WasteRecordResponse)
async def get_record(
    record_id: str,
    workspace_id: str = Depends(get_current_workspace_id),
    db: Any = Depends(get_db_dep),
) -> WasteRecordResponse:
    """Retrieves a single waste record by ID."""
    return await get_waste_record(record_id, workspace_id, db)


@router.put("/{record_id}", response_model=WasteRecordResponse)
async def update_record(
    record_id: str,
    req: WasteUpdateRequest,
    workspace_id: str = Depends(get_current_workspace_id),
    db: Any = Depends(get_db_dep),
) -> WasteRecordResponse:
    """Updates a waste record and recalculates treatment emissions."""
    return await update_waste_record(record_id, req, workspace_id, db)


@router.delete("/{record_id}", status_code=status.HTTP_200_OK)
async def delete_record(
    record_id: str,
    workspace_id: str = Depends(get_current_workspace_id),
    db: Any = Depends(get_db_dep),
) -> Dict[str, bool]:
    """Deletes a waste record."""
    await delete_waste_record(record_id, workspace_id, db)
    return {"success": True}
