"""
aggregator.py — Aggregate raw Binance data into a unified portfolio snapshot.

Computes:
  - Total equity (USDT-denominated)
  - Per-asset holdings: spot_qty, earn_qty, futures_net_qty
  - Net exposure per coin (spot + futures long - futures short)
  - Allocation % of total equity
  - Risk flags: concentration, stable%, margin health, high leverage
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from src.config import STABLE_COINS, PortfolioPolicy


@dataclass
class AssetPosition:
    asset:          str
    spot_qty:       float = 0.0
    earn_qty:       float = 0.0       # flexible + locked Earn
    futures_long:   float = 0.0       # positionAmt > 0
    futures_short:  float = 0.0       # abs(positionAmt) where positionAmt < 0
    price_usdt:     float = 0.0       # spot price
    mark_price:     float = 0.0       # futures mark price (fallback: spot price)

    @property
    def net_qty(self) -> float:
        """Net quantity: spot + earn + futures_long - futures_short."""
        return self.spot_qty + self.earn_qty + self.futures_long - self.futures_short

    @property
    def spot_value(self) -> float:
        return self.spot_qty * self.price_usdt

    @property
    def earn_value(self) -> float:
        return self.earn_qty * self.price_usdt

    @property
    def futures_notional(self) -> float:
        return (self.futures_long + self.futures_short) * self.mark_price

    @property
    def net_value(self) -> float:
        """Net USDT value: spot + earn + futures_long - futures_short (mark price)."""
        return (
            self.spot_qty  * self.price_usdt
            + self.earn_qty * self.price_usdt
            + self.futures_long  * self.mark_price
            - self.futures_short * self.mark_price
        )


@dataclass
class RiskFlag:
    level:   str    # "warning" | "danger"
    asset:   str
    message: str


@dataclass
class PortfolioSnapshot:
    # ── Totals ────────────────────────────────────────────────────────────────
    total_equity_usdt:        float
    spot_equity_usdt:         float
    earn_equity_usdt:         float
    futures_wallet_usdt:      float
    futures_unrealized_pnl:   float
    futures_available_margin: float
    futures_maint_margin:     float

    # ── Per-asset ─────────────────────────────────────────────────────────────
    positions: Dict[str, AssetPosition] = field(default_factory=dict)

    # ── Allocation % (of total equity) ───────────────────────────────────────
    allocation_pct: Dict[str, float]    = field(default_factory=dict)
    stable_pct:     float = 0.0

    # ── Risk ──────────────────────────────────────────────────────────────────
    risk_flags:     List[RiskFlag]      = field(default_factory=list)

    # ── Top assets ───────────────────────────────────────────────────────────
    def top_assets(self, n: int = 5) -> List[AssetPosition]:
        return sorted(
            [p for p in self.positions.values() if abs(p.net_value) > 0.01],
            key=lambda p: abs(p.net_value),
            reverse=True,
        )[:n]


def aggregate(raw: dict, policy: Optional[PortfolioPolicy] = None) -> PortfolioSnapshot:
    """Build a PortfolioSnapshot from raw fetcher output."""
    if policy is None:
        from src.config import DEFAULT_POLICY
        policy = DEFAULT_POLICY

    prices:     Dict[str, float] = raw["spot_prices"]
    mark_dict:  Dict[str, str]   = raw["mark_prices"]

    # ── Helper: price lookup ──────────────────────────────────────────────────
    def price_of(asset: str) -> float:
        if asset in STABLE_COINS:
            return 1.0
        return prices.get(asset, 0.0)

    def mark_of(asset: str) -> float:
        sym = f"{asset}USDT"
        if sym in mark_dict:
            return float(mark_dict[sym])
        return price_of(asset)

    # ── Build per-asset map ───────────────────────────────────────────────────
    pos: Dict[str, AssetPosition] = {}

    def get_or_create(asset: str) -> AssetPosition:
        if asset not in pos:
            pos[asset] = AssetPosition(
                asset=asset,
                price_usdt=price_of(asset),
                mark_price=mark_of(asset),
            )
        return pos[asset]

    # Spot balances
    for b in raw["spot_account"].get("balances", []):
        a = b["asset"]
        qty = float(b["free"]) + float(b["locked"])
        if qty > 0:
            get_or_create(a).spot_qty += qty

    # Earn flexible
    for row in raw["earn_flexible"].get("rows", []):
        a = row["asset"]
        get_or_create(a).earn_qty += float(row["totalAmount"])

    # Earn locked
    for row in raw["earn_locked"].get("rows", []):
        a = row["asset"]
        get_or_create(a).earn_qty += float(row.get("amount", row.get("totalAmount", 0)))

    # Futures positions
    for fp in raw["futures_positions"]:
        sym = fp["symbol"]
        if not sym.endswith("USDT"):
            continue
        a   = sym[:-4]
        amt = float(fp["positionAmt"])
        p   = get_or_create(a)
        p.mark_price = float(fp["markPrice"])
        if amt > 0:
            p.futures_long  += amt
        else:
            p.futures_short += abs(amt)

    # ── Futures account totals ────────────────────────────────────────────────
    fa = raw["futures_account"]
    futures_wallet   = float(fa.get("totalWalletBalance",    0))
    futures_upnl     = float(fa.get("totalUnrealizedProfit", 0))
    futures_available= float(fa.get("availableBalance",      0))
    futures_maint    = float(fa.get("totalMaintMargin",      0))

    # ── Equity totals ─────────────────────────────────────────────────────────
    spot_equity  = sum(p.spot_value  for p in pos.values())
    earn_equity  = sum(p.earn_value  for p in pos.values())
    total_equity = spot_equity + earn_equity + futures_wallet + futures_upnl

    # ── Allocation % ─────────────────────────────────────────────────────────
    alloc: Dict[str, float] = {}
    for a, p in pos.items():
        val = abs(p.net_value)
        alloc[a] = (val / total_equity * 100) if total_equity > 0 else 0.0

    stable_pct = sum(alloc.get(s, 0) for s in STABLE_COINS)

    # ── Risk flags ────────────────────────────────────────────────────────────
    flags: List[RiskFlag] = []

    # 1. Stable % too low
    if stable_pct < policy.min_stable_pct * 100:
        flags.append(RiskFlag(
            level="warning",
            asset="STABLE",
            message=f"Stable allocation {stable_pct:.1f}% < minimum {policy.min_stable_pct*100:.0f}% — consider adding USDT buffer"
        ))

    # 2. Single coin concentration
    for a, pct in alloc.items():
        if a in STABLE_COINS:
            continue
        if a in policy.allocations:
            _, max_pct = policy.allocations[a]
            if pct / 100 > max_pct:
                flags.append(RiskFlag(
                    level="warning",
                    asset=a,
                    message=f"{a} at {pct:.1f}% exceeds policy max {max_pct*100:.0f}%"
                ))
        elif pct / 100 > policy.max_single_alt_pct:
            flags.append(RiskFlag(
                level="warning",
                asset=a,
                message=f"Alt {a} at {pct:.1f}% exceeds max single alt {policy.max_single_alt_pct*100:.0f}%"
            ))

    # 3. Futures margin health
    if futures_wallet > 0:
        margin_ratio = futures_available / (futures_wallet + futures_upnl)
        if margin_ratio < policy.margin_health_threshold:
            flags.append(RiskFlag(
                level="danger",
                asset="FUTURES",
                message=f"Margin health {margin_ratio*100:.1f}% < threshold {policy.margin_health_threshold*100:.0f}% — risk of liquidation"
            ))

    # 4. High leverage positions
    for fp in raw["futures_positions"]:
        lev = float(fp.get("leverage", 1))
        if lev > policy.max_futures_leverage:
            flags.append(RiskFlag(
                level="danger",
                asset=fp["symbol"],
                message=f"{fp['symbol']} using {lev:.0f}× leverage > max {policy.max_futures_leverage:.0f}×"
            ))

    return PortfolioSnapshot(
        total_equity_usdt        = round(total_equity, 2),
        spot_equity_usdt         = round(spot_equity, 2),
        earn_equity_usdt         = round(earn_equity, 2),
        futures_wallet_usdt      = round(futures_wallet, 2),
        futures_unrealized_pnl   = round(futures_upnl, 2),
        futures_available_margin = round(futures_available, 2),
        futures_maint_margin     = round(futures_maint, 2),
        positions                = pos,
        allocation_pct           = alloc,
        stable_pct               = stable_pct,
        risk_flags               = flags,
    )
