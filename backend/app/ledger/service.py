from decimal import Decimal

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.models.entities import LedgerEntry, LedgerEntryType


def append_ledger_entry(
    db: Session,
    account_id: int,
    entry_type: LedgerEntryType,
    amount: Decimal,
    reference_id: str,
) -> LedgerEntry:
    entry = LedgerEntry(
        account_id=account_id,
        type=entry_type,
        amount=amount,
        reference_id=reference_id,
    )
    db.add(entry)
    db.flush()
    return entry


def get_account_balance(db: Session, account_id: int) -> Decimal:
    balance_query = select(
        func.coalesce(
            func.sum(
                case(
                    (LedgerEntry.type == LedgerEntryType.CREDIT, LedgerEntry.amount),
                    else_=-LedgerEntry.amount,
                )
            ),
            0,
        )
    ).where(LedgerEntry.account_id == account_id)

    balance = db.scalar(balance_query)
    return Decimal(balance or 0)


def list_account_entries(db: Session, account_id: int) -> list[LedgerEntry]:
    return list(
        db.scalars(
            select(LedgerEntry)
            .where(LedgerEntry.account_id == account_id)
            .order_by(LedgerEntry.created_at.desc())
        )
    )
