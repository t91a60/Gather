import pytest
from httpx import AsyncClient
from datetime import datetime, timezone, timedelta


@pytest.mark.asyncio
async def test_create_event(client: AsyncClient, auth_headers: dict):
    future = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
    response = await client.post(
        "/api/v1/events",
        json={
            "title": "My Event",
            "description": "Event description",
            "date": future,
            "location": "Warsaw, Poland",
        },
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "My Event"
    assert data["location"] == "Warsaw, Poland"
    assert "id" in data


@pytest.mark.asyncio
async def test_create_event_past_date(client: AsyncClient, auth_headers: dict):
    past = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    response = await client.post(
        "/api/v1/events",
        json={
            "title": "Past Event",
            "description": "Should fail",
            "date": past,
            "location": "Nowhere",
        },
        headers=auth_headers,
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_create_event_unauthenticated(client: AsyncClient):
    future = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
    response = await client.post(
        "/api/v1/events",
        json={
            "title": "Unauthorized Event",
            "description": "Should fail",
            "date": future,
            "location": "Nowhere",
        },
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_list_events(client: AsyncClient, auth_headers: dict):
    response = await client.get("/api/v1/events", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert "page" in data


@pytest.mark.asyncio
async def test_get_event(client: AsyncClient, sample_event, auth_headers: dict):
    response = await client.get(f"/api/v1/events/{sample_event.id}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(sample_event.id)


@pytest.mark.asyncio
async def test_get_event_not_found(client: AsyncClient, auth_headers: dict):
    import uuid

    response = await client.get(f"/api/v1/events/{uuid.uuid4()}", headers=auth_headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_event(client: AsyncClient, sample_event, auth_headers: dict):
    response = await client.put(
        f"/api/v1/events/{sample_event.id}",
        json={
            "title": "Updated Title",
        },
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["title"] == "Updated Title"


@pytest.mark.asyncio
async def test_delete_event(client: AsyncClient, sample_event, auth_headers: dict):
    response = await client.delete(f"/api/v1/events/{sample_event.id}", headers=auth_headers)
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_join_leave_event(client: AsyncClient, sample_event, second_auth_headers: dict):
    join_resp = await client.post(f"/api/v1/events/{sample_event.id}/join", headers=second_auth_headers)
    assert join_resp.status_code == 200

    leave_resp = await client.delete(f"/api/v1/events/{sample_event.id}/leave", headers=second_auth_headers)
    assert leave_resp.status_code == 200


@pytest.mark.asyncio
async def test_join_event_twice(client: AsyncClient, sample_event, second_auth_headers: dict):
    await client.post(f"/api/v1/events/{sample_event.id}/join", headers=second_auth_headers)
    resp = await client.post(f"/api/v1/events/{sample_event.id}/join", headers=second_auth_headers)
    assert resp.status_code == 409
