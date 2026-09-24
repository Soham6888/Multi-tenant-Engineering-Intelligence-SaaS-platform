from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import browser_mutation, current_user, database
from app.models import Organization, User
from app.schemas.organizations import (
    InvitationAccept,
    InvitationCreate,
    InvitationOutput,
    InvitationRole,
    MemberOutput,
    OrganizationCreate,
    OrganizationOutput,
    OrganizationSummary,
    Role,
    RoleUpdate,
)
from app.services.organizations import OrganizationService

router = APIRouter(prefix="/api/v1/organizations", tags=["organizations"])


def service_for(db: Annotated[AsyncSession, Depends(database)]) -> OrganizationService:
    return OrganizationService(db)


@router.get("", response_model=list[OrganizationSummary])
async def list_organizations(
    actor: Annotated[User, Depends(current_user)],
    service: Annotated[OrganizationService, Depends(service_for)],
) -> list[OrganizationSummary]:
    return [
        OrganizationSummary(
            id=org.id,
            name=org.name,
            slug=org.slug,
            created_at=org.created_at,
            role=Role(member.role),
        )
        for org, member in await service.repository.memberships(actor.id)
    ]


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=OrganizationOutput,
    dependencies=[Depends(browser_mutation)],
)
async def create_organization(
    data: OrganizationCreate,
    request: Request,
    actor: Annotated[User, Depends(current_user)],
    service: Annotated[OrganizationService, Depends(service_for)],
) -> Organization:
    return await service.create(actor, data, request.state.request_id)


@router.get("/{organization_id}", response_model=OrganizationSummary)
async def get_organization(
    organization_id: UUID,
    actor: Annotated[User, Depends(current_user)],
    service: Annotated[OrganizationService, Depends(service_for)],
) -> OrganizationSummary:
    organization, membership = await service.get(organization_id, actor)
    return OrganizationSummary(
        id=organization.id,
        name=organization.name,
        slug=organization.slug,
        created_at=organization.created_at,
        role=Role(membership.role),
    )


@router.get("/{organization_id}/members", response_model=list[MemberOutput])
async def get_members(
    organization_id: UUID,
    actor: Annotated[User, Depends(current_user)],
    service: Annotated[OrganizationService, Depends(service_for)],
) -> list[MemberOutput]:
    return [
        MemberOutput(
            id=member.id,
            user_id=user.id,
            email=user.email,
            name=user.name,
            role=Role(member.role),
            joined_at=member.created_at,
        )
        for member, user in await service.list_members(organization_id, actor)
    ]


@router.patch(
    "/{organization_id}/members/{user_id}",
    response_model=MemberOutput,
    dependencies=[Depends(browser_mutation)],
)
async def change_member_role(
    organization_id: UUID,
    user_id: UUID,
    data: RoleUpdate,
    request: Request,
    actor: Annotated[User, Depends(current_user)],
    service: Annotated[OrganizationService, Depends(service_for)],
) -> MemberOutput:
    member = await service.update_role(
        organization_id, user_id, data.role, actor, request.state.request_id
    )
    db_user = await service.db.get(User, user_id)
    assert db_user is not None
    return MemberOutput(
        id=member.id,
        user_id=db_user.id,
        email=db_user.email,
        name=db_user.name,
        role=Role(member.role),
        joined_at=member.created_at,
    )


@router.delete(
    "/{organization_id}/members/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(browser_mutation)],
)
async def remove_member(
    organization_id: UUID,
    user_id: UUID,
    request: Request,
    actor: Annotated[User, Depends(current_user)],
    service: Annotated[OrganizationService, Depends(service_for)],
) -> None:
    await service.remove_member(organization_id, user_id, actor, request.state.request_id)


@router.post(
    "/{organization_id}/invitations",
    status_code=status.HTTP_201_CREATED,
    response_model=InvitationOutput,
    dependencies=[Depends(browser_mutation)],
)
async def create_invitation(
    organization_id: UUID,
    data: InvitationCreate,
    request: Request,
    actor: Annotated[User, Depends(current_user)],
    service: Annotated[OrganizationService, Depends(service_for)],
) -> InvitationOutput:
    invitation, token = await service.invite(organization_id, data, actor, request.state.request_id)
    return InvitationOutput(
        organization_id=invitation.organization_id,
        email=invitation.email,
        role=InvitationRole(invitation.role),
        token=token,
        expires_at=invitation.expires_at,
    )


@router.post(
    "/invitations/accept",
    response_model=OrganizationSummary,
    dependencies=[Depends(browser_mutation)],
)
async def accept_invitation(
    data: InvitationAccept,
    request: Request,
    actor: Annotated[User, Depends(current_user)],
    service: Annotated[OrganizationService, Depends(service_for)],
) -> OrganizationSummary:
    organization, membership = await service.accept_invitation(
        data, actor, request.state.request_id
    )
    return OrganizationSummary(
        id=organization.id,
        name=organization.name,
        slug=organization.slug,
        created_at=organization.created_at,
        role=Role(membership.role),
    )
