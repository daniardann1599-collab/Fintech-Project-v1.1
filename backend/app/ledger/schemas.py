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


class LedgerVerificationResponse(BaseModel):
    account_id: int
    currency: str
    entries_count: int
    credits_total: Decimal
    debits_total: Decimal
    calculated_balance: Decimal
    is_valid: bool
    issues: list[str]


class SystemLedgerVerificationResponse(BaseModel):
    checked_accounts: int
    invalid_accounts: int
    results: list[LedgerVerificationResponse]
