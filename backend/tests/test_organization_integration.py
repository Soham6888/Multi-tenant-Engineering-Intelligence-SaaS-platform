"""Tenant authorization and role rules verified against migrated PostgreSQL."""

import hashlib
from uuid import UUID

import httpx
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker

from app.models import AuditLog, OrganizationInvitation

pytestmark = pytest.mark.anyio
HEADERS = {"Origin": "http://localhost:3000", "X-EIP-Request": "1"}
PASSWORD = "a memorable engineering passphrase"


async def create_user(client: httpx.AsyncClient, email: str) -> tuple[dict, str]:
    response = await client.post(
        "/api/v1/auth/register",
        json={"name": "Alex", "email": email, "password": PASSWORD},
    )
    assert response.status_code == 201, response.text
    return response.json()["user"], response.json()["csrf_token"]


async def logout(client: httpx.AsyncClient, csrf: str) -> None:
    response = await client.post("/api/v1/auth/logout", headers={"X-CSRF-Token": csrf})
    assert response.status_code == 204


async def test_organizations_are_tenant_scoped(client: httpx.AsyncClient) -> None:
    owner_a, csrf_a = await create_user(client, "owner-a@example.com")
    org_a = await client.post("/api/v1/organizations", json={"name": "Payments"})
    assert org_a.status_code == 201, org_a.text
    assert org_a.json()["slug"] == "payments"
    assert (await client.get("/api/v1/organizations")).json()["data"][0]["role"] == "OWNER"

    await logout(client, csrf_a)
    _, csrf_b = await create_user(client, "owner-b@example.com")
    org_b = await client.post("/api/v1/organizations", json={"name": "Payments"})
    assert org_b.status_code == 201
    assert org_b.json()["slug"] == "payments-2"
    assert (await client.get("/api/v1/organizations")).json()["data"][0]["id"] == org_b.json()["id"]

    await logout(client, csrf_b)
    signed_in = await client.post(
        "/api/v1/auth/login",
        json={"email": "owner-a@example.com", "password": PASSWORD},
    )
    assert signed_in.status_code == 200
    assert owner_a["email"] == "owner-a@example.com"
    outside = await client.get(f"/api/v1/organizations/{org_b.json()['id']}")
    hidden_members = await client.get(f"/api/v1/organizations/{org_b.json()['id']}/members")
    assert outside.status_code == hidden_members.status_code == 404
    assert outside.json()["error"]["code"] == "ORGANIZATION_NOT_FOUND"
    assert [org["id"] for org in (await client.get("/api/v1/organizations")).json()["data"]] == [
        org_a.json()["id"]
    ]


async def test_owner_invariant_and_single_use_invitation(
    client: httpx.AsyncClient, engine: AsyncEngine
) -> None:
    _, owner_csrf = await create_user(client, "owner@example.com")
    org = await client.post("/api/v1/organizations", json={"name": "Platform"})
    organization_id = UUID(org.json()["id"])
    members = await client.get(f"/api/v1/organizations/{organization_id}/members")
    owner_id = UUID(members.json()["data"][0]["user_id"])

    demote = await client.patch(
        f"/api/v1/organizations/{organization_id}/members/{owner_id}",
        json={"role": "MANAGER"},
    )
    remove = await client.delete(f"/api/v1/organizations/{organization_id}/members/{owner_id}")
    assert demote.status_code == remove.status_code == 409
    assert demote.json()["error"]["code"] == "LAST_OWNER"

    issued = await client.post(
        f"/api/v1/organizations/{organization_id}/invitations",
        json={"email": "lead@example.com", "role": "MANAGER"},
    )
    assert issued.status_code == 201, issued.text
    token = issued.json()["token"]
    replaced = await client.post(
        f"/api/v1/organizations/{organization_id}/invitations",
        json={"email": "lead@example.com", "role": "MANAGER"},
    )
    assert replaced.status_code == 201
    assert replaced.json()["token"] != token
    token = replaced.json()["token"]
    async with async_sessionmaker(engine, expire_on_commit=False)() as db:
        invitation = (await db.scalars(select(OrganizationInvitation))).one()
        assert invitation.token_hash == hashlib.sha256(token.encode()).hexdigest()
        assert token not in invitation.token_hash
        assert {entry.action for entry in (await db.scalars(select(AuditLog))).all()} >= {
            "ORGANIZATION_CREATED",
            "INVITATION_CREATED",
        }

    await logout(client, owner_csrf)
    _, invitee_csrf = await create_user(client, "lead@example.com")
    accepted = await client.post("/api/v1/organizations/invitations/accept", json={"token": token})
    assert accepted.status_code == 200, accepted.text
    assert accepted.json()["role"] == "MANAGER"
    members = await client.get(f"/api/v1/organizations/{organization_id}/members")
    assert {member["role"] for member in members.json()["data"]} == {"OWNER", "MANAGER"}
    second_use = await client.post(
        "/api/v1/organizations/invitations/accept", json={"token": token}
    )
    assert second_use.status_code == 404

    cannot_invite = await client.post(
        f"/api/v1/organizations/{organization_id}/invitations",
        json={"email": "someone@example.com", "role": "VIEWER"},
    )
    assert cannot_invite.status_code == 403
    assert invitee_csrf  # Session CSRF value is only returned in memory to the authenticated UI.
