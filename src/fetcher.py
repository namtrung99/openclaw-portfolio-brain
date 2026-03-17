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


async def _get_safe(client: httpx.AsyncClient, base: str, path: str,
                    params: Dict = None, signed: bool = False, fallback: Any = None) -> Any:
    """Same as _get but returns fallback instead of raising on error."""
    try:
        return await _get(client, base, path, params=params, signed=signed)
    except httpx.HTTPStatusError as e:
        # Silently skip 400 (invalid symbol) — very common for Alpha coins
        if e.response.status_code != 400:
            print(f"[WARN] {path} {e.response.status_code}: {e}")
        return fallback
    except Exception as e:
        print(f"[WARN] {path} failed: {e}")
        return fallback


async def fetch_all_real() -> Dict[str, Any]:
    """
    Fetch all portfolio data from Binance APIs in parallel.
    Each endpoint is fetched safely — failures return empty fallback instead of crashing.
    """
    async with httpx.AsyncClient(timeout=20.0) as client:
        (
            spot_account,
            spot_prices,
            futures_account,
            futures_positions,
            mark_prices,
            earn_flex_p1,
            earn_locked,
            exchange_info,
        ) = await asyncio.gather(
            _get_safe(client, SPOT_BASE_URL,    "/api/v3/account",
                      signed=True, params={"omitZeroBalances": "true"},
                      fallback={"balances": []}),
            _get_safe(client, SPOT_BASE_URL,    "/api/v3/ticker/price",
                      fallback=[]),
            _get_safe(client, FUTURES_BASE_URL, "/fapi/v3/account",
                      signed=True,
                      fallback={"totalWalletBalance": "0", "totalUnrealizedProfit": "0",
                                "availableBalance": "0", "totalMaintMargin": "0"}),
            _get_safe(client, FUTURES_BASE_URL, "/fapi/v3/positionRisk",
                      signed=True, fallback=[]),
            _get_safe(client, FUTURES_BASE_URL, "/fapi/v1/premiumIndex",
                      fallback=[]),
            _get_safe(client, SPOT_BASE_URL,    "/sapi/v1/simple-earn/flexible/position",
                      signed=True, params={"size": 200}, fallback={"rows": [], "total": 0}),
            _get_safe(client, SPOT_BASE_URL,    "/sapi/v1/simple-earn/locked/position",
                      signed=True, params={"size": 200}, fallback={"rows": []}),
            _get_safe(client, SPOT_BASE_URL,    "/api/v3/exchangeInfo",
                      params={"permissions": "SPOT"}, fallback={"symbols": []}),
        )

        # If earn_flex has more pages, fetch them
        earn_rows = list((earn_flex_p1 or {}).get("rows", []))
        total_earn = int((earn_flex_p1 or {}).get("total", len(earn_rows)))
        page = 1
        while len(earn_rows) < total_earn:
            more = await _get_safe(
                client, SPOT_BASE_URL, "/sapi/v1/simple-earn/flexible/position",
                signed=True, params={"size": 200, "current": page + 1},
                fallback={"rows": []}
            )
            new_rows = (more or {}).get("rows", [])
            if not new_rows:
                break
            earn_rows.extend(new_rows)
            page += 1

    # ── Normalise spot prices → {ASSET: float} ────────────────────────────────────
    prices: Dict[str, float] = {}
    if isinstance(spot_prices, list):
        for item in spot_prices:
            sym = item.get("symbol", "")
            if sym.endswith("USDT"):
                try:
                    prices[sym[:-4]] = float(item["price"])
                except (ValueError, KeyError):
                    pass
    prices.update({"USDT": 1.0, "USDC": 1.0, "BUSD": 1.0, "FDUSD": 1.0, "DAI": 1.0, "TUSD": 1.0})

    # ── Normalise mark prices → {SYMBOL: str} ─────────────────────────────────
    mark_dict: Dict[str, str] = {}
    if isinstance(mark_prices, list):
        for m in mark_prices:
            mark_dict[m["symbol"]] = m.get("markPrice", "0")
    elif isinstance(mark_prices, dict) and "symbol" in mark_prices:
        mark_dict[mark_prices["symbol"]] = mark_prices.get("markPrice", "0")

    # ── Filter open futures positions only ────────────────────────────────────
    open_positions = []
    if isinstance(futures_positions, list):
        for p in futures_positions:
            try:
                if float(p.get("positionAmt", 0)) != 0:
                    open_positions.append(p)
            except (ValueError, TypeError):
                pass

    # ── Separate LD* (earn) from real spot balances ───────────────────────────
    # Binance represents Flexible Earn as LD<ASSET> in spot account.
    # We strip LD prefix and put them into earn_from_spot dict.
    clean_balances = []
    earn_from_ld: Dict[str, float] = {}
    locked_spot: Dict[str, float] = {}

    for b in (spot_account or {}).get("balances", []):
        asset = b["asset"]
        free   = float(b.get("free",   0))
        locked = float(b.get("locked", 0))

        if asset.startswith("LD"):
            # Strip LD prefix → underlying asset
            underlying = asset[2:]
            earn_from_ld[underlying] = earn_from_ld.get(underlying, 0) + free + locked
        else:
            total_qty = free + locked
            if total_qty > 0:
                clean_balances.append({"asset": asset, "free": str(free), "locked": str(locked)})
            if locked > 0:
                locked_spot[asset] = locked_spot.get(asset, 0) + locked

    # Merge earn_rows (from API) with earn_from_ld (from LD* spot)
    # Use earn_rows as primary (more accurate), supplement with LD* for missing assets
    earn_api_assets = {r["asset"] for r in earn_rows}
    for asset, qty in earn_from_ld.items():
        if asset not in earn_api_assets:
            earn_rows.append({"asset": asset, "totalAmount": str(qty),
                              "latestAnnualPercentageRate": "0", "canRedeem": True})

    earn_flexible_clean = {"rows": earn_rows}
    if not isinstance(earn_locked, dict):
        earn_locked = {"rows": []}

    spot_account_clean = {**spot_account, "balances": clean_balances}

    # ── Build set of Binance spot-listed base assets ─────────────────────────
    spot_listed: set = set()
    if isinstance(exchange_info, dict):
        for s in exchange_info.get("symbols", []):
            if s.get("quoteAsset") == "USDT" and s.get("status") == "TRADING":
                spot_listed.add(s["baseAsset"])

    return {
        "spot_account":      spot_account_clean,
        "spot_prices":       prices,
        "futures_account":   futures_account,
        "futures_positions": open_positions,
        "mark_prices":       mark_dict,
        "earn_flexible":     earn_flexible_clean,
        "earn_locked":       earn_locked,
        "locked_spot":       locked_spot,
        "spot_listed":       spot_listed,     # set of assets trading on Binance spot USDT
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
        "locked_spot":       {},
        "spot_listed":       set(),   # empty in mock — no live exchange info
    }


