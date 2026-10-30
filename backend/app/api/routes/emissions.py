from typing import Any, List, Optional
from fastapi import APIRouter, Depends, Query
from app.api.dependencies import get_current_workspace_id, get_db_dep
from app.data.emission_factors import (
    EmissionFactor,
    get_factors_by_activity,
    list_emission_factors,
)
from app.schemas.ml import EmissionTrendResponse, ModelMetadataInfo
from app.services.ml_prediction_service import MlPredictionService

router = APIRouter(prefix="/emissions", tags=["Emissions & ML Forecasting"])


@router.get("/trend", response_model=EmissionTrendResponse)
async def get_emissions_trend_and_forecast(
    horizon: int = Query(3, ge=1, le=12, description="Forecast horizon in months (1-12)"),
    workspace_id: str = Depends(get_current_workspace_id),
    db: Any = Depends(get_db_dep),
) -> EmissionTrendResponse:
    """
    Returns historical monthly emissions along with an ML-predicted forward forecast.
    Enforces strict safeguards: requires real historical records; distinguishes historical
    observations from modeled predictions; never fabricates fake predictions if the pre-trained
    model artifact is missing.
    """
    return await MlPredictionService.get_emissions_trend_forecast(
        workspace_id=workspace_id,
        db=db,
        forecast_horizon_months=horizon,
    )


@router.get("/factors", response_model=List[dict])
async def get_emission_factors_catalog(
    activity_type: Optional[str] = Query(None, description="Filter by activity: electricity, transportation, waste"),
) -> List[dict]:
    """
    Returns the authoritative emission factor registry with complete provenance metadata,
    including Central Electricity Authority (CEA) v19/v20, GHG Protocol, IPCC, and EPA WARM sources.
    """
    if activity_type:
        factors = get_factors_by_activity(activity_type)
    else:
        factors = list_emission_factors()

    return [
        {
            "factor_id": f.factor_id,
            "activity_type": f.activity_type,
            "sub_category": f.sub_category,
            "value": f.value,
            "unit": f.unit,
            "geography": f.geography,
            "reporting_period": f.reporting_period,
            "source": f.source,
            "version": f.version,
            "is_authoritative": f.is_authoritative,
            "calculation_boundary": f.calculation_boundary,
            "notes": f.notes,
        }
        for f in factors
    ]


@router.get("/model-info", response_model=ModelMetadataInfo)
async def get_ml_model_status() -> ModelMetadataInfo:
    """
    Returns status and feature requirements of the configured pre-trained ML model artifact.
    """
    return MlPredictionService.get_model_info()

