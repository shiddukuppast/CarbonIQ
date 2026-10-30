import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient


@pytest.fixture
async def seeded_workspace(async_client: AsyncClient, auth_header_helper):
    # Register user
    reg = {
        "full_name": "Sustainability Officer",
        "email": "officer@carboniq.org",
        "password": "Password123!",
        "workspace_name": "Innovation Tech Park",
    }
    r_reg = await async_client.post("/api/auth/register", json=reg)
    token = r_reg.json()["access_token"]
    headers = auth_header_helper(token)

    # Add electricity record: 2,000 kWh -> 1,640 kg CO2e, ₹17,000 bill
    await async_client.post(
        "/api/electricity",
        json={"reporting_month": "2026-03", "consumption_kwh": 2000.0, "bill_amount_inr": 17000.0},
        headers=headers,
    )

    # Add transportation record: 500 km, 100 L diesel -> 268 kg CO2e, ₹9,450
    await async_client.post(
        "/api/transportation",
        json={"date": "2026-03-15", "mode": "Bus", "distance_km": 500.0, "fuel_consumed_liters": 100.0, "fuel_type": "Diesel"},
        headers=headers,
    )

    # Add waste record: 200 kg Landfill -> 250 kg CO2e
    await async_client.post(
        "/api/waste",
        json={"date": "2026-03-20", "category": "General", "quantity_kg": 200.0, "treatment_method": "Landfill"},
        headers=headers,
    )

    return {"token": token, "headers": headers}


@pytest.mark.asyncio
async def test_dashboard_summary_matches_stored_records(
    async_client: AsyncClient,
    seeded_workspace,
):
    headers = seeded_workspace["headers"]
    response = await async_client.get("/api/dashboard/summary", headers=headers)
    assert response.status_code == 200
    data = response.json()

    # Total emissions = 1640 (elec) + 268 (trans) + 250 (waste) = 2158.0 kg CO2e
    assert data["total_emissions_kg"] == 2158.0
    assert data["electricity"]["consumption_kwh"] == 2000.0
    assert data["transportation"]["fuel_liters"] == 100.0
    assert data["waste"]["total_kg"] == 200.0
    assert len(data["category_breakdown"]) == 3


@pytest.mark.asyncio
async def test_ai_electricity_advisor_with_groq_mock(
    async_client: AsyncClient,
    seeded_workspace,
):
    headers = seeded_workspace["headers"]
    mock_choice = MagicMock()
    mock_choice.message.content = "Under a 15% reduction scenario, saving 300 kWh saves approximately ₹2,400/month."
    mock_resp = MagicMock(choices=[mock_choice])

    with patch("app.core.config.settings.GROQ_API_KEY", "gsk_test"), \
         patch("app.services.ai_assistant_service.AsyncGroq") as mock_groq_cls:
        mock_instance = MagicMock()
        mock_instance.chat.completions.create = AsyncMock(return_value=mock_resp)
        mock_groq_cls.return_value = mock_instance

        # Ask for 15% reduction savings
        q_payload = {"question": "How much can I save by reducing electricity usage by 15%?"}
        r = await async_client.post("/api/ai/electricity", json=q_payload, headers=headers)
        assert r.status_code == 200
        res = r.json()
        assert "calculation_breakdown" in res
        assert res["calculation_breakdown"] is not None
        assert "300" in res["calculation_breakdown"]["result"] or "300" in res["content"]
        assert len(res["suggested_follow_ups"]) > 0


@pytest.mark.asyncio
async def test_ai_transportation_advisor(
    async_client: AsyncClient,
    seeded_workspace,
):
    headers = seeded_workspace["headers"]
    mock_choice = MagicMock()
    mock_choice.message.content = "To reduce fleet emissions, combine overlapping corridors and conduct tire pressure audits."
    mock_resp = MagicMock(choices=[mock_choice])

    with patch("app.core.config.settings.GROQ_API_KEY", "gsk_test"), \
         patch("app.services.ai_assistant_service.AsyncGroq") as mock_groq_cls:
        mock_instance = MagicMock()
        mock_instance.chat.completions.create = AsyncMock(return_value=mock_resp)
        mock_groq_cls.return_value = mock_instance

        q_payload = {"question": "How can I reduce transportation emissions?"}
        r = await async_client.post("/api/ai/transportation", json=q_payload, headers=headers)
        assert r.status_code == 200
        assert len(r.json()["content"]) > 20


@pytest.mark.asyncio
async def test_ai_waste_advisor(
    async_client: AsyncClient,
    seeded_workspace,
):
    headers = seeded_workspace["headers"]
    mock_choice = MagicMock()
    mock_choice.message.content = "General waste is your highest contributing stream at 200 kg."
    mock_resp = MagicMock(choices=[mock_choice])

    with patch("app.core.config.settings.GROQ_API_KEY", "gsk_test"), \
         patch("app.services.ai_assistant_service.AsyncGroq") as mock_groq_cls:
        mock_instance = MagicMock()
        mock_instance.chat.completions.create = AsyncMock(return_value=mock_resp)
        mock_groq_cls.return_value = mock_instance

        q_payload = {"question": "Which waste category contributes the most to our total waste?"}
        r = await async_client.post("/api/ai/waste", json=q_payload, headers=headers)
        assert r.status_code == 200
        assert "General" in r.json()["content"]
        assert r.json()["calculation_breakdown"] is not None


@pytest.mark.asyncio
async def test_demo_endpoints_are_isolated(async_client: AsyncClient):
    # Public unauthenticated demo access
    r_dash = await async_client.get("/api/demo/dashboard")
    assert r_dash.status_code == 200
    data = r_dash.json()
    assert data["is_demo"] is True
    assert "REVA Green Campus" in data["workspace_name"]

    r_elec = await async_client.get("/api/demo/electricity")
    assert r_elec.status_code == 200
    assert len(r_elec.json()) > 0
    assert all("demo_" in r["id"] for r in r_elec.json())
