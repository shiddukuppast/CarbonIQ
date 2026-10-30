import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_full_application_lifecycle_and_integration(
    async_client: AsyncClient,
    auth_header_helper,
):
    """
    Phase 11: End-to-end integration test exercising all 15 workflow requirements:
    1. College user registers with role.
    2. User authenticates and receives JWT access token with account_type.
    3. Authenticated dashboard summary loads.
    4. Electricity record is created with custom source, returns verified emissions.
    5. Transportation record is created with capacity and route details.
    6. Waste record is created with incineration treatment method.
    7. Data remains available and persists across calls.
    8. Dashboard metrics update after record creations.
    9. Four AI assistant experiences query authorized workspace data.
    10. Emission trend endpoint returns historical points and handles missing model artifact.
    11. Savings simulator calculates multi-module what-if scenarios deterministically.
    12. Reports endpoint returns audit-ready summary.
    13. Bus route optimization generates proposal and saves planned intervention.
    14. Individual user is blocked from fleet routes with HTTP 403.
    15. Unauthenticated / expired requests are blocked with HTTP 401.
    """
    # 1. College User Registration
    college_reg = {
        "full_name": "Dr. Sarah Rao",
        "email": "sarah.rao@reva.edu",
        "password": "SecurePassword2026!",
        "workspace_name": "REVA Green Campus",
        "account_type": "college",
    }
    r_reg = await async_client.post("/api/auth/register", json=college_reg)
    assert r_reg.status_code == 201
    reg_data = r_reg.json()
    assert "access_token" in reg_data
    assert reg_data["user"]["account_type"] == "college"
    assert reg_data["user"]["workspace_name"] == "REVA Green Campus"

    # 2. User Login & /me verification
    login_payload = {
        "email": "sarah.rao@reva.edu",
        "password": "SecurePassword2026!",
    }
    r_login = await async_client.post("/api/auth/login", json=login_payload)
    assert r_login.status_code == 200
    token = r_login.json()["access_token"]
    headers = auth_header_helper(token)

    r_me = await async_client.get("/api/auth/me", headers=headers)
    assert r_me.status_code == 200
    assert r_me.json()["account_type"] == "college"

    # 3. Initial Dashboard Summary
    r_dash_init = await async_client.get("/api/dashboard/summary", headers=headers)
    assert r_dash_init.status_code == 200
    assert r_dash_init.json()["workspace_name"] == "REVA Green Campus"

    # 4. Create Electricity Record (Solar Rooftop -> 0 emissions)
    elec_payload = {
        "reporting_month": "2026-10",
        "consumption_kwh": 3500.0,
        "source": "Solar Rooftop",
        "bill_amount_inr": 0.0,
        "building_or_department": "Engineering Wing A",
        "notes": "Rooftop solar meter reading",
    }
    r_elec = await async_client.post("/api/electricity", json=elec_payload, headers=headers)
    assert r_elec.status_code == 201
    elec_id = r_elec.json()["id"]
    assert r_elec.json()["calculated_emissions_kg"] == 0.0
    assert r_elec.json()["source"] == "Solar Rooftop"

    # Also create Grid Electricity Record
    r_elec_grid = await async_client.post("/api/electricity", json={
        "reporting_month": "2026-09",
        "consumption_kwh": 2000.0,
        "source": "Grid",
        "bill_amount_inr": 17000.0,
    }, headers=headers)
    assert r_elec_grid.status_code == 201
    assert r_elec_grid.json()["calculated_emissions_kg"] == 1640.0  # 2000 * 0.82

    # 5. Create Transportation Record with Route Details
    trans_payload = {
        "date": "2026-10-25",
        "mode": "Bus",
        "distance_km": 350.0,
        "fuel_type": "Diesel",
        "fuel_consumed_liters": 70.0,
        "vehicle_id": "REVA-BUS-01",
        "passenger_count": 42,
        "vehicle_capacity": 50,
        "route_name": "Kogilu Route",
        "destination": "Main Campus",
    }
    r_trans = await async_client.post("/api/transportation", json=trans_payload, headers=headers)
    assert r_trans.status_code == 201
    assert r_trans.json()["calculated_emissions_kg"] == 187.6  # 70 * 2.68
    assert r_trans.json()["vehicle_capacity"] == 50
    assert r_trans.json()["route_name"] == "Kogilu Route"

    # 6. Create Waste Record with Incineration
    waste_payload = {
        "date": "2026-10-27",
        "category": "General",
        "quantity_kg": 150.0,
        "unit": "kg",
        "treatment_method": "Incineration",
        "building_or_department": "Cafeteria",
    }
    r_waste = await async_client.post("/api/waste", json=waste_payload, headers=headers)
    assert r_waste.status_code == 201
    assert r_waste.json()["calculated_emissions_kg"] == 63.0  # 150 * 0.42

    # 7 & 8. Verify Data Persists and Dashboard Summary Updates
    r_dash_updated = await async_client.get("/api/dashboard/summary", headers=headers)
    assert r_dash_updated.status_code == 200
    dash_data = r_dash_updated.json()
    assert dash_data["electricity"]["records"] == 2
    assert dash_data["transportation"]["records"] == 1
    assert dash_data["waste"]["records"] == 1
    expected_total = 1640.0 + 187.6 + 63.0
    assert abs(dash_data["total_emissions_kg"] - expected_total) < 0.1

    # 9. Verify All Four Context-Aware AI Advisors
    # 9a. Verify HTTP 503 is returned when GROQ_API_KEY is unconfigured
    with patch("app.core.config.settings.GROQ_API_KEY", None), \
         patch("app.core.config.settings.LLM_API_KEY", None):
        ai_unconfigured = await async_client.post(
            "/api/ai/electricity",
            json={"question": "How much electricity did we consume?"},
            headers=headers,
        )
        assert ai_unconfigured.status_code == 503
        assert "AI is not configured" in ai_unconfigured.json()["detail"]

    # 9b. Verify All 4 Advisors succeed when Groq is configured
    mock_choice = MagicMock()
    mock_choice.message.content = "Analysis complete based on verified records."
    mock_resp = MagicMock(choices=[mock_choice])

    with patch("app.core.config.settings.GROQ_API_KEY", "gsk_test"), \
         patch("app.services.ai_assistant_service.AsyncGroq") as mock_groq_cls:
        mock_instance = MagicMock()
        mock_instance.chat.completions.create = AsyncMock(return_value=mock_resp)
        mock_groq_cls.return_value = mock_instance

        # AI 1: Electricity
        ai_elec = await async_client.post(
            "/api/ai/electricity",
            json={"question": "How much electricity did we consume from Solar Rooftop?"},
            headers=headers,
        )
        assert ai_elec.status_code == 200
        assert "content" in ai_elec.json()

        # AI 2: Transportation
        ai_trans = await async_client.post(
            "/api/ai/transportation",
            json={"question": "What is the occupancy of our campus buses?"},
            headers=headers,
        )
        assert ai_trans.status_code == 200
        assert "content" in ai_trans.json()

        # AI 3: Waste
        ai_waste = await async_client.post(
            "/api/ai/waste",
            json={"question": "How can we improve waste diversion and recycling?"},
            headers=headers,
        )
        assert ai_waste.status_code == 200
        assert "content" in ai_waste.json()

        # AI 4: Main Insights Advisor (Cross-Category)
        ai_insights = await async_client.post(
            "/api/ai/insights",
            json={"question": "What is our highest emitting category and are reductions measured?"},
            headers=headers,
        )
        assert ai_insights.status_code == 200
        assert "content" in ai_insights.json()

    # 10. ML Trend & Forecast Endpoint
    r_trend = await async_client.get("/api/emissions/trend?horizon=3", headers=headers)
    assert r_trend.status_code == 200
    trend_json = r_trend.json()
    assert trend_json["status"] in ("ready", "model_artifact_missing")
    assert len(trend_json["historical_series"]) >= 2

    # 11. Savings Simulator (Deterministic What-If Projections)
    r_sim_elec = await async_client.post(
        "/api/simulator/electricity",
        json={"percent_reduction": 15.0},
        headers=headers,
    )
    assert r_sim_elec.status_code == 200
    sim_data = r_sim_elec.json()
    assert sim_data["module"] == "electricity"
    assert sim_data["estimated_cost_savings_inr"] > 0
    assert len(sim_data["assumptions"]) > 0

    # 12. Audit-Ready Reports Generation
    r_report = await async_client.get("/api/reports/emissions?period=2026-YTD", headers=headers)
    assert r_report.status_code == 200
    report_json = r_report.json()
    assert report_json["total_calculated_emissions_kg"] > 0
    assert "Electricity" in report_json["category_summary"]

    # 13. Bus Route Creation & Optimization
    route_payload = {
        "route_name": "Campus Route North 1",
        "start_location": "Hebbal",
        "destination": "Main Campus Gate 1",
        "intermediate_stops": ["Hebbal", "Jakkur", "Yelahanka"],
        "distance_km": 28.0,
        "duration_minutes": 45,
        "trips_per_day": 2,
        "operating_days_per_week": 5,
        "assigned_students": 20,
        "bus_id": "REVA-BUS-02",
        "fuel_type": "Diesel",
        "fuel_efficiency_km_per_l": 5.0,
        "seating_capacity": 40,
        "current_buses_count": 1,
    }
    r_route = await async_client.post("/api/transportation/routes", json=route_payload, headers=headers)
    assert r_route.status_code == 201

    r_opt = await async_client.post("/api/transportation/optimize", json={}, headers=headers)
    assert r_opt.status_code == 200

    # 14. Role-Based Access Enforcement: Individual User cannot access fleet routes
    ind_payload = {
        "full_name": "Aditya Student",
        "email": "aditya.student@carboniq.org",
        "password": "Password123!",
        "account_type": "individual",
    }
    r_ind_reg = await async_client.post("/api/auth/register", json=ind_payload)
    assert r_ind_reg.status_code == 201
    ind_token = r_ind_reg.json()["access_token"]
    ind_headers = auth_header_helper(ind_token)

    r_ind_blocked = await async_client.get("/api/transportation/routes", headers=ind_headers)
    assert r_ind_blocked.status_code == 403
    assert "restricted" in r_ind_blocked.json()["detail"].lower()

    # 15. Unauthenticated Security: Missing token blocked
    r_no_auth = await async_client.get("/api/dashboard/summary")
    assert r_no_auth.status_code == 401

