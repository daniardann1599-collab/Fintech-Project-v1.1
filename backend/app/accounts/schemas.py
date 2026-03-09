from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class AccountCreateRequest(BaseModel):
    customer_id: int
    currency: str = Field(min_length=3, max_length=3)


class AccountResponse(BaseModel):
    id: int
    customer_id: int
    currency: str
    created_at: datetime

    class Config:
        from_attributes = True


class FundingRequest(BaseModel):
    amount: Decimal = Field(gt=0)
    reference_id: str = Field(min_length=3, max_length=100)


class BalanceResponse(BaseModel):
    account_id: int
    balance: Decimal
