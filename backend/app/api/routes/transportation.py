from typing import Any, Dict, List
from fastapi import APIRouter, Depends, Query, status
from app.api.dependencies import get_current_user, get_current_workspace_id, get_db_dep
from app.schemas.transportation import (
    TransportationCreateRequest,
    TransportationRecordResponse,
    TransportationSummaryResponse,
    TransportationUpdateRequest,
)
from app.services.transportation_service import (
    create_transportation_record,
    delete_transportation_record,
    get_transportation_record,
    get_transportation_summary,
    list_transportation_records,
    update_transportation_record,
)

router = APIRouter(prefix="/transportation", tags=["Transportation Management"])


@router.get("", response_model=List[TransportationRecordResponse])
async def get_records(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    workspace_id: str = Depends(get_current_workspace_id),
    db: Any = Depends(get_db_dep),
) -> List[TransportationRecordResponse]:
    """Retrieves all transportation activity records for the authenticated workspace."""
    return await list_transportation_records(workspace_id, db, skip=skip, limit=limit)


@router.post("", response_model=TransportationRecordResponse, status_code=status.HTTP_201_CREATED)
async def create_record(
    req: TransportationCreateRequest,
    workspace_id: str = Depends(get_current_workspace_id),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Any = Depends(get_db_dep),
) -> TransportationRecordResponse:
    """Logs a new travel record and calculates emissions using verified method boundaries."""
    return await create_transportation_record(req, workspace_id, current_user["id"], db)


@router.get("/summary", response_model=TransportationSummaryResponse)
async def get_summary(
    workspace_id: str = Depends(get_current_workspace_id),
    db: Any = Depends(get_db_dep),
) -> TransportationSummaryResponse:
    """Returns aggregated distance, fuel consumption, expenditure, and emissions metrics."""
    return await get_transportation_summary(workspace_id, db)


@router.get("/{record_id}", response_model=TransportationRecordResponse)
async def get_record(
    record_id: str,
    workspace_id: str = Depends(get_current_workspace_id),
    db: Any = Depends(get_db_dep),
) -> TransportationRecordResponse:
    """Retrieves a single transportation record by ID."""
    return await get_transportation_record(record_id, workspace_id, db)


@router.put("/{record_id}", response_model=TransportationRecordResponse)
async def update_record(
    record_id: str,
    req: TransportationUpdateRequest,
    workspace_id: str = Depends(get_current_workspace_id),
    db: Any = Depends(get_db_dep),
) -> TransportationRecordResponse:
    """Updates a transportation record and recalculates emissions."""
    return await update_transportation_record(record_id, req, workspace_id, db)


@router.delete("/{record_id}", status_code=status.HTTP_200_OK)
async def delete_record(
    record_id: str,
    workspace_id: str = Depends(get_current_workspace_id),
    db: Any = Depends(get_db_dep),
) -> Dict[str, bool]:
    """Deletes a transportation record."""
    await delete_transportation_record(record_id, workspace_id, db)
    return {"success": True}
