from typing import Any
from app.calculations.savings_calculator import (
    SimulatorProjectionResult,
    simulate_electricity_savings,
    simulate_transportation_savings,
    simulate_waste_savings,
)
from app.schemas.simulator import ElectricitySimRequest, TransportSimRequest, WasteSimRequest
from app.services.electricity_service import get_electricity_summary
from app.services.transportation_service import get_transportation_summary
from app.services.waste_service import get_waste_summary


async def run_electricity_simulation(
    req: ElectricitySimRequest,
    workspace_id: str,
    db: Any,
) -> SimulatorProjectionResult:
    summary = await get_electricity_summary(workspace_id, db)
    has_records = summary.record_count > 0 and summary.total_consumption_kwh > 0
    baseline_kwh = summary.total_consumption_kwh if has_records else 0.0
    res = simulate_electricity_savings(
        baseline_kwh=baseline_kwh,
        percent_reduction=req.percent_reduction,
        tariff_inr=req.custom_tariff_inr,
    )
    res.baseline["has_records"] = has_records
    if not has_records:
        res.limitations = "No electricity records logged for this workspace. Electricity reduction projection requires logged baseline electricity records."
    return res


async def run_transportation_simulation(
    req: TransportSimRequest,
    workspace_id: str,
    db: Any,
) -> SimulatorProjectionResult:
    summary = await get_transportation_summary(workspace_id, db)
    has_records = summary.record_count > 0 and summary.total_distance_km > 0
    baseline_km = summary.total_distance_km if has_records else 0.0
    res = simulate_transportation_savings(
        baseline_distance_km=baseline_km,
        percent_distance_reduction=req.percent_distance_reduction,
        fuel_efficiency_km_per_l=req.fuel_efficiency_km_per_l or 4.5,
        fuel_type=req.fuel_type or "Diesel",
    )
    res.baseline["has_records"] = has_records
    if not has_records:
        res.limitations = "No transportation records logged for this workspace. Transportation reduction projection requires logged baseline transportation records."
    return res


async def run_waste_simulation(
    req: WasteSimRequest,
    workspace_id: str,
    db: Any,
) -> SimulatorProjectionResult:
    summary = await get_waste_summary(workspace_id, db)
    has_records = summary.record_count > 0 and summary.total_waste_kg > 0
    baseline_kg = summary.total_waste_kg if has_records else 0.0
    res = simulate_waste_savings(
        baseline_quantity_kg=baseline_kg,
        percent_reduction=req.percent_reduction,
        target_recycling_percent=req.target_recycling_percent or 60.0,
    )
    res.baseline["has_records"] = has_records
    if not has_records:
        res.limitations = "No waste records logged for this workspace. Waste reduction projection requires logged baseline waste records."
    return res
