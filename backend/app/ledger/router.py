from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.accounts.service import get_account_by_id
from app.core.database import get_db
from app.core.dependencies import get_current_user, require_admin
from app.ledger.schemas import (
    LedgerEntryResponse,
    LedgerVerificationResponse,
    SystemLedgerVerificationResponse,
)
from app.ledger.service import list_account_entries, verify_account_ledger, verify_system_ledger
from app.models.entities import User, UserRole

router = APIRouter(prefix="/ledger", tags=["ledger"])


@router.get("/accounts/{account_id}/entries", response_model=list[LedgerEntryResponse])
def get_account_ledger_entries(
    account_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[LedgerEntryResponse]:
    account = get_account_by_id(db, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    if current_user.role != UserRole.ADMIN and account.customer.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not allowed to view this account ledger")

    return list_account_entries(db, account_id)


@router.get("/accounts/{account_id}/verify", response_model=LedgerVerificationResponse)
def verify_account_ledger_endpoint(
    account_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> LedgerVerificationResponse:
    account = get_account_by_id(db, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    if current_user.role != UserRole.ADMIN and account.customer.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not allowed to verify this account ledger")
    return LedgerVerificationResponse(**verify_account_ledger(db, account))


@router.get("/verify/system", response_model=SystemLedgerVerificationResponse)
def verify_system_ledger_endpoint(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> SystemLedgerVerificationResponse:
    return SystemLedgerVerificationResponse(**verify_system_ledger(db))
