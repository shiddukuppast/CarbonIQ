from collections import defaultdict
from typing import Any, Dict, List
from app.schemas.dashboard import DashboardSummaryResponse, DashboardTrendsResponse
from app.services.electricity_service import get_electricity_summary
from app.services.transportation_service import get_transportation_summary
from app.services.waste_service import get_waste_summary


async def get_dashboard_summary(
    workspace_id: str,
    db: Any,
) -> DashboardSummaryResponse:
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

    # Combine monthly trends
    monthly_emissions_map = defaultdict(float)
    for t in elec.monthly_trends:
        monthly_emissions_map[t.reporting_month] += t.calculated_emissions_kg
    for t in trans.monthly_trends:
        monthly_emissions_map[t["month"]] += t["emissions_kg"]
    for t in waste.monthly_trends:
        monthly_emissions_map[t["month"]] += t["emissions_kg"]

    sorted_trends = [
        {"month": m, "emissions_kg": round(val, 1), "value": round(val, 1)}
        for m, val in sorted(monthly_emissions_map.items())
    ]

    # Category breakdown
    category_breakdown = []
    if total_emissions > 0:
        category_breakdown = [
            {
                "name": "Electricity",
                "value": round((elec.total_calculated_emissions_kg / total_emissions) * 100, 1),
                "emissions_kg": elec.total_calculated_emissions_kg,
                "color": "#285943",
            },
            {
                "name": "Transportation",
                "value": round((trans.total_calculated_emissions_kg / total_emissions) * 100, 1),
                "emissions_kg": trans.total_calculated_emissions_kg,
                "color": "#647A67",
            },
            {
                "name": "Waste Management",
                "value": round((waste.total_calculated_emissions_kg / total_emissions) * 100, 1),
                "emissions_kg": waste.total_calculated_emissions_kg,
                "color": "#8DA399",
            },
        ]

    active_interventions_count = await db.interventions.count_documents(
        {"workspace_id": workspace_id, "status": {"$in": ["accepted_for_planning", "in_progress", "proposed"]}}
    )

    return DashboardSummaryResponse(
        workspace_id=workspace_id,
        workspace_name=workspace_name,
        total_emissions_kg=total_emissions,
        electricity={
            "consumption_kwh": elec.total_consumption_kwh,
            "total_kwh": elec.total_consumption_kwh,
            "cost_inr": elec.total_bill_inr,
            "emissions_kg": elec.total_calculated_emissions_kg,
            "records": elec.record_count,
            "record_count": elec.record_count,
        },
        transportation={
            "distance_km": trans.total_distance_km,
            "total_distance_km": trans.total_distance_km,
            "fuel_liters": trans.total_fuel_liters,
            "total_liters": trans.total_fuel_liters,
            "expenditure_inr": trans.total_expenditure_inr,
            "cost_inr": trans.total_expenditure_inr,
            "emissions_kg": trans.total_calculated_emissions_kg,
            "records": trans.record_count,
            "record_count": trans.record_count,
        },
        waste={
            "total_kg": waste.total_waste_kg,
            "total_weight_kg": waste.total_waste_kg,
            "recycled_kg": waste.recycled_waste_kg,
            "recycling_rate_percent": waste.recycling_rate_percent,
            "recovery_rate_pct": waste.recycling_rate_percent,
            "emissions_kg": waste.total_calculated_emissions_kg,
            "records": waste.record_count,
            "record_count": waste.record_count,
        },
        monthly_emissions_trend=sorted_trends,
        category_breakdown=category_breakdown,
        active_interventions_count=active_interventions_count,
    )


async def get_dashboard_trends(
    workspace_id: str,
    db: Any,
) -> DashboardTrendsResponse:
    elec = await get_electricity_summary(workspace_id, db)
    trans = await get_transportation_summary(workspace_id, db)

    monthly_emissions_map = defaultdict(float)
    monthly_costs_map = defaultdict(float)

    for t in elec.monthly_trends:
        monthly_emissions_map[t.reporting_month] += t.calculated_emissions_kg
        monthly_costs_map[t.reporting_month] += t.bill_amount_inr

    for t in trans.monthly_trends:
        monthly_emissions_map[t["month"]] += t["emissions_kg"]
        monthly_costs_map[t["month"]] += t["fuel_expenditure_inr"]

    all_months = sorted(set(list(monthly_emissions_map.keys()) + list(monthly_costs_map.keys())))
    emissions_list = [
        {"month": m, "emissions_kg": round(monthly_emissions_map[m], 1), "value": round(monthly_emissions_map[m], 1)}
        for m in all_months
    ]
    costs_list = [{"month": m, "cost_inr": round(monthly_costs_map[m], 0)} for m in all_months]

    return DashboardTrendsResponse(
        monthly_emissions=emissions_list,
        monthly_costs_inr=costs_list,
    )
