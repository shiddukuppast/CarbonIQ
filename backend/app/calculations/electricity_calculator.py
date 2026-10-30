from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from app.data.emission_factors import EMISSION_FACTORS, BENCHMARK_PRICES


class ElectricityEmissionsResult(BaseModel):
    consumption_kwh: float
    calculated_emissions_kg: float
    emission_factor_used: float
    factor_id: str
    factor_type: str  # "authoritative_grid_factor" | "measured" | "illustrative_grid_factor"
    factor_source: Optional[str] = None
    factor_version: Optional[str] = None
    calculation_boundary: Optional[str] = None
    unit: str = "kg CO2e"
    calculation_method: str = "consumption_kwh * grid_emission_factor"
    is_valid: bool = True
    notes: Optional[str] = None


class ElectricitySavingsScenario(BaseModel):
    current_kwh: float
    percent_reduction: float
    kwh_reduction: float
    cost_savings_inr: float
    emissions_reduction_kg: float
    tariff_inr_per_kwh: float
    assumptions: List[str]


def calculate_electricity_emissions(
    consumption_kwh: float,
    factor_id: str = "grid_in_cea_baseline",
    source: Optional[str] = None,
) -> ElectricityEmissionsResult:
    """
    Calculates electricity emissions based on consumption in kWh.
    Formula: Electricity emissions (kg CO2e) = consumption (kWh) × emission factor (kg CO2e/kWh)
    Respects electricity generation source (e.g., Solar Rooftop vs Grid).
    """
    # Check if electricity source is zero-emission renewable
    if source and ("solar" in source.lower() or "rooftop" in source.lower()):
        factor = EMISSION_FACTORS.get("electricity_solar_rooftop", EMISSION_FACTORS["grid_in_cea_baseline"])
    else:
        factor = EMISSION_FACTORS.get(factor_id, EMISSION_FACTORS["grid_in_cea_baseline"])

    factor_type_str = "illustrative_grid_factor" if factor.factor_id == "grid_in_cea_baseline" else ("authoritative_grid_factor" if factor.is_authoritative else "measured")

    if consumption_kwh is None or consumption_kwh < 0:
        return ElectricityEmissionsResult(
            consumption_kwh=0.0,
            calculated_emissions_kg=0.0,
            emission_factor_used=factor.value,
            factor_id=factor.factor_id,
            factor_type=factor_type_str,
            factor_source=factor.source,
            factor_version=factor.version,
            calculation_boundary=factor.calculation_boundary,
            is_valid=False,
            notes="Invalid consumption value. Must be a non-negative number.",
        )

    emissions = round(consumption_kwh * factor.value, 2)
    return ElectricityEmissionsResult(
        consumption_kwh=consumption_kwh,
        calculated_emissions_kg=emissions,
        emission_factor_used=factor.value,
        factor_id=factor.factor_id,
        factor_type=factor_type_str,
        factor_source=factor.source,
        factor_version=factor.version,
        calculation_boundary=factor.calculation_boundary,
        is_valid=True,
        notes=f"Calculated with {factor.source} ({factor.value} {factor.unit}).",
    )


def calculate_electricity_savings_scenario(
    current_kwh: float,
    percent_reduction: float,
    tariff_inr: Optional[float] = None,
    factor_id: str = "grid_in_cea_baseline"
) -> ElectricitySavingsScenario:
    """
    Calculates what-if financial and carbon savings for an electricity reduction scenario.
    """
    tariff = tariff_inr if tariff_inr is not None and tariff_inr > 0 else BENCHMARK_PRICES["electricity_tariff_inr_per_kwh"]
    factor = EMISSION_FACTORS.get(factor_id, EMISSION_FACTORS["grid_in_cea_baseline"])

    safe_kwh = max(0.0, current_kwh)
    safe_percent = max(0.0, min(100.0, percent_reduction))

    kwh_reduction = round((safe_kwh * safe_percent) / 100.0, 1)
    cost_savings = round(kwh_reduction * tariff, 0)
    emissions_reduction = round(kwh_reduction * factor.value, 1)

    return ElectricitySavingsScenario(
        current_kwh=safe_kwh,
        percent_reduction=safe_percent,
        kwh_reduction=kwh_reduction,
        cost_savings_inr=cost_savings,
        emissions_reduction_kg=emissions_reduction,
        tariff_inr_per_kwh=tariff,
        assumptions=[
            f"Emission factor: {factor.value} {factor.unit} ({factor.source}).",
            f"Estimated variable electricity tariff: INR {tariff}/kWh (excluding fixed meter and demand charges).",
        ],
    )
