import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from httpx import AsyncClient
import numpy as np
from app.data.emission_factors import EMISSION_FACTORS, get_emission_factor
from app.services.ml_prediction_service import MlPredictionService


@pytest.fixture
async def multi_month_workspace(async_client: AsyncClient, auth_header_helper):
    reg = {
        "full_name": "Climate Analyst",
        "email": "analyst@carboniq.org",
        "password": "Password123!",
        "workspace_name": "Analyst Testing Lab",
    }
    r_reg = await async_client.post("/api/auth/register", json=reg)
    token = r_reg.json()["access_token"]
    headers = auth_header_helper(token)

    # Month 1 (2026-01)
    await async_client.post(
        "/api/electricity",
        json={"reporting_month": "2026-01", "consumption_kwh": 1000.0, "source": "Grid"},
        headers=headers,
    )
    await async_client.post(
        "/api/transportation",
        json={"date": "2026-01-15", "mode": "Bus", "distance_km": 400.0, "fuel_consumed_liters": 80.0, "route_name": "North Shuttle", "vehicle_capacity": 45},
        headers=headers,
    )
    await async_client.post(
        "/api/waste",
        json={"date": "2026-01-20", "category": "Recyclable", "quantity_kg": 150.0, "treatment_method": "Recycling", "unit": "kg"},
        headers=headers,
    )

    # Month 2 (2026-02)
    await async_client.post(
        "/api/electricity",
        json={"reporting_month": "2026-02", "consumption_kwh": 1200.0, "source": "Grid"},
        headers=headers,
    )
    await async_client.post(
        "/api/transportation",
        json={"date": "2026-02-15", "mode": "Bus", "distance_km": 450.0, "fuel_consumed_liters": 90.0, "route_name": "North Shuttle", "vehicle_capacity": 45},
        headers=headers,
    )
    await async_client.post(
        "/api/waste",
        json={"date": "2026-02-20", "category": "General", "quantity_kg": 200.0, "treatment_method": "Landfill", "unit": "kg"},
        headers=headers,
    )

    return {"headers": headers, "token": token}


@pytest.mark.asyncio
async def test_emission_factors_registry_endpoint(async_client: AsyncClient):
    """Verifies that the factor registry returns CEA, GHG Protocol, IPCC, and EPA factors."""
    r = await async_client.get("/api/emissions/factors")
    assert r.status_code == 200
    factors = r.json()
    assert len(factors) >= 8

    factor_ids = [f["factor_id"] for f in factors]
    assert "grid_in_cea_baseline" in factor_ids
    assert "grid_in_cea_weighted_average" in factor_ids
    assert "fuel_diesel_standard" in factor_ids
    assert "waste_recycling" in factor_ids

    # Check CEA provenance metadata
    cea_factor = next(f for f in factors if f["factor_id"] == "grid_in_cea_weighted_average")
    assert "Central Electricity Authority" in cea_factor["source"]
    assert cea_factor["is_authoritative"] is True
    assert cea_factor["value"] == 0.716
    assert "Scope 2" in cea_factor["calculation_boundary"]


@pytest.mark.asyncio
async def test_emissions_factors_filter_by_activity(async_client: AsyncClient):
    r = await async_client.get("/api/emissions/factors?activity_type=electricity")
    assert r.status_code == 200
    factors = r.json()
    assert all(f["activity_type"] == "electricity" for f in factors)


@pytest.mark.asyncio
async def test_ml_model_info_endpoint(async_client: AsyncClient):
    r = await async_client.get("/api/emissions/model-info")
    assert r.status_code == 200
    info = r.json()
    assert "model_name" in info
    assert "format" in info
    assert "is_loaded" in info


