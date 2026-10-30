import pytest
from httpx import AsyncClient


@pytest.fixture
async def auth_user_token(async_client: AsyncClient) -> str:
    payload = {
        "full_name": "Campus Transport Lead",
        "email": "transport_lead@carboniq.org",
        "password": "Password123!",
    }
    res = await async_client.post("/api/auth/register", json=payload)
    return res.json()["access_token"]


@pytest.mark.asyncio
async def test_bus_route_crud_operations(
    async_client: AsyncClient,
    auth_user_token: str,
    auth_header_helper,
):
    headers = auth_header_helper(auth_user_token)

    # 1. Create Route A (25 students, 40 capacity, 30 km)
    route_a = {
        "route_name": "Route Alpha",
        "start_location": "Hebbal",
        "destination": "Main Campus",
        "intermediate_stops": ["Hebbal", "Jakkur Cross", "Yelahanka"],
        "distance_km": 30.0,
        "duration_minutes": 50,
        "trips_per_day": 2,
        "operating_days_per_week": 5,
        "assigned_students": 25,
        "bus_id": "BUS-01",
        "fuel_type": "Diesel",
        "fuel_efficiency_km_per_l": 5.0,
        "seating_capacity": 40,
        "current_buses_count": 1,
    }
    r_a = await async_client.post("/api/transportation/routes", json=route_a, headers=headers)
    assert r_a.status_code == 201
    route_a_id = r_a.json()["id"]

    # 2. Get Route
    r_get = await async_client.get(f"/api/transportation/routes/{route_a_id}", headers=headers)
    assert r_get.status_code == 200
    assert r_get.json()["route_name"] == "Route Alpha"

    # 3. Update Route
    r_up = await async_client.put(
        f"/api/transportation/routes/{route_a_id}",
        json={"assigned_students": 24},
        headers=headers,
    )
    assert r_up.status_code == 200
    assert r_up.json()["assigned_students"] == 24

    # 4. Delete Route
    r_del = await async_client.delete(f"/api/transportation/routes/{route_a_id}", headers=headers)
    assert r_del.status_code == 200


@pytest.mark.asyncio
async def test_route_optimization_and_capacity_check(
    async_client: AsyncClient,
    auth_user_token: str,
    auth_header_helper,
):
    headers = auth_header_helper(auth_user_token)

    # Route A: 20 students, 40 seat bus, 30 km, destination: "Main Campus"
    route_a = {
        "route_name": "Route A",
        "start_location": "Hebbal",
        "destination": "Main Campus",
        "intermediate_stops": ["Hebbal", "Jakkur Cross"],
        "distance_km": 30.0,
        "duration_minutes": 45,
        "trips_per_day": 2,
        "assigned_students": 20,
        "bus_id": "BUS-01",
        "fuel_efficiency_km_per_l": 5.0,
        "seating_capacity": 40,
    }
    await async_client.post("/api/transportation/routes", json=route_a, headers=headers)

    # Route B: 15 students, 40 seat bus, 28 km, destination: "Main Campus" (Combined students: 35 <= 40 capacity)
    route_b = {
        "route_name": "Route B",
        "start_location": "Sahakar Nagar",
        "destination": "Main Campus",
        "intermediate_stops": ["Sahakar Nagar", "Jakkur Cross"],
        "distance_km": 28.0,
        "duration_minutes": 45,
        "trips_per_day": 2,
        "assigned_students": 15,
        "bus_id": "BUS-02",
        "fuel_efficiency_km_per_l": 5.0,
        "seating_capacity": 40,
    }
    await async_client.post("/api/transportation/routes", json=route_b, headers=headers)

    # Run optimization
    r_opt = await async_client.post("/api/transportation/optimize", headers=headers)
    assert r_opt.status_code == 200
    data = r_opt.json()
    assert data["analyzed_routes_count"] == 2
    assert len(data["proposals"]) == 1

    proposal = data["proposals"][0]
    assert proposal["capacity_check_passed"] is True
    assert proposal["current_config"]["students_served"] == 35
    assert proposal["proposed_config"]["buses_count"] == 1
    assert proposal["estimated_distance_reduction_km"] > 0
    assert proposal["estimated_fuel_savings_liters"] > 0
    assert proposal["estimated_monthly_savings_inr"] > 0

    # Save proposal as planned intervention
    r_accept = await async_client.post(
        "/api/transportation/optimize/accept",
        json=proposal,
        headers=headers,
    )
    assert r_accept.status_code == 201
    assert r_accept.json()["status"] == "accepted_for_planning"


@pytest.mark.asyncio
async def test_infeasible_route_handling_over_capacity(
    async_client: AsyncClient,
    auth_user_token: str,
    auth_header_helper,
):
    headers = auth_header_helper(auth_user_token)

    # Route 1: 30 students, 40 seat bus
    r1 = {
        "route_name": "Heavy Route 1",
        "start_location": "East Gate",
        "destination": "Main Campus",
        "distance_km": 25.0,
        "duration_minutes": 40,
        "assigned_students": 30,
        "bus_id": "BUS-E1",
        "seating_capacity": 40,
    }
    await async_client.post("/api/transportation/routes", json=r1, headers=headers)

    # Route 2: 25 students, 40 seat bus (Combined = 55 students > 40 max capacity -> INFEASIBLE)
    r2 = {
        "route_name": "Heavy Route 2",
        "start_location": "West Gate",
        "destination": "Main Campus",
        "distance_km": 20.0,
        "duration_minutes": 35,
        "assigned_students": 25,
        "bus_id": "BUS-W2",
        "seating_capacity": 40,
    }
    await async_client.post("/api/transportation/routes", json=r2, headers=headers)

    # Optimization engine must reject consolidation because student demand exceeds capacity
    r_opt = await async_client.post("/api/transportation/optimize", headers=headers)
    assert r_opt.status_code == 200
    assert len(r_opt.json()["proposals"]) == 0
