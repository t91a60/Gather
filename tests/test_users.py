import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_profile_changes_are_visible_without_changing_omitted_fields(
    client: AsyncClient, auth_headers: dict, test_user
):
    response = await client.patch(
        "/api/v1/users/me", headers=auth_headers, json={"bio": "Weekend hiker"}
    )
    assert response.status_code == 200

    profile = await client.get(f"/api/v1/users/{test_user.id}")
    assert profile.status_code == 200
    assert profile.json()["bio"] == "Weekend hiker"
    assert profile.json()["username"] == "testuser"

    me = await client.get("/api/v1/users/me", headers=auth_headers)
    assert me.status_code == 200
    assert me.json() == profile.json()
    assert "hashed_password" not in me.json()


@pytest.mark.asyncio
async def test_follow_and_unfollow_update_both_public_lists(
    client: AsyncClient, auth_headers: dict, test_user, second_user
):
    path = f"/api/v1/users/{second_user.id}/follow"
    response = await client.post(path, headers=auth_headers)
    assert response.status_code == 200

    following = await client.get(f"/api/v1/users/{test_user.id}/following")
    followers = await client.get(f"/api/v1/users/{second_user.id}/followers")
    assert [user["id"] for user in following.json()] == [str(second_user.id)]
    assert [user["id"] for user in followers.json()] == [str(test_user.id)]

    duplicate = await client.post(path, headers=auth_headers)
    assert duplicate.status_code == 409

    response = await client.delete(path, headers=auth_headers)
    assert response.status_code == 200
    following = await client.get(f"/api/v1/users/{test_user.id}/following")
    followers = await client.get(f"/api/v1/users/{second_user.id}/followers")
    assert following.json() == []
    assert followers.json() == []
    assert (await client.delete(path, headers=auth_headers)).status_code == 409


@pytest.mark.asyncio
@pytest.mark.parametrize("method", ["POST", "DELETE"])
async def test_users_cannot_follow_or_unfollow_themselves(
    client: AsyncClient, auth_headers: dict, test_user, method: str
):
    response = await client.request(
        method, f"/api/v1/users/{test_user.id}/follow", headers=auth_headers
    )

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_profile_update_cannot_take_another_users_username(
    client: AsyncClient, auth_headers: dict, second_user
):
    response = await client.patch(
        "/api/v1/users/me", headers=auth_headers, json={"username": "seconduser"}
    )

    assert response.status_code == 409
    me = await client.get("/api/v1/users/me", headers=auth_headers)
    assert me.json()["username"] == "testuser"
