import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient
import groq
from groq import (
    AsyncGroq,
    APIConnectionError,
    APITimeoutError,
    AuthenticationError,
    NotFoundError,
    RateLimitError,
)
from app.core.config import settings


@pytest.fixture
def auth_header_helper():
    def _header(token: str):
        return {"Authorization": f"Bearer {token}"}
    return _header


@pytest.fixture
async def registered_user_headers(async_client: AsyncClient, auth_header_helper):
    reg = {
        "full_name": "Groq AI Tester",
        "email": "groq.tester@carboniq.org",
        "password": "Password123!",
        "workspace_name": "Groq Test Campus",
    }
    r = await async_client.post("/api/auth/register", json=reg)
    assert r.status_code == 201
    return auth_header_helper(r.json()["access_token"])


def test_groq_sdk_imports_successfully():
    """Requirement 1: Groq SDK and required exception types import cleanly."""
    assert AsyncGroq is not None
    assert AuthenticationError is not None
    assert RateLimitError is not None
    assert NotFoundError is not None
    assert APITimeoutError is not None
    assert APIConnectionError is not None


@pytest.mark.asyncio
async def test_groq_unconfigured_returns_503(
    async_client: AsyncClient,
    registered_user_headers,
):
    """Requirement 2: Missing API key returns a clear HTTP 503 configuration error."""
    with patch("app.core.config.settings.GROQ_API_KEY", None), \
         patch("app.core.config.settings.LLM_API_KEY", None):
        res = await async_client.post(
            "/api/ai/insights",
            json={"question": "What is our electricity reduction potential?"},
            headers=registered_user_headers,
        )
        assert res.status_code == 503
        data = res.json()
        assert "AI is not configured" in data["detail"]
        assert "GROQ_API_KEY" in data["detail"]


@pytest.mark.asyncio
async def test_groq_configured_no_records_returns_guidance(
    async_client: AsyncClient,
    registered_user_headers,
):
    """When GROQ_API_KEY is configured but user has no records, returns honest guidance."""
    with patch("app.core.config.settings.GROQ_API_KEY", "gsk_test_key_configured"):
        res = await async_client.post(
            "/api/ai/insights",
            json={"question": "Analyze footprint across all departments"},
            headers=registered_user_headers,
        )
        assert res.status_code == 200
        data = res.json()
        assert "No records available in your workspace yet" in data["content"]


@pytest.mark.asyncio
async def test_groq_authentication_error_handled_safely(
    async_client: AsyncClient,
    registered_user_headers,
):
    """Requirement 3: Invalid API key returns HTTP 502 without leaking secrets."""
    await async_client.post(
        "/api/electricity",
        json={"reporting_month": "2026-10", "consumption_kwh": 1000.0, "source": "Grid"},
        headers=registered_user_headers,
    )

    mock_auth_err = AuthenticationError("Invalid API Key", response=MagicMock(status_code=401), body=None)

    with patch("app.core.config.settings.GROQ_API_KEY", "gsk_invalid_test_key_12345"), \
         patch("app.services.ai_assistant_service.AsyncGroq") as mock_groq_cls:
        mock_instance = MagicMock()
        mock_instance.chat.completions.create = AsyncMock(side_effect=mock_auth_err)
        mock_groq_cls.return_value = mock_instance

        res = await async_client.post(
            "/api/ai/electricity",
            json={"question": "Analyze solar potential for our facility"},
            headers=registered_user_headers,
        )
        assert res.status_code == 502
        detail = res.json()["detail"]
        assert "Groq authentication failed" in detail or "GROQ_API_KEY" in detail
        assert "gsk_invalid_test_key_12345" not in detail


@pytest.mark.asyncio
async def test_groq_unsupported_model_handled_safely(
    async_client: AsyncClient,
    registered_user_headers,
):
    """Requirement 4: Unsupported model returns HTTP 502 with actionable guidance."""
    await async_client.post(
        "/api/electricity",
        json={"reporting_month": "2026-10", "consumption_kwh": 1000.0, "source": "Grid"},
        headers=registered_user_headers,
    )

    mock_nf_err = NotFoundError(
        "The model `nonexistent-model-xyz` does not exist",
        response=MagicMock(status_code=404),
        body=None,
    )

    with patch("app.core.config.settings.GROQ_API_KEY", "gsk_test_key"), \
         patch("app.core.config.settings.GROQ_MODEL", "nonexistent-model-xyz"), \
         patch("app.services.ai_assistant_service.AsyncGroq") as mock_groq_cls:
        mock_instance = MagicMock()
        mock_instance.chat.completions.create = AsyncMock(side_effect=mock_nf_err)
        mock_groq_cls.return_value = mock_instance

        res = await async_client.post(
            "/api/ai/electricity",
            json={"question": "Analyze solar potential"},
            headers=registered_user_headers,
        )
        assert res.status_code == 502
        detail = res.json()["detail"]
        assert "not supported or accessible" in detail or "GROQ_MODEL" in detail


