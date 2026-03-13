"""initial schema

Revision ID: 0001_initial
Revises: 
Create Date: 2026-03-13

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    user_role = sa.Enum("ADMIN", "CUSTOMER", name="user_role")
    customer_status = sa.Enum("PENDING", "VERIFIED", "SUSPENDED", name="customer_status")
    ledger_entry_type = sa.Enum("DEBIT", "CREDIT", name="ledger_entry_type")
    transfer_status = sa.Enum("PENDING", "COMPLETED", "FAILED", name="transfer_status")
    event_status = sa.Enum("PENDING", "PROCESSED", name="event_status")
    asset_type = sa.Enum("STOCK", name="asset_type")
    asset_market = sa.Enum("BIST", "SP500", name="asset_market")
    investment_side = sa.Enum("BUY", "SELL", name="investment_side")
    deposit_status = sa.Enum("ACTIVE", "MATURED", "COMPLETED", name="deposit_status")
    loan_status = sa.Enum("PENDING", "APPROVED", "REJECTED", name="loan_status")
    card_status = sa.Enum("ACTIVE", "INACTIVE", name="card_status")

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", user_role, nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "customers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("status", customer_status, nullable=False, server_default="PENDING"),
        sa.Column("kyc_full_name", sa.String(length=255), nullable=False),
        sa.Column("kyc_document_id", sa.String(length=100), nullable=False),
        sa.Column("phone", sa.String(length=50), nullable=True),
        sa.Column("address", sa.String(length=255), nullable=True),
        sa.Column("city", sa.String(length=100), nullable=True),
        sa.Column("country", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_customers_user_id", "customers", ["user_id"], unique=True)

    op.create_table(
        "accounts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("customer_id", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("iban", sa.String(length=34), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_accounts_customer_id", "accounts", ["customer_id"], unique=False)
    op.create_index("ix_accounts_iban", "accounts", ["iban"], unique=True)

    op.create_table(
        "ledger_entries",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("account_id", sa.Integer(), nullable=False),
        sa.Column("type", ledger_entry_type, nullable=False),
        sa.Column("amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("reference_id", sa.String(length=100), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_ledger_entries_account_id", "ledger_entries", ["account_id"], unique=False)
    op.create_index("ix_ledger_entries_reference_id", "ledger_entries", ["reference_id"], unique=False)

    op.create_table(
        "transfers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("from_account", sa.Integer(), nullable=False),
        sa.Column("to_account", sa.Integer(), nullable=False),
        sa.Column("amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("status", transfer_status, nullable=False, server_default="PENDING"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["from_account"], ["accounts.id"]),
        sa.ForeignKeyConstraint(["to_account"], ["accounts.id"]),
    )
    op.create_index("ix_transfers_from_account", "transfers", ["from_account"], unique=False)
    op.create_index("ix_transfers_to_account", "transfers", ["to_account"], unique=False)

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("action", sa.String(length=255), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("outcome", sa.String(length=50), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
    )
    op.create_index("ix_audit_logs_user_id", "audit_logs", ["user_id"], unique=False)

    op.create_table(
        "outbox_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("aggregate_type", sa.String(length=100), nullable=False),
        sa.Column("aggregate_id", sa.String(length=100), nullable=False),
        sa.Column("event_type", sa.String(length=100), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("status", event_status, nullable=False, server_default="PENDING"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "investment_assets",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("symbol", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("asset_type", asset_type, nullable=False),
        sa.Column("market", asset_market, nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("exchange", sa.String(length=16), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_investment_assets_symbol", "investment_assets", ["symbol"], unique=False)

    op.create_table(
        "investment_positions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("asset_id", sa.Integer(), nullable=False),
        sa.Column("quantity", sa.Numeric(18, 6), nullable=False, server_default="0"),
        sa.Column("average_price", sa.Numeric(18, 6), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["asset_id"], ["investment_assets.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_investment_positions_user_id", "investment_positions", ["user_id"], unique=False)
    op.create_index("ix_investment_positions_asset_id", "investment_positions", ["asset_id"], unique=False)

    op.create_table(
        "investment_transactions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("account_id", sa.Integer(), nullable=False),
        sa.Column("asset_id", sa.Integer(), nullable=False),
        sa.Column("side", investment_side, nullable=False),
        sa.Column("quantity", sa.Numeric(18, 6), nullable=False),
        sa.Column("price", sa.Numeric(18, 6), nullable=False),
        sa.Column("total", sa.Numeric(18, 6), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["asset_id"], ["investment_assets.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_investment_transactions_user_id", "investment_transactions", ["user_id"], unique=False)
    op.create_index("ix_investment_transactions_account_id", "investment_transactions", ["account_id"], unique=False)
    op.create_index("ix_investment_transactions_asset_id", "investment_transactions", ["asset_id"], unique=False)

    op.create_table(
        "time_deposits",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("account_id", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("principal", sa.Numeric(18, 2), nullable=False),
        sa.Column("annual_rate", sa.Numeric(5, 2), nullable=False),
        sa.Column("duration_months", sa.Integer(), nullable=False),
        sa.Column("expected_return", sa.Numeric(18, 2), nullable=False),
        sa.Column("opened_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("maturity_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", deposit_status, nullable=False, server_default="ACTIVE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_time_deposits_user_id", "time_deposits", ["user_id"], unique=False)
    op.create_index("ix_time_deposits_account_id", "time_deposits", ["account_id"], unique=False)

    op.create_table(
        "loans",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("account_id", sa.Integer(), nullable=True),
        sa.Column("amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("purpose", sa.String(length=255), nullable=False),
        sa.Column("status", loan_status, nullable=False, server_default="PENDING"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("approved_by", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["approved_by"], ["users.id"]),
    )
    op.create_index("ix_loans_user_id", "loans", ["user_id"], unique=False)

    op.create_table(
        "cards",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("account_id", sa.Integer(), nullable=False),
        sa.Column("card_number", sa.String(length=19), nullable=False),
        sa.Column("expiry_month", sa.Integer(), nullable=False),
        sa.Column("expiry_year", sa.Integer(), nullable=False),
        sa.Column("status", card_status, nullable=False, server_default="ACTIVE"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_cards_account_id", "cards", ["account_id"], unique=False)
    op.create_index("ix_cards_card_number", "cards", ["card_number"], unique=True)


def downgrade() -> None:
    op.drop_table("cards")
    op.drop_table("loans")
    op.drop_table("time_deposits")
    op.drop_table("investment_transactions")
    op.drop_table("investment_positions")
    op.drop_table("investment_assets")
    op.drop_table("outbox_events")
    op.drop_table("audit_logs")
    op.drop_table("transfers")
    op.drop_table("ledger_entries")
    op.drop_table("accounts")
    op.drop_table("customers")
    op.drop_table("users")

    op.execute("DROP TYPE IF EXISTS card_status")
    op.execute("DROP TYPE IF EXISTS loan_status")
    op.execute("DROP TYPE IF EXISTS deposit_status")
    op.execute("DROP TYPE IF EXISTS investment_side")
    op.execute("DROP TYPE IF EXISTS asset_market")
    op.execute("DROP TYPE IF EXISTS asset_type")
    op.execute("DROP TYPE IF EXISTS event_status")
    op.execute("DROP TYPE IF EXISTS transfer_status")
    op.execute("DROP TYPE IF EXISTS ledger_entry_type")
    op.execute("DROP TYPE IF EXISTS customer_status")
    op.execute("DROP TYPE IF EXISTS user_role")
