"""Real PostgreSQL tests. Each test owns a disposable schema, never existing tables."""

import asyncio
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import httpx
import pytest
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker

from app.models import AuditLog, Session, User

pytestmark = pytest.mark.anyio
PASSWORD = "a memorable engineering passphrase"
HEADERS = {"Origin": "http://localhost:3000", "X-EIP-Request": "1"}


async def register(client: httpx.AsyncClient, email: str | None = None) -> httpx.Response:
    return await client.post(
        "/api/v1/auth/register",
        json={
            "name": "Alex",
            "email": email or f"alex-{uuid4().hex}@example.com",
            "password": PASSWORD,
        },
    )


async def test_full_session_lifecycle_and_safe_persistence(
    client: httpx.AsyncClient, engine: AsyncEngine
) -> None:
    created = await register(client)
    assert created.status_code == 201, created.text
    token = client.cookies["eip_session"]
    assert "HttpOnly" in created.headers["set-cookie"]
    assert "SameSite=lax" in created.headers["set-cookie"]
    assert created.headers["cache-control"] == "no-store"
    assert "password" not in created.text
    assert (await client.get("/api/v1/auth/me")).json()["user"] == created.json()["user"]
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    async with sessions() as db:
        user = (await db.scalars(select(User))).one()
        session = (await db.scalars(select(Session))).one()
        assert user.password_hash.startswith("$argon2id$") and user.password_hash != PASSWORD
        assert token not in session.token_hash
    logged_out = await client.post(
        "/api/v1/auth/logout", headers={"X-CSRF-Token": created.json()["csrf_token"]}
    )
    assert logged_out.status_code == 204
    assert (await client.get("/api/v1/auth/me")).status_code == 401
    assert (
        await client.get("/api/v1/auth/me", headers={"Cookie": f"eip_session={token}"})
    ).status_code == 401
    async with sessions() as db:
        assert (await db.scalars(select(Session))).all() == []
        assert set((await db.scalars(select(AuditLog.action))).all()) == {"REGISTER", "LOGOUT"}


async def test_duplicate_registration_is_atomic(
    client: httpx.AsyncClient, engine: AsyncEngine
) -> None:
    email = f"alex-{uuid4().hex}@example.com"
    results = await asyncio.gather(register(client, email), register(client, email.upper()))
    assert sorted(r.status_code for r in results) == [201, 409]
    async with async_sessionmaker(engine)() as db:
        assert len((await db.scalars(select(User))).all()) == 1
        assert len((await db.scalars(select(Session))).all()) == 1
        assert len((await db.scalars(select(AuditLog))).all()) == 1


async def test_login_rotates_session_and_rejects_bad_credentials(client: httpx.AsyncClient) -> None:
    created = await register(client)
    old = client.cookies["eip_session"]
    email = created.json()["user"]["email"]
    bad = await client.post("/api/v1/auth/login", json={"email": email, "password": "wrong"})
    missing = await client.post(
        "/api/v1/auth/login",
        json={"email": f"missing-{uuid4().hex}@example.com", "password": "wrong"},
    )
    assert bad.status_code == missing.status_code == 401
    assert bad.json()["error"]["message"] == missing.json()["error"]["message"]
    signed_in = await client.post(
        "/api/v1/auth/login", json={"email": email.upper(), "password": PASSWORD}
    )
    assert signed_in.status_code == 200
    assert client.cookies["eip_session"] != old
    assert (
        await client.get("/api/v1/auth/me", headers={"Cookie": f"eip_session={old}"})
    ).status_code == 401


async def test_expired_sessions_are_rejected(
    client: httpx.AsyncClient, engine: AsyncEngine
) -> None:
    await register(client)
    async with engine.begin() as connection:
        await connection.execute(
            update(Session).values(expires_at=datetime.now(UTC) - timedelta(seconds=1))
        )
    assert (await client.get("/api/v1/auth/me")).status_code == 401


async def test_csrf_and_origin_guards(client: httpx.AsyncClient) -> None:
    created = await register(client)
    assert (await client.post("/api/v1/auth/logout")).status_code == 403
    assert (
        await client.post("/api/v1/auth/logout", headers={"X-CSRF-Token": "wrong"})
    ).status_code == 403
    assert (
        await client.post(
            "/api/v1/auth/logout",
            headers={
                "Origin": "https://evil.example",
                "X-CSRF-Token": created.json()["csrf_token"],
            },
        )
    ).status_code == 403
    assert (await client.get("/api/v1/auth/me")).status_code == 200
    client.headers.pop("Origin")
    assert (await register(client)).status_code == 403


async def test_account_rate_limit(client: httpx.AsyncClient) -> None:
    email = f"missing-{uuid4().hex}@example.com"
    statuses = []
    for _ in range(11):
        response = await client.post(
            "/api/v1/auth/login", json={"email": email, "password": "incorrect"}
        )
        statuses.append(response.status_code)
    assert statuses == [401] * 10 + [429]
    assert response.headers["retry-after"] == "300"
