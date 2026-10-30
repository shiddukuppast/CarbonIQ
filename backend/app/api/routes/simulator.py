from typing import Any
from fastapi import APIRouter, Depends
from app.api.dependencies import get_current_workspace_id, get_db_dep
from app.calculations.savings_calculator import SimulatorProjectionResult
from app.schemas.simulator import ElectricitySimRequest, TransportSimRequest, WasteSimRequest
from app.services.simulator_service import (
    run_electricity_simulation,
    run_transportation_simulation,
    run_waste_simulation,
)

router = APIRouter(prefix="/simulator", tags=["Savings Simulator"])


@router.post("/electricity", response_model=SimulatorProjectionResult)
async def simulate_electricity(
    req: ElectricitySimRequest,
    workspace_id: str = Depends(get_current_workspace_id),
    db: Any = Depends(get_db_dep),
) -> SimulatorProjectionResult:
    """Models hypothetical electricity reduction scenarios without modifying stored records."""
    return await run_electricity_simulation(req, workspace_id, db)


@router.post("/transportation", response_model=SimulatorProjectionResult)
async def simulate_transportation(
    req: TransportSimRequest,
    workspace_id: str = Depends(get_current_workspace_id),
    db: Any = Depends(get_db_dep),
) -> SimulatorProjectionResult:
    """Models hypothetical route distance reduction scenarios."""
    return await run_transportation_simulation(req, workspace_id, db)


@router.post("/waste", response_model=SimulatorProjectionResult)
async def simulate_waste(
    req: WasteSimRequest,
    workspace_id: str = Depends(get_current_workspace_id),
    db: Any = Depends(get_db_dep),
) -> SimulatorProjectionResult:
    """Models hypothetical waste minimization and recycling diversion scenarios."""
    return await run_waste_simulation(req, workspace_id, db)
