from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.entities import AssetMarket, AssetType, InvestmentSide


class InvestmentTradeRequest(BaseModel):
    account_id: int = Field(gt=0)
    market: AssetMarket
    symbol: str = Field(min_length=1, max_length=32)
    quantity: Decimal = Field(gt=0)
    name: str | None = None


class InvestmentTransactionResponse(BaseModel):
    id: int
    account_id: int
    asset_id: int
    side: InvestmentSide
    symbol: str
    market: AssetMarket
    quantity: Decimal
    price: Decimal
    total: Decimal
    currency: str
    created_at: datetime

    class Config:
        from_attributes = True


class InvestmentPositionResponse(BaseModel):
    asset_id: int
    symbol: str
    name: str
    market: AssetMarket
    asset_type: AssetType
    currency: str
    quantity: Decimal
    average_price: Decimal
    invested_amount: Decimal
    current_price: Decimal
    current_value: Decimal
    pnl_abs: Decimal
    pnl_pct: Decimal


class PortfolioSummaryResponse(BaseModel):
    currency: str
    invested_total: Decimal
    current_value: Decimal
    pnl_abs: Decimal
    pnl_pct: Decimal


class PortfolioResponse(BaseModel):
    positions: list[InvestmentPositionResponse]
    summaries: list[PortfolioSummaryResponse]
