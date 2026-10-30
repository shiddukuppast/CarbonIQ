from typing import Any, Dict, List, Optional, Union
from fastapi import APIRouter, Body, Depends, Query, status
from app.api.dependencies import get_current_user, get_current_workspace_id, get_db_dep, require_fleet_access
from app.calculations.route_optimizer import RouteOptimizationProposal
from app.schemas.bus_route import (
    BusRouteCreateRequest,
    BusRouteResponse,
    BusRouteUpdateRequest,
    RouteOptimizationRequest,
    RouteOptimizationResponse,
)
from app.services.bus_route_service import (
    create_bus_route,
    delete_bus_route,
    get_bus_route,
    list_bus_routes,
    optimize_workspace_bus_routes,
    save_proposal_as_intervention,
    update_bus_route,
)

router = APIRouter(prefix="/transportation", tags=["Bus Route Management & Optimization"])


@router.get("/routes", response_model=List[BusRouteResponse])
async def get_routes(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    current_user: Dict[str, Any] = Depends(require_fleet_access),
    db: Any = Depends(get_db_dep),
) -> List[BusRouteResponse]:
    """Retrieves all registered bus routes in the workspace."""
    return await list_bus_routes(current_user["workspace_id"], db, skip=skip, limit=limit)


@router.post("/routes", response_model=BusRouteResponse, status_code=status.HTTP_201_CREATED)
async def create_route(
    req: BusRouteCreateRequest,
    current_user: Dict[str, Any] = Depends(require_fleet_access),
    db: Any = Depends(get_db_dep),
) -> BusRouteResponse:
    """Creates a new bus route with student demand and vehicle capacity constraints."""
    return await create_bus_route(req, current_user["workspace_id"], current_user["id"], db)


@router.post("/optimize", response_model=RouteOptimizationResponse)
async def optimize_routes(
    payload: Optional[Union[RouteOptimizationRequest, List[str]]] = Body(None),
    route_ids: Optional[List[str]] = Query(None),
    current_user: Dict[str, Any] = Depends(require_fleet_access),
    db: Any = Depends(get_db_dep),
) -> RouteOptimizationResponse:
    """
    Evaluates candidate bus routes for feasible consolidation opportunities.
    Considers student demand, seating capacity, and shared corridors.
    """
    target_ids = None
    if isinstance(payload, list):
        target_ids = payload
    elif isinstance(payload, RouteOptimizationRequest) and payload.route_ids is not None:
        target_ids = payload.route_ids
    elif route_ids is not None:
        target_ids = route_ids

    return await optimize_workspace_bus_routes(current_user["workspace_id"], db, route_ids=target_ids)


@router.post("/optimize/accept", status_code=status.HTTP_201_CREATED)
async def accept_proposal(
    proposal: RouteOptimizationProposal,
    current_user: Dict[str, Any] = Depends(require_fleet_access),
    db: Any = Depends(get_db_dep),
) -> Dict[str, Any]:
    """
    Saves an optimization proposal as a planned intervention.
    Does NOT alter real bus schedules or assign students automatically.
    """
    return await save_proposal_as_intervention(proposal, current_user["workspace_id"], current_user["id"], db)


@router.get("/routes/{route_id}", response_model=BusRouteResponse)
async def get_route(
    route_id: str,
    workspace_id: str = Depends(get_current_workspace_id),
    db: Any = Depends(get_db_dep),
) -> BusRouteResponse:
    """Retrieves a single bus route by ID."""
    return await get_bus_route(route_id, workspace_id, db)


@router.put("/routes/{route_id}", response_model=BusRouteResponse)
async def update_route(
    route_id: str,
    req: BusRouteUpdateRequest,
    workspace_id: str = Depends(get_current_workspace_id),
    db: Any = Depends(get_db_dep),
) -> BusRouteResponse:
    """Updates a bus route's parameters or status."""
    return await update_bus_route(route_id, req, workspace_id, db)


@router.delete("/routes/{route_id}", status_code=status.HTTP_200_OK)
async def delete_route(
    route_id: str,
    workspace_id: str = Depends(get_current_workspace_id),
    db: Any = Depends(get_db_dep),
) -> Dict[str, bool]:
    """Deletes a bus route from the workspace."""
    await delete_bus_route(route_id, workspace_id, db)
    return {"success": True}