@pytest.mark.asyncio
async def test_emissions_trend_insufficient_data(async_client: AsyncClient, auth_header_helper):
    """When workspace has fewer than 2 monthly periods, returns status 'insufficient_data'."""
    reg = {
        "full_name": "New User",
        "email": "single@carboniq.org",
        "password": "Password123!",
        "workspace_name": "Single Month Corp",
    }
    r_reg = await async_client.post("/api/auth/register", json=reg)
    headers = auth_header_helper(r_reg.json()["access_token"])

    # Log only 1 month
    await async_client.post(
        "/api/electricity",
        json={"reporting_month": "2026-05", "consumption_kwh": 500.0},
        headers=headers,
    )

    r = await async_client.get("/api/emissions/trend", headers=headers)
    assert r.status_code == 200
    res = r.json()
    assert res["status"] == "insufficient_data"
    assert len(res["forecast_series"]) == 0
    assert len(res["historical_series"]) == 1
    assert "2 distinct monthly" in res["message"]


@pytest.mark.asyncio
async def test_emissions_trend_missing_artifact_graceful_handling(
    async_client: AsyncClient,
    multi_month_workspace,
):
    """
    When model artifact is missing, system must NOT invent predictions or substitute fake values.
    Returns status 'model_artifact_missing' while preserving real historical data.
    """
    headers = multi_month_workspace["headers"]
    r = await async_client.get("/api/emissions/trend?horizon=3", headers=headers)
    assert r.status_code == 200
    res = r.json()

    # Model is not placed yet in backend/app/models/
    assert res["status"] in ["model_artifact_missing", "ready"]
    if res["status"] == "model_artifact_missing":
        assert len(res["forecast_series"]) == 0
        assert len(res["historical_series"]) == 2
        assert "Place 'emission_trend_model.joblib'" in res["message"]
        assert not res["combined_series"][0]["is_forecast"]


@pytest.mark.asyncio
async def test_frontend_additional_fields_persisted(
    async_client: AsyncClient,
    multi_month_workspace,
):
    """
    Verifies that new frontend fields (source, vehicle_capacity, route_name, unit)
    are accepted and persisted in MongoDB documents.
    """
    headers = multi_month_workspace["headers"]

    # Electricity with source
    r_elec = await async_client.get("/api/electricity", headers=headers)
    assert r_elec.status_code == 200
    elec_records = r_elec.json()
    assert len(elec_records) >= 2
    assert elec_records[0]["source"] == "Grid"

    # Transportation with route_name, vehicle_capacity
    r_trans = await async_client.get("/api/transportation", headers=headers)
    assert r_trans.status_code == 200
    trans_records = r_trans.json()
    assert len(trans_records) >= 2
    assert trans_records[0]["route_name"] == "North Shuttle"
    assert trans_records[0]["vehicle_capacity"] == 45

    # Waste with unit
    r_waste = await async_client.get("/api/waste", headers=headers)
    assert r_waste.status_code == 200
    waste_records = r_waste.json()
    assert len(waste_records) >= 2
    assert waste_records[0]["unit"] == "kg"


@pytest.mark.asyncio
async def test_ai_insights_cross_category_experience(
    async_client: AsyncClient,
    multi_month_workspace,
):
    """
    Verifies LLM Experience 4: Main AI Insights Assistant with cross-category synthesis.
    """
    headers = multi_month_workspace["headers"]
    mock_choice = MagicMock()
    mock_choice.message.content = "Electricity is your largest emission source. Observed reductions are measured from operational utility data."
    mock_resp = MagicMock(choices=[mock_choice])

    with patch("app.core.config.settings.GROQ_API_KEY", "gsk_test"), \
         patch("app.services.ai_assistant_service.AsyncGroq") as mock_groq_cls:
        mock_instance = MagicMock()
        mock_instance.chat.completions.create = AsyncMock(return_value=mock_resp)
        mock_groq_cls.return_value = mock_instance

        # 1. Largest emission source
        r1 = await async_client.post(
            "/api/ai/insights",
            json={"question": "What is my largest emission source?"},
            headers=headers,
        )
        assert r1.status_code == 200
        data1 = r1.json()
        assert "Electricity" in data1["content"] or "Transportation" in data1["content"]
        assert "calculation_breakdown" in data1
        assert data1["calculation_breakdown"] is not None

        # 2. Prioritize actions
        r2 = await async_client.post(
            "/api/ai/insights",
            json={"question": "What should we prioritise to reduce emissions?"},
            headers=headers,
        )
        assert r2.status_code == 200
        data2 = r2.json()
        assert len(data2["content"]) > 10

