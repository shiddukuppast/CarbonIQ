from typing import Any, Dict
from app.data.emission_factors import EMISSION_FACTORS
from app.schemas.reports import EmissionsReportResponse
from app.services.electricity_service import get_electricity_summary
from app.services.transportation_service import get_transportation_summary
from app.services.waste_service import get_waste_summary
from app.utils.dates import utc_iso


async def generate_emissions_report(
    workspace_id: str,
    db: Any,
    period: str = "2026-YTD",
) -> EmissionsReportResponse:
    workspace = await db.workspaces.find_one({"id": workspace_id})
    workspace_name = workspace.get("name", "Workspace") if workspace else "Workspace"

    elec = await get_electricity_summary(workspace_id, db)
    trans = await get_transportation_summary(workspace_id, db)
    waste = await get_waste_summary(workspace_id, db)

    total_emissions = round(
        elec.total_calculated_emissions_kg
        + trans.total_calculated_emissions_kg
        + waste.total_calculated_emissions_kg,
        1,
    )

    category_summary = {
        "Electricity": {
            "consumption_kwh": elec.total_consumption_kwh,
            "emissions_kg": elec.total_calculated_emissions_kg,
            "cost_inr": elec.total_bill_inr,
            "factor_used": f"{EMISSION_FACTORS['grid_in_cea_baseline'].value} kg CO2e/kWh",
        },
        "Transportation": {
            "distance_km": trans.total_distance_km,
            "fuel_liters": trans.total_fuel_liters,
            "emissions_kg": trans.total_calculated_emissions_kg,
            "expenditure_inr": trans.total_expenditure_inr,
            "factor_used": f"{EMISSION_FACTORS['fuel_diesel_standard'].value} kg CO2e/L (Diesel standard)",
        },
        "Waste": {
            "total_kg": waste.total_waste_kg,
            "recycled_kg": waste.recycled_waste_kg,
            "recycling_rate_percent": waste.recycling_rate_percent,
            "emissions_kg": waste.total_calculated_emissions_kg,
            "net_status": "Includes avoided emissions credits for verified recycling streams",
        },
    }

    notes = [
        "All calculations were computed strictly from authorized workspace persistent records.",
        "Emissions are expressed in kilograms of Carbon Dioxide Equivalent (kg CO2e).",
        "Estimated savings from route optimization are classified as planned interventions, not achieved savings.",
    ]

    assumptions = [
        f"Electricity factor: {EMISSION_FACTORS['grid_in_cea_baseline'].source}.",
        f"Diesel factor: {EMISSION_FACTORS['fuel_diesel_standard'].source}.",
        f"Waste treatment factors: {EMISSION_FACTORS['waste_landfill'].source} & {EMISSION_FACTORS['waste_recycling'].source}.",
    ]

    return EmissionsReportResponse(
        reporting_period=period,
        workspace_name=workspace_name,
        total_calculated_emissions_kg=total_emissions,
        category_summary=category_summary,
        electricity_kwh=elec.total_consumption_kwh,
        transport_distance_km=trans.total_distance_km,
        waste_generated_kg=waste.total_waste_kg,
        recycling_rate_percent=waste.recycling_rate_percent,
        data_completeness_notes=notes,
        calculation_assumptions=assumptions,
        generated_at=utc_iso(),
    )
