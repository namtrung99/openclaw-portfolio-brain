"""
app.py — Streamlit dashboard for OpenClaw Portfolio Brain.

Run: streamlit run app.py
     or with real API: USE_MOCK_DATA=false streamlit run app.py
"""
import os
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from src.config import DEFAULT_POLICY, PortfolioPolicy, STABLE_COINS
from src.fetcher import fetch_portfolio
from src.aggregator import aggregate
from src.planner import generate_plan

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="🧠 Portfolio Brain",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS (Binance dark theme) ──────────────────────────────────────────
st.markdown("""
<style>
body, .stApp { background: #0B0E11; color: #EAECEF; }
.stMetric { background: #1E2329; border-radius: 10px; padding: 16px; border: 1px solid #2B3139; }
.stMetric label { color: #848E9C !important; }
.stMetric [data-testid="stMetricValue"] { color: #EAECEF !important; font-size: 22px !important; }
.stAlert { border-radius: 8px; }
h1, h2, h3 { color: #F0B90B; }
.risk-danger  { background: rgba(246,70,93,.12); border-left: 4px solid #F6465D; padding: 10px 16px; border-radius: 6px; margin: 6px 0; }
.risk-warning { background: rgba(240,185,11,.10); border-left: 4px solid #F0B90B; padding: 10px 16px; border-radius: 6px; margin: 6px 0; }
</style>
""", unsafe_allow_html=True)

# ── Sidebar — Settings ───────────────────────────────────────────────────────
with st.sidebar:
    st.image("https://public.bnbstatic.com/static/images/common/favicon.ico", width=32)
    st.title("⚙️ Settings")

    data_mode = st.radio("Data Source", ["🎭 Mock Data (Demo)", "🔑 Real API"])
    use_mock  = data_mode.startswith("🎭")

    st.divider()
    st.subheader("📐 Portfolio Policy")

    btc_min  = st.slider("BTC min %",  0, 60, 30)
    btc_max  = st.slider("BTC max %",  0, 60, 45)
    eth_min  = st.slider("ETH min %",  0, 40, 10)
    eth_max  = st.slider("ETH max %",  0, 40, 25)
    bnb_min  = st.slider("BNB min %",  0, 20, 5)
    bnb_max  = st.slider("BNB max %",  0, 20, 10)
    stab_min = st.slider("Stable min %", 0, 40, 15)
    stab_max = st.slider("Stable max %", 0, 40, 25)
    max_alt  = st.slider("Max single alt %", 1, 20, 8)

    dca_amount = st.number_input("DCA amount (USDT)", min_value=0.0, value=0.0, step=100.0)

    policy = PortfolioPolicy(
        allocations={
            "BTC":    (btc_min/100,  btc_max/100),
            "ETH":    (eth_min/100,  eth_max/100),
            "BNB":    (bnb_min/100,  bnb_max/100),
            "STABLE": (stab_min/100, stab_max/100),
        },
        max_single_alt_pct=max_alt/100,
        min_stable_pct=stab_min/100,
    )

    refresh = st.button("🔄 Refresh Portfolio", use_container_width=True)

# ── Load data ────────────────────────────────────────────────────────────────
@st.cache_data(ttl=30, show_spinner="Fetching portfolio data…")
def load(mock: bool):
    raw      = fetch_portfolio(use_mock=mock)
    snap     = aggregate(raw, policy=DEFAULT_POLICY)
    return raw, snap

if "snap" not in st.session_state or refresh:
    with st.spinner("Loading portfolio…"):
        raw, snap = load(use_mock=use_mock)
    st.session_state["snap"] = snap
    st.session_state["raw"]  = raw

snap = st.session_state["snap"]
plan = generate_plan(snap, policy=policy, dca_amount_usdt=dca_amount)

# ── Header ────────────────────────────────────────────────────────────────────
st.title("🧠 OpenClaw Portfolio Brain")
st.caption("Binance AI Agent Skills — Full-stack portfolio aggregator & rebalance planner")

mode_badge = "🎭 Mock Data" if use_mock else "🔑 Live API"
st.info(f"**Mode:** {mode_badge}  |  Powered by Binance Spot · Futures · Earn APIs")

# ── KPI Metrics ───────────────────────────────────────────────────────────────
col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("💰 Total Equity",   f"${snap.total_equity_usdt:,.2f}")
col2.metric("📦 Spot",           f"${snap.spot_equity_usdt:,.2f}")
col3.metric("🌾 Earn",           f"${snap.earn_equity_usdt:,.2f}")
col4.metric("📈 Futures Wallet", f"${snap.futures_wallet_usdt:,.2f}",
            delta=f"uPnL ${snap.futures_unrealized_pnl:+,.2f}")
col5.metric("🛡️ Stable %",       f"{snap.stable_pct:.1f}%",
            delta_color="inverse" if snap.stable_pct < policy.min_stable_pct*100 else "normal",
            delta=f"min {policy.min_stable_pct*100:.0f}%")

st.divider()

# ── Two column layout ─────────────────────────────────────────────────────────
left, right = st.columns([1, 1], gap="large")

