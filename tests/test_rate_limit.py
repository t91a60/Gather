import pytest
from httpx import ASGITransport, AsyncClient

from app.config import settings
from app.main import app


@pytest.mark.asyncio
async def test_auth_requests_over_limit_return_429(client: AsyncClient, monkeypatch):
    monkeypatch.setattr(settings, "rate_limit_auth_per_minute", 2)

    for _ in range(2):
        response = await client.post(
            "/api/v1/auth/refresh", json={"refresh_token": "invalid_token"}
        )
        assert response.status_code == 401

    response = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": "invalid_token"}
    )

    assert response.status_code == 429
    assert response.json() == {
        "detail": "Rate limit exceeded. Max 2 requests per minute."
    }


@pytest.mark.asyncio
@pytest.mark.parametrize("path", ["/api/v1/events", "/api/v1/posts"])
async def test_content_write_attempts_over_limit_return_429(
    client: AsyncClient, monkeypatch, path: str
):
    monkeypatch.setattr(settings, "rate_limit_content_per_minute", 1)

    response = await client.post(path, json={})
    assert response.status_code == 403

    response = await client.post(path, json={})

    assert response.status_code == 429
    assert response.json() == {
        "detail": "Rate limit exceeded. Max 1 requests per minute."
    }


@pytest.mark.asyncio
async def test_auth_requests_are_allowed_when_rate_limit_window_expires(
    client: AsyncClient, monkeypatch
):
    monkeypatch.setattr(settings, "rate_limit_auth_per_minute", 1)
    now = 1000.0
    monkeypatch.setattr("app.middleware.rate_limit.time.time", lambda: now)

    response = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": "invalid_token"}
    )
    assert response.status_code == 401

    now = 1059.999
    response = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": "invalid_token"}
    )
    assert response.status_code == 429

    now = 1060.0
    response = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": "invalid_token"}
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_rate_limit_does_not_block_a_different_client_ip(
    client: AsyncClient, monkeypatch
):
    monkeypatch.setattr(settings, "rate_limit_auth_per_minute", 1)
    body = {"refresh_token": "invalid_token"}
    assert (await client.post("/api/v1/auth/refresh", json=body)).status_code == 401
    assert (await client.post("/api/v1/auth/refresh", json=body)).status_code == 429

    transport = ASGITransport(app=app, client=("192.0.2.10", 12345))
    async with AsyncClient(transport=transport, base_url="http://test") as other_client:
        response = await other_client.post("/api/v1/auth/refresh", json=body)

    assert response.status_code == 401
