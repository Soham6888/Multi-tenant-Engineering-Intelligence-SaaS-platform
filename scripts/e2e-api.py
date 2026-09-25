"""Test-only loopback API with a disposable PostgreSQL schema and Fakeredis.

Run from backend with EIP_TEST_DATABASE_URL set. Never use for actual accounts.
The schema is dropped on graceful shutdown. Redis behavior here is simulated;
the container CI job remains the real Redis validation gate.
"""

import os
from contextlib import asynccontextmanager
from uuid import uuid4

import uvicorn
from alembic import command
from alembic.config import Config
from fakeredis.aioredis import FakeRedis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.main import create_app

app = create_app()
original_lifespan = app.router.lifespan_context


@asynccontextmanager
async def test_lifespan(application):
    url = os.environ["EIP_TEST_DATABASE_URL"]
    schema = f"e2e_test_{uuid4().hex}"
    admin = create_async_engine(url, poolclass=NullPool)
    engine = create_async_engine(
        url, poolclass=NullPool, connect_args={"server_settings": {"search_path": schema}}
    )
    redis = FakeRedis()

    def migrate(connection):
        config = Config("alembic.ini")
        config.attributes["connection"] = connection
        command.upgrade(config, "head")

    async with admin.begin() as connection:
        await connection.execute(text(f'CREATE SCHEMA "{schema}"'))
    try:
        async with engine.begin() as connection:
            await connection.run_sync(migrate)
        async with original_lifespan(application):
            application.state.engine = engine
            application.state.redis = redis
            application.state.sessions = async_sessionmaker(engine, expire_on_commit=False)
            yield
    finally:
        await redis.aclose()
        await engine.dispose()
        async with admin.begin() as connection:
            await connection.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
        await admin.dispose()


app.router.lifespan_context = test_lifespan
if __name__ == "__main__":
    print("TEST ONLY: disposable PostgreSQL schema and simulated Redis; loopback API")
    uvicorn.run(app, host="127.0.0.1", port=8000, access_log=False)
