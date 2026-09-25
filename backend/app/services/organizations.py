import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    AuditLog,
    Organization,
    OrganizationInvitation,
    OrganizationMember,
    User,
)
from app.repositories.organizations import OrganizationRepository
from app.schemas.organizations import InvitationAccept, InvitationCreate, OrganizationCreate, Role
from app.services.organization_errors import OrganizationError
from app.services.slug import make_slug


class OrganizationService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repository = OrganizationRepository(db)

    def audit(
        self, actor: User, action: str, organization_id: UUID, resource_id: UUID, request_id: str
    ) -> None:
        self.db.add(
            AuditLog(
                user_id=actor.id,
                organization_id=organization_id,
                action=action,
                resource_type=(
                    "ORGANIZATION_MEMBER"
                    if action in ("ROLE_CHANGED", "USER_REMOVED")
                    else "ORGANIZATION_INVITATION"
                    if action.startswith("INVITATION_")
                    else "ORGANIZATION"
                ),
                resource_id=resource_id,
                request_id=request_id,
            )
        )

    async def create(self, actor: User, data: OrganizationCreate, request_id: str) -> Organization:
        # A bounded suffix search handles concurrent creation safely via the unique index.
        base = make_slug(data.name)
        for suffix in range(1, 6):
            slug = base if suffix == 1 else make_slug(data.name, suffix)
            organization = Organization(name=data.name, slug=slug)
            try:
                async with self.db.begin_nested():
                    self.db.add(organization)
                    await self.db.flush()
                    self.db.add(
                        OrganizationMember(
                            organization_id=organization.id, user_id=actor.id, role=Role.OWNER.value
                        )
                    )
                    self.audit(
                        actor, "ORGANIZATION_CREATED", organization.id, organization.id, request_id
                    )
                    await self.db.flush()
                await self.db.commit()
                return organization
            except IntegrityError as exc:
                if suffix == 5:
                    raise OrganizationError(
                        409, "SLUG_CONFLICT", "Could not create organization"
                    ) from exc
        raise OrganizationError(409, "SLUG_CONFLICT", "Could not create organization")

    async def require_member(self, organization_id: UUID, actor: User) -> OrganizationMember:
        member = await self.repository.member(organization_id, actor.id)
        if member is None:
            raise OrganizationError(404, "ORGANIZATION_NOT_FOUND", "Organization not found")
        return member

    async def lock_organization(self, organization_id: UUID) -> None:
        # Acquire before reading permissions or targets. All membership mutations
        # use this same lock, so a waiting request rechecks current permissions.
        await self.db.scalar(
            select(Organization.id).where(Organization.id == organization_id).with_for_update()
        )

    async def get(
        self, organization_id: UUID, actor: User
    ) -> tuple[Organization, OrganizationMember]:
        member = await self.require_member(organization_id, actor)
        organization = await self.repository.organization(organization_id)
        if organization is None:
            raise OrganizationError(404, "ORGANIZATION_NOT_FOUND", "Organization not found")
        return organization, member

    async def list_members(
        self, organization_id: UUID, actor: User, limit: int = 25, after: UUID | None = None
    ) -> list[tuple[OrganizationMember, User]]:
        await self.require_member(organization_id, actor)
        return await self.repository.members(organization_id, limit, after)

    async def update_role(
        self, organization_id: UUID, user_id: UUID, role: Role, actor: User, request_id: str
    ) -> OrganizationMember:
        await self.lock_organization(organization_id)
        manager = await self.require_member(organization_id, actor)
        target = await self.repository.member(organization_id, user_id)
        if target is None:
            raise OrganizationError(404, "MEMBER_NOT_FOUND", "Member not found")
        if manager.role not in (Role.OWNER.value, Role.ADMIN.value):
            raise OrganizationError(403, "FORBIDDEN", "You cannot manage organization members")
        if manager.role == Role.ADMIN.value and (
            target.role in (Role.OWNER.value, Role.ADMIN.value) or role in (Role.OWNER, Role.ADMIN)
        ):
            raise OrganizationError(403, "FORBIDDEN", "You cannot manage this role")
        if target.role == Role.OWNER.value and role != Role.OWNER:
            await self.db.scalar(
                select(Organization.id).where(Organization.id == organization_id).with_for_update()
            )
            owner_count = await self.db.scalar(
                select(func.count())
                .select_from(OrganizationMember)
                .where(
                    OrganizationMember.organization_id == organization_id,
                    OrganizationMember.role == Role.OWNER.value,
                )
            )
            if owner_count == 1:
                raise OrganizationError(
                    409, "LAST_OWNER", "An organization must have at least one owner"
                )
        target.role = role.value
        self.audit(actor, "ROLE_CHANGED", organization_id, target.id, request_id)
        await self.db.commit()
        return target

    async def remove_member(
        self, organization_id: UUID, user_id: UUID, actor: User, request_id: str
    ) -> None:
        await self.lock_organization(organization_id)
        manager = await self.require_member(organization_id, actor)
        target = await self.repository.member(organization_id, user_id)
        if target is None:
            raise OrganizationError(404, "MEMBER_NOT_FOUND", "Member not found")
        if manager.role not in (Role.OWNER.value, Role.ADMIN.value):
            raise OrganizationError(403, "FORBIDDEN", "You cannot manage organization members")
        if manager.role == Role.ADMIN.value and target.role in (Role.OWNER.value, Role.ADMIN.value):
            raise OrganizationError(403, "FORBIDDEN", "You cannot manage this role")
        if target.role == Role.OWNER.value:
            await self.db.scalar(
                select(Organization.id).where(Organization.id == organization_id).with_for_update()
            )
            owner_count = await self.db.scalar(
                select(func.count())
                .select_from(OrganizationMember)
                .where(
                    OrganizationMember.organization_id == organization_id,
                    OrganizationMember.role == Role.OWNER.value,
                )
            )
            if owner_count == 1:
                raise OrganizationError(
                    409, "LAST_OWNER", "An organization must have at least one owner"
                )
        self.audit(actor, "USER_REMOVED", organization_id, target.id, request_id)
        await self.db.delete(target)
        await self.db.commit()

    async def invite(
        self, organization_id: UUID, data: InvitationCreate, actor: User, request_id: str
    ) -> tuple[OrganizationInvitation, str]:
        await self.lock_organization(organization_id)
        manager = await self.require_member(organization_id, actor)
        if manager.role not in (Role.OWNER.value, Role.ADMIN.value):
            raise OrganizationError(403, "FORBIDDEN", "You cannot invite organization members")
        if manager.role == Role.ADMIN.value and data.role.value == Role.ADMIN.value:
            raise OrganizationError(403, "FORBIDDEN", "You cannot invite an administrator")
        email = str(data.email).casefold()
        existing_user = await self.db.scalar(select(User).where(User.email == email))
        if existing_user and await self.repository.member(organization_id, existing_user.id):
            raise OrganizationError(409, "ALREADY_A_MEMBER", "User is already a member")
        raw = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(raw.encode()).hexdigest()
        previous = await self.db.scalar(
            select(OrganizationInvitation)
            .where(
                OrganizationInvitation.organization_id == organization_id,
                OrganizationInvitation.email == email,
            )
            .with_for_update()
        )
        invitation = OrganizationInvitation(
            id=uuid4(),
            organization_id=organization_id,
            email=email,
            role=data.role.value,
            token_hash=token_hash,
            invited_by=actor.id,
            expires_at=datetime.now(UTC) + timedelta(days=7),
        )
        try:
            if previous:
                await self.db.delete(previous)
                await self.db.flush()
            self.db.add(invitation)
            self.audit(actor, "INVITATION_CREATED", organization_id, invitation.id, request_id)
            await self.db.commit()
        except IntegrityError as exc:
            await self.db.rollback()
            raise OrganizationError(
                409, "INVITATION_CONFLICT", "Could not create invitation"
            ) from exc
        # Raw bearer token is returned once for the admin to deliver out-of-band.
        return invitation, raw

    async def accept_invitation(
        self, data: InvitationAccept, actor: User, request_id: str
    ) -> tuple[Organization, OrganizationMember]:
        digest = hashlib.sha256(data.token.encode()).hexdigest()
        invitation = await self.repository.invitation(digest)
        if invitation is not None:
            await self.lock_organization(invitation.organization_id)
            # An invite may have been replaced, accepted or expired while waiting.
            invitation = await self.repository.invitation(digest)
        if invitation is None or invitation.email != actor.email.casefold():
            raise OrganizationError(404, "INVITATION_NOT_FOUND", "Invitation not found or expired")
        issuer = await self.repository.member(invitation.organization_id, invitation.invited_by)
        if (
            issuer is None
            or issuer.role not in (Role.OWNER.value, Role.ADMIN.value)
            or (invitation.role == Role.ADMIN.value and issuer.role != Role.OWNER.value)
        ):
            raise OrganizationError(404, "INVITATION_NOT_FOUND", "Invitation not found or expired")
        try:
            async with self.db.begin_nested():
                invitation.accepted_at = datetime.now(UTC)
                member = OrganizationMember(
                    organization_id=invitation.organization_id,
                    user_id=actor.id,
                    role=invitation.role,
                )
                self.db.add(member)
                self.audit(
                    actor,
                    "INVITATION_ACCEPTED",
                    invitation.organization_id,
                    invitation.id,
                    request_id,
                )
                await self.db.flush()
            await self.db.commit()
        except IntegrityError as exc:
            await self.db.rollback()
            raise OrganizationError(
                409, "INVITATION_ALREADY_USED", "Invitation cannot be accepted"
            ) from exc
        organization = await self.repository.organization(invitation.organization_id)
        if organization is None:
            raise OrganizationError(404, "INVITATION_NOT_FOUND", "Invitation not found or expired")
        return organization, member
