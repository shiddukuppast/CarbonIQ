from typing import Any, Dict, List, Optional, Union
from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_validator

SUPPORTED_FUEL_TYPES = ("Diesel", "Petrol", "CNG", "Electric")
_FUEL_TYPE_MAP = {f.lower(): f for f in SUPPORTED_FUEL_TYPES}


class TransportationCreateRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    date: str = Field(
        ...,
        validation_alias=AliasChoices("date", "reporting_period", "reportingPeriod", "period"),
        description="Date or period of travel (YYYY-MM-DD or YYYY-MM)",
    )
    mode: str = Field(
        ...,
        validation_alias=AliasChoices("mode", "vehicle_type", "vehicleType"),
        description="Transport mode: Bus, Fleet Van, Car, Two-Wheeler, Public Transit",
    )
    distance_km: float = Field(
        ...,
        validation_alias=AliasChoices("distance_km", "distanceKm", "distance"),
        ge=0,
        description="Total distance travelled in km",
    )
    fuel_type: Optional[str] = Field(
        "Diesel",
        validation_alias=AliasChoices("fuel_type", "fuelType"),
        description="Diesel, Petrol, CNG, Electric",
    )
    fuel_consumed_liters: Optional[float] = Field(
        None,
        validation_alias=AliasChoices("fuel_consumed_liters", "fuelConsumedLiters", "fuel_consumption", "fuelConsumed"),
        ge=0,
        description="Actual fuel consumed in Litres/kg",
    )
    fuel_efficiency_km_per_l: Optional[float] = Field(
        None,
        validation_alias=AliasChoices("fuel_efficiency_km_per_l", "fuelEfficiencyKmPerL", "fuel_efficiency", "fuelEfficiency"),
        gt=0,
        description="Fuel efficiency in km/L",
    )
    fuel_expenditure_inr: Optional[float] = Field(
        None,
        validation_alias=AliasChoices("fuel_expenditure_inr", "fuelExpenditureInr", "fuel_cost", "fuelCost"),
        ge=0,
        description="Fuel expense in INR",
    )
    vehicle_id: Optional[str] = Field(
        None,
        validation_alias=AliasChoices("vehicle_id", "vehicleId", "bus_id", "busId"),
        max_length=50,
    )
    passenger_count: Optional[int] = Field(
        None,
        validation_alias=AliasChoices("passenger_count", "passengerCount", "passengers"),
        ge=0,
    )
    vehicle_capacity: Optional[int] = Field(
        None,
        validation_alias=AliasChoices("vehicle_capacity", "vehicleCapacity", "capacity", "seating_capacity", "seatingCapacity"),
        ge=0,
    )
    route_name: Optional[str] = Field(
        None,
        validation_alias=AliasChoices("route_name", "routeName"),
        max_length=100,
    )
    pickup_locations: Optional[Union[List[str], str]] = Field(
        None,
        validation_alias=AliasChoices("pickup_locations", "pickupLocations", "start_location", "startLocation"),
    )
    destination: Optional[str] = Field(
        None,
        max_length=100,
    )
    notes: Optional[str] = Field(None, max_length=500)

    @field_validator("fuel_type")
    @classmethod
    def validate_fuel_type(cls, v: Optional[str]) -> str:
        if v is None:
            return "Diesel"
        cleaned = v.strip()
        matched = _FUEL_TYPE_MAP.get(cleaned.lower())
        if not matched:
            supported = ", ".join(SUPPORTED_FUEL_TYPES)
            raise ValueError(f"Invalid fuel type '{v}'. Supported fuel types are: {supported}")
        return matched

    @field_validator("pickup_locations")
    @classmethod
    def normalize_pickups(cls, v: Optional[Union[List[str], str]]) -> Optional[List[str]]:
        if v is None:
            return None
        if isinstance(v, str):
            return [s.strip() for s in v.split(",") if s.strip()]
        return v


class TransportationUpdateRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    date: Optional[str] = Field(
        None,
        validation_alias=AliasChoices("date", "reporting_period", "reportingPeriod", "period"),
    )
    mode: Optional[str] = Field(
        None,
        validation_alias=AliasChoices("mode", "vehicle_type", "vehicleType"),
    )
    distance_km: Optional[float] = Field(
        None,
        validation_alias=AliasChoices("distance_km", "distanceKm", "distance"),
        ge=0,
    )
    fuel_type: Optional[str] = Field(
        None,
        validation_alias=AliasChoices("fuel_type", "fuelType"),
    )
    fuel_consumed_liters: Optional[float] = Field(
        None,
        validation_alias=AliasChoices("fuel_consumed_liters", "fuelConsumedLiters", "fuel_consumption", "fuelConsumed"),
        ge=0,
    )
    fuel_efficiency_km_per_l: Optional[float] = Field(
        None,
        validation_alias=AliasChoices("fuel_efficiency_km_per_l", "fuelEfficiencyKmPerL", "fuel_efficiency", "fuelEfficiency"),
        gt=0,
    )
    fuel_expenditure_inr: Optional[float] = Field(
        None,
        validation_alias=AliasChoices("fuel_expenditure_inr", "fuelExpenditureInr", "fuel_cost", "fuelCost"),
        ge=0,
    )
    vehicle_id: Optional[str] = Field(
        None,
        validation_alias=AliasChoices("vehicle_id", "vehicleId", "bus_id", "busId"),
    )
    passenger_count: Optional[int] = Field(
        None,
        validation_alias=AliasChoices("passenger_count", "passengerCount", "passengers"),
        ge=0,
    )
    vehicle_capacity: Optional[int] = Field(
        None,
        validation_alias=AliasChoices("vehicle_capacity", "vehicleCapacity", "capacity", "seating_capacity", "seatingCapacity"),
        ge=0,
    )
    route_name: Optional[str] = Field(
        None,
        validation_alias=AliasChoices("route_name", "routeName"),
    )
    pickup_locations: Optional[Union[List[str], str]] = Field(
        None,
        validation_alias=AliasChoices("pickup_locations", "pickupLocations", "start_location", "startLocation"),
    )
    destination: Optional[str] = None
    notes: Optional[str] = None

    @field_validator("fuel_type")
    @classmethod
    def validate_fuel_type(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        cleaned = v.strip()
        matched = _FUEL_TYPE_MAP.get(cleaned.lower())
        if not matched:
            supported = ", ".join(SUPPORTED_FUEL_TYPES)
            raise ValueError(f"Invalid fuel type '{v}'. Supported fuel types are: {supported}")
        return matched

    @field_validator("pickup_locations")
    @classmethod
    def normalize_pickups(cls, v: Optional[Union[List[str], str]]) -> Optional[List[str]]:
        if v is None:
            return None
        if isinstance(v, str):
            return [s.strip() for s in v.split(",") if s.strip()]
        return v


class TransportationRecordResponse(BaseModel):
    id: str
    workspace_id: str
    date: str
    mode: str
    distance_km: float
    fuel_type: Optional[str] = None
    fuel_consumed_liters: Optional[float] = None
    fuel_efficiency_km_per_l: Optional[float] = None
    fuel_expenditure_inr: Optional[float] = None
    vehicle_id: Optional[str] = None
    passenger_count: Optional[int] = None
    vehicle_capacity: Optional[int] = None
    route_name: Optional[str] = None
    pickup_locations: Optional[List[str]] = None
    destination: Optional[str] = None
    notes: Optional[str] = None
    calculation_method: str
    calculated_emissions_kg: float
    emission_factor_used: Optional[float] = None
    factor_id: Optional[str] = None
    factor_source: Optional[str] = None
    factor_version: Optional[str] = None
    calculation_boundary: Optional[str] = None
    created_at: str
    updated_at: str


class TransportationSummaryResponse(BaseModel):
    total_distance_km: float
    total_fuel_liters: float
    total_expenditure_inr: float
    total_calculated_emissions_kg: float
    record_count: int
    mode_breakdown: List[Dict[str, Any]]
    monthly_trends: List[Dict[str, Any]]
