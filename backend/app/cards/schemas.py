from datetime import datetime

from pydantic import BaseModel

from app.models.entities import CardStatus


class CardCreateRequest(BaseModel):
    account_id: int


class CardResponse(BaseModel):
    id: int
    account_id: int
    card_number: str
    expiry_month: int
    expiry_year: int
    status: CardStatus
    created_at: datetime

    class Config:
        from_attributes = True


class CardStatusUpdate(BaseModel):
    status: CardStatus
