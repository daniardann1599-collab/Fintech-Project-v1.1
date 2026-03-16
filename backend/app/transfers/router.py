from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.audit.service import log_action
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.logging import get_logger
from app.events.service import enqueue_event
from app.pacs.manager import bank_ws_manager
from app.pacs.pacs008 import build_pacs008
from app.models.entities import Transfer, User, UserRole
from app.transfers.schemas import (
    TransferExecutionResponse,
    TransferInitiateRequest,
    TransferResponse,
)
from app.transfers.service import execute_transfer, initiate_transfer

router = APIRouter(prefix="/transfers", tags=["transfers"])
logger = get_logger("banking.transfers")


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

        try:
            from app.accounts.service import get_account_by_id

            from_account = get_account_by_id(db, transfer.from_account)
            to_account = get_account_by_id(db, transfer.to_account)
            if from_account and to_account:
                debtor_name = (
                    from_account.customer.kyc_full_name
                    if from_account.customer
                    else f"Customer {from_account.customer_id}"
                )
                creditor_name = (
                    to_account.customer.kyc_full_name
                    if to_account.customer
                    else f"Customer {to_account.customer_id}"
                )
                xml_payload, from_bank, to_bank = build_pacs008(
                    transfer,
                    from_account,
                    to_account,
                    debtor_name,
                    creditor_name,
                )
                bank_ws_manager.broadcast_sync(
                    from_bank,
                    {
                        "type": "pacs.008",
                        "direction": "OUTBOUND",
                        "bank_code": from_bank,
                        "transfer_id": transfer.id,
                        "xml": xml_payload,
                    },
                )
                bank_ws_manager.broadcast_sync(
                    to_bank,
                    {
                        "type": "pacs.008",
                        "direction": "INBOUND",
                        "bank_code": to_bank,
                        "transfer_id": transfer.id,
                        "xml": xml_payload,
                    },
                )
        except Exception as exc:  # pragma: no cover - do not block transfer
            logger.warning("pacs008.broadcast.failed", extra={"extra_fields": {"error": str(exc)}})
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
