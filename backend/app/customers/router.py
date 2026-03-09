from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.audit.service import log_action
from app.core.database import get_db
from app.core.dependencies import get_current_user, require_admin
from app.customers.schemas import (
    CustomerCreateRequest,
    CustomerResponse,
    CustomerStatusUpdateRequest,
)
from app.customers.service import create_customer, get_customer_by_id, update_customer_status
from app.events.service import enqueue_event
from app.models.entities import User, UserRole

router = APIRouter(prefix="/customers", tags=["customers"])


@router.post("", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
def create_customer_endpoint(
    payload: CustomerCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CustomerResponse:
    if current_user.role != UserRole.ADMIN and current_user.id != payload.user_id:
        raise HTTPException(status_code=403, detail="Not allowed to create customer for another user")

    try:
        customer = create_customer(db, payload.user_id, payload.kyc_full_name, payload.kyc_document_id)
        enqueue_event(
            db,
            aggregate_type="customer",
            aggregate_id=str(customer.id),
            event_type="CUSTOMER_CREATED",
            payload={"customer_id": customer.id, "user_id": customer.user_id},
        )
        log_action(db, current_user.id, "customer.create", "SUCCESS")
        db.commit()
        db.refresh(customer)
        return customer
    except ValueError as exc:
        db.rollback()
        log_action(db, current_user.id, "customer.create", "FAILED")
        db.commit()
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/{customer_id}", response_model=CustomerResponse)
def get_customer_endpoint(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CustomerResponse:
    customer = get_customer_by_id(db, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    if current_user.role != UserRole.ADMIN and current_user.id != customer.user_id:
        raise HTTPException(status_code=403, detail="Not allowed to view this customer")
    return customer


@router.patch("/{customer_id}/status", response_model=CustomerResponse)
def update_customer_status_endpoint(
    customer_id: int,
    payload: CustomerStatusUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> CustomerResponse:
    customer = get_customer_by_id(db, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    customer = update_customer_status(db, customer, payload.status)
    enqueue_event(
        db,
        aggregate_type="customer",
        aggregate_id=str(customer.id),
        event_type="CUSTOMER_STATUS_UPDATED",
        payload={"customer_id": customer.id, "status": customer.status},
    )
    log_action(db, current_user.id, "customer.status_update", "SUCCESS")
    db.commit()
    db.refresh(customer)
    return customer
