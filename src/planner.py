"""
planner.py — Generate DCA / Rebalance trade suggestions based on target policy.

Logic:
  For each tracked asset in policy:
    - If current allocation < min_pct  → BUY (bring to midpoint)
    - If current allocation > max_pct  → SELL (bring to midpoint)
    - Within range                     → HOLD
  For alts exceeding max_single_alt_pct → SELL excess
  DCA distributes available stablecoin balance to underweight assets.
"""
from dataclasses import dataclass, field
from typing import List, Optional

from src.aggregator import PortfolioSnapshot
from src.config import STABLE_COINS, PortfolioPolicy


@dataclass
class TradeSuggestion:
    action:       str    # "BUY" | "SELL" | "HOLD"
    asset:        str
    amount_usdt:  float  # positive USDT value to buy or sell
    qty:          float  # approximate quantity (amount_usdt / price)
    reason:       str
    priority:     int    # 1=high, 2=medium, 3=low


@dataclass
class RebalancePlan:
    suggestions:        List[TradeSuggestion] = field(default_factory=list)
    total_buy_usdt:     float = 0.0
    total_sell_usdt:    float = 0.0
    stable_available:   float = 0.0
    plan_note:          str   = ""

    def buys(self)  -> List[TradeSuggestion]: return [s for s in self.suggestions if s.action == "BUY"]
    def sells(self) -> List[TradeSuggestion]: return [s for s in self.suggestions if s.action == "SELL"]
    def holds(self) -> List[TradeSuggestion]: return [s for s in self.suggestions if s.action == "HOLD"]


def generate_plan(
    snapshot: PortfolioSnapshot,
    policy: Optional[PortfolioPolicy] = None,
    dca_amount_usdt: float = 0.0,   # extra USDT to DCA this period (0 = rebalance only)
) -> RebalancePlan:
    """
    Generate rebalance / DCA trade suggestions.

    Args:
        snapshot: aggregated portfolio snapshot
        policy:   target allocation policy
        dca_amount_usdt: new USDT to deploy (DCA mode). 0 = pure rebalance.
    """
    if policy is None:
        from src.config import DEFAULT_POLICY
        policy = DEFAULT_POLICY

    total = snapshot.total_equity_usdt
    if total <= 0:
        return RebalancePlan(plan_note="⚠️ Portfolio is empty or could not be valued.")

    suggestions: List[TradeSuggestion] = []

    # ── Available stable balance (for buys) ──────────────────────────────────
    stable_val = sum(
        snapshot.positions[s].net_value
        for s in STABLE_COINS
        if s in snapshot.positions
    )
    budget = stable_val + dca_amount_usdt   # total USDT we can spend on buys

    # ── Check policy-tracked assets ──────────────────────────────────────────
    for asset, (min_pct, max_pct) in policy.allocations.items():
        if asset == "STABLE":
            current_pct = snapshot.stable_pct / 100
        else:
            current_pct = snapshot.allocation_pct.get(asset, 0.0) / 100

        mid_pct = (min_pct + max_pct) / 2.0
        current_val = current_pct * total
        target_val  = mid_pct * total

        price = 1.0 if asset == "STABLE" else (
            snapshot.positions[asset].price_usdt if asset in snapshot.positions else 0.0
        )

        # Only act when OUTSIDE the min–max band (not just off midpoint)
        if current_pct < min_pct:          # BUY — genuinely underweight
            diff_usdt = target_val - current_val
            if diff_usdt > 10:
                qty = (diff_usdt / price) if price > 0 else 0
                suggestions.append(TradeSuggestion(
                    action="BUY",
                    asset=asset,
                    amount_usdt=round(diff_usdt, 2),
                    qty=round(qty, 6),
                    reason=f"{asset} at {current_pct*100:.1f}% — below min {min_pct*100:.0f}% → target {mid_pct*100:.0f}%",
                    priority=1 if current_pct < min_pct * 0.7 else 2,
                ))
            else:
                suggestions.append(TradeSuggestion(
                    action="HOLD", asset=asset, amount_usdt=0.0, qty=0.0,
                    reason=f"{asset} at {current_pct*100:.1f}% — within policy range [{min_pct*100:.0f}%–{max_pct*100:.0f}%]",
                    priority=3,
                ))
        elif current_pct > max_pct:        # SELL — genuinely overweight
            sell_amt = current_val - target_val
            if sell_amt > 10:
                qty = (sell_amt / price) if price > 0 else 0
                suggestions.append(TradeSuggestion(
                    action="SELL",
                    asset=asset,
                    amount_usdt=round(sell_amt, 2),
                    qty=round(qty, 6),
                    reason=f"{asset} at {current_pct*100:.1f}% — above max {max_pct*100:.0f}% → trim to {mid_pct*100:.0f}%",
                    priority=1 if current_pct > max_pct * 1.3 else 2,
                ))
            else:
                suggestions.append(TradeSuggestion(
                    action="HOLD", asset=asset, amount_usdt=0.0, qty=0.0,
                    reason=f"{asset} at {current_pct*100:.1f}% — within policy range [{min_pct*100:.0f}%–{max_pct*100:.0f}%]",
                    priority=3,
                ))
        else:                              # HOLD — within acceptable band
            suggestions.append(TradeSuggestion(
                action="HOLD",
                asset=asset,
                amount_usdt=0.0,
                qty=0.0,
                reason=f"{asset} at {current_pct*100:.1f}% — within policy range [{min_pct*100:.0f}%–{max_pct*100:.0f}%]",
                priority=3,
            ))

    # ── Check alts exceeding max_single_alt_pct ───────────────────────────────
    for asset, pct in snapshot.allocation_pct.items():
        if asset in STABLE_COINS:
            continue
        if asset in policy.allocations:
            continue   # already handled above
        if pct / 100 > policy.max_single_alt_pct:
            excess_pct  = pct / 100 - policy.max_single_alt_pct
            excess_usdt = excess_pct * total
            price = snapshot.positions[asset].price_usdt if asset in snapshot.positions else 1.0
            qty   = excess_usdt / price if price > 0 else 0
            suggestions.append(TradeSuggestion(
                action="SELL",
                asset=asset,
                amount_usdt=round(excess_usdt, 2),
                qty=round(qty, 6),
                reason=f"Alt {asset} at {pct:.1f}% exceeds max single alt {policy.max_single_alt_pct*100:.0f}% — trim excess",
                priority=2,
            ))

    # ── Sort: SELL first (free up capital), then BUY by priority, then HOLD ──
    suggestions.sort(key=lambda s: (
        0 if s.action == "SELL" else (1 if s.action == "BUY" else 2),
        s.priority,
    ))

    total_buy  = sum(s.amount_usdt for s in suggestions if s.action == "BUY")
    total_sell = sum(s.amount_usdt for s in suggestions if s.action == "SELL")

    note = ""
    if total_buy > budget:
        note = (
            f"⚠️ Total buys ${total_buy:,.0f} exceed available stable ${budget:,.0f}. "
            "Execute SELLs first or add more USDT."
        )
    elif dca_amount_usdt > 0:
        note = f"✅ DCA mode: deploying ${dca_amount_usdt:,.0f} USDT + existing stable ${stable_val:,.0f} USDT."
    else:
        note = "✅ Pure rebalance mode: no new capital needed, sell overweight then buy underweight."

    return RebalancePlan(
        suggestions=suggestions,
        total_buy_usdt=round(total_buy, 2),
        total_sell_usdt=round(total_sell, 2),
        stable_available=round(budget, 2),
        plan_note=note,
    )
