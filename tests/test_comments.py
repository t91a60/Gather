import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_comment_is_visible_in_post_details_and_comment_list(
    client: AsyncClient, published_post: dict, second_auth_headers: dict
):
    path = f"/api/v1/posts/{published_post['id']}"
    response = await client.post(
        f"{path}/comments",
        headers=second_auth_headers,
        json={"content": "Count me in!"},
    )
    assert response.status_code == 201
    comment = response.json()
    assert comment["author"]["username"] == "seconduser"
    assert comment["post_id"] == published_post["id"]

    comments = await client.get(f"{path}/comments")
    assert comments.status_code == 200
    assert comments.json() == [comment]
    details = await client.get(path)
    assert details.status_code == 200
    assert details.json()["comments"] == [comment]
    assert details.json()["comment_count"] == 1

    listing = await client.get("/api/v1/posts")
    assert listing.json()["items"][0]["comment_count"] == 1
