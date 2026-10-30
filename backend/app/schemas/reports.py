from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class EmissionsReportResponse(BaseModel):
    reporting_period: str
    workspace_name: str
    total_calculated_emissions_kg: float
    category_summary: Dict[str, Any]
    electricity_kwh: float
    transport_distance_km: float
    waste_generated_kg: float
    recycling_rate_percent: Optional[float] = None
    data_completeness_notes: List[str]
    calculation_assumptions: List[str]
    generated_at: str
