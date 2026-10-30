from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field


class HistoricalEmissionPoint(BaseModel):
    month: str = Field(..., description="Reporting month (YYYY-MM)")
    period: Optional[str] = Field(None, description="Alias for reporting month")
    value: float = Field(..., description="Total emissions in kg CO2e")
    electricity_emissions_kg: float = 0.0
    transportation_emissions_kg: float = 0.0
    waste_emissions_kg: float = 0.0
    is_forecast: bool = False
    data_quality: str = "measured"


class ForecastEmissionPoint(BaseModel):
    month: str = Field(..., description="Forecasted month (YYYY-MM)")
    period: Optional[str] = Field(None, description="Alias for forecasted month")
    value: float = Field(..., description="Predicted emissions in kg CO2e")
    predicted_emissions_kg: Optional[float] = Field(None, description="Predicted emissions in kg CO2e")
    unit: str = "kg CO2e"
    is_forecast: bool = True
    confidence_interval_lower: Optional[float] = None
    confidence_interval_upper: Optional[float] = None
    model_version: Optional[str] = None


class ModelMetadataInfo(BaseModel):
    model_name: str
    model_version: str
    format: str  # "joblib" | "pickle" | "keras" | "none"
    artifact_path: str
    is_loaded: bool
    algorithm: Optional[str] = "XGBoost Regressor Pipeline"
    feature_count: Optional[int] = None
    feature_names: Optional[List[str]] = None
    evaluation_metrics: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None


class EmissionTrendResponse(BaseModel):
    status: str  # "ready" | "model_artifact_missing" | "insufficient_data" | "error"
    message: str
    model_available: bool = True
    forecast_type: str = "monthly"
    target: str = "total_emissions_kg"
    unit: str = "kg CO2e"
    historical: List[Dict[str, Any]] = []
    predictions: List[Dict[str, Any]] = []
    historical_series: List[HistoricalEmissionPoint] = []
    forecast_series: List[ForecastEmissionPoint] = []
    combined_series: List[Dict[str, Any]] = []
    model_metrics: Optional[Dict[str, Any]] = None
    model_info: Optional[ModelMetadataInfo] = None
    limitations: Union[str, List[str]] = ""
