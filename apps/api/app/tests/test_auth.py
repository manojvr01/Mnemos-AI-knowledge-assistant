import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_success(async_client: AsyncClient):
    payload = {
        "email": "analyst@mnemos.ai",
        "password": "SecurePassword123!",
        "full_name": "Senior Analyst",
    }
    response = await async_client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()

    assert data["user"]["email"] == "analyst@mnemos.ai"
    assert data["user"]["full_name"] == "Senior Analyst"
    assert "id" in data["user"]
    assert "workspace" in data
    assert data["workspace"]["name"] == "Senior Analyst's Workspace"
    assert data["workspace"]["role"] == "OWNER"

    # Verify httpOnly cookie was set
    assert "access_token" in response.cookies


@pytest.mark.asyncio
async def test_register_duplicate_email(async_client: AsyncClient):
    payload = {
        "email": "duplicate@mnemos.ai",
        "password": "Password12345!",
        "full_name": "First User",
    }
    first_res = await async_client.post("/api/v1/auth/register", json=payload)
    assert first_res.status_code == 201

    # Attempt duplicate
    second_res = await async_client.post("/api/v1/auth/register", json=payload)
    assert second_res.status_code == 409
    assert "already exists" in second_res.json()["detail"]


@pytest.mark.asyncio
async def test_login_success(async_client: AsyncClient):
    # Register user first
    reg_payload = {
        "email": "login_test@mnemos.ai",
        "password": "SecretPassword123!",
        "full_name": "Login Tester",
    }
    await async_client.post("/api/v1/auth/register", json=reg_payload)

    # Login
    login_payload = {
        "email": "login_test@mnemos.ai",
        "password": "SecretPassword123!",
    }
    login_res = await async_client.post("/api/v1/auth/login", json=login_payload)
    assert login_res.status_code == 200
    data = login_res.json()
    assert data["user"]["email"] == "login_test@mnemos.ai"
    assert "access_token" in login_res.cookies


@pytest.mark.asyncio
async def test_login_invalid_password(async_client: AsyncClient):
    reg_payload = {
        "email": "wrong_pwd@mnemos.ai",
        "password": "CorrectPassword123!",
        "full_name": "Test User",
    }
    await async_client.post("/api/v1/auth/register", json=reg_payload)

    # Attempt login with bad password
    bad_login = {
        "email": "wrong_pwd@mnemos.ai",
        "password": "WrongPassword123!",
    }
    login_res = await async_client.post("/api/v1/auth/login", json=bad_login)
    assert login_res.status_code == 401
    assert "Invalid email or password" in login_res.json()["detail"]


@pytest.mark.asyncio
async def test_get_me_with_cookie(async_client: AsyncClient):
    reg_payload = {
        "email": "me_test@mnemos.ai",
        "password": "ValidPassword999!",
        "full_name": "Me Tester",
    }
    reg_res = await async_client.post("/api/v1/auth/register", json=reg_payload)
    assert reg_res.status_code == 201
    token = reg_res.cookies.get("access_token")

    # Call /auth/me with cookie
    async_client.cookies.set("access_token", token)
    me_res = await async_client.get("/api/v1/auth/me")
    assert me_res.status_code == 200
    me_data = me_res.json()
    assert me_data["user"]["email"] == "me_test@mnemos.ai"
    assert me_data["workspace"]["role"] == "OWNER"
