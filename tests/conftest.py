import uuid
from datetime import datetime, timezone, timedelta
from typing import AsyncGenerator

import pytest
import pytest_asyncio
import redis.asyncio as aioredis
from redis.exceptions import ConnectionError as RedisConnectionError
from httpx import ASGITransport, AsyncClient
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base, get_session
from app.main import app
from app.middleware.auth import hash_password
from app.middleware.rate_limit import RateLimitMiddleware
from app.models.user import User
from app.redis_client import close_redis


@pytest_asyncio.fixture
async def database_engine(tmp_path):
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'test.db'}")

    @event.listens_for(engine.sync_engine, "connect")
    def enable_foreign_keys(connection, _):
        cursor = connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    try:
        yield engine
    finally:
        await engine.dispose()


@pytest.fixture(autouse=True)
def reset_rate_limiter():
    RateLimitMiddleware.reset()


@pytest_asyncio.fixture(autouse=True)
async def isolate_cache(request, monkeypatch):
    await close_redis()
    if request.node.get_closest_marker("redis") is None:

        async def unavailable(*args, **kwargs):
            raise RedisConnectionError("Redis unavailable in isolated API tests")

        monkeypatch.setattr(aioredis.Redis, "execute_command", unavailable)
    try:
        yield
    finally:
        await close_redis()


@pytest_asyncio.fixture(autouse=True)
async def setup_db(database_engine):
    async with database_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


@pytest_asyncio.fixture(autouse=True)
async def override_request_session(database_engine, setup_db):
    session_factory = async_sessionmaker(database_engine, expire_on_commit=False)

    async def override_get_session():
        async with session_factory() as session:
            yield session

    previous = app.dependency_overrides.copy()
    app.dependency_overrides[get_session] = override_get_session
    try:
        yield
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(previous)


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def db_session(database_engine) -> AsyncGenerator[AsyncSession, None]:
    session_factory = async_sessionmaker(database_engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession) -> User:
    user = User(
        id=uuid.uuid4(),
        username="testuser",
        email="test@example.com",
        hashed_password=hash_password("password123"),
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def second_user(db_session: AsyncSession) -> User:
    user = User(
        id=uuid.uuid4(),
        username="seconduser",
        email="second@example.com",
        hashed_password=hash_password("password123"),
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def auth_headers(client: AsyncClient, test_user: User) -> dict:
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "test@example.com",
            "password": "password123",
        },
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def second_auth_headers(client: AsyncClient, second_user: User) -> dict:
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "second@example.com",
            "password": "password123",
        },
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def sample_event(db_session: AsyncSession, test_user: User):
    from app.repositories.event import EventRepository

    repo = EventRepository(db_session)
    event = await repo.create(
        title="Test Event",
        description="A test event",
        date=datetime.now(timezone.utc) + timedelta(days=7),
        location="Test Location",
        organizer_id=test_user.id,
    )
    return event


@pytest_asyncio.fixture
async def published_post(client: AsyncClient, auth_headers: dict) -> dict:
    response = await client.post(
        "/api/v1/posts",
        headers=auth_headers,
        json={"title": "A published post", "content": "Discussion starts here."},
    )
    assert response.status_code == 201
    return response.json()
