import random
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.accounts.service import get_account_by_id
from app.audit.service import log_action
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.entities import Card, CardStatus, User, UserRole
from app.cards.schemas import CardCreateRequest, CardResponse, CardStatusUpdate

router = APIRouter(prefix="/cards", tags=["cards"])


def _generate_card_number() -> str:
    base = "4" + "".join(str(random.randint(0, 9)) for _ in range(14))
    return base + str(random.randint(0, 9))


def _generate_expiry() -> tuple[int, int]:
    now = datetime.utcnow()
    return now.month, now.year + 3


@router.post("", response_model=CardResponse, status_code=status.HTTP_201_CREATED)
def create_card(
    payload: CardCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CardResponse:
    account = get_account_by_id(db, payload.account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    if current_user.role != UserRole.ADMIN and account.customer.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not allowed to create card for this account")

    expiry_month, expiry_year = _generate_expiry()
    card = Card(
        account_id=payload.account_id,
        card_number=_generate_card_number(),
        expiry_month=expiry_month,
        expiry_year=expiry_year,
        status=CardStatus.ACTIVE,
    )
    db.add(card)
    db.commit()
    db.refresh(card)
    return card


@router.get("", response_model=list[CardResponse])
def list_cards(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[CardResponse]:
    query = db.query(Card)
    if current_user.role != UserRole.ADMIN:
        # only cards for user's accounts
        from app.accounts.service import list_accounts

        account_ids = [acc.id for acc in list_accounts(db) if acc.customer.user_id == current_user.id]
        query = query.filter(Card.account_id.in_(account_ids))
    return query.order_by(Card.created_at.desc()).all()


@router.post("/{card_id}/status", response_model=CardResponse)
def update_card_status(
    card_id: int,
    payload: CardStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CardResponse:
    card = db.get(Card, card_id)
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")

    account = get_account_by_id(db, card.account_id)
    if current_user.role != UserRole.ADMIN and account.customer.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not allowed to update this card")

    card.status = payload.status
    db.add(card)
    db.commit()
    db.refresh(card)
    return card


@router.delete("/{card_id}")
def delete_card(
    card_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    card = db.get(Card, card_id)
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")

    account = get_account_by_id(db, card.account_id)
    if current_user.role != UserRole.ADMIN and account.customer.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not allowed to delete this card")

    db.delete(card)
    log_action(db, current_user.id, "card.delete", "SUCCESS")
    db.commit()
    return {"status": "deleted", "card_id": card_id}
