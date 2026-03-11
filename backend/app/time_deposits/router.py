from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.time_deposits.schemas import (
    TimeDepositClaimResponse,
    TimeDepositCreateRequest,
    TimeDepositResponse,
)
from app.time_deposits.service import claim_time_deposit, open_time_deposit
from app.models.entities import DepositStatus, TimeDeposit, User

router = APIRouter(prefix="/time-deposits", tags=["time-deposits"])


@router.post("", response_model=TimeDepositResponse, status_code=status.HTTP_201_CREATED)
def create_time_deposit(
    payload: TimeDepositCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TimeDepositResponse:
    try:
        deposit = open_time_deposit(
            db,
            current_user,
            payload.account_id,
            payload.amount,
            payload.annual_rate,
            payload.duration_months,
        )
        db.commit()
        db.refresh(deposit)
        return _deposit_to_response(deposit)
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except PermissionError as exc:
        db.rollback()
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@router.get("", response_model=list[TimeDepositResponse])
def list_time_deposits(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[TimeDepositResponse]:
    deposits = (
        db.query(TimeDeposit)
        .filter(TimeDeposit.user_id == current_user.id)
        .order_by(TimeDeposit.opened_at.desc())
        .all()
    )
    return [_deposit_to_response(dep) for dep in deposits]


@router.post("/{deposit_id}/claim", response_model=TimeDepositClaimResponse)
def claim_deposit(
    deposit_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TimeDepositClaimResponse:
    try:
        deposit, credited_amount = claim_time_deposit(db, current_user, deposit_id)
        db.commit()
        db.refresh(deposit)
        return TimeDepositClaimResponse(
            id=deposit.id,
            status=deposit.status,
            credited_amount=credited_amount,
            maturity_date=deposit.maturity_date,
        )
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except PermissionError as exc:
        db.rollback()
        raise HTTPException(status_code=403, detail=str(exc)) from exc


def _deposit_to_response(deposit: TimeDeposit) -> TimeDepositResponse:
    now = datetime.now(timezone.utc)
    matured = now >= deposit.maturity_date
    if matured and deposit.status == DepositStatus.ACTIVE:
        status = DepositStatus.MATURED
    else:
        status = deposit.status

    return TimeDepositResponse(
        id=deposit.id,
        account_id=deposit.account_id,
        currency=deposit.currency,
        principal=deposit.principal,
        annual_rate=deposit.annual_rate,
        duration_months=deposit.duration_months,
        expected_return=deposit.expected_return,
        opened_at=deposit.opened_at,
        maturity_date=deposit.maturity_date,
        status=status,
        matured=matured,
    )
