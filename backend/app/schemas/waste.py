from typing import Any, Dict, List, Optional
from pydantic import AliasChoices, BaseModel, ConfigDict, Field


class WasteCreateRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    date: str = Field(
        ...,
        validation_alias=AliasChoices("date", "reporting_period", "reportingPeriod", "period"),
        description="Date or period (YYYY-MM-DD or YYYY-MM)",
    )
    category: str = Field(
        ...,
        description="Biodegradable, Recyclable, General, E-waste",
    )
    quantity_kg: float = Field(
        ...,
        validation_alias=AliasChoices("quantity_kg", "quantityKg", "quantity"),
        ge=0,
        description="Waste generated in kilograms",
    )
    unit: str = Field(
        "kg",
        description="Unit of measurement: kg, metric tonnes",
    )
    treatment_method: Optional[str] = Field(
        "Other / Unknown",
        validation_alias=AliasChoices("treatment_method", "treatmentMethod", "treatment"),
        description="Composting, Recycling, Landfill, Incineration, Other / Unknown",
    )
    building_or_department: Optional[str] = Field(
        None,
        validation_alias=AliasChoices("building_or_department", "buildingOrDepartment", "department", "building"),
    )
    collection_provider: Optional[str] = Field(
        None,
        validation_alias=AliasChoices("collection_provider", "collectionProvider", "provider"),
    )
    disposal_cost_inr: Optional[float] = Field(
        None,
        validation_alias=AliasChoices("disposal_cost_inr", "disposalCostInr", "disposal_cost", "cost"),
        ge=0,
    )
    notes: Optional[str] = None


class WasteUpdateRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    date: Optional[str] = Field(
        None,
        validation_alias=AliasChoices("date", "reporting_period", "reportingPeriod", "period"),
    )
    category: Optional[str] = None
    quantity_kg: Optional[float] = Field(
        None,
        validation_alias=AliasChoices("quantity_kg", "quantityKg", "quantity"),
        ge=0,
    )
    unit: Optional[str] = None
    treatment_method: Optional[str] = Field(
        None,
        validation_alias=AliasChoices("treatment_method", "treatmentMethod", "treatment"),
    )
    building_or_department: Optional[str] = Field(
        None,
        validation_alias=AliasChoices("building_or_department", "buildingOrDepartment", "department", "building"),
    )
    collection_provider: Optional[str] = Field(
        None,
        validation_alias=AliasChoices("collection_provider", "collectionProvider", "provider"),
    )
    disposal_cost_inr: Optional[float] = Field(
        None,
        validation_alias=AliasChoices("disposal_cost_inr", "disposalCostInr", "disposal_cost", "cost"),
        ge=0,
    )
    notes: Optional[str] = None


class WasteRecordResponse(BaseModel):
    id: str
    workspace_id: str
    date: str
    category: str
    quantity_kg: float
    unit: str = "kg"
    treatment_method: Optional[str] = None
    building_or_department: Optional[str] = None
    collection_provider: Optional[str] = None
    disposal_cost_inr: Optional[float] = None
    notes: Optional[str] = None
    calculated_emissions_kg: float
    emission_factor_used: Optional[float] = None
    factor_id: Optional[str] = None
    factor_source: Optional[str] = None
    factor_version: Optional[str] = None
    calculation_boundary: Optional[str] = None
    status: str = "Verified"
    created_at: str
    updated_at: str


class WasteSummaryResponse(BaseModel):
    total_waste_kg: float
    recycled_waste_kg: float
    recycling_rate_percent: Optional[float] = None
    total_calculated_emissions_kg: float
    record_count: int
    category_breakdown: List[Dict[str, Any]]
    treatment_breakdown: List[Dict[str, Any]]
    monthly_trends: List[Dict[str, Any]]
