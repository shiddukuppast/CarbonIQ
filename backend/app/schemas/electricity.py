from typing import Any, Dict, List, Optional
from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_validator
from app.utils.dates import normalize_month


class ElectricityCreateRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    reporting_month: str = Field(
        ...,
        validation_alias=AliasChoices("reporting_month", "reportingMonth", "reporting_period", "month"),
        description="Reporting month (YYYY-MM or YYYY-MM-DD)",
    )
    consumption_kwh: float = Field(
        ...,
        validation_alias=AliasChoices("consumption_kwh", "consumptionKwh", "usage"),
        ge=0,
        description="Electricity consumption in kWh",
    )
    source: Optional[str] = Field(
        "Grid",
        validation_alias=AliasChoices("source", "electricity_source", "electricitySource"),
        description="Electricity source: Grid, Solar Rooftop, Green Tariff, Generator",
    )
    bill_amount_inr: Optional[float] = Field(
        None,
        validation_alias=AliasChoices("bill_amount_inr", "billAmountInr", "bill_amount", "cost"),
        ge=0,
        description="Optional recorded bill amount in INR",
    )
    building_or_department: Optional[str] = Field(
        None,
        validation_alias=AliasChoices("building_or_department", "buildingOrDepartment", "building", "department"),
        max_length=100,
    )
    notes: Optional[str] = Field(None, max_length=500)

    @field_validator("reporting_month")
    @classmethod
    def validate_month(cls, v: str) -> str:
        norm = normalize_month(v)
        if len(norm) != 7 or norm[4] != "-":
            raise ValueError("Reporting month must be in format YYYY-MM")
        return norm


class ElectricityUpdateRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    reporting_month: Optional[str] = Field(
        None,
        validation_alias=AliasChoices("reporting_month", "reportingMonth", "reporting_period", "month"),
    )
    consumption_kwh: Optional[float] = Field(
        None,
        validation_alias=AliasChoices("consumption_kwh", "consumptionKwh", "usage"),
        ge=0,
    )
    source: Optional[str] = Field(
        None,
        validation_alias=AliasChoices("source", "electricity_source", "electricitySource"),
    )
    bill_amount_inr: Optional[float] = Field(
        None,
        validation_alias=AliasChoices("bill_amount_inr", "billAmountInr", "bill_amount", "cost"),
        ge=0,
    )
    building_or_department: Optional[str] = Field(
        None,
        validation_alias=AliasChoices("building_or_department", "buildingOrDepartment", "building", "department"),
    )
    notes: Optional[str] = None

    @field_validator("reporting_month")
    @classmethod
    def validate_month(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            norm = normalize_month(v)
            if len(norm) != 7 or norm[4] != "-":
                raise ValueError("Reporting month must be in format YYYY-MM")
            return norm
        return v


class ElectricityRecordResponse(BaseModel):
    id: str
    workspace_id: str
    reporting_month: str
    consumption_kwh: float
    source: Optional[str] = "Grid"
    bill_amount_inr: Optional[float] = None
    building_or_department: Optional[str] = None
    notes: Optional[str] = None
    calculated_emissions_kg: float
    emission_factor_used: float
    factor_id: Optional[str] = None
    factor_type: str
    factor_source: Optional[str] = None
    factor_version: Optional[str] = None
    calculation_boundary: Optional[str] = None
    created_at: str
    updated_at: str


class MonthlyElectricityTrend(BaseModel):
    reporting_month: str
    consumption_kwh: float
    bill_amount_inr: float
    calculated_emissions_kg: float


class ElectricitySummaryResponse(BaseModel):
    total_consumption_kwh: float
    total_bill_inr: float
    total_calculated_emissions_kg: float
    record_count: int
    monthly_trends: List[MonthlyElectricityTrend]
    department_breakdown: List[Dict[str, Any]]
    previous_period_comparison: Optional[Dict[str, Any]] = None
