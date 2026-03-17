"""remove investments module

Revision ID: 0002_remove_investments
Revises: 0001_initial
Create Date: 2026-03-17

"""
from __future__ import annotations

from alembic import op

# revision identifiers, used by Alembic.
revision = "0002_remove_investments"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("DROP TABLE IF EXISTS investment_transactions CASCADE")
    op.execute("DROP TABLE IF EXISTS investment_positions CASCADE")
    op.execute("DROP TABLE IF EXISTS investment_assets CASCADE")
    op.execute("DROP TYPE IF EXISTS investment_side")
    op.execute("DROP TYPE IF EXISTS asset_market")
    op.execute("DROP TYPE IF EXISTS asset_type")


def downgrade() -> None:
    # No downgrade: investment module removed.
    pass
