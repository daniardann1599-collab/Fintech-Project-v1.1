from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.entities import Account, Transfer, TransferStatus, User, UserRole


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
