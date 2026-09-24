"""Integration fixtures use isolated PostgreSQL schemas and independent Redis state."""

import os
from collections.abc import AsyncIterator
from uuid import uuid4

import httpx
import pytest
from alembic import command
from alembic.config import Config
from fakeredis.aioredis import FakeRedis
from redis.asyncio import Redis
from sqlalchemy import Connection, text
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.main import create_app


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture
async def engine() -> AsyncIterator[AsyncEngine]:
    url = os.getenv("EIP_TEST_DATABASE_URL")
    if not url:
        pytest.skip("Set EIP_TEST_DATABASE_URL to run real PostgreSQL tests")
    schema = f"eip_test_{uuid4().hex}"
    admin = create_async_engine(url, poolclass=NullPool)
    async with admin.begin() as connection:
        await connection.execute(text(f'CREATE SCHEMA "{schema}"'))
    test_engine = create_async_engine(
        url, poolclass=NullPool, connect_args={"server_settings": {"search_path": schema}}
    )

    def migrate(connection: Connection) -> None:
        config = Config("alembic.ini")
        config.attributes["connection"] = connection
        command.upgrade(config, "head")

    try:
        async with test_engine.begin() as connection:
            await connection.run_sync(migrate)
        yield test_engine
    finally:
        await test_engine.dispose()
        async with admin.begin() as connection:
            await connection.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
        await admin.dispose()


@pytest.fixture
async def client(engine: AsyncEngine) -> AsyncIterator[httpx.AsyncClient]:
    app = create_app()
    async with app.router.lifespan_context(app):
        original_redis = app.state.redis
        redis_url = os.getenv("EIP_TEST_REDIS_URL")
        redis = Redis.from_url(redis_url) if redis_url else FakeRedis()
        app.state.sessions = async_sessionmaker(engine, expire_on_commit=False)
        app.state.redis = redis
        transport = httpx.ASGITransport(app=app, client=(f"test-{uuid4().hex}", 12345))
        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://testserver",
            headers={"Origin": "http://localhost:3000", "X-EIP-Request": "1"},
        ) as test_client:
            yield test_client
        await redis.aclose()
        app.state.redis = original_redis
