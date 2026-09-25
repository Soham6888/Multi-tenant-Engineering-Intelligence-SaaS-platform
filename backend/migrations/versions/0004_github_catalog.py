"""Tenant-safe GitHub installation bindings and repository catalog."""

import sqlalchemy as sa
from alembic import op

revision = "0004_github_catalog"
down_revision = "0003_audit_tenant"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "integrations",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "organization_id",
            sa.Uuid(),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("provider_host", sa.String(255), server_default="github.com", nullable=False),
        sa.Column("app_id", sa.BigInteger(), nullable=False),
        sa.Column("installation_id", sa.BigInteger(), nullable=False),
        sa.Column("account_id", sa.BigInteger(), nullable=False),
        sa.Column("account_login", sa.String(100), nullable=False),
        sa.Column("status", sa.String(16), server_default="active", nullable=False),
        sa.Column("generation", sa.Integer(), server_default="1", nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.UniqueConstraint("organization_id", "id", "provider_host", name="uq_integration_tenant"),
        sa.CheckConstraint(
            "status IN ('active', 'suspended', 'disconnected')", name="ck_integration_status"
        ),
        sa.CheckConstraint(
            "app_id > 0 AND installation_id > 0 AND account_id > 0", name="ck_integration_ids"
        ),
        sa.CheckConstraint("generation > 0", name="ck_integration_generation"),
        sa.CheckConstraint("provider_host = 'github.com'", name="ck_integration_host"),
    )
    op.create_index("ix_integrations_organization_id", "integrations", ["organization_id"])
    op.create_index(
        "uq_integration_active_installation",
        "integrations",
        ["provider_host", "app_id", "installation_id"],
        unique=True,
        postgresql_where=sa.text("status <> 'disconnected'"),
    )
    op.create_table(
        "repositories",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("integration_id", sa.Uuid(), nullable=False),
        sa.Column("provider_host", sa.String(255), server_default="github.com", nullable=False),
        sa.Column("external_id", sa.BigInteger(), nullable=False),
        sa.Column("full_name", sa.String(256), nullable=False),
        sa.Column("private", sa.Boolean(), nullable=False),
        sa.Column("archived", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("selected", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("accessible", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("catalog_refreshed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["organization_id", "integration_id", "provider_host"],
            ["integrations.organization_id", "integrations.id", "integrations.provider_host"],
            name="fk_repository_tenant_integration",
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint(
            "organization_id", "provider_host", "external_id", name="uq_repository_external"
        ),
        sa.CheckConstraint("external_id > 0", name="ck_repository_external_id"),
    )
    op.create_index(
        "ix_repository_integration", "repositories", ["organization_id", "integration_id"]
    )


def downgrade() -> None:
    op.drop_table("repositories")
    op.drop_table("integrations")
