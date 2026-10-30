import pytest
from httpx import AsyncClient


@pytest.fixture
async def auth_user_token(async_client: AsyncClient) -> str:
    payload = {
        "full_name": "Waste Coordinator",
        "email": "waste@carboniq.org",
        "password": "Password123!",
    }
    res = await async_client.post("/api/auth/register", json=payload)
    return res.json()["access_token"]


@pytest.mark.asyncio
async def test_waste_crud_and_emissions(
    async_client: AsyncClient,
    auth_user_token: str,
    auth_header_helper,
):
    headers = auth_header_helper(auth_user_token)

    # 1. Log Composting: 100 kg × 0.10 kg CO2e/kg = 10.0 kg CO2e
    c_payload = {
        "date": "2026-03-01",
        "category": "Biodegradable",
        "quantity_kg": 100.0,
        "treatment_method": "Composting",
    }
    r1 = await async_client.post("/api/waste", json=c_payload, headers=headers)
    assert r1.status_code == 201
    assert r1.json()["calculated_emissions_kg"] == 10.0
    rec_id = r1.json()["id"]

    # 2. Log Recycling: 100 kg × (-0.45) kg CO2e/kg = -45.0 kg CO2e (Avoided emissions credit)
    r_payload = {
        "date": "2026-03-05",
        "category": "Recyclable",
        "quantity_kg": 100.0,
        "treatment_method": "Recycling",
    }
    r2 = await async_client.post("/api/waste", json=r_payload, headers=headers)
    assert r2.status_code == 201
    assert r2.json()["calculated_emissions_kg"] == -45.0

    # 3. Log Landfill: 200 kg × 1.25 kg CO2e/kg = 250.0 kg CO2e
    l_payload = {
        "date": "2026-03-10",
        "category": "General",
        "quantity_kg": 200.0,
        "treatment_method": "Landfill",
    }
    r3 = await async_client.post("/api/waste", json=l_payload, headers=headers)
    assert r3.status_code == 201
    assert r3.json()["calculated_emissions_kg"] == 250.0

    # Total Waste: 100 + 100 + 200 = 400 kg. Recycled: 100 kg -> Rate: (100 / 400) * 100 = 25.0%
    # Total net emissions: 10 - 45 + 250 = 215.0 kg CO2e
    r_sum = await async_client.get("/api/waste/summary", headers=headers)
    assert r_sum.status_code == 200
    summary = r_sum.json()
    assert summary["total_waste_kg"] == 400.0
    assert summary["recycled_waste_kg"] == 100.0
    assert summary["recycling_rate_percent"] == 25.0
    assert summary["total_calculated_emissions_kg"] == 215.0

    # 4. Update
    r_up = await async_client.put(f"/api/waste/{rec_id}", json={"quantity_kg": 150.0}, headers=headers)
    assert r_up.status_code == 200
    assert r_up.json()["calculated_emissions_kg"] == 15.0

    # 5. Delete
    r_del = await async_client.delete(f"/api/waste/{rec_id}", headers=headers)
    assert r_del.status_code == 200
