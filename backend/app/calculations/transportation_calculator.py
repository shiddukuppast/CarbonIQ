from typing import List, Optional
from pydantic import BaseModel
from app.data.emission_factors import EMISSION_FACTORS, BENCHMARK_PRICES


class TransportationEmissionsResult(BaseModel):
    distance_km: float
    fuel_type: str
    fuel_consumed_liters: Optional[float] = None
    fuel_efficiency_km_per_l: Optional[float] = None
    calculated_fuel_liters: float
    calculated_emissions_kg: float
    calculation_method: str  # "actual_fuel" | "distance_efficiency_estimate" | "uncalculated"
    emission_factor_used: float
    factor_id: str
    factor_source: Optional[str] = None
    factor_version: Optional[str] = None
    calculation_boundary: Optional[str] = None
    unit: str = "kg CO2e"
    is_valid: bool = True
    explanation: str


def calculate_transportation_emissions(
    distance_km: float,
    fuel_type: str = "Diesel",
    fuel_consumed_liters: Optional[float] = None,
    fuel_efficiency_km_per_l: Optional[float] = None,
) -> TransportationEmissionsResult:
    """
    Calculates transportation emissions strictly using EITHER actual fuel or distance/efficiency.
    Prevents double-counting by prioritizing verified actual fuel logs.
    """
    normalized_fuel = fuel_type.strip().capitalize() if fuel_type else "Diesel"
    factor_key_map = {
        "Diesel": "fuel_diesel_standard",
        "Petrol": "fuel_petrol_standard",
        "Cng": "fuel_cng_standard",
        "Electric": "fuel_electric_standard",
    }
    factor_key = factor_key_map.get(normalized_fuel, "fuel_diesel_standard")
    factor = EMISSION_FACTORS[factor_key]

    # Method 1: Actual fuel consumed is known
    if fuel_consumed_liters is not None and fuel_consumed_liters > 0:
        emissions = round(fuel_consumed_liters * factor.value, 2)
        return TransportationEmissionsResult(
            distance_km=max(0.0, distance_km or 0.0),
            fuel_type=normalized_fuel,
            fuel_consumed_liters=fuel_consumed_liters,
            fuel_efficiency_km_per_l=fuel_efficiency_km_per_l,
            calculated_fuel_liters=fuel_consumed_liters,
            calculated_emissions_kg=emissions,
            calculation_method="actual_fuel",
            emission_factor_used=factor.value,
            factor_id=factor.factor_id,
            factor_source=factor.source,
            factor_version=factor.version,
            calculation_boundary=factor.calculation_boundary,
            is_valid=True,
            explanation=(
                f"Calculated from {fuel_consumed_liters} L of actual {normalized_fuel} consumed "
                f"× {factor.value} {factor.unit} ({factor.source})."
            ),
        )

    # Method 2: Distance and fuel efficiency known
    if (
        distance_km is not None
        and distance_km > 0
        and fuel_efficiency_km_per_l is not None
        and fuel_efficiency_km_per_l > 0
    ):
        estimated_fuel = round(distance_km / fuel_efficiency_km_per_l, 2)
        emissions = round(estimated_fuel * factor.value, 2)
        return TransportationEmissionsResult(
            distance_km=distance_km,
            fuel_type=normalized_fuel,
            fuel_consumed_liters=None,
            fuel_efficiency_km_per_l=fuel_efficiency_km_per_l,
            calculated_fuel_liters=estimated_fuel,
            calculated_emissions_kg=emissions,
            calculation_method="distance_efficiency_estimate",
            emission_factor_used=factor.value,
            factor_id=factor.factor_id,
            factor_source=factor.source,
            factor_version=factor.version,
            calculation_boundary=factor.calculation_boundary,
            is_valid=True,
            explanation=(
                f"Estimated from {distance_km} km ÷ {fuel_efficiency_km_per_l} km/L = {estimated_fuel} L {normalized_fuel} "
                f"× {factor.value} {factor.unit} ({factor.source})."
            ),
        )

    # Missing required inputs
    return TransportationEmissionsResult(
        distance_km=max(0.0, distance_km or 0.0),
        fuel_type=normalized_fuel,
        fuel_consumed_liters=fuel_consumed_liters,
        fuel_efficiency_km_per_l=fuel_efficiency_km_per_l,
        calculated_fuel_liters=0.0,
        calculated_emissions_kg=0.0,
        calculation_method="uncalculated",
        emission_factor_used=factor.value,
        factor_id=factor.factor_id,
        factor_source=factor.source,
        factor_version=factor.version,
        calculation_boundary=factor.calculation_boundary,
        is_valid=False,
        explanation=(
            "Insufficient fuel or efficiency data. Enter actual fuel volume or both distance and fuel efficiency (km/L)."
        ),
    )
