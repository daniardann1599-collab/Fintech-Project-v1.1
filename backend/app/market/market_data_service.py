from __future__ import annotations

import time
from decimal import Decimal

import httpx

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger("banking.market_data")

SP500_SYMBOLS: list[dict[str, str]] = [
    {"symbol": "AAPL", "name": "Apple Inc"},
    {"symbol": "MSFT", "name": "Microsoft"},
    {"symbol": "AMZN", "name": "Amazon"},
    {"symbol": "GOOGL", "name": "Alphabet"},
    {"symbol": "META", "name": "Meta Platforms"},
    {"symbol": "TSLA", "name": "Tesla"},
    {"symbol": "NVDA", "name": "NVIDIA"},
    {"symbol": "JPM", "name": "JPMorgan Chase"},
    {"symbol": "V", "name": "Visa"},
]

BIST100_SYMBOLS: list[dict[str, str]] = [
    {"symbol": "THYAO", "name": "Turkish Airlines"},
    {"symbol": "GARAN", "name": "Garanti BBVA"},
    {"symbol": "AKBNK", "name": "Akbank"},
    {"symbol": "KCHOL", "name": "Koc Holding"},
    {"symbol": "EREGL", "name": "Eregli Demir Celik"},
    {"symbol": "ASELS", "name": "Aselsan"},
    {"symbol": "BIMAS", "name": "BIM"},
    {"symbol": "TUPRS", "name": "Tupras"},
    {"symbol": "SISE", "name": "Sise"},
]

_snapshot_cache: dict[str, tuple[float, dict]] = {}


def _cache_key(market: str, symbol: str) -> str:
    return f"{market}:{symbol.upper()}"


def _get_cached_snapshot(market: str, symbol: str) -> dict | None:
    key = _cache_key(market, symbol)
    cached = _snapshot_cache.get(key)
    if not cached:
        return None
    ts, payload = cached
    if time.time() - ts > settings.market_table_cache_seconds:
        return None
    return payload


def _set_cached_snapshot(market: str, symbol: str, payload: dict) -> None:
    key = _cache_key(market, symbol)
    _snapshot_cache[key] = (time.time(), payload)


def _fetch_snapshot(symbol: str, name: str, exchange: str | None, market: str) -> dict:
    cached = _get_cached_snapshot(market, symbol)
    if cached:
        return cached

    if not settings.twelvedata_api_key:
        raise ValueError("Twelve Data API key is not configured")

    params = {
        "symbol": symbol.upper(),
        "interval": "1min",
        "outputsize": 2,
        "apikey": settings.twelvedata_api_key,
    }
    if exchange:
        params["exchange"] = exchange

    url = "https://api.twelvedata.com/time_series"
    with httpx.Client(timeout=10) as client:
        response = client.get(url, params=params)
        response.raise_for_status()
        payload = response.json()

    values = payload.get("values") or []
    if not values:
        raise ValueError(f"Market price not available for {symbol}")

    price = Decimal(values[0]["close"])
    previous = Decimal(values[1]["close"]) if len(values) > 1 else Decimal("0")
    change_percent = (
        (price - previous) / previous * Decimal("100") if previous else Decimal("0")
    )

    snapshot = {
        "symbol": symbol.upper(),
        "name": name,
        "price": float(price),
        "change_percent": float(change_percent),
    }
    _set_cached_snapshot(market, symbol, snapshot)

    logger.info(
        "market.snapshot",
        extra={
            "extra_fields": {
                "symbol": symbol,
                "market": market,
                "price": str(price),
                "change_percent": str(change_percent),
            }
        },
    )
    return snapshot


def get_sp500_snapshots() -> list[dict]:
    snapshots: list[dict] = []
    for item in SP500_SYMBOLS:
        snapshots.append(_fetch_snapshot(item["symbol"], item["name"], None, "SP500"))
    return snapshots


def get_bist100_snapshots() -> list[dict]:
    snapshots: list[dict] = []
    for item in BIST100_SYMBOLS:
        snapshots.append(_fetch_snapshot(item["symbol"], item["name"], "XIST", "BIST100"))
    return snapshots
