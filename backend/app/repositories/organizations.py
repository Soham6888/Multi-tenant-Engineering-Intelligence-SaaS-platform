from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select, true
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Organization, OrganizationInvitation, OrganizationMember, User


class OrganizationRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def memberships(
        self, user_id: UUID, limit: int = 25, after: UUID | None = None
    ) -> list[tuple[Organization, OrganizationMember]]:
        rows = await self.db.execute(
            select(Organization, OrganizationMember)
            .join(OrganizationMember, OrganizationMember.organization_id == Organization.id)
            .where(OrganizationMember.user_id == user_id)
            .where(Organization.id > after if after is not None else true())
            .order_by(Organization.id)
            .limit(limit + 1)
        )
        return list(rows.tuples().all())

    async def member(self, organization_id: UUID, user_id: UUID) -> OrganizationMember | None:
        rows = await self.db.execute(
            select(OrganizationMember)
            .execution_options(populate_existing=True)
            .where(
                OrganizationMember.organization_id == organization_id,
                OrganizationMember.user_id == user_id,
            )
        )
        return rows.scalar_one_or_none()

    async def organization(self, organization_id: UUID) -> Organization | None:
        return await self.db.get(Organization, organization_id)

    async def members(
        self, organization_id: UUID, limit: int = 25, after: UUID | None = None
    ) -> list[tuple[OrganizationMember, User]]:
        rows = await self.db.execute(
            select(OrganizationMember, User)
            .join(User, User.id == OrganizationMember.user_id)
            .where(OrganizationMember.organization_id == organization_id)
            .where(OrganizationMember.id > after if after is not None else true())
            .order_by(OrganizationMember.id)
            .limit(limit + 1)
        )
        return list(rows.tuples().all())

    async def invitation(self, token_hash: str) -> OrganizationInvitation | None:
        now = datetime.now(UTC)
        rows = await self.db.execute(
            select(OrganizationInvitation)
            .execution_options(populate_existing=True)
            .where(
                OrganizationInvitation.token_hash == token_hash,
                OrganizationInvitation.accepted_at.is_(None),
                OrganizationInvitation.expires_at > now,
            )
        )
        return rows.scalar_one_or_none()
