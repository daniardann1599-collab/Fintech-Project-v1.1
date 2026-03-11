from __future__ import annotations

from decimal import Decimal

from sqlalchemy.orm import Session

from app.accounts.service import get_account_by_id
from app.ledger.service import append_ledger_entry
from app.models.entities import Loan, LoanStatus, LedgerEntryType, User, UserRole


def request_loan(
    db: Session,
    user: User,
    account_id: int,
    amount: Decimal,
    currency: str,
    purpose: str,
) -> Loan:
    account = get_account_by_id(db, account_id)
    if not account:
        raise ValueError("Account not found")
    if user.role != UserRole.ADMIN and account.customer.user_id != user.id:
        raise PermissionError("Not allowed to request loan on this account")
    if account.currency != currency.upper():
        raise ValueError("Loan currency must match account currency")

    loan = Loan(
        user_id=user.id,
        account_id=account_id,
        amount=amount,
        currency=currency.upper(),
        purpose=purpose,
        status=LoanStatus.PENDING,
    )
    db.add(loan)
    db.flush()
    return loan


def update_loan_status(db: Session, loan: Loan, status: LoanStatus, admin: User) -> Loan:
    if admin.role != UserRole.ADMIN:
        raise PermissionError("Admin privileges required")

    loan.status = status
    loan.approved_by = admin.id
    db.add(loan)

    if status == LoanStatus.APPROVED and loan.account_id:
        append_ledger_entry(
            db,
            loan.account_id,
            LedgerEntryType.CREDIT,
            loan.amount,
            reference_id=f"loan:{loan.id}:disbursement",
        )

    db.flush()
    return loan
