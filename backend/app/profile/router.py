from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.security import get_password_hash, verify_password
from app.models.entities import Customer, User
from app.profile.schemas import PasswordChangeRequest, ProfileResponse, ProfileUpdateRequest

router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("", response_model=ProfileResponse)
def get_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProfileResponse:
    customer = db.scalar(select(Customer).where(Customer.user_id == current_user.id))
    return _to_response(current_user, customer)


@router.put("", response_model=ProfileResponse)
def update_profile(
    payload: ProfileUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProfileResponse:
    if payload.email and payload.email != current_user.email:
        existing = db.scalar(select(User).where(User.email == payload.email))
        if existing:
            raise HTTPException(status_code=400, detail="Email already in use")
        current_user.email = payload.email

    customer = db.scalar(select(Customer).where(Customer.user_id == current_user.id))
    if customer:
        if payload.phone is not None:
            customer.phone = payload.phone
        if payload.address is not None:
            customer.address = payload.address
        if payload.city is not None:
            customer.city = payload.city
        if payload.country is not None:
            customer.country = payload.country
        db.add(customer)

    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    if customer:
        db.refresh(customer)

    return _to_response(current_user, customer)


@router.post("/password")
def change_password(
    payload: PasswordChangeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    if not verify_password(payload.current_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="Current password is incorrect")

    current_user.password_hash = get_password_hash(payload.new_password)
    db.add(current_user)
    db.commit()
    return {"status": "password_updated"}


def _to_response(user: User, customer: Customer | None) -> ProfileResponse:
    return ProfileResponse(
        user_id=user.id,
        customer_id=customer.id if customer else None,
        status=customer.status if customer else None,
        email=user.email,
        full_name=customer.kyc_full_name if customer else None,
        document_id=customer.kyc_document_id if customer else None,
        phone=customer.phone if customer else None,
        address=customer.address if customer else None,
        city=customer.city if customer else None,
        country=customer.country if customer else None,
    )