async def fetch_cost_basis_real(
    assets: list,
    prices: Dict[str, float],
    start_ts: int = None,
    end_ts:   int = None,
) -> Dict[str, Any]:
    """
    Fetch /api/v3/myTrades for a broad set of assets (current holdings +
    Alpha coins + common alts that may have been fully sold).
    Supports optional time range (start_ts / end_ts in ms).
    Returns per-asset data + '__summary__' with all-time totals.
    """
    from src.config import STABLE_COINS
    from src.mock_data import BINANCE_ALPHA_COINS

    # Expand: current holdings + Alpha list + common alts (catch fully-sold)
    COMMON_ALTS = {
        "SOL", "XRP", "ADA", "DOT", "AVAX", "ATOM", "LTC", "BCH",
        "NEAR", "APT", "SUI", "OP", "ARB", "INJ", "TIA", "SEI",
        "JUP", "PENDLE", "WLD", "STRK", "FIL", "SAND", "MANA",
        "DOGE", "SHIB", "PEPE", "FLOKI", "BONK", "WIF",
        "ONDO", "PYTH", "JTO", "TNSR", "ETHFI", "ARKM",
        "RENDER", "FET", "AGIX", "OCEAN", "GRT",
    }
    all_assets_to_scan = (set(assets) | BINANCE_ALPHA_COINS | COMMON_ALTS) - STABLE_COINS
    trade_assets = sorted(all_assets_to_scan)

    QUOTE_PRIORITY = ["USDT"]
    BATCH_SIZE = 10

    async def fetch_best_trades(client: httpx.AsyncClient, asset: str) -> list:
        for quote in QUOTE_PRIORITY:
            params: Dict[str, Any] = {"symbol": f"{asset}{quote}", "limit": 1000}
            if start_ts: params["startTime"] = start_ts
            if end_ts:   params["endTime"]   = end_ts
            trades = await _get_safe(
                client, SPOT_BASE_URL, "/api/v3/myTrades",
                signed=True, params=params, fallback=[]
            )
            if isinstance(trades, list) and trades:
                return trades
        return []

    all_results: Dict[str, list] = {}
    async with httpx.AsyncClient(timeout=30.0) as client:
        for i in range(0, len(trade_assets), BATCH_SIZE):
            batch = trade_assets[i : i + BATCH_SIZE]
            batch_results = await asyncio.gather(*[
                fetch_best_trades(client, asset) for asset in batch
            ])
            for asset, trades in zip(batch, batch_results):
                all_results[asset] = trades
            if i + BATCH_SIZE < len(trade_assets):
                await asyncio.sleep(0.15)

    cost_basis: Dict[str, Any] = {}
    summary_spent    = 0.0
    summary_received = 0.0

    for asset, trades in all_results.items():
        if not isinstance(trades, list) or not trades:
            continue
        total_buy_qty      = 0.0
        total_buy_cost     = 0.0
        total_sell_qty     = 0.0
        total_sell_revenue = 0.0

        for t in trades:
            qty        = float(t.get("qty", 0))
            quote_qty  = float(t.get("quoteQty", 0))
            commission = float(t.get("commission", 0))
            comm_asset = t.get("commissionAsset", "")
            comm_usdt  = commission if comm_asset == "USDT" else commission * prices.get(comm_asset, 0)
            if t.get("isBuyer", False):
                total_buy_qty  += qty
                total_buy_cost += quote_qty + comm_usdt
            else:
                total_sell_qty     += qty
                total_sell_revenue += quote_qty - comm_usdt

        summary_spent    += total_buy_cost
        summary_received += total_sell_revenue

        net_qty  = total_buy_qty - total_sell_qty
        avg_cost = total_buy_cost / total_buy_qty if total_buy_qty > 0 else 0.0
        remaining_cost = max(net_qty, 0) * avg_cost
        cost_of_sold   = total_sell_qty * avg_cost
        realized       = total_sell_revenue - cost_of_sold
        current_value  = max(net_qty, 0) * prices.get(asset, 0)
        unrealized     = current_value - remaining_cost

        cost_basis[asset] = {
            "avg_cost":       avg_cost,
            "total_invested": remaining_cost,
            "realized_pnl":   realized,
            "unrealized_pnl": unrealized,
            "trades":         trades,
            "fully_sold":     net_qty <= 0,   # position fully closed
        }

    # Global summary across ALL scanned assets
    _summary_realized   = sum(v["realized_pnl"]   for v in cost_basis.values())
    _summary_unrealized = sum(v["unrealized_pnl"]  for v in cost_basis.values())
    _summary_invested   = sum(v["total_invested"]   for v in cost_basis.values() if not v["fully_sold"])
    cost_basis["__summary__"] = {
        "total_spent":    summary_spent,
        "total_received": summary_received,
        # Net P&L = realized (from completed sells) + unrealized (current holdings vs cost)
        # Do NOT use (received - spent) as that double-counts unrealized
        "net_pnl":        _summary_realized + _summary_unrealized,
        "realized_pnl":   _summary_realized,
        "unrealized_pnl": _summary_unrealized,
        "total_invested": _summary_invested,
    }
    return cost_basis


def fetch_cost_basis(
    assets: list,
    prices: Dict[str, float],
    use_mock: bool = None,
    start_ts: int = None,
    end_ts:   int = None,
) -> Dict[str, Any]:
    """Wrapper: fetch real cost basis or return empty dict for mock mode."""
    should_mock = use_mock if use_mock is not None else (USE_MOCK_DATA or not BINANCE_API_KEY)
    if should_mock:
        return {}
    return asyncio.run(fetch_cost_basis_real(assets, prices, start_ts=start_ts, end_ts=end_ts))


def fetch_portfolio(use_mock: bool = None) -> Dict[str, Any]:
    """
    Main entry point. Use mock if USE_MOCK_DATA=true or no API keys set.
    """
    should_mock = use_mock if use_mock is not None else (USE_MOCK_DATA or not BINANCE_API_KEY)
    if should_mock:
        return fetch_all_mock()
    return asyncio.run(fetch_all_real())
