from typing import Optional
from pydantic import BaseModel
from app.data.emission_factors import EMISSION_FACTORS


class WasteEmissionsResult(BaseModel):
    quantity_kg: float
    treatment_method: Optional[str]
    category: Optional[str]
    calculated_emissions_kg: float
    emission_factor_used: Optional[float]
    factor_id: Optional[str]
    factor_source: Optional[str] = None
    factor_version: Optional[str] = None
    calculation_boundary: Optional[str] = None
    unit: str = "kg CO2e"
    is_valid: bool = True
    explanation: str


def calculate_waste_emissions(
    quantity_kg: float,
    treatment_method: Optional[str] = None,
    category: Optional[str] = None,
) -> WasteEmissionsResult:
    """
    Calculates waste emissions from quantity in kg and treatment method.
    Negative emission factor indicates avoided virgin material emissions (Recycling).
    Positive emission factor indicates net greenhouse gas generation (Landfill / Composting / Incineration).
    """
    if quantity_kg is None or quantity_kg < 0:
        return WasteEmissionsResult(
            quantity_kg=0.0,
            treatment_method=treatment_method,
            category=category,
            calculated_emissions_kg=0.0,
            emission_factor_used=None,
            factor_id=None,
            is_valid=False,
            explanation="Invalid waste quantity. Must be a non-negative number.",
        )

    method_key_map = {
        "composting": "waste_composting",
        "recycling": "waste_recycling",
        "landfill": "waste_landfill",
        "incineration": "waste_incineration",
        "waste-to-energy": "waste_incineration",
        "other / unknown": "waste_other",
        "other": "waste_other",
    }
    norm_method = (treatment_method or "other / unknown").strip().lower()
    factor_key = method_key_map.get(norm_method, "waste_other")
    factor = EMISSION_FACTORS.get(factor_key, EMISSION_FACTORS["waste_other"])

    emissions = round(quantity_kg * factor.value, 2)
    return WasteEmissionsResult(
        quantity_kg=quantity_kg,
        treatment_method=treatment_method or "Other / Unknown",
        category=category,
        calculated_emissions_kg=emissions,
        emission_factor_used=factor.value,
        factor_id=factor.factor_id,
        factor_source=factor.source,
        factor_version=factor.version,
        calculation_boundary=factor.calculation_boundary,
        is_valid=True,
        explanation=(
            f"Calculated from {quantity_kg} kg via {factor.sub_category} "
            f"× {factor.value} {factor.unit} ({factor.source})."
        ),
    )


def calculate_recycling_rate(recycled_kg: float, total_generated_kg: float) -> Optional[float]:
    """
    Calculates percentage of waste recycled out of total generated.
    Returns None if total is 0 or invalid to avoid deceptive 0% or 100%.
    """
    if total_generated_kg is None or total_generated_kg <= 0:
        return None
    if recycled_kg is None or recycled_kg < 0:
        return 0.0
    rate = round((recycled_kg / total_generated_kg) * 100.0, 1)
    return min(100.0, rate)
