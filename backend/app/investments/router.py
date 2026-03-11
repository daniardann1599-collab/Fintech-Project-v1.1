from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.investments.schemas import (
    InvestmentPositionResponse,
    InvestmentTradeRequest,
    InvestmentTransactionResponse,
    PortfolioResponse,
    PortfolioSummaryResponse,
)
from app.investments.service import buy_asset, list_positions, list_transactions, sell_asset
from app.market.service import get_asset_price
from app.models.entities import InvestmentTransaction, User

router = APIRouter(prefix="/investments", tags=["investments"])


@router.post("/buy", response_model=InvestmentTransactionResponse, status_code=status.HTTP_201_CREATED)
def buy_investment(
    payload: InvestmentTradeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> InvestmentTransactionResponse:
    try:
        transaction = buy_asset(db, current_user, payload)
        db.commit()
        db.refresh(transaction)
        return _transaction_to_response(db, transaction)
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except PermissionError as exc:
        db.rollback()
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@router.post("/sell", response_model=InvestmentTransactionResponse)
def sell_investment(
    payload: InvestmentTradeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> InvestmentTransactionResponse:
    try:
        transaction = sell_asset(db, current_user, payload)
        db.commit()
        db.refresh(transaction)
        return _transaction_to_response(db, transaction)
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except PermissionError as exc:
        db.rollback()
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@router.get("/portfolio", response_model=PortfolioResponse)
def get_portfolio(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PortfolioResponse:
    positions = list_positions(db, current_user)
    responses: list[InvestmentPositionResponse] = []
    summary_map: dict[str, dict[str, Decimal]] = {}

    for position in positions:
        asset = position.asset
        try:
            price, currency = get_asset_price(asset)
        except ValueError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc
        invested_amount = position.average_price * position.quantity
        current_value = price * position.quantity
        pnl = current_value - invested_amount
        pnl_pct = (pnl / invested_amount * Decimal("100")) if invested_amount else Decimal("0")

        responses.append(
            InvestmentPositionResponse(
                asset_id=asset.id,
                symbol=asset.symbol,
                name=asset.name,
                market=asset.market,
                asset_type=asset.asset_type,
                currency=currency,
                quantity=position.quantity,
                average_price=position.average_price,
                invested_amount=invested_amount,
                current_price=price,
                current_value=current_value,
                pnl_abs=pnl,
                pnl_pct=pnl_pct,
            )
        )

        if currency not in summary_map:
            summary_map[currency] = {
                "invested": Decimal("0"),
                "current": Decimal("0"),
            }
        summary_map[currency]["invested"] += invested_amount
        summary_map[currency]["current"] += current_value

    summaries = []
    for currency, totals in summary_map.items():
        invested = totals["invested"]
        current = totals["current"]
        pnl = current - invested
        pnl_pct = (pnl / invested * Decimal("100")) if invested else Decimal("0")
        summaries.append(
            PortfolioSummaryResponse(
                currency=currency,
                invested_total=invested,
                current_value=current,
                pnl_abs=pnl,
                pnl_pct=pnl_pct,
            )
        )

    return PortfolioResponse(positions=responses, summaries=summaries)


@router.get("/transactions", response_model=list[InvestmentTransactionResponse])
def get_investment_transactions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[InvestmentTransactionResponse]:
    transactions = list_transactions(db, current_user)
    return [_transaction_to_response(db, transaction) for transaction in transactions]


def _transaction_to_response(
    db: Session, transaction: InvestmentTransaction
) -> InvestmentTransactionResponse:
    asset = transaction.asset
    return InvestmentTransactionResponse(
        id=transaction.id,
        account_id=transaction.account_id,
        asset_id=asset.id,
        side=transaction.side,
        symbol=asset.symbol,
        market=asset.market,
        quantity=transaction.quantity,
        price=transaction.price,
        total=transaction.total,
        currency=asset.currency,
        created_at=transaction.created_at,
    )
