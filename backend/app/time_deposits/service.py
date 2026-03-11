from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from app.accounts.service import get_account_by_id
from app.ledger.service import append_ledger_entry, get_account_balance
from app.models.entities import DepositStatus, LedgerEntryType, TimeDeposit, User, UserRole


def _calculate_maturity(principal: Decimal, annual_rate: Decimal, duration_months: int) -> Decimal:
    rate = annual_rate / Decimal("100")
    years = Decimal(duration_months) / Decimal("12")
    return principal + (principal * rate * years)


def open_time_deposit(
    db: Session,
    user: User,
    account_id: int,
    amount: Decimal,
    annual_rate: Decimal,
    duration_months: int,
) -> TimeDeposit:
    account = get_account_by_id(db, account_id)
    if not account:
        raise ValueError("Account not found")
    if user.role != UserRole.ADMIN and account.customer.user_id != user.id:
        raise PermissionError("Not allowed to open deposit on this account")

    balance = get_account_balance(db, account_id)
    if balance < amount:
        raise ValueError("Insufficient funds for time deposit")

    expected_return = _calculate_maturity(amount, annual_rate, duration_months)
    maturity_date = datetime.now(timezone.utc) + timedelta(days=30 * duration_months)

    deposit = TimeDeposit(
        user_id=user.id,
        account_id=account_id,
        currency=account.currency,
        principal=amount,
        annual_rate=annual_rate,
        duration_months=duration_months,
        expected_return=expected_return,
        maturity_date=maturity_date,
        status=DepositStatus.ACTIVE,
    )
    db.add(deposit)
    db.flush()

    append_ledger_entry(
        db,
        account_id,
        LedgerEntryType.DEBIT,
        amount,
        reference_id=f"time_deposit:{deposit.id}:open",
    )
    db.flush()

    return deposit


def claim_time_deposit(db: Session, user: User, deposit_id: int) -> tuple[TimeDeposit, Decimal]:
    deposit = db.get(TimeDeposit, deposit_id)
    if not deposit:
        raise ValueError("Time deposit not found")
    if user.role != UserRole.ADMIN and deposit.user_id != user.id:
        raise PermissionError("Not allowed to claim this deposit")

    now = datetime.now(timezone.utc)
    matured = now >= deposit.maturity_date
    if not matured:
        raise ValueError("Deposit has not matured yet")

    if deposit.status == DepositStatus.COMPLETED:
        raise ValueError("Deposit already completed")

    credit_amount = deposit.expected_return

    append_ledger_entry(
        db,
        deposit.account_id,
        LedgerEntryType.CREDIT,
        credit_amount,
        reference_id=f"time_deposit:{deposit.id}:claim",
    )

    deposit.status = DepositStatus.COMPLETED
    db.add(deposit)
    db.flush()
    return deposit, credit_amount
