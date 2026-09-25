import asyncio
import secrets
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import httpx
import pytest
from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker

from app.core.security import token_digest
from app.models import Organization, OrganizationInvitation, OrganizationMember, Session, User

pytestmark = pytest.mark.anyio
ROLES = ["OWNER", "ADMIN", "MANAGER", "DEVELOPER", "VIEWER"]


async def seed(engine: AsyncEngine, actor_role: str = "OWNER", target_role: str = "DEVELOPER"):
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as db:
        users = [
            User(
                id=uuid4(),
                name=name,
                email=f"{name}-{uuid4().hex}@example.com",
                password_hash="unused-by-session-test",
            )
            for name in ("actor", "target", "owner")
        ]
        org = Organization(id=uuid4(), name="Private workspace", slug=uuid4().hex)
        db.add_all([*users, org])
        await db.flush()
        tokens = [secrets.token_urlsafe(32) for _ in users]
        for user, role, token in zip(
            users, [actor_role, target_role, "OWNER"], tokens, strict=True
        ):
            db.add(OrganizationMember(organization_id=org.id, user_id=user.id, role=role))
            db.add(
                Session(
                    user_id=user.id,
                    token_hash=token_digest(token),
                    expires_at=datetime.now(UTC) + timedelta(hours=1),
                )
            )
        await db.commit()
    return org, users, tokens


@pytest.mark.parametrize("actor_role", ROLES)
@pytest.mark.parametrize("target_role", ROLES)
@pytest.mark.parametrize("method", ["PATCH", "DELETE"])
async def test_role_matrix(
    client: httpx.AsyncClient, engine: AsyncEngine, actor_role: str, target_role: str, method: str
) -> None:
    org, users, tokens = await seed(engine, actor_role, target_role)
    client.cookies.set("eip_session", tokens[0])
    response = await client.request(
        method,
        f"/api/v1/organizations/{org.id}/members/{users[1].id}",
        json={"role": "VIEWER"} if method == "PATCH" else None,
    )
    allowed = actor_role == "OWNER" or (
        actor_role == "ADMIN" and target_role not in ("OWNER", "ADMIN")
    )
    assert response.status_code == ((200 if method == "PATCH" else 204) if allowed else 403)


async def test_admin_cannot_promote_to_owner_or_admin(
    client: httpx.AsyncClient, engine: AsyncEngine
):
    org, users, tokens = await seed(engine, "ADMIN")
    client.cookies.set("eip_session", tokens[0])
    for role in ["OWNER", "ADMIN"]:
        response = await client.patch(
            f"/api/v1/organizations/{org.id}/members/{users[1].id}", json={"role": role}
        )
        assert response.status_code == 403
    response = await client.post(
        f"/api/v1/organizations/{org.id}/invitations",
        json={"email": "new@example.com", "role": "ADMIN"},
    )
    assert response.status_code == 403


async def test_cross_tenant_writes_hidden(client: httpx.AsyncClient, engine: AsyncEngine):
    org, users, _ = await seed(engine)
    _, _, other_tokens = await seed(engine)
    client.cookies.set("eip_session", other_tokens[0])
    path = f"/api/v1/organizations/{org.id}"
    responses = [
        await client.patch(f"{path}/members/{users[1].id}", json={"role": "OWNER"}),
        await client.delete(f"{path}/members/{users[1].id}"),
        await client.post(
            f"{path}/invitations", json={"email": "new@example.com", "role": "VIEWER"}
        ),
    ]
    assert [r.status_code for r in responses] == [404, 404, 404]


