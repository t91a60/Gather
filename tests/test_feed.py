import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_feed_contains_only_followed_authors_and_updates_after_unfollow(
    client: AsyncClient,
    auth_headers: dict,
    second_auth_headers: dict,
    second_user,
    published_post: dict,
):
    stranger = await client.post(
        "/api/v1/auth/register",
        json={
            "username": "stranger",
            "email": "stranger@example.com",
            "password": "password123",
        },
    )
    assert stranger.status_code == 201
    stranger_post = await client.post(
        "/api/v1/posts",
        headers={"Authorization": f"Bearer {stranger.json()['access_token']}"},
        json={"title": "Not followed", "content": "Not in the feed"},
    )
    assert stranger_post.status_code == 201

    followed_ids = set()
    for title in ("First update", "Second update"):
        response = await client.post(
            "/api/v1/posts",
            headers=second_auth_headers,
            json={"title": title, "content": "From a followed author"},
        )
        assert response.status_code == 201
        followed_ids.add(response.json()["id"])

    empty = await client.get("/api/v1/posts/feed", headers=auth_headers)
    assert empty.json()["items"] == []
    assert empty.json()["total"] == 0

    follow_path = f"/api/v1/users/{second_user.id}/follow"
    assert (await client.post(follow_path, headers=auth_headers)).status_code == 200
    pages = []
    for page in (1, 2):
        response = await client.get(
            "/api/v1/posts/feed",
            headers=auth_headers,
            params={"page": page, "page_size": 1},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert data["total_pages"] == 2
        assert len(data["items"]) == 1
        pages.append(data["items"][0]["id"])
    assert set(pages) == followed_ids

    assert (await client.delete(follow_path, headers=auth_headers)).status_code == 200
    empty = await client.get("/api/v1/posts/feed", headers=auth_headers)
    assert empty.json()["items"] == []
    assert empty.json()["total_pages"] == 0
