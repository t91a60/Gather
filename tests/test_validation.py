import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "path", ["/api/v1/events", "/api/v1/posts", "/api/v1/posts/feed"]
)
@pytest.mark.parametrize(
    "query", [{"page": 0}, {"page": -1}, {"page_size": 0}, {"page_size": 101}]
)
async def test_collection_pagination_rejects_out_of_range_values(
    client: AsyncClient, auth_headers: dict, path: str, query: dict
):
    response = await client.get(path, headers=auth_headers, params=query)

    assert response.status_code == 422


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "method,path,body",
    [
        (
            "POST",
            "/api/v1/auth/register",
            {"username": "ab", "email": "ok@example.com", "password": "password123"},
        ),
        (
            "POST",
            "/api/v1/auth/register",
            {
                "username": "validuser",
                "email": "not-an-email",
                "password": "password123",
            },
        ),
        (
            "POST",
            "/api/v1/auth/register",
            {"username": "validuser", "email": "ok@example.com", "password": "short"},
        ),
        ("PATCH", "/api/v1/users/me", {"username": "has spaces"}),
        ("PATCH", "/api/v1/users/me", {"bio": "x" * 501}),
        ("POST", "/api/v1/posts", {"title": "", "content": "Valid content"}),
        ("POST", "/api/v1/posts", {"title": "Valid title", "content": ""}),
        ("POST", "/api/v1/posts", {"title": "x" * 201, "content": "Valid content"}),
        ("POST", "/api/v1/posts", {"title": "Valid title", "content": "x" * 10001}),
        (
            "POST",
            "/api/v1/posts",
            {
                "title": "Valid title",
                "content": "Valid content",
                "event_id": "not-a-uuid",
            },
        ),
        (
            "POST",
            "/api/v1/events",
            {"title": "Valid title", "location": "Park", "date": "not-a-date"},
        ),
        (
            "POST",
            "/api/v1/events",
            {"title": "", "location": "Park", "date": "2099-01-01T12:00:00Z"},
        ),
        (
            "POST",
            "/api/v1/events",
            {"title": "Valid title", "location": "", "date": "2099-01-01T12:00:00Z"},
        ),
        (
            "POST",
            "/api/v1/posts/00000000-0000-0000-0000-000000000001/comments",
            {"content": ""},
        ),
        (
            "POST",
            "/api/v1/posts/00000000-0000-0000-0000-000000000001/comments",
            {"content": "x" * 2001},
        ),
    ],
)
async def test_invalid_request_fields_return_422(
    client: AsyncClient, auth_headers: dict, method: str, path: str, body: dict
):
    response = await client.request(method, path, headers=auth_headers, json=body)

    assert response.status_code == 422
