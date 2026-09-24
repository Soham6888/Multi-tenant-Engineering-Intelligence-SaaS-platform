from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class Role(StrEnum):
    OWNER = "OWNER"
    ADMIN = "ADMIN"
    MANAGER = "MANAGER"
    DEVELOPER = "DEVELOPER"
    VIEWER = "VIEWER"


class InvitationRole(StrEnum):
    ADMIN = "ADMIN"
    MANAGER = "MANAGER"
    DEVELOPER = "DEVELOPER"
    VIEWER = "VIEWER"


class OrganizationCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=120)

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        result = value.strip()
        if not result:
            raise ValueError("Organization name is required")
        return result


class OrganizationOutput(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    slug: str
    created_at: datetime


class OrganizationSummary(OrganizationOutput):
    role: Role


class MemberOutput(BaseModel):
    id: UUID
    user_id: UUID
    email: EmailStr
    name: str
    role: Role
    joined_at: datetime


class RoleUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: Role


class InvitationCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    role: InvitationRole


class InvitationOutput(BaseModel):
    organization_id: UUID
    email: EmailStr
    role: InvitationRole
    token: str = Field(
        description="Display once to the organization administrator for out-of-band delivery"
    )
    expires_at: datetime


class InvitationAccept(BaseModel):
    model_config = ConfigDict(extra="forbid")

    token: str = Field(min_length=43, max_length=43)
