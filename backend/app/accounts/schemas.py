from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator


class AccountCreateRequest(BaseModel):
    customer_id: int = Field(gt=0)
    currency: str = Field(min_length=3, max_length=3)

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        normalized = value.upper()
        if not normalized.isalpha() or len(normalized) != 3:
            raise ValueError("currency must be a 3-letter ISO code")
        return normalized


class AccountResponse(BaseModel):
    id: int
    customer_id: int
    currency: str
    iban: str
    created_at: datetime

    class Config:
        from_attributes = True


class FundingRequest(BaseModel):
    amount: Decimal = Field(gt=0)
    reference_id: str = Field(min_length=3, max_length=100)


class BalanceResponse(BaseModel):
    account_id: int
    balance: Decimal
