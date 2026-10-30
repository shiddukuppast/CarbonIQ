from typing import Any, Dict, List
from app.calculations.route_optimizer import optimize_bus_routes
from app.data.demo_data import (
    DEMO_BUS_ROUTES,
    DEMO_ELECTRICITY_RECORDS,
    DEMO_TRANSPORTATION_RECORDS,
    DEMO_WASTE_RECORDS,
    DEMO_WORKSPACE,
)


def get_demo_workspace() -> Dict[str, Any]:
    return DEMO_WORKSPACE


def get_demo_electricity() -> List[Dict[str, Any]]:
    return DEMO_ELECTRICITY_RECORDS


def get_demo_transportation() -> List[Dict[str, Any]]:
    return DEMO_TRANSPORTATION_RECORDS


def get_demo_routes() -> List[Dict[str, Any]]:
    return DEMO_BUS_ROUTES


def get_demo_waste() -> List[Dict[str, Any]]:
    return DEMO_WASTE_RECORDS


def get_demo_dashboard() -> Dict[str, Any]:
    elec_kwh = sum(r["consumption_kwh"] for r in DEMO_ELECTRICITY_RECORDS)
    elec_emissions = sum(r["calculated_emissions_kg"] for r in DEMO_ELECTRICITY_RECORDS)
    elec_cost = sum(r["bill_amount_inr"] for r in DEMO_ELECTRICITY_RECORDS)

    trans_dist = sum(r["distance_km"] for r in DEMO_TRANSPORTATION_RECORDS)
    trans_fuel = sum(r["fuel_consumed_liters"] for r in DEMO_TRANSPORTATION_RECORDS)
    trans_emissions = sum(r["calculated_emissions_kg"] for r in DEMO_TRANSPORTATION_RECORDS)
    trans_exp = sum(r["fuel_expenditure_inr"] for r in DEMO_TRANSPORTATION_RECORDS)

    waste_kg = sum(r["quantity_kg"] for r in DEMO_WASTE_RECORDS)
    waste_recycled = sum(r["quantity_kg"] for r in DEMO_WASTE_RECORDS if r.get("treatment_method") == "Recycling")
    waste_emissions = sum(r["calculated_emissions_kg"] for r in DEMO_WASTE_RECORDS)

    total_emissions = round(elec_emissions + trans_emissions + waste_emissions, 1)

    return {
        "workspace_id": DEMO_WORKSPACE["id"],
        "workspace_name": DEMO_WORKSPACE["name"],
        "is_demo": True,
        "total_emissions_kg": total_emissions,
        "electricity": {
            "consumption_kwh": elec_kwh,
            "cost_inr": elec_cost,
            "emissions_kg": round(elec_emissions, 1),
            "records": len(DEMO_ELECTRICITY_RECORDS),
        },
        "transportation": {
            "distance_km": trans_dist,
            "fuel_liters": round(trans_fuel, 1),
            "expenditure_inr": trans_exp,
            "emissions_kg": round(trans_emissions, 1),
            "records": len(DEMO_TRANSPORTATION_RECORDS),
        },
        "waste": {
            "total_kg": waste_kg,
            "recycled_kg": waste_recycled,
            "recycling_rate_percent": round((waste_recycled / waste_kg) * 100, 1) if waste_kg > 0 else 0,
            "emissions_kg": round(waste_emissions, 1),
            "records": len(DEMO_WASTE_RECORDS),
        },
        "category_breakdown": [
            {"name": "Electricity", "value": round((elec_emissions / total_emissions) * 100, 1), "color": "#285943"},
            {"name": "Transportation", "value": round((trans_emissions / total_emissions) * 100, 1), "color": "#647A67"},
            {"name": "Waste Management", "value": round((waste_emissions / total_emissions) * 100, 1), "color": "#8DA399"},
        ],
        "demo_notice": "Public sample demonstration data. Persistent mutations are disabled.",
    }
