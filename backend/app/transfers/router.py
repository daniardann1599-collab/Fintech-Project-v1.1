from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.audit.service import log_action
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.events.service import enqueue_event
from app.models.entities import Transfer, User, UserRole
from app.transfers.schemas import (
    TransferExecutionResponse,
    TransferInitiateRequest,
    TransferResponse,
)
from app.transfers.service import execute_transfer, initiate_transfer

router = APIRouter(prefix="/transfers", tags=["transfers"])


@router.post("/initiate", response_model=TransferResponse, status_code=status.HTTP_201_CREATED)
def initiate_transfer_endpoint(
    payload: TransferInitiateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TransferResponse:
    try:
        transfer = initiate_transfer(
            db,
            payload.from_account,
            payload.to_account,
            payload.amount,
            current_user,
        )
        enqueue_event(
            db,
            aggregate_type="transfer",
            aggregate_id=str(transfer.id),
            event_type="TRANSFER_INITIATED",
            payload={
                "transfer_id": transfer.id,
                "from_account": transfer.from_account,
                "to_account": transfer.to_account,
                "amount": str(transfer.amount),
                "status": transfer.status,
            },
        )
        log_action(db, current_user.id, "transfer.initiate", "SUCCESS")
        db.commit()
        db.refresh(transfer)
        return transfer
    except LookupError as exc:
        db.rollback()
        log_action(db, current_user.id, "transfer.initiate", "FAILED")
        db.commit()
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except PermissionError as exc:
        db.rollback()
        log_action(db, current_user.id, "transfer.initiate", "FAILED")
        db.commit()
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        db.rollback()
        log_action(db, current_user.id, "transfer.initiate", "FAILED")
        db.commit()
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{transfer_id}/execute", response_model=TransferExecutionResponse)
def execute_transfer_endpoint(
    transfer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TransferExecutionResponse:
    try:
        transfer, from_balance, to_balance = execute_transfer(db, transfer_id, current_user)
        enqueue_event(
            db,
            aggregate_type="transfer",
            aggregate_id=str(transfer.id),
            event_type="TRANSFER_EXECUTED",
            payload={
                "transfer_id": transfer.id,
                "from_account": transfer.from_account,
                "to_account": transfer.to_account,
                "amount": str(transfer.amount),
                "status": transfer.status,
            },
        )
        log_action(db, current_user.id, "transfer.execute", "SUCCESS")
        db.commit()
        db.refresh(transfer)
        return TransferExecutionResponse(
            transfer=transfer,
            from_account_balance=from_balance,
            to_account_balance=to_balance,
        )
    except LookupError as exc:
        db.rollback()
        log_action(db, current_user.id, "transfer.execute", "FAILED")
        db.commit()
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except PermissionError as exc:
        db.rollback()
        log_action(db, current_user.id, "transfer.execute", "FAILED")
        db.commit()
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        db.rollback()
        log_action(db, current_user.id, "transfer.execute", "FAILED")
        db.commit()
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("", response_model=list[TransferResponse])
def list_transfers_endpoint(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[TransferResponse]:
    transfers = list(db.scalars(select(Transfer).order_by(Transfer.id.desc())))
    if current_user.role == UserRole.ADMIN:
        return transfers

    # For customers, return transfers where user owns from_account via subquery in Python for simplicity.
    from app.accounts.service import get_account_by_id

    visible: list[Transfer] = []
    for transfer in transfers:
        account = get_account_by_id(db, transfer.from_account)
        if account and account.customer.user_id == current_user.id:
            visible.append(transfer)
    return visible


@router.get("/{transfer_id}", response_model=TransferResponse)
def get_transfer_endpoint(
    transfer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TransferResponse:
    transfer = db.get(Transfer, transfer_id)
    if not transfer:
        raise HTTPException(status_code=404, detail="Transfer not found")

    if current_user.role != UserRole.ADMIN:
        from app.accounts.service import get_account_by_id

        account = get_account_by_id(db, transfer.from_account)
        if not account or account.customer.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not allowed to view this transfer")

    return transfer
