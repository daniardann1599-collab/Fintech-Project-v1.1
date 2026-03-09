from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.entities import Customer, User


def create_customer(
    db: Session,
    user_id: int,
    kyc_full_name: str,
    kyc_document_id: str,
) -> Customer:
    user = db.get(User, user_id)
    if not user:
        raise ValueError("User not found")

    existing_customer = db.scalar(select(Customer).where(Customer.user_id == user_id))
    if existing_customer:
        raise ValueError("Customer already exists for this user")

    customer = Customer(
        user_id=user_id,
        kyc_full_name=kyc_full_name,
        kyc_document_id=kyc_document_id,
    )
    db.add(customer)
    db.flush()
    return customer


def get_customer_by_id(db: Session, customer_id: int) -> Customer | None:
    return db.get(Customer, customer_id)


def update_customer_status(db: Session, customer: Customer, status: str) -> Customer:
    customer.status = status
    db.add(customer)
    db.flush()
    return customer
