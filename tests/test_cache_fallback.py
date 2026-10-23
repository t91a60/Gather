import pytest
import redis.asyncio as aioredis
from httpx import AsyncClient
from redis.exceptions import TimeoutError as RedisTimeoutError


@pytest.mark.asyncio
async def test_event_crud_remains_available_when_redis_times_out(
    client: AsyncClient, auth_headers: dict, monkeypatch
):
    async def timeout(*args, **kwargs):
        raise RedisTimeoutError("Cache request timed out")

    monkeypatch.setattr(aioredis.Redis, "execute_command", timeout)
    created = await client.post(
        "/api/v1/events",
        headers=auth_headers,
        json={
            "title": "Cache outage",
            "date": "2099-01-01T12:00:00Z",
            "location": "Park",
        },
    )
    assert created.status_code == 201
    path = f"/api/v1/events/{created.json()['id']}"

    listing = await client.get("/api/v1/events")
    assert listing.status_code == 200
    assert listing.json()["items"][0]["title"] == "Cache outage"
    updated = await client.put(
        path, headers=auth_headers, json={"title": "Still available"}
    )
    assert updated.status_code == 200
    deleted = await client.delete(path, headers=auth_headers)
    assert deleted.status_code == 200
    assert (await client.get(path)).status_code == 404


@pytest.mark.asyncio
async def test_invalid_cached_json_does_not_break_event_listing(
    client: AsyncClient, sample_event, monkeypatch
):
    async def corrupted_value(*args, **kwargs):
        return "{invalid-json"

    monkeypatch.setattr(aioredis.Redis, "get", corrupted_value)

    response = await client.get("/api/v1/events")

    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["id"] == str(sample_event.id)
