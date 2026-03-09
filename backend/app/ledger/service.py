from decimal import Decimal

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.models.entities import Account, LedgerEntry, LedgerEntryType


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


def verify_account_ledger(db: Session, account: Account) -> dict:
    entries = list(
        db.scalars(select(LedgerEntry).where(LedgerEntry.account_id == account.id))
    )
    credits = sum(
        (Decimal(entry.amount) for entry in entries if entry.type == LedgerEntryType.CREDIT),
        start=Decimal("0"),
    )
    debits = sum(
        (Decimal(entry.amount) for entry in entries if entry.type == LedgerEntryType.DEBIT),
        start=Decimal("0"),
    )
    calculated_balance = credits - debits

    issues: list[str] = []
    for entry in entries:
        if Decimal(entry.amount) <= 0:
            issues.append(f"Ledger entry {entry.id} has non-positive amount")
        if entry.type not in (LedgerEntryType.DEBIT, LedgerEntryType.CREDIT):
            issues.append(f"Ledger entry {entry.id} has invalid type")

    return {
        "account_id": account.id,
        "currency": account.currency,
        "entries_count": len(entries),
        "credits_total": credits,
        "debits_total": debits,
        "calculated_balance": calculated_balance,
        "is_valid": len(issues) == 0,
        "issues": issues,
    }


def verify_system_ledger(db: Session) -> dict:
    accounts = list(db.scalars(select(Account).order_by(Account.id.asc())))
    results = [verify_account_ledger(db, account) for account in accounts]
    invalid_count = sum(1 for item in results if not item["is_valid"])
    return {
        "checked_accounts": len(accounts),
        "invalid_accounts": invalid_count,
        "results": results,
    }
