"""Associate organization-scoped audit records with their tenant."""

import sqlalchemy as sa
from alembic import op

revision = "0003_audit_tenant"
down_revision = "0002_organizations"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("audit_logs", sa.Column("organization_id", sa.Uuid(), nullable=True))
    op.create_foreign_key(
        "fk_audit_logs_organization_id_organizations",
        "audit_logs",
        "organizations",
        ["organization_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_audit_logs_organization_id", "audit_logs", ["organization_id"])


def downgrade() -> None:
    op.drop_index("ix_audit_logs_organization_id", table_name="audit_logs")
    op.drop_constraint(
        "fk_audit_logs_organization_id_organizations", "audit_logs", type_="foreignkey"
    )
    op.drop_column("audit_logs", "organization_id")
