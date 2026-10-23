import pytest
from httpx import AsyncClient


pytestmark = [pytest.mark.postgres, pytest.mark.redis, pytest.mark.asyncio]


async def test_real_cache_is_invalidated_after_event_and_membership_changes(
    client: AsyncClient, auth_headers: dict, second_auth_headers: dict, real_cache
):
    initial = await client.get("/api/v1/events")
    assert initial.status_code == 200
    assert initial.json()["total"] == 0
    assert await real_cache.dbsize() > 0
    cached = await client.get("/api/v1/events")
    assert cached.json() == initial.json()

    created = await client.post(
        "/api/v1/events",
        headers=auth_headers,
        json={
            "title": "Cached event",
            "date": "2099-01-01T12:00:00Z",
            "location": "Park",
        },
    )
    assert created.status_code == 201
    path = f"/api/v1/events/{created.json()['id']}"
    for page_size in (1, 20):
        listing = await client.get("/api/v1/events", params={"page_size": page_size})
        assert listing.json()["total"] == 1
        assert listing.json()["items"][0]["title"] == "Cached event"

    updated = await client.put(
        path, headers=auth_headers, json={"title": "Fresh title"}
    )
    assert updated.status_code == 200
    for page_size in (1, 20):
        listing = await client.get("/api/v1/events", params={"page_size": page_size})
        assert listing.json()["items"][0]["title"] == "Fresh title"

    joined = await client.post(f"{path}/join", headers=second_auth_headers)
    assert joined.status_code == 200
    listing = await client.get("/api/v1/events")
    assert listing.json()["items"][0]["participant_count"] == 1
    left = await client.delete(f"{path}/leave", headers=second_auth_headers)
    assert left.status_code == 200
    listing = await client.get("/api/v1/events")
    assert listing.json()["items"][0]["participant_count"] == 0

    deleted = await client.delete(path, headers=auth_headers)
    assert deleted.status_code == 200
    for page_size in (1, 20):
        listing = await client.get("/api/v1/events", params={"page_size": page_size})
        assert listing.json()["items"] == []
        assert listing.json()["total"] == 0
