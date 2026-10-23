import pytest
from httpx import AsyncClient


MISSING_ID = "00000000-0000-0000-0000-000000000001"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "method,path",
    [
        ("GET", f"/api/v1/users/{MISSING_ID}"),
        ("POST", f"/api/v1/users/{MISSING_ID}/follow"),
        ("DELETE", f"/api/v1/users/{MISSING_ID}/follow"),
        ("GET", f"/api/v1/events/{MISSING_ID}"),
        ("PUT", f"/api/v1/events/{MISSING_ID}"),
        ("DELETE", f"/api/v1/events/{MISSING_ID}"),
        ("POST", f"/api/v1/events/{MISSING_ID}/join"),
        ("DELETE", f"/api/v1/events/{MISSING_ID}/leave"),
        ("GET", f"/api/v1/posts/{MISSING_ID}"),
        ("PUT", f"/api/v1/posts/{MISSING_ID}"),
        ("DELETE", f"/api/v1/posts/{MISSING_ID}"),
        ("GET", f"/api/v1/posts/{MISSING_ID}/comments"),
        ("POST", f"/api/v1/posts/{MISSING_ID}/comments"),
    ],
)
async def test_missing_resources_return_404(
    client: AsyncClient, auth_headers: dict, method: str, path: str
):
    kwargs = {"json": {"content": "A comment"}} if method in ("POST", "PUT") else {}
    response = await client.request(method, path, headers=auth_headers, **kwargs)

    assert response.status_code == 404
    assert "detail" in response.json()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "method,path",
    [
        ("GET", "/api/v1/users/me"),
        ("PATCH", "/api/v1/users/me"),
        ("POST", f"/api/v1/users/{MISSING_ID}/follow"),
        ("DELETE", f"/api/v1/users/{MISSING_ID}/follow"),
        ("POST", "/api/v1/events"),
        ("PUT", f"/api/v1/events/{MISSING_ID}"),
        ("DELETE", f"/api/v1/events/{MISSING_ID}"),
        ("POST", f"/api/v1/events/{MISSING_ID}/join"),
        ("DELETE", f"/api/v1/events/{MISSING_ID}/leave"),
        ("POST", "/api/v1/posts"),
        ("PUT", f"/api/v1/posts/{MISSING_ID}"),
        ("DELETE", f"/api/v1/posts/{MISSING_ID}"),
        ("POST", f"/api/v1/posts/{MISSING_ID}/comments"),
        ("GET", "/api/v1/posts/feed"),
    ],
)
async def test_protected_endpoints_require_authentication(
    client: AsyncClient, method: str, path: str
):
    kwargs = {"json": {}} if method in ("POST", "PUT", "PATCH") else {}

    response = await client.request(method, path, **kwargs)

    assert response.status_code == 403
