from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.accounts.service import get_account_by_id
from app.core.logging import get_logger
from app.events.service import enqueue_event
from app.investments.schemas import InvestmentTradeRequest
from app.ledger.service import append_ledger_entry, get_account_balance
from app.market.service import determine_exchange, get_asset_price
from app.models.entities import (
    AssetMarket,
    AssetType,
    InvestmentAsset,
    InvestmentPosition,
    InvestmentSide,
    InvestmentTransaction,
    LedgerEntryType,
    User,
    UserRole,
)

logger = get_logger("banking.investments")


def _resolve_asset(db: Session, payload: InvestmentTradeRequest) -> InvestmentAsset:
    symbol = payload.symbol.upper()
    asset = db.scalar(
        select(InvestmentAsset).where(
            InvestmentAsset.symbol == symbol, InvestmentAsset.market == payload.market
        )
    )
    if asset:
        return asset

    asset_type = AssetType.STOCK
    name = payload.name or symbol
    exchange = determine_exchange(payload.market)

    asset = InvestmentAsset(
        symbol=symbol,
        name=name,
        asset_type=asset_type,
        market=payload.market,
        currency="USD" if payload.market != AssetMarket.BIST else "TRY",
        exchange=exchange,
    )
    db.add(asset)
    db.flush()
    return asset


def _resolve_account(db: Session, user: User, account_id: int, currency: str):
    account = get_account_by_id(db, account_id)
    if not account:
        raise ValueError("Account not found")
    if user.role != UserRole.ADMIN and account.customer.user_id != user.id:
        raise PermissionError("Not allowed to use this account")
    if account.currency != currency:
        raise ValueError(f"Account currency must be {currency}")
    return account


def buy_asset(db: Session, user: User, payload: InvestmentTradeRequest) -> InvestmentTransaction:
    asset = _resolve_asset(db, payload)
    price, currency = get_asset_price(asset)
    account = _resolve_account(db, user, payload.account_id, currency)

    total_cost = price * payload.quantity
    balance = get_account_balance(db, account.id)
    if balance < total_cost:
        raise ValueError("Insufficient funds for investment")

    transaction = InvestmentTransaction(
        user_id=user.id,
        account_id=account.id,
        asset_id=asset.id,
        side=InvestmentSide.BUY,
        quantity=payload.quantity,
        price=price,
        total=total_cost,
    )
    db.add(transaction)
    db.flush()

    append_ledger_entry(
        db,
        account.id,
        LedgerEntryType.DEBIT,
        total_cost,
        reference_id=f"investment:{transaction.id}:buy",
    )
    enqueue_event(
        db,
        aggregate_type="account",
        aggregate_id=str(account.id),
        event_type="AccountDebited",
        payload={
            "account_id": account.id,
            "amount": str(total_cost),
            "reference_id": f"investment:{transaction.id}:buy",
        },
    )

    position = db.scalar(
        select(InvestmentPosition).where(
            InvestmentPosition.user_id == user.id, InvestmentPosition.asset_id == asset.id
        )
    )
    if not position:
        position = InvestmentPosition(
            user_id=user.id,
            asset_id=asset.id,
            quantity=payload.quantity,
            average_price=price,
        )
        db.add(position)
    else:
        total_cost = position.average_price * position.quantity + price * payload.quantity
        total_qty = position.quantity + payload.quantity
        position.quantity = total_qty
        position.average_price = total_cost / total_qty
        db.add(position)

    asset.currency = currency
    db.add(asset)
    db.flush()

    logger.info(
        "investments.buy",
        extra={
            "extra_fields": {
                "user_id": user.id,
                "asset": asset.symbol,
                "market": asset.market,
                "quantity": str(payload.quantity),
                "price": str(price),
            }
        },
    )
    return transaction


def sell_asset(db: Session, user: User, payload: InvestmentTradeRequest) -> InvestmentTransaction:
    asset = _resolve_asset(db, payload)
    position = db.scalar(
        select(InvestmentPosition).where(
            InvestmentPosition.user_id == user.id, InvestmentPosition.asset_id == asset.id
        )
    )
    if not position or position.quantity < payload.quantity:
        raise ValueError("Not enough holdings to sell")

    price, currency = get_asset_price(asset)
    account = _resolve_account(db, user, payload.account_id, currency)

    transaction = InvestmentTransaction(
        user_id=user.id,
        account_id=account.id,
        asset_id=asset.id,
        side=InvestmentSide.SELL,
        quantity=payload.quantity,
        price=price,
        total=price * payload.quantity,
    )
    db.add(transaction)
    db.flush()

    proceeds = price * payload.quantity
    append_ledger_entry(
        db,
        account.id,
        LedgerEntryType.CREDIT,
        proceeds,
        reference_id=f"investment:{transaction.id}:sell",
    )
    enqueue_event(
        db,
        aggregate_type="account",
        aggregate_id=str(account.id),
        event_type="AccountCredited",
        payload={
            "account_id": account.id,
            "amount": str(proceeds),
            "reference_id": f"investment:{transaction.id}:sell",
        },
    )

    position.quantity -= payload.quantity
    if position.quantity <= 0:
        db.delete(position)
    else:
        db.add(position)

    asset.currency = currency
    db.add(asset)
    db.flush()

    logger.info(
        "investments.sell",
        extra={
            "extra_fields": {
                "user_id": user.id,
                "asset": asset.symbol,
                "market": asset.market,
                "quantity": str(payload.quantity),
                "price": str(price),
            }
        },
    )
    return transaction


def list_positions(db: Session, user: User) -> list[InvestmentPosition]:
    return list(db.scalars(select(InvestmentPosition).where(InvestmentPosition.user_id == user.id)))


def list_transactions(db: Session, user: User) -> list[InvestmentTransaction]:
    return list(
        db.scalars(
            select(InvestmentTransaction)
            .where(InvestmentTransaction.user_id == user.id)
            .order_by(InvestmentTransaction.created_at.desc())
        )
    )
