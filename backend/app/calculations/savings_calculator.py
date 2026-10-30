from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from app.data.emission_factors import EMISSION_FACTORS, BENCHMARK_PRICES


class SimulatorProjectionResult(BaseModel):
    module: str  # "electricity" | "transportation" | "waste" | "aggregate"
    baseline: Dict[str, Any]
    proposed: Dict[str, Any]
    difference: Dict[str, Any]
    estimated_cost_savings_inr: float
    estimated_emissions_reduction_kg: float
    assumptions: List[str]
    limitations: str


def simulate_electricity_savings(
    baseline_kwh: float,
    percent_reduction: float,
    tariff_inr: Optional[float] = None
) -> SimulatorProjectionResult:
    """Simulates hypothetical electricity reduction scenarios."""
    safe_percent = max(0.0, min(100.0, percent_reduction))
    tariff = tariff_inr or BENCHMARK_PRICES["electricity_tariff_inr_per_kwh"]
    factor = EMISSION_FACTORS["grid_in_cea_baseline"].value

    kwh_diff = round((baseline_kwh * safe_percent) / 100.0, 1)
    proposed_kwh = max(0.0, round(baseline_kwh - kwh_diff, 1))
    cost_diff = round(kwh_diff * tariff, 0)
    emissions_diff = round(kwh_diff * factor, 1)

    return SimulatorProjectionResult(
        module="electricity",
        baseline={
            "consumption_kwh": baseline_kwh,
            "estimated_cost_inr": round(baseline_kwh * tariff, 0),
            "emissions_kg": round(baseline_kwh * factor, 1),
            "has_records": baseline_kwh > 0,
        },
        proposed={
            "consumption_kwh": proposed_kwh,
            "estimated_cost_inr": round(proposed_kwh * tariff, 0),
            "emissions_kg": round(proposed_kwh * factor, 1),
        },
        difference={
            "kwh_reduction": kwh_diff,
            "percent_reduction": safe_percent,
        },
        estimated_cost_savings_inr=cost_diff,
        estimated_emissions_reduction_kg=emissions_diff,
        assumptions=[
            f"Variable tariff of ₹{tariff}/kWh (excluding fixed meter and demand charges).",
            f"Grid emission factor of {factor} kg CO2e/kWh.",
        ],
        limitations="Hypothetical scenario. Actual bills vary with tariff slabs, power factor penalties, and taxes.",
    )


def simulate_transportation_savings(
    baseline_distance_km: float,
    percent_distance_reduction: float,
    fuel_efficiency_km_per_l: float = 4.5,
    fuel_type: str = "Diesel"
) -> SimulatorProjectionResult:
    """Simulates hypothetical transportation route and distance reduction."""
    safe_percent = max(0.0, min(100.0, percent_distance_reduction))
    fuel_price = BENCHMARK_PRICES["diesel_inr_per_l"] if fuel_type == "Diesel" else BENCHMARK_PRICES["petrol_inr_per_l"]
    factor = EMISSION_FACTORS["fuel_diesel_standard"].value if fuel_type == "Diesel" else EMISSION_FACTORS["fuel_petrol_standard"].value

    eff = max(0.5, fuel_efficiency_km_per_l)
    baseline_fuel = round(baseline_distance_km / eff, 1)
    dist_diff = round((baseline_distance_km * safe_percent) / 100.0, 1)
    proposed_dist = max(0.0, round(baseline_distance_km - dist_diff, 1))
    proposed_fuel = round(proposed_dist / eff, 1)

    fuel_diff = round(baseline_fuel - proposed_fuel, 1)
    cost_diff = round(fuel_diff * fuel_price, 0)
    emissions_diff = round(fuel_diff * factor, 1)

    return SimulatorProjectionResult(
        module="transportation",
        baseline={
            "distance_km": baseline_distance_km,
            "fuel_liters": baseline_fuel,
            "estimated_cost_inr": round(baseline_fuel * fuel_price, 0),
            "emissions_kg": round(baseline_fuel * factor, 1),
            "has_records": baseline_distance_km > 0,
        },
        proposed={
            "distance_km": proposed_dist,
            "fuel_liters": proposed_fuel,
            "estimated_cost_inr": round(proposed_fuel * fuel_price, 0),
            "emissions_kg": round(proposed_fuel * factor, 1),
        },
        difference={
            "distance_reduction_km": dist_diff,
            "fuel_savings_liters": fuel_diff,
            "percent_reduction": safe_percent,
        },
        estimated_cost_savings_inr=cost_diff,
        estimated_emissions_reduction_kg=emissions_diff,
        assumptions=[
            f"Assumed fuel: {fuel_type} @ ₹{fuel_price}/L with {eff} km/L baseline efficiency.",
            f"Combustion emission factor: {factor} kg CO2e/L.",
        ],
        limitations="Does not account for traffic congestion, idling, or vehicle load variations.",
    )


def simulate_waste_savings(
    baseline_quantity_kg: float,
    percent_reduction: float,
    target_recycling_percent: float = 60.0
) -> SimulatorProjectionResult:
    """Simulates hypothetical waste reduction and segregation improvements."""
    safe_percent = max(0.0, min(100.0, percent_reduction))
    safe_recycle = max(0.0, min(100.0, target_recycling_percent))

    qty_diff = round((baseline_quantity_kg * safe_percent) / 100.0, 1)
    proposed_qty = max(0.0, round(baseline_quantity_kg - qty_diff, 1))

    landfill_factor = EMISSION_FACTORS["waste_landfill"].value  # 1.25
    recycling_factor = EMISSION_FACTORS["waste_recycling"].value  # -0.45

    baseline_emissions = round(baseline_quantity_kg * landfill_factor, 1)
    recycled_amount = round((proposed_qty * safe_recycle) / 100.0, 1)
    landfill_amount = max(0.0, round(proposed_qty - recycled_amount, 1))

    proposed_emissions = round((landfill_amount * landfill_factor) + (recycled_amount * recycling_factor), 1)
    emissions_diff = round(baseline_emissions - proposed_emissions, 1)

    return SimulatorProjectionResult(
        module="waste",
        baseline={
            "quantity_kg": baseline_quantity_kg,
            "emissions_kg": baseline_emissions,
            "has_records": baseline_quantity_kg > 0,
        },
        proposed={
            "quantity_kg": proposed_qty,
            "recycled_kg": recycled_amount,
            "landfill_kg": landfill_amount,
            "emissions_kg": proposed_emissions,
        },
        difference={
            "quantity_reduction_kg": qty_diff,
            "waste_kg_reduction": qty_diff,
            "recycled_kg": recycled_amount,
            "percent_reduction": safe_percent,
        },
        estimated_cost_savings_inr=round(qty_diff * 4.5, 0),  # ₹4.5/kg disposal benchmark
        estimated_emissions_reduction_kg=emissions_diff,
        assumptions=[
            f"Baseline assumed 100% landfill ({landfill_factor} kg CO2e/kg).",
            f"Proposed scenario diverts {safe_recycle}% to verified recycling ({recycling_factor} kg CO2e/kg credit).",
        ],
        limitations="Actual emissions depend on purity of waste streams and local municipal processing capabilities.",
    )