async def test_invite_expiry_wrong_email_replacement_and_revoked_issuer(client, engine):
    org, users, tokens = await seed(engine)
    email = f"invitee-{uuid4().hex}@example.com"
    client.cookies.set("eip_session", tokens[0])
    path = f"/api/v1/organizations/{org.id}/invitations"
    first = (await client.post(path, json={"email": email, "role": "VIEWER"})).json()["token"]
    second = (await client.post(path, json={"email": email, "role": "VIEWER"})).json()["token"]
    accept = "/api/v1/organizations/invitations/accept"
    assert (await client.post(accept, json={"token": first})).status_code == 404
    assert (await client.post(accept, json={"token": second})).status_code == 404
    async with async_sessionmaker(engine, expire_on_commit=False)() as db:
        # Switch an existing test account to the intended recipient, keeping its session.
        await db.execute(update(User).where(User.id == users[1].id).values(email=email))
        await db.execute(
            update(OrganizationInvitation)
            .where(OrganizationInvitation.organization_id == org.id)
            .values(expires_at=datetime.now(UTC) - timedelta(seconds=1))
        )
        await db.commit()
    client.cookies.set("eip_session", tokens[1])
    assert (await client.post(accept, json={"token": second})).status_code == 404
    async with async_sessionmaker(engine)() as db:
        await db.execute(
            update(OrganizationInvitation)
            .where(OrganizationInvitation.organization_id == org.id)
            .values(expires_at=datetime.now(UTC) + timedelta(days=1))
        )
        await db.execute(
            update(OrganizationMember)
            .where(
                OrganizationMember.organization_id == org.id,
                OrganizationMember.user_id == users[0].id,
            )
            .values(role="VIEWER")
        )
        await db.commit()
    assert (await client.post(accept, json={"token": second})).status_code == 404


async def test_concurrent_owner_changes_keep_owner_and_recheck_permission(client, engine):
    org, users, tokens = await seed(engine, "OWNER", "OWNER")
    # Remove the fixture's extra owner, leaving two owners who try to demote each other.
    async with async_sessionmaker(engine)() as db:
        await db.execute(
            update(OrganizationMember)
            .where(
                OrganizationMember.organization_id == org.id,
                OrganizationMember.user_id == users[2].id,
            )
            .values(role="VIEWER")
        )
        await db.commit()
    client.cookies.clear()
    responses = await asyncio.gather(
        *[
            client.patch(
                f"/api/v1/organizations/{org.id}/members/{users[1 - i].id}",
                headers={"Cookie": f"eip_session={tokens[i]}"},
                json={"role": "VIEWER"},
            )
            for i in [0, 1]
        ]
    )
    assert sorted(r.status_code for r in responses) == [200, 403]
    async with async_sessionmaker(engine)() as db:
        count = await db.scalar(
            select(func.count())
            .select_from(OrganizationMember)
            .where(OrganizationMember.organization_id == org.id, OrganizationMember.role == "OWNER")
        )
        assert count == 1


async def test_concurrent_self_demotion_keeps_last_owner(client, engine):
    org, users, tokens = await seed(engine, "OWNER", "OWNER")
    async with async_sessionmaker(engine)() as db:
        await db.execute(
            update(OrganizationMember)
            .where(
                OrganizationMember.organization_id == org.id,
                OrganizationMember.user_id == users[2].id,
            )
            .values(role="VIEWER")
        )
        await db.commit()
    client.cookies.clear()
    responses = await asyncio.gather(
        *[
            client.patch(
                f"/api/v1/organizations/{org.id}/members/{users[i].id}",
                headers={"Cookie": f"eip_session={tokens[i]}"},
                json={"role": "VIEWER"},
            )
            for i in [0, 1]
        ]
    )
    assert sorted(r.status_code for r in responses) == [200, 409]


async def test_pagination_is_bounded_and_scoped(client, engine):
    org, users, tokens = await seed(engine)
    client.cookies.set("eip_session", tokens[0])
    first = await client.get(f"/api/v1/organizations/{org.id}/members?limit=1")
    assert first.status_code == 200
    assert first.headers["cache-control"] == "no-store"
    body = first.json()
    assert len(body["data"]) == 1 and body["pagination"]["has_more"]
    cursor = body["pagination"]["next_cursor"]
    second = await client.get(f"/api/v1/organizations/{org.id}/members", params={"cursor": cursor})
    assert len(second.json()["data"]) == 2
    assert body["data"][0]["id"] not in [m["id"] for m in second.json()["data"]]
    assert second.json()["pagination"] == {"has_more": False, "next_cursor": None}
    assert (await client.get("/api/v1/organizations", params={"cursor": cursor})).status_code == 422
    client.cookies.set("eip_session", tokens[1])
    assert (
        await client.get(f"/api/v1/organizations/{org.id}/members", params={"cursor": cursor})
    ).status_code == 422
    for query in ["limit=0", "limit=101", "cursor=broken"]:
        assert (await client.get(f"/api/v1/organizations?{query}")).status_code == 422


