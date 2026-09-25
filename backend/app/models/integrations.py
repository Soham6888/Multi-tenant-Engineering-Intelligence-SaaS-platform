"""GitHub catalog identities. Credentials and engineering events live elsewhere."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    String,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.auth import Base


class Integration(Base):
    __tablename__ = "integrations"
    __table_args__ = (
        UniqueConstraint("organization_id", "id", "provider_host", name="uq_integration_tenant"),
        CheckConstraint(
            "status IN ('active', 'suspended', 'disconnected')", name="ck_integration_status"
        ),
        CheckConstraint(
            "app_id > 0 AND installation_id > 0 AND account_id > 0", name="ck_integration_ids"
        ),
        CheckConstraint("generation > 0", name="ck_integration_generation"),
        CheckConstraint("provider_host = 'github.com'", name="ck_integration_host"),
        Index(
            "uq_integration_active_installation",
            "provider_host",
            "app_id",
            "installation_id",
            unique=True,
            postgresql_where=text("status <> 'disconnected'"),
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), index=True
    )
    provider_host: Mapped[str] = mapped_column(String(255), server_default="github.com")
    app_id: Mapped[int] = mapped_column(BigInteger)
    installation_id: Mapped[int] = mapped_column(BigInteger)
    account_id: Mapped[int] = mapped_column(BigInteger)
    account_login: Mapped[str] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(16), server_default="active")
    generation: Mapped[int] = mapped_column(server_default="1")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class Repository(Base):
    __tablename__ = "repositories"
    __table_args__ = (
        ForeignKeyConstraint(
            ["organization_id", "integration_id", "provider_host"],
            ["integrations.organization_id", "integrations.id", "integrations.provider_host"],
            name="fk_repository_tenant_integration",
            ondelete="CASCADE",
        ),
        UniqueConstraint(
            "organization_id", "provider_host", "external_id", name="uq_repository_external"
        ),
        CheckConstraint("external_id > 0", name="ck_repository_external_id"),
        Index("ix_repository_integration", "organization_id", "integration_id"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column()
    integration_id: Mapped[UUID] = mapped_column()
    provider_host: Mapped[str] = mapped_column(String(255), server_default="github.com")
    external_id: Mapped[int] = mapped_column(BigInteger)
    full_name: Mapped[str] = mapped_column(String(256))
    private: Mapped[bool] = mapped_column(Boolean)
    archived: Mapped[bool] = mapped_column(Boolean, server_default="false")
    selected: Mapped[bool] = mapped_column(Boolean, server_default="false")
    accessible: Mapped[bool] = mapped_column(Boolean, server_default="true")
    catalog_refreshed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
