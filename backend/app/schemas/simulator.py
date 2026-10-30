from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from app.calculations.savings_calculator import SimulatorProjectionResult


class ElectricitySimRequest(BaseModel):
    percent_reduction: float = Field(..., ge=0, le=100, description="Percentage reduction target (0-100)")
    custom_tariff_inr: Optional[float] = Field(None, gt=0)


class TransportSimRequest(BaseModel):
    percent_distance_reduction: float = Field(..., ge=0, le=100)
    fuel_efficiency_km_per_l: Optional[float] = Field(4.5, gt=0)
    fuel_type: Optional[str] = "Diesel"


class WasteSimRequest(BaseModel):
    percent_reduction: float = Field(..., ge=0, le=100)
    target_recycling_percent: Optional[float] = Field(60.0, ge=0, le=100)
