from typing import Any, List
from fastapi import APIRouter, Depends, status
from app.api.dependencies import get_current_workspace_id, get_db_dep
from app.schemas.progress import (
    GoalCreateRequest,
    GoalResponse,
    InterventionCreateRequest,
    InterventionResponse,
)
from app.services.progress_service import (
    create_goal,
    create_intervention,
    list_goals,
    list_interventions,
)

router = APIRouter(prefix="/progress", tags=["Progress & Interventions"])


@router.get("/goals", response_model=List[GoalResponse])
async def get_goals(
    workspace_id: str = Depends(get_current_workspace_id),
    db: Any = Depends(get_db_dep),
) -> List[GoalResponse]:
    """Retrieves all sustainability goals for the workspace."""
    return await list_goals(workspace_id, db)


@router.post("/goals", response_model=GoalResponse, status_code=status.HTTP_201_CREATED)
async def add_goal(
    req: GoalCreateRequest,
    workspace_id: str = Depends(get_current_workspace_id),
    db: Any = Depends(get_db_dep),
) -> GoalResponse:
    """Creates a new quantifiable sustainability goal."""
    return await create_goal(req, workspace_id, db)


@router.get("/interventions", response_model=List[InterventionResponse])
async def get_interventions(
    workspace_id: str = Depends(get_current_workspace_id),
    db: Any = Depends(get_db_dep),
) -> List[InterventionResponse]:
    """Retrieves planned interventions (such as accepted route optimizations)."""
    return await list_interventions(workspace_id, db)


@router.post("/interventions", response_model=InterventionResponse, status_code=status.HTTP_201_CREATED)
async def add_intervention(
    req: InterventionCreateRequest,
    workspace_id: str = Depends(get_current_workspace_id),
    db: Any = Depends(get_db_dep),
) -> InterventionResponse:
    """Logs a planned sustainability intervention."""
    return await create_intervention(req, workspace_id, db)
