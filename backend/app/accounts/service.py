from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.entities import Account, Customer


def create_account(db: Session, customer_id: int, currency: str) -> Account:
    customer = db.get(Customer, customer_id)
    if not customer:
        raise ValueError("Customer not found")

    account = Account(customer_id=customer_id, currency=currency.upper())
    db.add(account)
    db.flush()
    return account


def get_account_by_id(db: Session, account_id: int) -> Account | None:
    return db.scalar(
        select(Account)
        .options(joinedload(Account.customer))
        .where(Account.id == account_id)
    )


def list_accounts(db: Session) -> list[Account]:
    return list(db.scalars(select(Account).order_by(Account.id.asc())))
