import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_successful_registration(async_client: AsyncClient):
    payload = {
        "full_name": "Test Engineer",
        "email": "engineer@carboniq.org",
        "password": "Password123!",
        "workspace_name": "Clean Tech Campus",
    }
    response = await async_client.post("/api/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "engineer@carboniq.org"
    assert data["user"]["full_name"] == "Test Engineer"
    assert data["user"]["workspace_name"] == "Clean Tech Campus"
    assert len(data["user"]["workspace_id"]) > 0


@pytest.mark.asyncio
async def test_duplicate_email_rejection(async_client: AsyncClient):
    payload = {
        "full_name": "Primary User",
        "email": "duplicate@carboniq.org",
        "password": "Password123!",
    }
    r1 = await async_client.post("/api/auth/register", json=payload)
    assert r1.status_code == 201

    # Second registration with case variation of the same email
    payload_dup = {
        "full_name": "Imposter User",
        "email": "DUPLICATE@carboniq.org",
        "password": "Password123!",
    }
    r2 = await async_client.post("/api/auth/register", json=payload_dup)
    assert r2.status_code == 409
    assert "already exists" in r2.json()["detail"].lower()


@pytest.mark.asyncio
async def test_successful_login(async_client: AsyncClient):
    reg = {
        "full_name": "Login User",
        "email": "login@carboniq.org",
        "password": "CorrectPassword123!",
    }
    await async_client.post("/api/auth/register", json=reg)

    login_req = {
        "email": "login@carboniq.org",
        "password": "CorrectPassword123!",
    }
    response = await async_client.post("/api/auth/login", json=login_req)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["email"] == "login@carboniq.org"


@pytest.mark.asyncio
async def test_invalid_password_rejection(async_client: AsyncClient):
    reg = {
        "full_name": "Protected User",
        "email": "protected@carboniq.org",
        "password": "CorrectPassword123!",
    }
    await async_client.post("/api/auth/register", json=reg)

    bad_login = {
        "email": "protected@carboniq.org",
        "password": "WrongPassword999!",
    }
    response = await async_client.post("/api/auth/login", json=bad_login)
    assert response.status_code == 401
    assert "invalid email address or password" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_protected_endpoint_me(async_client: AsyncClient, auth_header_helper):
    reg = {
        "full_name": "Me User",
        "email": "me@carboniq.org",
        "password": "Password123!",
    }
    r_reg = await async_client.post("/api/auth/register", json=reg)
    token = r_reg.json()["access_token"]

    # Authorized request
    headers = auth_header_helper(token)
    r_me = await async_client.get("/api/auth/me", headers=headers)
    assert r_me.status_code == 200
    data = r_me.json()
    assert data["email"] == "me@carboniq.org"
    assert data["full_name"] == "Me User"

    # Unauthorized request (no token)
    r_unauth = await async_client.get("/api/auth/me")
    assert r_unauth.status_code == 401

    # Unauthorized request (tampered token)
    r_bad_token = await async_client.get("/api/auth/me", headers={"Authorization": "Bearer bad.token.value"})
    assert r_bad_token.status_code == 401


@pytest.mark.asyncio
async def test_individual_account_fleet_restriction(async_client: AsyncClient, auth_header_helper):
    # Register individual account
    reg_ind = {
        "full_name": "Student Aarav",
        "email": "aarav.student@carboniq.org",
        "password": "Password123!",
        "account_type": "individual",
    }
    r_ind = await async_client.post("/api/auth/register", json=reg_ind)
    assert r_ind.status_code == 201
    assert r_ind.json()["user"]["account_type"] == "individual"
    ind_token = r_ind.json()["access_token"]
    ind_headers = auth_header_helper(ind_token)

    # Calling fleet routes as individual must be forbidden with 403
    r_blocked = await async_client.get("/api/transportation/routes", headers=ind_headers)
    assert r_blocked.status_code == 403
    assert "restricted" in r_blocked.json()["detail"].lower()

