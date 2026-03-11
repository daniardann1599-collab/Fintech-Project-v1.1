from __future__ import annotations

import time
from decimal import Decimal
from typing import Any

import httpx

from app.core.config import settings
from app.core.logging import get_logger
from app.models.entities import AssetMarket, AssetType, InvestmentAsset

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


def fetch_stock_price(symbol: str, exchange: str | None = None) -> tuple[Decimal, str]:
    cache_market = f"STOCK:{exchange or 'GLOBAL'}"
    cached = _get_cached_price(cache_market, symbol)
    if cached:
        return cached

    if not settings.twelvedata_api_key:
        raise ValueError("Twelve Data API key is not configured")

    params: dict[str, Any] = {
        "symbol": symbol.upper(),
        "interval": "1min",
        "outputsize": 1,
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
        raise ValueError("Market price not available")

    price = Decimal(values[0]["close"])
    currency = payload.get("meta", {}).get("currency", "USD")

    _set_cached_price(cache_market, symbol, price, currency)
    logger.info(
        "market.stock_price",
        extra={"extra_fields": {"symbol": symbol, "price": str(price), "currency": currency}},
    )
    return price, currency


def fetch_metal_price(metal_code: str) -> tuple[Decimal, str]:
    cached = _get_cached_price("METAL", metal_code)
    if cached:
        return cached

    if not settings.metals_api_key:
        raise ValueError("Metals API key is not configured")

    url = "https://api.metals.dev/v1/latest"
    params = {
        "api_key": settings.metals_api_key,
        "currency": "USD",
        "unit": "toz",
    }

    with httpx.Client(timeout=10) as client:
        response = client.get(url, params=params)
        response.raise_for_status()
        payload = response.json()

    rates = payload.get("metals") or payload.get("rates") or {}
    rate = rates.get(metal_code.upper())
    if rate is None:
        raise ValueError("Metal price not available")

    price = Decimal(rate)
    currency = payload.get("currency", "USD")

    _set_cached_price("METAL", metal_code, price, currency)
    logger.info(
        "market.metal_price",
        extra={"extra_fields": {"metal": metal_code, "price": str(price), "currency": currency}},
    )
    return price, currency


def get_asset_price(asset: InvestmentAsset) -> tuple[Decimal, str]:
    if asset.asset_type == AssetType.METAL:
        return fetch_metal_price(asset.metal_code or asset.symbol)
    return fetch_stock_price(asset.symbol, asset.exchange)


def determine_exchange(market: AssetMarket) -> str | None:
    if market == AssetMarket.BIST:
        return "XIST"
    return None
