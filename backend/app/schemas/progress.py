from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class GoalCreateRequest(BaseModel):
    goal_name: str = Field(..., min_length=2, max_length=150)
    category: str = Field(..., description="Electricity, Transportation, Waste, Aggregate")
    baseline_value: float = Field(..., ge=0)
    target_value: float = Field(..., ge=0)
    target_period: str = Field(..., description="Target completion period (e.g. 2026-12)")
    unit: str = Field(..., max_length=50)


class GoalResponse(BaseModel):
    id: str
    workspace_id: str
    goal_name: str
    category: str
    baseline_value: float
    target_value: float
    target_period: str
    unit: str
    current_value: Optional[float] = None
    progress_percentage: Optional[float] = None
    status: str = "in_progress"  # "in_progress" | "achieved" | "off_track"
    created_at: str
    updated_at: str


class InterventionCreateRequest(BaseModel):
    title: str = Field(..., min_length=2, max_length=150)
    category: str = Field(..., description="Electricity, Transportation, Waste")
    proposal_id: Optional[str] = None
    description: str
    estimated_benefit: str
    estimated_cost_savings_inr: Optional[float] = None
    estimated_emissions_savings_kg: Optional[float] = None
    status: str = Field(default="accepted_for_planning")  # "proposed" | "accepted_for_planning" | "rejected" | "implemented"
    assumptions: List[str] = Field(default_factory=list)


class InterventionResponse(BaseModel):
    id: str
    workspace_id: str
    title: str
    category: str
    proposal_id: Optional[str] = None
    description: str
    estimated_benefit: str
    estimated_cost_savings_inr: Optional[float] = None
    estimated_emissions_savings_kg: Optional[float] = None
    status: str
    assumptions: List[str]
    actual_result: Optional[str] = None
    created_at: str
    updated_at: str
