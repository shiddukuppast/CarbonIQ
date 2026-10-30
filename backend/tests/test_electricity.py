import pytest
from httpx import AsyncClient


@pytest.fixture
async def auth_user_token(async_client: AsyncClient) -> str:
    payload = {
        "full_name": "Energy Analyst",
        "email": "energy@carboniq.org",
        "password": "Password123!",
    }
    res = await async_client.post("/api/auth/register", json=payload)
    return res.json()["access_token"]


@pytest.mark.asyncio
async def test_electricity_crud_and_calculations(
    async_client: AsyncClient,
    auth_user_token: str,
    auth_header_helper,
):
    headers = auth_header_helper(auth_user_token)

    # 1. Create record (1,000 kWh -> 0.82 kg CO2e/kWh factor -> 820 kg CO2e)
    create_payload = {
        "reporting_month": "2026-03",
        "consumption_kwh": 1000.0,
        "bill_amount_inr": 8500.0,
        "building_or_department": "Engineering Wing",
        "notes": "March baseline reading",
    }
    r_create = await async_client.post("/api/electricity", json=create_payload, headers=headers)
    assert r_create.status_code == 201
    created = r_create.json()
    assert created["consumption_kwh"] == 1000.0
    assert created["bill_amount_inr"] == 8500.0
    assert created["building_or_department"] == "Engineering Wing"
    assert created["calculated_emissions_kg"] == 820.0
    assert created["emission_factor_used"] == 0.82
    record_id = created["id"]

    # 2. Get record by ID
    r_get = await async_client.get(f"/api/electricity/{record_id}", headers=headers)
    assert r_get.status_code == 200
    assert r_get.json()["id"] == record_id

    # 3. List records
    r_list = await async_client.get("/api/electricity", headers=headers)
    assert r_list.status_code == 200
    assert len(r_list.json()) == 1

    # 4. Filter by month
    r_filtered = await async_client.get("/api/electricity?month=2026-03", headers=headers)
    assert r_filtered.status_code == 200
    assert len(r_filtered.json()) == 1

    r_empty_month = await async_client.get("/api/electricity?month=2025-01", headers=headers)
    assert len(r_empty_month.json()) == 0

    # 5. Update record (Update to 1,500 kWh -> should recalculate to 1230.0 kg CO2e)
    update_payload = {"consumption_kwh": 1500.0}
    r_update = await async_client.put(f"/api/electricity/{record_id}", json=update_payload, headers=headers)
    assert r_update.status_code == 200
    assert r_update.json()["consumption_kwh"] == 1500.0
    assert r_update.json()["calculated_emissions_kg"] == 1230.0

    # 6. Summary endpoint
    r_summary = await async_client.get("/api/electricity/summary", headers=headers)
    assert r_summary.status_code == 200
    summary = r_summary.json()
    assert summary["total_consumption_kwh"] == 1500.0
    assert summary["total_calculated_emissions_kg"] == 1230.0
    assert len(summary["monthly_trends"]) == 1

    # 7. Delete record
    r_del = await async_client.delete(f"/api/electricity/{record_id}", headers=headers)
    assert r_del.status_code == 200

    # Confirm deletion
    r_check = await async_client.get(f"/api/electricity/{record_id}", headers=headers)
    assert r_check.status_code == 404


@pytest.mark.asyncio
async def test_electricity_input_validation(
    async_client: AsyncClient,
    auth_user_token: str,
    auth_header_helper,
):
    headers = auth_header_helper(auth_user_token)

    # Negative consumption must be rejected
    invalid_payload = {
        "reporting_month": "2026-03",
        "consumption_kwh": -50.0,
    }
    r = await async_client.post("/api/electricity", json=invalid_payload, headers=headers)
    assert r.status_code == 422

    # Malformed month string must be rejected
    bad_month_payload = {
        "reporting_month": "invalid-month-date",
        "consumption_kwh": 100.0,
    }
    r_month = await async_client.post("/api/electricity", json=bad_month_payload, headers=headers)
    assert r_month.status_code == 422


@pytest.mark.asyncio
async def test_electricity_field_aliases_and_persistence(
    async_client: AsyncClient,
    auth_user_token: str,
    auth_header_helper,
):
    headers = auth_header_helper(auth_user_token)

    # Create using Postman field names: bill_amount and building
    postman_payload = {
        "reporting_month": "2026-03",
        "consumption_kwh": 1240.0,
        "bill_amount": 10540.0,
        "building": "Engineering Academic Wing",
        "notes": "Post semester break energy audit",
    }
    r_create = await async_client.post("/api/electricity", json=postman_payload, headers=headers)
    assert r_create.status_code == 201
    created = r_create.json()
    assert created["consumption_kwh"] == 1240.0
    assert created["bill_amount_inr"] == 10540.0
    assert created["building_or_department"] == "Engineering Academic Wing"
    assert created["calculated_emissions_kg"] == 1016.8
    assert created["emission_factor_used"] == 0.82
    assert created["factor_type"] == "illustrative_grid_factor"
    record_id = created["id"]

    # Verify persistence via GET
    r_get = await async_client.get(f"/api/electricity/{record_id}", headers=headers)
    assert r_get.status_code == 200
    fetched = r_get.json()
    assert fetched["bill_amount_inr"] == 10540.0
    assert fetched["building_or_department"] == "Engineering Academic Wing"

    # Update using alias fields
    update_payload = {
        "bill_amount": 11200.0,
        "building": "Main Administrative Block",
    }
    r_update = await async_client.put(f"/api/electricity/{record_id}", json=update_payload, headers=headers)
    assert r_update.status_code == 200
    updated = r_update.json()
    assert updated["bill_amount_inr"] == 11200.0
    assert updated["building_or_department"] == "Main Administrative Block"

    # Verify persisted update via GET
    r_get_updated = await async_client.get(f"/api/electricity/{record_id}", headers=headers)
    assert r_get_updated.status_code == 200
    assert r_get_updated.json()["bill_amount_inr"] == 11200.0
    assert r_get_updated.json()["building_or_department"] == "Main Administrative Block"
