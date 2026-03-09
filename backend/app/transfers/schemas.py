from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.entities import TransferStatus


class TransferInitiateRequest(BaseModel):
    from_account: int = Field(gt=0)
    to_account: int = Field(gt=0)
    amount: Decimal = Field(gt=0)


class TransferResponse(BaseModel):
    id: int
    from_account: int
    to_account: int
    amount: Decimal
    status: TransferStatus
    created_at: datetime

    class Config:
        from_attributes = True


class TransferExecutionResponse(BaseModel):
    transfer: TransferResponse
    from_account_balance: Decimal
    to_account_balance: Decimal
