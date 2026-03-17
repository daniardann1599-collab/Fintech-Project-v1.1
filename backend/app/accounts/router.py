from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.accounts.schemas import AccountCreateRequest, AccountResponse, BalanceResponse, FundingRequest
from app.accounts.service import create_account, get_account_by_id, list_accounts
from app.audit.service import log_action
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.events.service import enqueue_event
from app.ledger.service import append_ledger_entry, get_account_balance
from app.models.entities import LedgerEntryType, User, UserRole

router = APIRouter(prefix="/accounts", tags=["accounts"])


@router.post("", response_model=AccountResponse, status_code=status.HTTP_201_CREATED)
def create_account_endpoint(
    payload: AccountCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AccountResponse:
    if current_user.role != UserRole.ADMIN:
        if not current_user.customer or current_user.customer.id != payload.customer_id:
            raise HTTPException(status_code=403, detail="Not allowed to create account for this customer")

    try:
        account = create_account(db, payload.customer_id, payload.currency)
        enqueue_event(
            db,
            aggregate_type="account",
            aggregate_id=str(account.id),
            event_type="ACCOUNT_CREATED",
            payload={"account_id": account.id, "customer_id": account.customer_id},
        )
        log_action(db, current_user.id, "account.create", "SUCCESS")
        db.commit()
        db.refresh(account)
        return account
    except ValueError as exc:
        db.rollback()
        log_action(db, current_user.id, "account.create", "FAILED")
        db.commit()
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("", response_model=list[AccountResponse])
def list_accounts_endpoint(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[AccountResponse]:
    accounts = list_accounts(db)
    if current_user.role == UserRole.ADMIN:
        return accounts
    return [account for account in accounts if account.customer.user_id == current_user.id]


@router.get("/{account_id}", response_model=AccountResponse)
def get_account_endpoint(
    account_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AccountResponse:
    account = get_account_by_id(db, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    if current_user.role != UserRole.ADMIN and account.customer.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not allowed to view this account")
    return account


@router.get("/{account_id}/balance", response_model=BalanceResponse)
def get_balance_endpoint(
    account_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BalanceResponse:
    account = get_account_by_id(db, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    if current_user.role != UserRole.ADMIN and account.customer.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not allowed to view this account")

    balance = get_account_balance(db, account_id)
    return BalanceResponse(account_id=account_id, balance=balance)


@router.post("/{account_id}/deposit", response_model=BalanceResponse)
def deposit_endpoint(
    account_id: int,
    payload: FundingRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BalanceResponse:
    account = get_account_by_id(db, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    if current_user.role != UserRole.ADMIN and account.customer.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not allowed to deposit to this account")

    append_ledger_entry(db, account_id, LedgerEntryType.CREDIT, payload.amount, payload.reference_id)
    enqueue_event(
        db,
        aggregate_type="account",
        aggregate_id=str(account_id),
        event_type="DEPOSIT_CREATED",
        payload={"account_id": account_id, "amount": str(payload.amount), "reference_id": payload.reference_id},
    )
    log_action(db, current_user.id, "account.deposit", "SUCCESS")
    db.commit()

    return BalanceResponse(account_id=account_id, balance=get_account_balance(db, account_id))


@router.post("/{account_id}/withdraw", response_model=BalanceResponse)
def withdraw_endpoint(
    account_id: int,
    payload: FundingRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BalanceResponse:
    account = get_account_by_id(db, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    if current_user.role != UserRole.ADMIN and account.customer.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not allowed to withdraw from this account")

    current_balance: Decimal = get_account_balance(db, account_id)
    if current_balance < payload.amount:
        log_action(db, current_user.id, "account.withdraw", "FAILED")
        db.commit()
        raise HTTPException(status_code=400, detail="Insufficient funds")

    append_ledger_entry(db, account_id, LedgerEntryType.DEBIT, payload.amount, payload.reference_id)
    enqueue_event(
        db,
        aggregate_type="account",
        aggregate_id=str(account_id),
        event_type="WITHDRAWAL_CREATED",
        payload={"account_id": account_id, "amount": str(payload.amount), "reference_id": payload.reference_id},
    )
    log_action(db, current_user.id, "account.withdraw", "SUCCESS")
    db.commit()

    return BalanceResponse(account_id=account_id, balance=get_account_balance(db, account_id))
