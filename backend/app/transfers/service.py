from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.ledger.service import append_ledger_entry, get_account_balance
from app.models.entities import Account, LedgerEntryType, Transfer, TransferStatus, User, UserRole


def initiate_transfer(
    db: Session,
    from_account_id: int,
    to_account_id: int,
    amount,
    actor: User,
) -> Transfer:
    if from_account_id == to_account_id:
        raise ValueError("from_account and to_account must be different")

    from_account = db.scalar(
        select(Account)
        .options(joinedload(Account.customer))
        .where(Account.id == from_account_id)
    )
    to_account = db.scalar(
        select(Account)
        .options(joinedload(Account.customer))
        .where(Account.id == to_account_id)
    )

    if not from_account or not to_account:
        raise LookupError("One or both accounts do not exist")

    if from_account.currency != to_account.currency:
        raise ValueError("Accounts must have the same currency for internal transfer")

    if actor.role != UserRole.ADMIN and from_account.customer.user_id != actor.id:
        raise PermissionError("Not allowed to transfer from this account")

    transfer = Transfer(
        from_account=from_account_id,
        to_account=to_account_id,
        amount=amount,
        status=TransferStatus.PENDING,
    )
    db.add(transfer)
    db.flush()
    return transfer


def execute_transfer(
    db: Session,
    transfer_id: int,
    actor: User,
) -> tuple[Transfer, Decimal, Decimal]:
    transfer = db.get(Transfer, transfer_id)
    if not transfer:
        raise LookupError("Transfer not found")
    if transfer.status != TransferStatus.PENDING:
        raise ValueError("Only PENDING transfers can be executed")

    from_account = db.scalar(
        select(Account)
        .options(joinedload(Account.customer))
        .where(Account.id == transfer.from_account)
    )
    to_account = db.scalar(
        select(Account)
        .options(joinedload(Account.customer))
        .where(Account.id == transfer.to_account)
    )
    if not from_account or not to_account:
        raise LookupError("Transfer accounts are missing")
    if from_account.currency != to_account.currency:
        raise ValueError("Transfer accounts must share the same currency")

    if actor.role != UserRole.ADMIN and from_account.customer.user_id != actor.id:
        raise PermissionError("Not allowed to execute transfer from this account")

    from_balance = get_account_balance(db, from_account.id)
    if from_balance < transfer.amount:
        raise ValueError("Insufficient funds to execute transfer")

    append_ledger_entry(
        db,
        from_account.id,
        LedgerEntryType.DEBIT,
        transfer.amount,
        reference_id=f"transfer:{transfer.id}:debit",
    )
    append_ledger_entry(
        db,
        to_account.id,
        LedgerEntryType.CREDIT,
        transfer.amount,
        reference_id=f"transfer:{transfer.id}:credit",
    )

    transfer.status = TransferStatus.COMPLETED
    db.add(transfer)
    db.flush()

    updated_from_balance = get_account_balance(db, from_account.id)
    updated_to_balance = get_account_balance(db, to_account.id)
    return transfer, updated_from_balance, updated_to_balance
