"""
fetcher.py — Async fetcher for Binance API (Spot, Futures, Simple Earn, Prices).
Falls back to mock data when USE_MOCK_DATA=true or API keys not configured.
"""
import asyncio
import hashlib
import hmac
import time
from typing import Any, Dict

import httpx

from src.config import (
    BINANCE_API_KEY,
    BINANCE_SECRET_KEY,
    FUTURES_BASE_URL,
    SPOT_BASE_URL,
    USER_AGENT,
    USE_MOCK_DATA,
)
from src.mock_data import (
    MOCK_EARN_FLEXIBLE,
    MOCK_EARN_LOCKED,
    MOCK_FUTURES_ACCOUNT,
    MOCK_FUTURES_POSITIONS,
    MOCK_MARK_PRICES,
    MOCK_SPOT_ACCOUNT,
    MOCK_SPOT_PRICES,
)


def _sign(params: Dict[str, Any], secret: str) -> Dict[str, Any]:
    """Sign request params with HMAC-SHA256."""
    params["timestamp"] = int(time.time() * 1000)
    query = "&".join(f"{k}={v}" for k, v in params.items())
    sig = hmac.new(secret.encode(), query.encode(), hashlib.sha256).hexdigest()
    params["signature"] = sig
    return params


def _headers() -> Dict[str, str]:
    return {
        "X-MBX-APIKEY": BINANCE_API_KEY,
        "User-Agent": USER_AGENT,
    }


async def _get(client: httpx.AsyncClient, base: str, path: str, params: Dict = None, signed: bool = False) -> Any:
    """Generic async GET with optional signing."""
    p = dict(params or {})
    if signed:
        p = _sign(p, BINANCE_SECRET_KEY)
    resp = await client.get(f"{base}{path}", params=p, headers=_headers())
    resp.raise_for_status()
    return resp.json()


async def fetch_all_real() -> Dict[str, Any]:
    """
    Fetch all portfolio data from Binance APIs in parallel.
    Requires BINANCE_API_KEY and BINANCE_SECRET_KEY.
    """
    async with httpx.AsyncClient(timeout=15.0) as client:
        (
            spot_account,
            spot_prices,
            futures_account,
            futures_positions,
            mark_prices,
            earn_flexible,
            earn_locked,
        ) = await asyncio.gather(
            _get(client, SPOT_BASE_URL,    "/api/v3/account",                              signed=True, params={"omitZeroBalances": "true"}),
            _get(client, SPOT_BASE_URL,    "/api/v3/ticker/price"),
            _get(client, FUTURES_BASE_URL, "/fapi/v3/account",                             signed=True),
            _get(client, FUTURES_BASE_URL, "/fapi/v3/positionRisk",                        signed=True),
            _get(client, FUTURES_BASE_URL, "/fapi/v1/premiumIndex"),
            _get(client, SPOT_BASE_URL,    "/sapi/v1/simple-earn/flexible/position",       signed=True),
            _get(client, SPOT_BASE_URL,    "/sapi/v1/simple-earn/locked/position",         signed=True),
        )

    # Normalise prices to dict {SYMBOL: float}
    prices: Dict[str, float] = {}
    for item in spot_prices:
        sym = item["symbol"]
        if sym.endswith("USDT"):
            prices[sym[:-4]] = float(item["price"])
    prices.update({"USDT": 1.0, "USDC": 1.0, "BUSD": 1.0, "FDUSD": 1.0})

    mark_dict: Dict[str, str] = {}
    if isinstance(mark_prices, list):
        for m in mark_prices:
            mark_dict[m["symbol"]] = m["markPrice"]
    else:
        mark_dict[mark_prices["symbol"]] = mark_prices["markPrice"]

    return {
        "spot_account":      spot_account,
        "spot_prices":       prices,
        "futures_account":   futures_account,
        "futures_positions": [p for p in futures_positions if float(p["positionAmt"]) != 0],
        "mark_prices":       mark_dict,
        "earn_flexible":     earn_flexible,
        "earn_locked":       earn_locked,
    }


def fetch_all_mock() -> Dict[str, Any]:
    """Return realistic mock data (no API key required)."""
    return {
        "spot_account":      MOCK_SPOT_ACCOUNT,
        "spot_prices":       MOCK_SPOT_PRICES,
        "futures_account":   MOCK_FUTURES_ACCOUNT,
        "futures_positions": MOCK_FUTURES_POSITIONS,
        "mark_prices":       MOCK_MARK_PRICES,
        "earn_flexible":     MOCK_EARN_FLEXIBLE,
        "earn_locked":       MOCK_EARN_LOCKED,
    }


def fetch_portfolio(use_mock: bool = None) -> Dict[str, Any]:
    """
    Main entry point. Use mock if USE_MOCK_DATA=true or no API keys set.
    """
    should_mock = use_mock if use_mock is not None else (USE_MOCK_DATA or not BINANCE_API_KEY)
    if should_mock:
        return fetch_all_mock()
    return asyncio.run(fetch_all_real())
