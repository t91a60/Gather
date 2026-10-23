import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_created_post_can_be_read(client: AsyncClient, auth_headers: dict):
    created = await client.post(
        "/api/v1/posts",
        headers=auth_headers,
        json={"title": "Weekend walk", "content": "Meet at the park."},
    )
    assert created.status_code == 201
    post_id = created.json()["id"]

    response = await client.get(f"/api/v1/posts/{post_id}")

    assert response.status_code == 200
    assert response.json()["title"] == "Weekend walk"
    assert response.json()["content"] == "Meet at the park."
    assert response.json()["author"]["username"] == "testuser"
    assert response.json()["comments"] == []
    assert response.json()["comment_count"] == 0


@pytest.mark.asyncio
async def test_author_can_update_and_delete_a_post(
    client: AsyncClient, auth_headers: dict
):
    created = await client.post(
        "/api/v1/posts",
        headers=auth_headers,
        json={"title": "Original", "content": "Keep this content"},
    )
    assert created.status_code == 201
    path = f"/api/v1/posts/{created.json()['id']}"

    updated = await client.put(path, headers=auth_headers, json={"title": "Changed"})
    assert updated.status_code == 200
    retrieved = await client.get(path)
    assert retrieved.json()["title"] == "Changed"
    assert retrieved.json()["content"] == "Keep this content"

    deleted = await client.delete(path, headers=auth_headers)
    assert deleted.status_code == 200
    assert (await client.get(path)).status_code == 404
    listing = await client.get("/api/v1/posts")
    assert listing.json()["total"] == 0
    assert listing.json()["items"] == []


@pytest.mark.asyncio
@pytest.mark.parametrize("method", ["PUT", "DELETE"])
async def test_other_users_cannot_modify_posts(
    client: AsyncClient, auth_headers: dict, second_auth_headers: dict, method: str
):
    created = await client.post(
        "/api/v1/posts",
        headers=auth_headers,
        json={"title": "Private ownership", "content": "Original content"},
    )
    assert created.status_code == 201
    path = f"/api/v1/posts/{created.json()['id']}"
    kwargs = {"json": {"title": "Unauthorized change"}} if method == "PUT" else {}

    response = await client.request(method, path, headers=second_auth_headers, **kwargs)

    assert response.status_code == 403
    retrieved = await client.get(path)
    assert retrieved.status_code == 200
    assert retrieved.json()["title"] == "Private ownership"


@pytest.mark.asyncio
async def test_event_filter_and_pagination_only_return_matching_posts(
    client: AsyncClient, auth_headers: dict, sample_event
):
    matching_ids = set()
    for title, event_id in (
        ("Event update one", str(sample_event.id)),
        ("Unrelated", None),
        ("Event update two", str(sample_event.id)),
    ):
        created = await client.post(
            "/api/v1/posts",
            headers=auth_headers,
            json={"title": title, "content": "Update", "event_id": event_id},
        )
        assert created.status_code == 201
        if event_id:
            matching_ids.add(created.json()["id"])

    returned_ids = []
    for page in (1, 2):
        response = await client.get(
            "/api/v1/posts",
            params={"event_id": str(sample_event.id), "page": page, "page_size": 1},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert data["total_pages"] == 2
        assert data["page"] == page
        assert len(data["items"]) == 1
        returned_ids.append(data["items"][0]["id"])
    assert set(returned_ids) == matching_ids

    beyond_end = await client.get(
        "/api/v1/posts",
        params={"event_id": str(sample_event.id), "page": 3, "page_size": 1},
    )
    assert beyond_end.json()["items"] == []
    assert beyond_end.json()["total"] == 2


@pytest.mark.asyncio
async def test_post_cannot_reference_a_missing_event(
    client: AsyncClient, auth_headers: dict
):
    response = await client.post(
        "/api/v1/posts",
        headers=auth_headers,
        json={
            "title": "Event report",
            "content": "Report",
            "event_id": "00000000-0000-0000-0000-000000000001",
        },
    )

    assert response.status_code == 404
    listing = await client.get("/api/v1/posts")
    assert listing.json()["total"] == 0
