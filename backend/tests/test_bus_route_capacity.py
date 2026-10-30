import pytest
from httpx import AsyncClient

@pytest.fixture
async def auth_user_token(async_client: AsyncClient) -> str:
    payload = {
        "full_name": "Transport Lead",
        "email": "transport_lead@carboniq.org",
        "password": "Password123!",
    }
    res = await async_client.post("/api/auth/register", json=payload)
    return res.json()["access_token"]

@pytest.mark.asyncio
async def test_route_capacity_validation(auth_user_token: str, async_client: AsyncClient, auth_header_helper):
    headers = auth_header_helper(auth_user_token)
    # Overcapacity case
    over_route = {
        "route_name": "Overflow",
        "start_location": "A",
        "destination": "B",
        "intermediate_stops": [],
        "distance_km": 10.0,
        "duration_minutes": 20,
        "trips_per_day": 1,
        "operating_days_per_week": 5,
        "assigned_students": 50,
        "bus_id": "BUS-99",
        "fuel_type": "Diesel",
        "fuel_efficiency_km_per_l": 5.0,
        "seating_capacity": 40,
        "current_buses_count": 1,
    }
    resp = await async_client.post("/api/transportation/routes", json=over_route, headers=headers)
    assert resp.status_code == 422
    # Valid case
    valid_route = over_route.copy()
    valid_route["assigned_students"] = 25
    valid_route["route_name"] = "Valid"
    resp2 = await async_client.post("/api/transportation/routes", json=valid_route, headers=headers)
    assert resp2.status_code == 201
    data = resp2.json()
    assert data["assigned_students"] == 25
    assert data["seating_capacity"] == 40
    assert data["status"] == "active"
