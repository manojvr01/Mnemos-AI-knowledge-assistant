import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_security_headers_present(async_client: AsyncClient):
    """Verify security headers are applied to HTTP responses."""
    resp = await async_client.get("/health")
    assert resp.status_code == 200
    assert resp.headers.get("x-content-type-options") == "nosniff"
    assert resp.headers.get("x-frame-options") == "DENY"
    assert resp.headers.get("x-xss-protection") == "1; mode=block"
    assert resp.headers.get("referrer-policy") == "strict-origin-when-cross-origin"


@pytest.mark.asyncio
async def test_cors_policy(async_client: AsyncClient):
    """Verify CORS headers respond correctly to allowed origins."""
    headers = {
        "Origin": "http://localhost:3000",
        "Access-Control-Request-Method": "POST",
    }
    resp = await async_client.options("/api/v1/auth/login", headers=headers)
    assert resp.status_code == 200
    assert resp.headers.get("access-control-allow-origin") == "http://localhost:3000"
    assert resp.headers.get("access-control-allow-credentials") == "true"


@pytest.mark.asyncio
async def test_unauthenticated_protected_endpoint(async_client: AsyncClient):
    """Verify accessing protected routes without session returns 401 Unauthorized."""
    resp = await async_client.get("/api/v1/documents")
    assert resp.status_code == 401
    assert "detail" in resp.json()
