import pytest
from httpx import AsyncClient
from jose import jwt

from app.config import settings


@pytest.mark.asyncio
async def test_register_success(client: AsyncClient):
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "username": "newuser",
            "email": "new@example.com",
            "password": "strongpass123",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient):
    await client.post(
        "/api/v1/auth/register",
        json={
            "username": "user1",
            "email": "dup@example.com",
            "password": "strongpass123",
        },
    )
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "username": "user2",
            "email": "dup@example.com",
            "password": "strongpass123",
        },
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, test_user):
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "test@example.com",
            "password": "password123",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data


@pytest.mark.asyncio
async def test_login_invalid_password(client: AsyncClient, test_user):
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "test@example.com",
            "password": "wrongpassword",
        },
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_refresh_token(client: AsyncClient, test_user):
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "test@example.com",
            "password": "password123",
        },
    )
    refresh_token = login_resp.json()["refresh_token"]

    response = await client.post(
        "/api/v1/auth/refresh",
        json={
            "refresh_token": refresh_token,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data


@pytest.mark.asyncio
async def test_refresh_invalid_token(client: AsyncClient):
    response = await client.post(
        "/api/v1/auth/refresh",
        json={
            "refresh_token": "invalid_token_here",
        },
    )
    assert response.status_code == 401


@pytest.mark.asyncio
@pytest.mark.parametrize("subject", [None, "not-a-uuid", ""])
@pytest.mark.parametrize("token_type", ["access", "refresh"])
async def test_tokens_without_a_valid_user_id_are_rejected(
    client: AsyncClient, subject, token_type: str
):
    claims = {"type": token_type}
    if subject is not None:
        claims["sub"] = subject
    token = jwt.encode(
        claims, settings.jwt_secret_key, algorithm=settings.jwt_algorithm
    )

    if token_type == "access":
        response = await client.get(
            "/api/v1/users/me", headers={"Authorization": f"Bearer {token}"}
        )
    else:
        response = await client.post(
            "/api/v1/auth/refresh", json={"refresh_token": token}
        )

    assert response.status_code == 401


@pytest.mark.asyncio
@pytest.mark.parametrize("token_type", ["access", "refresh"])
@pytest.mark.parametrize(
    "invalid_claim", ["expired", "wrong_type", "missing_type", "wrong_signature"]
)
async def test_invalid_tokens_cannot_authenticate_or_refresh(
    client: AsyncClient, test_user, token_type: str, invalid_claim: str
):
    claims = {"sub": str(test_user.id), "type": token_type, "exp": 4102444800}
    secret = settings.jwt_secret_key
    if invalid_claim == "expired":
        claims["exp"] = 0
    elif invalid_claim == "wrong_type":
        claims["type"] = "refresh" if token_type == "access" else "access"
    elif invalid_claim == "missing_type":
        del claims["type"]
    else:
        secret = "a-different-signing-secret"
    token = jwt.encode(claims, secret, algorithm=settings.jwt_algorithm)

    if token_type == "access":
        response = await client.get(
            "/api/v1/users/me", headers={"Authorization": f"Bearer {token}"}
        )
    else:
        response = await client.post(
            "/api/v1/auth/refresh", json={"refresh_token": token}
        )

    assert response.status_code == 401
