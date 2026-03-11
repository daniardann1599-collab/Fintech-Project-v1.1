from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.entities import DepositStatus


class TimeDepositCreateRequest(BaseModel):
    account_id: int
    amount: Decimal = Field(gt=0)
    annual_rate: Decimal = Field(gt=0)
    duration_months: int = Field(gt=0)


class TimeDepositResponse(BaseModel):
    id: int
    account_id: int
    currency: str
    principal: Decimal
    annual_rate: Decimal
    duration_months: int
    expected_return: Decimal
    opened_at: datetime
    maturity_date: datetime
    status: DepositStatus
    matured: bool


class TimeDepositClaimResponse(BaseModel):
    id: int
    status: DepositStatus
    credited_amount: Decimal
    maturity_date: datetime
