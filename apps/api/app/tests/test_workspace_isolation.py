import pytest
import uuid
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_workspace_isolation_denies_cross_workspace_access(async_client: AsyncClient):
    # 1. Register User A
    user_a_payload = {
        "email": "user_a@mnemos.ai",
        "password": "PasswordUserA123!",
        "full_name": "User Alpha",
    }
    res_a = await async_client.post("/api/v1/auth/register", json=user_a_payload)
    assert res_a.status_code == 201
    data_a = res_a.json()
    token_a = res_a.cookies.get("access_token")
    workspace_a_id = data_a["workspace"]["id"]

    # 2. Register User B
    user_b_payload = {
        "email": "user_b@mnemos.ai",
        "password": "PasswordUserB123!",
        "full_name": "User Beta",
    }
    res_b = await async_client.post("/api/v1/auth/register", json=user_b_payload)
    assert res_b.status_code == 201
    data_b = res_b.json()
    workspace_b_id = data_b["workspace"]["id"]

    # Clear cookies so requests rely strictly on headers
    async_client.cookies.clear()

    # 3. User A queries /auth/me with User A's token -> Success
    headers_a = {"Authorization": f"Bearer {token_a}"}
    me_a = await async_client.get("/api/v1/auth/me", headers=headers_a)
    assert me_a.status_code == 200
    assert me_a.json()["workspace"]["id"] == workspace_a_id

    # 4. User A attempts to access Workspace B via X-Workspace-ID header
    unauthorized_headers = {
        "Authorization": f"Bearer {token_a}",
        "X-Workspace-ID": str(workspace_b_id),
    }
    denied_res = await async_client.get("/api/v1/auth/me", headers=unauthorized_headers)
    assert denied_res.status_code == 403
    assert "Access denied to requested workspace" in denied_res.json()["detail"]


@pytest.mark.asyncio
async def test_workspace_isolation_denies_nonexistent_workspace(async_client: AsyncClient):
    # Register user
    payload = {
        "email": "isolation_test@mnemos.ai",
        "password": "Password123!",
        "full_name": "Iso Tester",
    }
    reg_res = await async_client.post("/api/v1/auth/register", json=payload)
    token = reg_res.cookies.get("access_token")

    # Request random non-existent workspace UUID
    fake_ws_id = str(uuid.uuid4())
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Workspace-ID": fake_ws_id,
    }
    res = await async_client.get("/api/v1/auth/me", headers=headers)
    assert res.status_code == 403