async def test_api_limits_and_request_body_bound(client, engine):
    _, _, tokens = await seed(engine)
    client.cookies.set("eip_session", tokens[0])
    # Lower the test app limit without changing production configuration.
    client._transport.app.state.settings.api_user_limit = 2
    assert (await client.get("/api/v1/organizations")).status_code == 200
    assert (await client.get("/api/v1/organizations")).status_code == 200
    limited = await client.get("/api/v1/organizations")
    assert limited.status_code == 429 and limited.headers["retry-after"] == "60"
    oversized = await client.post("/api/v1/organizations", content=b"x" * 16385)
    assert oversized.status_code == 413


async def test_organization_cursor_traversal(client, engine):
    org, _, tokens = await seed(engine)
    client.cookies.set("eip_session", tokens[0])
    expected = {str(org.id)}
    for name in ["Second", "Third"]:
        response = await client.post("/api/v1/organizations", json={"name": name})
        assert response.status_code == 201
        expected.add(response.json()["id"])
    found = []
    cursor = None
    for _ in range(3):
        params = {"limit": 1}
        if cursor:
            params["cursor"] = cursor
        response = await client.get("/api/v1/organizations", params=params)
        assert response.status_code == 200
        page = response.json()
        found.extend(item["id"] for item in page["data"])
        cursor = page["pagination"]["next_cursor"]
    assert cursor is None and len(found) == 3 and set(found) == expected


async def test_simultaneous_invitation_acceptance_is_single_use(client, engine):
    org, users, tokens = await seed(engine)
    async with async_sessionmaker(engine)() as db:
        await db.execute(
            delete(OrganizationMember).where(
                OrganizationMember.organization_id == org.id,
                OrganizationMember.user_id == users[1].id,
            )
        )
        await db.commit()
    client.cookies.set("eip_session", tokens[0])
    invitation = await client.post(
        f"/api/v1/organizations/{org.id}/invitations",
        json={"email": users[1].email, "role": "DEVELOPER"},
    )
    assert invitation.status_code == 201
    assert invitation.headers["cache-control"] == "no-store"
    client.cookies.set("eip_session", tokens[1])
    responses = await asyncio.gather(
        *[
            client.post(
                "/api/v1/organizations/invitations/accept",
                json={"token": invitation.json()["token"]},
            )
            for _ in range(2)
        ]
    )
    assert sorted(r.status_code for r in responses) == [200, 404]
    async with async_sessionmaker(engine)() as db:
        count = await db.scalar(
            select(func.count())
            .select_from(OrganizationMember)
            .where(
                OrganizationMember.organization_id == org.id,
                OrganizationMember.user_id == users[1].id,
            )
        )
        assert count == 1


async def test_organization_origin_guard_and_redis_failure(client, engine, monkeypatch):
    from unittest.mock import AsyncMock

    from redis.exceptions import ConnectionError as RedisConnectionError

    _, _, tokens = await seed(engine)
    client.cookies.set("eip_session", tokens[0])
    response = await client.post(
        "/api/v1/organizations",
        json={"name": "Denied"},
        headers={"Origin": "https://untrusted.example"},
    )
    assert response.status_code == 403
    monkeypatch.setattr(
        client._transport.app.state.redis,
        "eval",
        AsyncMock(side_effect=RedisConnectionError("test failure")),
    )
    response = await client.get("/api/v1/organizations")
    assert response.status_code == 503
    assert response.headers["cache-control"] == "no-store"
    assert "test failure" not in response.text
