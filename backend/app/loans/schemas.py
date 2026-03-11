from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.entities import LoanStatus


class LoanRequest(BaseModel):
    account_id: int
    amount: Decimal = Field(gt=0)
    currency: str = Field(min_length=3, max_length=3)
    purpose: str = Field(min_length=3, max_length=255)


class LoanResponse(BaseModel):
    id: int
    user_id: int
    account_id: int | None
    amount: Decimal
    currency: str
    purpose: str
    status: LoanStatus
    created_at: datetime
    updated_at: datetime
    approved_by: int | None

    class Config:
        from_attributes = True


class LoanStatusUpdate(BaseModel):
    status: LoanStatus
