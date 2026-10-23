import asyncio

import pytest
from httpx import AsyncClient


pytestmark = [pytest.mark.postgres, pytest.mark.asyncio]


async def test_migrations_can_be_reversed_and_reapplied(client: AsyncClient, migrate):
    await asyncio.to_thread(migrate, "base", "downgrade")
    await asyncio.to_thread(migrate, "head")

    registered = await client.post(
        "/api/v1/auth/register",
        json={
            "username": "after_migration",
            "email": "migration@example.com",
            "password": "password123",
        },
    )
    assert registered.status_code == 201
    headers = {"Authorization": f"Bearer {registered.json()['access_token']}"}
    profile = await client.get("/api/v1/users/me", headers=headers)
    assert profile.status_code == 200
    assert profile.json()["username"] == "after_migration"


async def test_deleting_event_preserves_posts_and_deleting_post_removes_comments(
    client: AsyncClient, auth_headers: dict, second_auth_headers: dict
):
    event = await client.post(
        "/api/v1/events",
        headers=auth_headers,
        json={
            "title": "Database lifecycle",
            "date": "2099-01-01T12:00:00Z",
            "location": "Park",
        },
    )
    assert event.status_code == 201
    event_id = event.json()["id"]
    joined = await client.post(
        f"/api/v1/events/{event_id}/join", headers=second_auth_headers
    )
    assert joined.status_code == 200
    post = await client.post(
        "/api/v1/posts",
        headers=auth_headers,
        json={
            "title": "Event report",
            "content": "Preserve this",
            "event_id": event_id,
        },
    )
    assert post.status_code == 201
    post_path = f"/api/v1/posts/{post.json()['id']}"
    comment = await client.post(
        f"{post_path}/comments",
        headers=second_auth_headers,
        json={"content": "Attended!"},
    )
    assert comment.status_code == 201

    deleted = await client.delete(f"/api/v1/events/{event_id}", headers=auth_headers)
    assert deleted.status_code == 200
    preserved = await client.get(post_path)
    assert preserved.status_code == 200
    assert preserved.json()["event_id"] is None
    assert preserved.json()["comment_count"] == 1

    deleted = await client.delete(post_path, headers=auth_headers)
    assert deleted.status_code == 200
    assert (await client.get(f"{post_path}/comments")).status_code == 404
