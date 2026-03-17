"""
main.py — CLI entry point for OpenClaw Portfolio Brain.
Prints a full portfolio report to the terminal.

Usage:
    python main.py              # mock data
    USE_MOCK_DATA=false python main.py   # real API
    python main.py --dca 500    # generate DCA plan with $500 USDT
"""
import argparse
from src.fetcher import fetch_portfolio
from src.aggregator import aggregate
from src.planner import generate_plan
from src.config import DEFAULT_POLICY


def print_banner():
    print("""
======================================================
  OpenClaw Portfolio Brain  --  Binance AI Skill
  github.com/namtrung99/openclaw-portfolio-brain
======================================================
""")


def print_section(title: str):
    print(f"\n{'-'*54}")
    print(f"  {title}")
    print('-'*54)


def main():
    parser = argparse.ArgumentParser(description="OpenClaw Portfolio Brain CLI")
    parser.add_argument("--mock",  action="store_true", default=None,  help="Force mock data")
    parser.add_argument("--real",  action="store_true", default=False,  help="Force real API")
    parser.add_argument("--dca",   type=float, default=0.0,             help="DCA amount in USDT")
    args = parser.parse_args()

    use_mock = True if args.mock else (False if args.real else None)

    print_banner()
    print("  Fetching portfolio data...")
    raw  = fetch_portfolio(use_mock=use_mock)
    snap = aggregate(raw, policy=DEFAULT_POLICY)
    plan = generate_plan(snap, policy=DEFAULT_POLICY, dca_amount_usdt=args.dca)

    # ── 1. Summary ────────────────────────────────────────────────────────────
    print_section("PORTFOLIO SUMMARY")
    print(f"  Total Equity     : ${snap.total_equity_usdt:>12,.2f} USDT")
    print(f"  -- Spot          : ${snap.spot_equity_usdt:>12,.2f}")
    print(f"  -- Earn          : ${snap.earn_equity_usdt:>12,.2f}")
    print(f"  -- Futures       : ${snap.futures_wallet_usdt:>12,.2f}  (uPnL {snap.futures_unrealized_pnl:+,.2f})")
    print(f"  Stable %         : {snap.stable_pct:>10.1f}%")

    # ── 2. Top positions ──────────────────────────────────────────────────────
    print_section("TOP POSITIONS")
    print(f"  {'Asset':<6} {'Net Qty':>12} {'Price':>12} {'Value':>12} {'Alloc%':>8}")
    print(f"  {'-'*6} {'-'*12} {'-'*12} {'-'*12} {'-'*8}")
    for p in snap.top_assets(8):
        pct = snap.allocation_pct.get(p.asset, 0)
        print(f"  {p.asset:<6} {p.net_qty:>12.4f} ${p.price_usdt:>11,.2f} ${p.net_value:>11,.2f} {pct:>7.1f}%")

    # ── 3. Net exposure ───────────────────────────────────────────────────────
    print_section("NET EXPOSURE (Spot + Earn + Futures)")
    for p in snap.top_assets(6):
        spot_str = f"spot {p.spot_qty:.4f}"
        earn_str = f"earn {p.earn_qty:.4f}" if p.earn_qty > 0 else ""
        fut_str  = ""
        if p.futures_long > 0:
            fut_str = f"long +{p.futures_long:.4f}"
        elif p.futures_short > 0:
            fut_str = f"short -{p.futures_short:.4f}"
        parts = [x for x in [spot_str, earn_str, fut_str] if x]
        print(f"  {p.asset:<6} net {p.net_qty:>10.4f}  ({', '.join(parts)})")

    # ── 4. Risk flags ─────────────────────────────────────────────────────────
    print_section("RISK FLAGS")
    if not snap.risk_flags:
        print("  [OK] No risk flags detected!")
    for flag in snap.risk_flags:
        icon = "[!!]" if flag.level == "danger" else "[!]"
        print(f"  {icon} [{flag.asset}] {flag.message}")

    # ── 5. Rebalance / DCA plan ───────────────────────────────────────────────
    print_section("REBALANCE / DCA PLAN")
    print(f"  {plan.plan_note}")
    print(f"  Stable available : ${plan.stable_available:,.2f}")
    print(f"  Total BUYs       : ${plan.total_buy_usdt:,.2f}")
    print(f"  Total SELLs      : ${plan.total_sell_usdt:,.2f}")
    print()
    for s in plan.suggestions:
        if s.action == "HOLD":
            continue
        tag = "[BUY]" if s.action == "BUY" else "[SELL]"
        print(f"  {tag} {s.action:<5} {s.asset:<6}  ${s.amount_usdt:>9,.2f}  (~{s.qty:.4f})  {s.reason}")

    print("\n" + "="*54)
    print("  Not investment advice. DYOR. Binance ToS applies.")
    print("="*54 + "\n")


if __name__ == "__main__":
    main()
