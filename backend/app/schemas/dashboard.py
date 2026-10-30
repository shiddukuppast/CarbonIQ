from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class ModuleSummaryMetric(BaseModel):
    label: str
    value: str
    unit: Optional[str] = None
    subtext: Optional[str] = None


class DashboardSummaryResponse(BaseModel):
    workspace_id: str
    workspace_name: str
    total_emissions_kg: float
    electricity: Dict[str, Any]
    transportation: Dict[str, Any]
    waste: Dict[str, Any]
    monthly_emissions_trend: List[Dict[str, Any]]
    category_breakdown: List[Dict[str, Any]]
    active_interventions_count: int


class CategoryBreakdownItem(BaseModel):
    name: str
    value: float  # Percentage
    emissions_kg: float
    color: str


class DashboardTrendsResponse(BaseModel):
    monthly_emissions: List[Dict[str, Any]]
    monthly_costs_inr: List[Dict[str, Any]]
