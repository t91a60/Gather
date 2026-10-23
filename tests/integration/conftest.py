import asyncio
import os
from pathlib import Path
import subprocess
import sys
import uuid

import pytest
import pytest_asyncio
import redis.asyncio as aioredis
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import NullPool

from app.redis_client import close_redis


@pytest_asyncio.fixture
async def database_engine():
    url = os.environ.get("TEST_POSTGRES_URL")
    if not url:
        pytest.skip(
            "Set TEST_POSTGRES_URL to run isolated PostgreSQL integration tests"
        )
    admin_url = make_url(url)
    if admin_url.drivername != "postgresql+asyncpg":
        pytest.fail("TEST_POSTGRES_URL must use postgresql+asyncpg")
    database_name = f"gather_test_{uuid.uuid4().hex}"
    admin = create_async_engine(
        admin_url, isolation_level="AUTOCOMMIT", poolclass=NullPool
    )
    engine = None
    created = False
    try:
        async with admin.connect() as connection:
            await connection.execute(text(f'CREATE DATABASE "{database_name}"'))
        created = True
        engine = create_async_engine(
            admin_url.set(database=database_name), poolclass=NullPool
        )
        yield engine
    finally:
        if engine is not None:
            await engine.dispose()
        try:
            if created:
                async with admin.connect() as connection:
                    await connection.execute(
                        text(f'DROP DATABASE "{database_name}" WITH (FORCE)')
                    )
        finally:
            await admin.dispose()


@pytest.fixture
def migrate(database_engine):
    root = Path(__file__).resolve().parents[2]

    def run(revision: str, direction: str = "upgrade"):
        env = os.environ.copy()
        env["DATABASE_URL"] = database_engine.url.render_as_string(hide_password=False)
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "alembic",
                "-c",
                str(root / "alembic.ini"),
                direction,
                revision,
            ],
            cwd=root,
            env=env,
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, result.stderr

    return run


@pytest_asyncio.fixture(autouse=True)
async def setup_db(migrate):
    await asyncio.to_thread(migrate, "head")
    yield


@pytest_asyncio.fixture
async def real_cache(monkeypatch):
    url = os.environ.get("TEST_REDIS_URL")
    if not url:
        pytest.skip("Set TEST_REDIS_URL to an isolated empty Redis database")
    factory = aioredis.from_url
    probe = factory(url, decode_responses=True)
    await close_redis()
    try:
        await probe.ping()
        if await probe.dbsize():
            pytest.fail("TEST_REDIS_URL must point to an empty dedicated test database")
        monkeypatch.setattr(
            aioredis, "from_url", lambda _url, **kwargs: factory(url, **kwargs)
        )
        try:
            yield probe
        finally:
            await close_redis()
            keys = [key async for key in probe.scan_iter(match="events:list:*")]
            if keys:
                await probe.delete(*keys)
    finally:
        await probe.close()
