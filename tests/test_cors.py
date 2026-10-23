import pytest
from httpx import AsyncClient

from app.config import settings


@pytest.mark.asyncio
async def test_rate_limit_responses_include_cors_headers(
    client: AsyncClient, monkeypatch
):
    monkeypatch.setattr(settings, "rate_limit_auth_per_minute", 1)
    headers = {"Origin": "https://client.example.com"}
    response = await client.post(
        "/api/v1/auth/refresh", headers=headers, json={"refresh_token": "invalid_token"}
    )
    assert response.status_code == 401

    response = await client.post(
        "/api/v1/auth/refresh", headers=headers, json={"refresh_token": "invalid_token"}
    )

    assert response.status_code == 429
    assert response.headers.get("access-control-allow-origin") == "*"


@pytest.mark.asyncio
async def test_preflight_allows_authorization_without_consuming_rate_limit(
    client: AsyncClient, monkeypatch
):
    monkeypatch.setattr(settings, "rate_limit_auth_per_minute", 1)
    response = await client.options(
        "/api/v1/auth/refresh",
        headers={
            "Origin": "https://client.example.com",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "authorization,content-type",
        },
    )
    assert response.status_code == 200
    assert "POST" in response.headers["access-control-allow-methods"]
    assert "authorization" in response.headers["access-control-allow-headers"].lower()

    response = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": "invalid_token"}
    )
    assert response.status_code == 401