@pytest.mark.asyncio
async def test_groq_rate_limit_handled_safely(
    async_client: AsyncClient,
    registered_user_headers,
):
    """Requirement 6a: Groq RateLimitError returns HTTP 429."""
    await async_client.post(
        "/api/electricity",
        json={"reporting_month": "2026-10", "consumption_kwh": 1200.0, "source": "Grid"},
        headers=registered_user_headers,
    )

    mock_rate_err = RateLimitError("Rate limit exceeded", response=MagicMock(status_code=429), body=None)

    with patch("app.core.config.settings.GROQ_API_KEY", "gsk_test_key"), \
         patch("app.services.ai_assistant_service.AsyncGroq") as mock_groq_cls:
        mock_instance = MagicMock()
        mock_instance.chat.completions.create = AsyncMock(side_effect=mock_rate_err)
        mock_groq_cls.return_value = mock_instance

        res = await async_client.post(
            "/api/ai/electricity",
            json={"question": "Analyze solar potential for our facility"},
            headers=registered_user_headers,
        )
        assert res.status_code == 429
        detail = res.json()["detail"]
        assert "rate-limited" in detail.lower()


@pytest.mark.asyncio
async def test_groq_timeout_handled_safely(
    async_client: AsyncClient,
    registered_user_headers,
):
    """Requirement 6b: Groq APITimeoutError returns HTTP 504 Gateway Timeout."""
    await async_client.post(
        "/api/electricity",
        json={"reporting_month": "2026-10", "consumption_kwh": 1200.0, "source": "Grid"},
        headers=registered_user_headers,
    )

    mock_timeout_err = APITimeoutError(request=MagicMock())

    with patch("app.core.config.settings.GROQ_API_KEY", "gsk_test_key"), \
         patch("app.services.ai_assistant_service.AsyncGroq") as mock_groq_cls:
        mock_instance = MagicMock()
        mock_instance.chat.completions.create = AsyncMock(side_effect=mock_timeout_err)
        mock_groq_cls.return_value = mock_instance

        res = await async_client.post(
            "/api/ai/electricity",
            json={"question": "Analyze solar potential for our facility"},
            headers=registered_user_headers,
        )
        assert res.status_code == 504
        detail = res.json()["detail"]
        assert "timed out" in detail.lower()


@pytest.mark.asyncio
async def test_groq_successful_grounded_response_schema(
    async_client: AsyncClient,
    registered_user_headers,
):
    """Requirement 5 & 7: Valid configured request returns schema parseable by frontend."""
    await async_client.post(
        "/api/electricity",
        json={"reporting_month": "2026-10", "consumption_kwh": 2500.0, "source": "Grid"},
        headers=registered_user_headers,
    )

    mock_choice = MagicMock()
    mock_choice.message.content = "Based on your 2,500 kWh consumption, shifting 30% to solar will yield substantial abatement."
    mock_response = MagicMock(choices=[mock_choice])

    with patch("app.core.config.settings.GROQ_API_KEY", "gsk_valid_key"), \
         patch("app.services.ai_assistant_service.AsyncGroq") as mock_groq_cls:
        mock_instance = MagicMock()
        mock_instance.chat.completions.create = AsyncMock(return_value=mock_response)
        mock_groq_cls.return_value = mock_instance

        res = await async_client.post(
            "/api/ai/electricity",
            json={"question": "Analyze solar potential for our facility"},
            headers=registered_user_headers,
        )
        assert res.status_code == 200
        data = res.json()
        # Verify required contract fields
        assert "id" in data
        assert data["role"] == "assistant"
        assert "content" in data
        assert "2,500 kWh" in data["content"]
        assert "timestamp" in data
        assert "suggested_follow_ups" in data
        assert isinstance(data["suggested_follow_ups"], list)


@pytest.mark.asyncio
async def test_live_groq_api_call_with_env_key(
    async_client: AsyncClient,
    registered_user_headers,
):
    """
    Requirement 5 live test: If a valid GROQ_API_KEY is configured in backend/.env,
    performs a real request to api.groq.com and verifies the response.
    """
    real_key = settings.effective_groq_api_key
    if not real_key or not real_key.startswith("gsk_"):
        pytest.skip("GROQ_API_KEY not configured in backend/.env; skipping live API test.")

    # Seed a verified record
    await async_client.post(
        "/api/electricity",
        json={"reporting_month": "2026-10", "consumption_kwh": 1500.0, "source": "Grid"},
        headers=registered_user_headers,
    )

    res = await async_client.post(
        "/api/ai/electricity",
        json={"question": "What is our latest recorded electricity consumption?"},
        headers=registered_user_headers,
    )
    assert res.status_code == 200
    data = res.json()
    assert "content" in data
    assert len(data["content"]) > 10
    # Zero mock fallback
    assert "mock" not in data["content"].lower()