# ── LEFT: Allocation pie chart ────────────────────────────────────────────────
with left:
    st.subheader("📊 Portfolio Allocation")

    alloc_data = []
    for asset, pct in sorted(snap.allocation_pct.items(), key=lambda x: -x[1]):
        if pct > 0.1:
            alloc_data.append({"Asset": asset, "Allocation %": round(pct, 2)})

    if alloc_data:
        df_alloc = pd.DataFrame(alloc_data)
        # Group small alts into "Others"
        threshold = 1.5
        big  = df_alloc[df_alloc["Allocation %"] >= threshold]
        tiny = df_alloc[df_alloc["Allocation %"] <  threshold]
        if not tiny.empty:
            others_row = pd.DataFrame([{"Asset": "Others", "Allocation %": tiny["Allocation %"].sum()}])
            df_pie = pd.concat([big, others_row], ignore_index=True)
        else:
            df_pie = big

        colors = ["#F0B90B", "#627EEA", "#F3BA2F", "#9945FF",
                  "#00FFA3", "#FF6B6B", "#4ECDC4", "#848E9C"]
        fig = px.pie(
            df_pie,
            names="Asset",
            values="Allocation %",
            color_discrete_sequence=colors,
            hole=0.45,
        )
        fig.update_layout(
            paper_bgcolor="#1E2329",
            plot_bgcolor="#1E2329",
            font_color="#EAECEF",
            showlegend=True,
            legend=dict(font=dict(color="#EAECEF")),
            margin=dict(t=20, b=20, l=10, r=10),
        )
        fig.update_traces(textfont_color="#0B0E11", textfont_size=12)
        st.plotly_chart(fig, use_container_width=True)

# ── RIGHT: Top positions table ────────────────────────────────────────────────
with right:
    st.subheader("🏆 Top Positions")
    top = snap.top_assets(8)
    if top:
        rows = []
        for p in top:
            is_stable = p.asset in STABLE_COINS
            rows.append({
                "Asset": p.asset,
                "Net Qty": f"{p.net_qty:.4f}" if not is_stable else f"{p.net_qty:,.2f}",
                "Price": f"${p.price_usdt:,.2f}",
                "Net Value": f"${p.net_value:,.2f}",
                "% Portfolio": f"{snap.allocation_pct.get(p.asset, 0):.1f}%",
                "Spot": f"{p.spot_qty:.4f}",
                "Earn": f"{p.earn_qty:.4f}" if p.earn_qty > 0 else "—",
                "Futures": (
                    f"+{p.futures_long:.4f}" if p.futures_long > 0 else
                    f"-{p.futures_short:.4f}" if p.futures_short > 0 else "—"
                ),
            })
        df_top = pd.DataFrame(rows)
        st.dataframe(df_top, use_container_width=True, hide_index=True)

    # Futures margin bar
    if snap.futures_wallet_usdt > 0:
        total_margin  = snap.futures_wallet_usdt + snap.futures_unrealized_pnl
        avail_ratio   = snap.futures_available_margin / total_margin if total_margin > 0 else 1
        health_color  = "#0ECB81" if avail_ratio > 0.5 else ("#F0B90B" if avail_ratio > 0.3 else "#F6465D")
        st.markdown(f"**Futures Margin Health**: {avail_ratio*100:.1f}%")
        st.progress(float(avail_ratio), text=f"Available ${snap.futures_available_margin:,.0f} / Total ${total_margin:,.0f}")

st.divider()

# ── RISK FLAGS ───────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["⚠️ Risk Flags", "📋 Rebalance Plan", "📈 Open Futures"])

with tab1:
    if not snap.risk_flags:
        st.success("✅ No risk flags — portfolio looks healthy!")
    else:
        for flag in snap.risk_flags:
            icon  = "🔴" if flag.level == "danger" else "🟡"
            css_class = "risk-danger" if flag.level == "danger" else "risk-warning"
            st.markdown(
                f'<div class="{css_class}">{icon} <strong>[{flag.asset}]</strong> {flag.message}</div>',
                unsafe_allow_html=True,
            )

# ── REBALANCE PLAN ────────────────────────────────────────────────────────────
with tab2:
    st.caption(plan.plan_note)

    c1, c2, c3 = st.columns(3)
    c1.metric("💵 Stable Available",  f"${plan.stable_available:,.2f}")
    c2.metric("🟢 Total Buys",        f"${plan.total_buy_usdt:,.2f}")
    c3.metric("🔴 Total Sells",       f"${plan.total_sell_usdt:,.2f}")

    if plan.suggestions:
        rows = []
        for s in plan.suggestions:
            emoji = "🟢" if s.action == "BUY" else ("🔴" if s.action == "SELL" else "⚪")
            rows.append({
                "Action": f"{emoji} {s.action}",
                "Asset":  s.asset,
                "Amount (USDT)": f"${s.amount_usdt:,.2f}" if s.amount_usdt else "—",
                "Approx Qty":    f"{s.qty:.4f}" if s.qty else "—",
                "Priority": "🔥 High" if s.priority == 1 else ("⚡ Med" if s.priority == 2 else "✅ Low"),
                "Reason": s.reason,
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

# ── FUTURES POSITIONS ─────────────────────────────────────────────────────────
with tab3:
    fut_pos = [fp for fp in st.session_state["raw"]["futures_positions"]
               if float(fp["positionAmt"]) != 0]
    if not fut_pos:
        st.info("No open futures positions.")
    else:
        rows = []
        for fp in fut_pos:
            amt  = float(fp["positionAmt"])
            side = "🟢 LONG" if amt > 0 else "🔴 SHORT"
            upnl = float(fp.get("unRealizedProfit", 0))
            rows.append({
                "Symbol":    fp["symbol"],
                "Side":      side,
                "Size":      f"{abs(amt):.4f}",
                "Entry":     f"${float(fp['entryPrice']):,.2f}",
                "Mark":      f"${float(fp['markPrice']):,.2f}",
                "uPnL":      f"${upnl:+,.2f}",
                "Leverage":  f"{fp.get('leverage', '—')}×",
                "Liq. Price":f"${float(fp.get('liquidationPrice', 0)):,.2f}",
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

# ── Footer ─────────────────────────────────────────────────────────────────────
st.divider()
st.caption("🧠 OpenClaw Portfolio Brain · [GitHub](https://github.com/namtrung99/openclaw-portfolio-brain) · Built for Binance #AIBinance · ⚠️ Not investment advice")
