from __future__ import annotations

import time
from decimal import Decimal
import httpx

from app.core.config import settings
from app.core.logging import get_logger
from app.models.entities import AssetMarket, InvestmentAsset

logger = get_logger("banking.market")

_price_cache: dict[str, tuple[float, Decimal, str]] = {}


def _cache_key(market: str, symbol: str) -> str:
    return f"{market}:{symbol.upper()}"


def _get_cached_price(market: str, symbol: str) -> tuple[Decimal, str] | None:
    key = _cache_key(market, symbol)
    cached = _price_cache.get(key)
    if not cached:
        return None
    ts, price, currency = cached
    if time.time() - ts > settings.market_price_cache_seconds:
        return None
    return price, currency


def _set_cached_price(market: str, symbol: str, price: Decimal, currency: str) -> None:
    key = _cache_key(market, symbol)
    _price_cache[key] = (time.time(), price, currency)


def _alpaca_headers() -> dict[str, str]:
    if not settings.alpaca_api_key or not settings.alpaca_api_secret:
        raise ValueError("Alpaca API credentials are not configured")
    return {
        "APCA-API-KEY-ID": settings.alpaca_api_key,
        "APCA-API-SECRET-KEY": settings.alpaca_api_secret,
    }


def fetch_stock_price(symbol: str, exchange: str | None = None) -> tuple[Decimal, str]:
    if exchange:
        raise ValueError("Alpaca does not support this exchange")

    cache_market = "STOCK:ALPACA"
    cached = _get_cached_price(cache_market, symbol)
    if cached:
        return cached

    url = f"https://data.alpaca.markets/v2/stocks/{symbol.upper()}/snapshot"
    with httpx.Client(timeout=10) as client:
        response = client.get(url, headers=_alpaca_headers())
        response.raise_for_status()
        payload = response.json()

    latest_trade = payload.get("latestTrade") or {}
    daily_bar = payload.get("dailyBar") or {}
    price_value = latest_trade.get("p") or daily_bar.get("c")
    if price_value is None:
        raise ValueError("Market price not available")

    price = Decimal(str(price_value))
    currency = "USD"

    _set_cached_price(cache_market, symbol, price, currency)
    logger.info(
        "market.stock_price",
        extra={"extra_fields": {"symbol": symbol, "price": str(price), "currency": currency}},
    )
    return price, currency


def get_asset_price(asset: InvestmentAsset) -> tuple[Decimal, str]:
    return fetch_stock_price(asset.symbol, asset.exchange)


def determine_exchange(market: AssetMarket) -> str | None:
    if market == AssetMarket.BIST:
        return "XIST"
    return None
