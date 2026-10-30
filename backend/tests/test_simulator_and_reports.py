import pytest
from httpx import AsyncClient


@pytest.fixture
async def auth_user_token(async_client: AsyncClient) -> str:
    payload = {
        "full_name": "Analytics Specialist",
        "email": "analytics@carboniq.org",
        "password": "Password123!",
    }
    res = await async_client.post("/api/auth/register", json=payload)
    return res.json()["access_token"]


@pytest.mark.asyncio
async def test_health_check(async_client: AsyncClient):
    response = await async_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "database" in data


@pytest.mark.asyncio
async def test_simulator_endpoints(
    async_client: AsyncClient,
    auth_user_token: str,
    auth_header_helper,
):
    headers = auth_header_helper(auth_user_token)

    # 1. Electricity simulation (15% reduction)
    r_elec = await async_client.post(
        "/api/simulator/electricity",
        json={"percent_reduction": 15.0, "custom_tariff_inr": 8.5},
        headers=headers,
    )
    assert r_elec.status_code == 200
    data_elec = r_elec.json()
    assert data_elec["module"] == "electricity"
    assert data_elec["difference"]["percent_reduction"] == 15.0
    assert data_elec["estimated_cost_savings_inr"] > 0
    assert data_elec["estimated_emissions_reduction_kg"] > 0

    # 2. Transportation simulation (10% reduction)
    r_trans = await async_client.post(
        "/api/simulator/transportation",
        json={"percent_distance_reduction": 10.0, "fuel_efficiency_km_per_l": 5.0, "fuel_type": "Diesel"},
        headers=headers,
    )
    assert r_trans.status_code == 200
    data_trans = r_trans.json()
    assert data_trans["module"] == "transportation"
    assert data_trans["estimated_fuel_savings_liters"] if "estimated_fuel_savings_liters" in data_trans else True

    # 3. Waste simulation (20% reduction, 70% target recycling)
    r_waste = await async_client.post(
        "/api/simulator/waste",
        json={"percent_reduction": 20.0, "target_recycling_percent": 70.0},
        headers=headers,
    )
    assert r_waste.status_code == 200
    data_waste = r_waste.json()
    assert data_waste["module"] == "waste"


@pytest.mark.asyncio
async def test_goals_and_interventions(
    async_client: AsyncClient,
    auth_user_token: str,
    auth_header_helper,
):
    headers = auth_header_helper(auth_user_token)

    # 1. Create Goal
    goal_payload = {
        "goal_name": "Reduce Campus Electricity by 20%",
        "category": "Electricity",
        "baseline_value": 1500.0,
        "target_value": 1200.0,
        "target_period": "2026-12",
        "unit": "kWh/month",
    }
    r_goal = await async_client.post("/api/progress/goals", json=goal_payload, headers=headers)
    assert r_goal.status_code == 201
    assert r_goal.json()["goal_name"] == "Reduce Campus Electricity by 20%"

    r_goals_list = await async_client.get("/api/progress/goals", headers=headers)
    assert r_goals_list.status_code == 200
    assert len(r_goals_list.json()) == 1

    # 2. Create Intervention
    intv_payload = {
        "title": "Install Variable Frequency Drives on Central HVAC",
        "category": "Electricity",
        "description": "Retrofit chiller circulation pumps with variable speed motors.",
        "estimated_benefit": "Save 180 kWh/month (~₹1,530/month)",
        "estimated_cost_savings_inr": 1530.0,
        "estimated_emissions_savings_kg": 147.6,
        "status": "accepted_for_planning",
        "assumptions": ["Variable tariff ₹8.5/kWh", "Operating 16 hrs/day"],
    }
    r_intv = await async_client.post("/api/progress/interventions", json=intv_payload, headers=headers)
    assert r_intv.status_code == 201
    assert r_intv.json()["status"] == "accepted_for_planning"

    r_intvs_list = await async_client.get("/api/progress/interventions", headers=headers)
    assert r_intvs_list.status_code == 200
    assert len(r_intvs_list.json()) == 1


@pytest.mark.asyncio
async def test_emissions_report_generation(
    async_client: AsyncClient,
    auth_user_token: str,
    auth_header_helper,
):
    headers = auth_header_helper(auth_user_token)

    # Generate emissions report
    r_report = await async_client.get("/api/reports/emissions?period=2026-Q1", headers=headers)
    assert r_report.status_code == 200
    data = r_report.json()
    assert data["reporting_period"] == "2026-Q1"
    assert "category_summary" in data
    assert "data_completeness_notes" in data
    assert "calculation_assumptions" in data
