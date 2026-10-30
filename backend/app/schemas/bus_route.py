from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, model_validator

from app.calculations.route_optimizer import RouteOptimizationProposal


class BusRouteCreateRequest(BaseModel):
    route_name: str = Field(..., min_length=2, max_length=100)
    start_location: str = Field(..., min_length=1, max_length=100)
    destination: str = Field(..., min_length=1, max_length=100)
    intermediate_stops: List[str] = Field(default_factory=list)
    distance_km: float = Field(..., gt=0)
    duration_minutes: int = Field(..., gt=0)
    trips_per_day: int = Field(default=2, ge=1)
    operating_days_per_week: int = Field(default=5, ge=1, le=7)
    seating_capacity: int = Field(default=40, ge=1)
    assigned_students: int = Field(..., ge=0)
    bus_id: str = Field(..., min_length=1, max_length=50)
    fuel_type: str = Field(default="Diesel")
    fuel_efficiency_km_per_l: float = Field(default=4.5, gt=0)
    fuel_consumption_per_day_liters: Optional[float] = Field(None, ge=0)
    current_buses_count: int = Field(default=1, ge=1)
    status: str = Field(default="active")  # "active" | "consolidated" | "under_review"
    notes: Optional[str] = None

    @model_validator(mode="after")
    def check_capacity(self) -> "BusRouteCreateRequest":
        if self.assigned_students > self.seating_capacity:
            raise ValueError(f"assigned_students ({self.assigned_students}) exceeds seating_capacity ({self.seating_capacity})")
        return self


class BusRouteUpdateRequest(BaseModel):
    route_name: Optional[str] = None
    start_location: Optional[str] = None
    destination: Optional[str] = None
    intermediate_stops: Optional[List[str]] = None
    distance_km: Optional[float] = Field(None, gt=0)
    duration_minutes: Optional[int] = Field(None, gt=0)
    trips_per_day: Optional[int] = Field(None, ge=1)
    operating_days_per_week: Optional[int] = Field(None, ge=1, le=7)
    assigned_students: Optional[int] = Field(None, ge=0)
    bus_id: Optional[str] = None
    fuel_type: Optional[str] = None
    fuel_efficiency_km_per_l: Optional[float] = Field(None, gt=0)
    fuel_consumption_per_day_liters: Optional[float] = Field(None, ge=0)
    seating_capacity: Optional[int] = Field(None, ge=1)
    current_buses_count: Optional[int] = Field(None, ge=1)
    status: Optional[str] = None
    notes: Optional[str] = None


class BusRouteResponse(BaseModel):
    id: str
    workspace_id: str
    route_name: str
    start_location: str
    destination: str
    intermediate_stops: List[str]
    distance_km: float
    duration_minutes: int
    trips_per_day: int
    operating_days_per_week: int
    assigned_students: int
    bus_id: str
    fuel_type: str
    fuel_efficiency_km_per_l: float
    fuel_consumption_per_day_liters: Optional[float] = None
    seating_capacity: int
    current_buses_count: int
    status: str
    notes: Optional[str] = None
    created_at: str
    updated_at: str


class RouteOptimizationRequest(BaseModel):
    route_ids: Optional[List[str]] = Field(default=None, description="Optional list of specific route IDs to optimize")


class RouteOptimizationResponse(BaseModel):
    proposals: List[RouteOptimizationProposal]
    analyzed_routes_count: int
    timestamp: str