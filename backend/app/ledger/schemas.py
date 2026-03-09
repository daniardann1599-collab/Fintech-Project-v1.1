from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel

from app.models.entities import LedgerEntryType


class LedgerEntryResponse(BaseModel):
    id: int
    account_id: int
    type: LedgerEntryType
    amount: Decimal
    reference_id: str
    created_at: datetime

    class Config:
        from_attributes = True


class AccountBalanceResponse(BaseModel):
    account_id: int
    balance: Decimal
