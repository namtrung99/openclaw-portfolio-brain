"""
app.py — OpenClaw Portfolio Brain
Rendering strategy: wallet cards load first → trade history loads after → AI analysis last.
"""
from __future__ import annotations

import datetime
import importlib
import json
import os
import time
from typing import Any

from dotenv import load_dotenv
import src.config as _src_config
import src.fetcher as _src_fetcher

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.aggregator import aggregate
from src.chatbot import build_portfolio_context, chat_with_groq
from src.config import BINANCE_API_KEY, DEFAULT_POLICY, STABLE_COINS, USE_MOCK_DATA
from src.fetcher import fetch_cost_basis, fetch_portfolio, fetch_tax_data, fetch_futures_trades, fetch_futures_income
from src.mock_data import BINANCE_ALPHA_COINS, get_risk_level
from src.planner import generate_plan

# ─────────────────────────────────────────────────────────────────────────────
#  Constants
# ─────────────────────────────────────────────────────────────────────────────

ENV_PATH = os.path.join(os.path.dirname(__file__), ".env")

RISK_COLORS = {"safe": "kpi-green", "medium": "kpi-gold", "risky": "kpi-red"}
RISK_LABELS = {"safe": "Safe", "medium": "Medium", "risky": "Risky"}

PIE_COLORS = [
    "#F0B90B", "#627EEA", "#2ECC71", "#0ECB81",
    "#9945FF", "#848E9C", "#F6465D", "#26A17B", "#3498DB",
]

GRADE_MAP = {
    "A": ("#0ECB81", "Healthy"),
    "B": ("#F0B90B", "Moderate"),
    "C": ("#FF8C00", "At Risk"),
    "D": ("#F6465D", "Danger"),
}

# ─────────────────────────────────────────────────────────────────────────────
#  Page config
# ─────────────────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Portfolio Brain",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
body, .stApp { background: #0B0E11 !important; color: #EAECEF; }
section[data-testid="stSidebar"] { background: #161A1E; border-right: 1px solid #2B3139; }
.block-container  { padding-top: 1rem; padding-bottom: 2rem; }

/* ── Streamlit header: transparent, no height, sidebar toggle still works ── */
header[data-testid="stHeader"] {
    background: transparent !important;
    height: 0 !important;
    min-height: 0 !important;
    padding: 0 !important;
    border: none !important;
}
[data-testid="stToolbar"],
[data-testid="stStatusWidget"],
.stDeployButton,
#MainMenu { display: none !important; }
footer { display: none !important; }

/* sidebar toggle button floats above content, no overlap */
[data-testid="stSidebarCollapsedControl"] {
    top: 8px !important;
    z-index: 999 !important;
}

/* ── Smooth hover transitions (no page animation — avoids black flash on rerun) ── */
.card, .alert-ok, .alert-warn, .alert-danger, .ai-box { transition: all .2s ease; }
.card:hover { border-color: #F0B90B40; }

.card      { background: #1E2329; border: 1px solid #2B3139; border-radius: 12px; padding: 18px 20px; }
.kpi-label { color: #848E9C; font-size: 11px; font-weight: 500; text-transform: uppercase;
             letter-spacing: .5px; margin-bottom: 6px; }
.kpi-value { color: #EAECEF; font-size: 24px; font-weight: 700; line-height: 1.2; }
.kpi-sub   { color: #5E6673; font-size: 11px; margin-top: 5px; }

.kpi-green { color: #0ECB81 !important; }
.kpi-red   { color: #F6465D !important; }
.kpi-gold  { color: #F0B90B !important; }

.sec-hdr {
    font-size: 13px; font-weight: 700; color: #F0B90B; letter-spacing: .3px;
    border-bottom: 1px solid #2B3139; padding-bottom: 6px; margin: 24px 0 14px;
}
.alert-ok     { background: #0ECB8110; border-left: 3px solid #0ECB81;
                border-radius: 0 6px 6px 0; padding: 9px 14px; margin: 5px 0; font-size: 12px; }
.alert-warn   { background: #F0B90B10; border-left: 3px solid #F0B90B;
                border-radius: 0 6px 6px 0; padding: 9px 14px; margin: 5px 0; font-size: 12px; }
.alert-danger { background: #F6465D10; border-left: 3px solid #F6465D;
                border-radius: 0 6px 6px 0; padding: 9px 14px; margin: 5px 0; font-size: 12px; }

.ai-box { background: linear-gradient(135deg, #1E2329 0%, #161A1E 100%);
          border: 1px solid #F0B90B40; border-radius: 12px; padding: 16px 20px; }
.ai-tag { display: inline-block; background: #F0B90B20; color: #F0B90B; font-size: 10px;
          font-weight: 700; letter-spacing: 1px; border-radius: 4px;
          padding: 2px 8px; margin-bottom: 8px; }

h1, h2, h3 { color: #F0B90B !important; }

/* ── Global button dark override ── */
button[kind="secondary"], div.stButton > button {
    background: #1E2329 !important;
    color: #EAECEF !important;
    border: 1px solid #2B3139 !important;
    border-radius: 8px !important;
    font-size: 12px !important;
    font-weight: 500 !important;
    transition: border-color .2s, background .2s !important;
}
div.stButton > button:hover {
    background: #2B3139 !important;
    border-color: #F0B90B !important;
    color: #F0B90B !important;
}

/* ── Quick-question pill buttons ── */
.q-btn > div.stButton > button {
    background: #161A1E !important;
    border: 1px solid #2B3139 !important;
    border-radius: 20px !important;
    color: #848E9C !important;
    font-size: 12px !important;
    padding: 6px 14px !important;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
.q-btn > div.stButton > button:hover {
    border-color: #627EEA !important;
    color: #627EEA !important;
    background: #1E2329 !important;
}

/* ── Chat message bubbles ── */
[data-testid="stChatMessage"] {
    background: #161A1E !important;
    border: 1px solid #2B3139 !important;
    border-radius: 12px !important;
    padding: 10px 14px !important;
    margin-bottom: 8px !important;
}
[data-testid="stChatMessage"][data-testid*="user"] {
    background: #1E2329 !important;
    border-color: #627EEA40 !important;
}

/* ── Hide floating chat input bar ── */
[data-testid="stBottom"] { display: none !important; }

/* ── Inline chat text input styling ── */
.chat-input input { background: #1E2329 !important; color: #EAECEF !important;
    border: 1px solid #2B3139 !important; border-radius: 10px !important; }
.chat-input input:focus { border-color: #627EEA !important;
    box-shadow: 0 0 0 2px #627EEA20 !important; }
.chat-input label { display: none !important; }

/* ── Spinner / st.status ── */
.stSpinner > div { border-top-color: #F0B90B !important; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
#  UI helper functions
# ─────────────────────────────────────────────────────────────────────────────

def render_kpi(col: Any, label: str, value: str, sub: str = "", color: str = "") -> None:
    """Render a single KPI metric card inside *col*."""
    col.markdown(
        f'<div class="card" style="text-align:center">'
        f'<div class="kpi-label">{label}</div>'
        f'<div class="kpi-value {color}">{value}</div>'
        f'<div class="kpi-sub">{sub}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


def render_section(title: str, color: str = "#F0B90B") -> None:
    """Render a section header divider."""
    st.markdown(
        f'<div class="sec-hdr" style="color:{color}">{title}</div>',
        unsafe_allow_html=True,
    )


def render_alert(level: str, message: str) -> None:
    """Render a coloured alert box (level: ok | warn | danger)."""
    css_class = f"alert-{level}"
    st.markdown(f'<div class="{css_class}">{message}</div>', unsafe_allow_html=True)


def pnl_color(value: float) -> str:
    """Return CSS class name for a P&L value."""
    return "kpi-green" if value >= 0 else "kpi-red"


# ─────────────────────────────────────────────────────────────────────────────
#  .env helpers
# ─────────────────────────────────────────────────────────────────────────────

def read_env() -> dict[str, str]:
    """Parse the .env file into a key→value dict (skips comments)."""
    if not os.path.exists(ENV_PATH):
        return {}
    result: dict[str, str] = {}
    with open(ENV_PATH) as fh:
        for line in fh:
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                key, value = line.split("=", 1)
                result[key.strip()] = value.strip()
    return result


def write_env(updates: dict[str, str]) -> None:
    """Patch specific keys in the .env file, appending any new keys at the end."""
    lines: list[str] = []
    pending = dict(updates)  # keys still to be written

    if os.path.exists(ENV_PATH):
        with open(ENV_PATH) as fh:
            for line in fh:
                key = line.split("=", 1)[0].strip()
                if key in pending:
                    lines.append(f"{key}={pending.pop(key)}\n")
                else:
                    lines.append(line)

    for key, value in pending.items():
        lines.append(f"{key}={value}\n")

    with open(ENV_PATH, "w") as fh:
        fh.writelines(lines)


# ─────────────────────────────────────────────────────────────────────────────
#  AI — Health Score
# ─────────────────────────────────────────────────────────────────────────────

def compute_health_score(snap: Any, cb_summary: dict) -> dict:
    """
    Compute a 0–100 composite health score across five risk dimensions.

    Dimensions and max points:
        stable_buffer   25 pts  — % of portfolio in stablecoins
        risk_mix        25 pts  — ratio of safe vs risky assets
        diversification 20 pts  — number of meaningful positions
        pnl_health      20 pts  — net P&L as % of invested capital
        futures_exposure 10 pts — futures wallet as % of total
    """
    total  = snap.total_equity_usdt or 1.0
    scores: dict[str, int] = {}
    tips:   list[tuple[str, str]] = []

    # 1 ── Stable buffer ──────────────────────────────────────────────────────
    stable_pct = snap.stable_pct
    if 15 <= stable_pct <= 30:
        scores["stable"] = 25
        tips.append(("✅", f"Stable buffer {stable_pct:.0f}% — healthy"))
    elif 10 <= stable_pct < 15:
        scores["stable"] = 15
        tips.append(("⚠️", f"Stable {stable_pct:.0f}% — consider adding USDT"))
    elif stable_pct > 40:
        scores["stable"] = 15
        tips.append(("⚠️", f"Stable {stable_pct:.0f}% — too conservative"))
    else:
        scores["stable"] = 5
        tips.append(("🔴", f"Stable only {stable_pct:.0f}% — high risk"))

    # 2 ── Risk mix ───────────────────────────────────────────────────────────
    safe_pct = sum(
        abs(pos.net_value) / total * 100
        for asset, pos in snap.positions.items()
        if get_risk_level(asset) == "safe" and abs(pos.net_value) > 0.5
    )
    risky_pct = sum(
        abs(pos.net_value) / total * 100
        for asset, pos in snap.positions.items()
        if get_risk_level(asset) == "risky" and abs(pos.net_value) > 0.5
    )
    if safe_pct >= 50:
        scores["risk_mix"] = 25
        tips.append(("✅", f"Safe assets {safe_pct:.0f}% — well protected"))
    elif safe_pct >= 30:
        scores["risk_mix"] = 15
        tips.append(("⚠️", f"Safe {safe_pct:.0f}%, Risky {risky_pct:.0f}% — moderate"))
    else:
        scores["risk_mix"] = 5
        tips.append(("🔴", f"Risky assets {risky_pct:.0f}% — high volatility"))

    # 3 ── Diversification ────────────────────────────────────────────────────
    position_count = sum(1 for pos in snap.positions.values() if abs(pos.net_value) > 10)
    if 5 <= position_count <= 15:
        scores["diversification"] = 20
        tips.append(("✅", f"{position_count} positions — well diversified"))
    elif position_count < 5:
        scores["diversification"] = 10
        tips.append(("⚠️", f"Only {position_count} positions — concentrated"))
    else:
        scores["diversification"] = 10
        tips.append(("⚠️", f"{position_count} positions — over-diversified"))

    # 4 ── P&L health ─────────────────────────────────────────────────────────
    total_spent = cb_summary.get("total_spent", 0)
    if total_spent > 0:
        pnl_pct = cb_summary.get("net_pnl", 0) / total_spent * 100
        if pnl_pct >= 0:
            scores["pnl"] = 20
            tips.append(("✅", f"Net P&L {pnl_pct:+.1f}% — in profit"))
        elif pnl_pct >= -25:
            scores["pnl"] = 12
            tips.append(("⚠️", f"Net P&L {pnl_pct:+.1f}% — moderate loss"))
        elif pnl_pct >= -50:
            scores["pnl"] = 6
            tips.append(("🔴", f"Net P&L {pnl_pct:+.1f}% — significant loss"))
        else:
            scores["pnl"] = 2
            tips.append(("🔴", f"Net P&L {pnl_pct:+.1f}% — heavy loss"))
    else:
        scores["pnl"] = 10  # no trade data available

    # 5 ── Futures exposure ───────────────────────────────────────────────────
    futures_pct = snap.futures_wallet_usdt / total * 100
    if snap.futures_wallet_usdt <= 0:
        scores["futures"] = 10
        tips.append(("✅", "No open futures — safe"))
    elif futures_pct < 10:
        scores["futures"] = 10
        tips.append(("✅", f"Futures {futures_pct:.0f}% — low risk"))
    elif futures_pct < 25:
        scores["futures"] = 6
        tips.append(("⚠️", f"Futures {futures_pct:.0f}% — moderate"))
    else:
        scores["futures"] = 2
        tips.append(("🔴", f"Futures {futures_pct:.0f}% — high leverage"))

    # ── Final grade ──────────────────────────────────────────────────────────
    total_score = sum(scores.values())
    if   total_score >= 75: grade = "A"
    elif total_score >= 55: grade = "B"
    elif total_score >= 35: grade = "C"
    else:                   grade = "D"

    color, label = GRADE_MAP[grade]
    return {
        "score": total_score,
        "grade": grade,
        "color": color,
        "label": label,
        "tips":  tips,
    }


# ─────────────────────────────────────────────────────────────────────────────
#  AI — Insights Engine
# ─────────────────────────────────────────────────────────────────────────────

def generate_ai_insights(
    snap: Any,
    cb_summary: dict,
    health: dict,
    futures_positions: list[dict],
) -> list[tuple[str, str, str]]:
    """
    Rule-based AI engine that reads portfolio signals and returns actionable insights.

    Returns a list of (level, label, message) tuples where
    level ∈ {"ok", "warn", "danger"}.
    """
    tips: list[tuple[str, str, str]] = []
    total = snap.total_equity_usdt or 1.0

    # ── Stable buffer ────────────────────────────────────────────────────────
    stable_pct = snap.stable_pct
    if stable_pct < 10:
        needed = total * (0.20 - stable_pct / 100)
        tips.append(("danger", "🤖 AI",
            f"Stable buffer critical at {stable_pct:.0f}%. A 20–30% cash reserve helps you "
            f"buy dips and survive drawdowns. "
            f"Consider converting ${needed:,.0f} worth of altcoins to USDT."
        ))
    elif stable_pct < 15:
        needed = total * (0.15 - stable_pct / 100)
        tips.append(("warn", "🤖 AI",
            f"Stable buffer at {stable_pct:.0f}% is below the recommended 15%. "
            f"Building up ~${needed:,.0f} more in USDT would improve downside protection."
        ))
    elif stable_pct > 45:
        excess = total * (stable_pct / 100 - 0.30)
        tips.append(("warn", "🤖 AI",
            f"You're holding {stable_pct:.0f}% in stables — more than needed as a buffer. "
            f"Consider deploying ${excess:,.0f} into quality assets (BTC/BNB) to grow your portfolio."
        ))

    # ── Concentration risk ───────────────────────────────────────────────────
    for asset, alloc_pct in snap.allocation_pct.items():
        risk = get_risk_level(asset)
        if alloc_pct > 40 and risk != "safe":
            potential_loss = total * alloc_pct / 100 * 0.30
            trim_amount    = total * (alloc_pct - 25) / 100
            tips.append(("danger", f"🤖 AI [{asset}]",
                f"{asset} is {alloc_pct:.0f}% of your portfolio — very concentrated. "
                f"A 30% drop would cost ~${potential_loss:,.0f}. "
                f"Trimming to 25% would free ${trim_amount:,.0f} to diversify."
            ))
        elif alloc_pct > 25 and risk == "risky":
            tips.append(("warn", f"🤖 AI [{asset}]",
                f"{asset} is classified HIGH RISK and takes {alloc_pct:.0f}% of your portfolio. "
                f"Consider reducing to under 10% for better risk management."
            ))

    # ── P&L context ──────────────────────────────────────────────────────────
    total_spent = cb_summary.get("total_spent", 0)
    net_pnl     = cb_summary.get("net_pnl", 0)
    if total_spent > 0:
        pnl_pct = net_pnl / total_spent * 100
        if pnl_pct < -30:
            tips.append(("danger", "🤖 AI [P&L]",
                f"Portfolio is down {pnl_pct:.0f}% overall (${net_pnl:,.0f}). "
                f"Avoid panic selling — average down only on high-conviction assets (BTC, BNB). "
                f"Stop-loss positions that no longer have a clear thesis."
            ))
        elif pnl_pct < -10:
            tips.append(("warn", "🤖 AI [P&L]",
                f"Down {pnl_pct:.0f}% (${net_pnl:,.0f}). Focus on quality — trim small "
                f"altcoin positions and consolidate into stronger assets."
            ))
        elif pnl_pct > 50:
            tips.append(("ok", "🤖 AI [P&L]",
                f"Excellent: +{pnl_pct:.0f}% (${net_pnl:+,.0f}). "
                f"Consider taking 10–15% profit into USDT to lock in gains and rebuild buffer."
            ))

    # ── Futures leverage ─────────────────────────────────────────────────────
    if futures_positions:
        notional = sum(
            abs(float(fp.get("positionAmt", 0))) * float(fp.get("markPrice", 0))
            for fp in futures_positions
        )
        notional_pct = notional / total * 100
        if notional_pct > 30:
            tips.append(("danger", "🤖 AI [Futures]",
                f"Futures notional ${notional:,.0f} ({notional_pct:.0f}% of portfolio). "
                f"High leverage amplifies losses. Reduce position sizes or add margin."
            ))
        elif notional_pct > 10:
            tips.append(("warn", "🤖 AI [Futures]",
                f"Futures notional ${notional:,.0f}. Monitor liquidation prices closely and "
                f"keep at least 2× margin buffer to avoid forced liquidation."
            ))

    # ── Risky altcoin ratio ──────────────────────────────────────────────────
    risky_value = sum(
        abs(pos.net_value)
        for asset, pos in snap.positions.items()
        if get_risk_level(asset) == "risky"
    )
    risky_pct = risky_value / total * 100
    if risky_pct > 40:
        tips.append(("danger", "🤖 AI [Altcoins]",
            f"Risky altcoins are {risky_pct:.0f}% of your portfolio (${risky_value:,.0f}). "
            f"In a bear market these can drop 70–90%. Target under 20% in speculative assets."
        ))
    elif risky_pct > 20:
        tips.append(("warn", "🤖 AI [Altcoins]",
            f"Risky altcoins at {risky_pct:.0f}%. Review each position — "
            f"exit coins with weak fundamentals or no upcoming catalysts."
        ))

    # ── Diversification ──────────────────────────────────────────────────────
    position_count = sum(1 for pos in snap.positions.values() if abs(pos.net_value) > 10)
    if position_count > 20:
        tips.append(("warn", "🤖 AI [Diversification]",
            f"You hold {position_count} positions. Over-diversification dilutes returns — "
            f"focus on your best 10–15 ideas."
        ))
    elif position_count < 4:
        tips.append(("warn", "🤖 AI [Diversification]",
            f"Only {position_count} positions — very concentrated. "
            f"Consider spreading across 5–10 assets in different sectors."
        ))

    # ── Healthy fallback ─────────────────────────────────────────────────────
    if health["grade"] in ("A", "B") and not tips:
        tips.append(("ok", "🤖 AI",
            f"Portfolio looks well-structured (Grade {health['grade']}). "
            f"Maintain your stable buffer and review positions monthly. "
            f"Consider setting take-profit orders on winners above +50%."
        ))

    return tips


# ─────────────────────────────────────────────────────────────────────────────
#  Sidebar — navigation
# ─────────────────────────────────────────────────────────────────────────────

has_api_key = bool(BINANCE_API_KEY and BINANCE_API_KEY != "your_api_key_here")

with st.sidebar:
    st.markdown("## 🧠 Portfolio Brain")
    st.divider()

    _nav_pages = ["📊 Dashboard", "📋 Tax Report", "⚙️ API Settings"]
    _cur_page  = st.session_state.get("_page", "dashboard")
    _nav_idx   = 2 if _cur_page == "settings" else (1 if _cur_page == "tax" else 0)
    nav_choice = st.radio(
        "Navigation",
        _nav_pages,
        label_visibility="collapsed",
        index=_nav_idx,
    )
    if nav_choice.startswith("⚙️"):
        st.session_state["_page"] = "settings"
    elif nav_choice.startswith("📋"):
        st.session_state["_page"] = "tax"
    else:
        st.session_state["_page"] = "dashboard"
    st.divider()

    if has_api_key:
        st.success("✅ API Key active")
    else:
        st.warning("⚠️ No API key")
    st.divider()

    refresh = st.button("🔄 Refresh Data", use_container_width=True)
    st.caption("Wallet: 60s cache\nTrades: 5 min cache")


# ─────────────────────────────────────────────────────────────────────────────
#  Page: Settings
# ─────────────────────────────────────────────────────────────────────────────

if st.session_state.get("_page") == "settings":
    _s_l, _s_r = st.columns([5, 1])
    with _s_l:
        st.markdown("## ⚙️ API Settings")
    with _s_r:
        if st.button("← Dashboard", key="_back_dash", use_container_width=True):
            st.session_state["_page"] = "dashboard"
            st.rerun()
    st.caption("Your keys are stored locally in `.env` and never sent anywhere else.")
    st.markdown("")

    # Welcome banner for first-run users
    if st.session_state.pop("_first_run", False):
        st.markdown(
            '<div class="alert-ok" style="font-size:13px;padding:14px 18px;margin-bottom:8px">'
            '<b>👋 Welcome to OpenClaw Portfolio Brain!</b><br>'
            'Add your Binance API key below to start analyzing your portfolio. '
            'It only takes 30 seconds.'
            '</div>',
            unsafe_allow_html=True,
        )
        st.markdown("")

    env        = read_env()
    cur_key    = env.get("BINANCE_API_KEY", "")
    cur_secret = env.get("BINANCE_SECRET_KEY", "")
    cur_groq = env.get("GROQ_API_KEY", "")

    # ── Binance credentials ──────────────────────────────────────────────────
    with st.form("api_form"):
        st.markdown("### 🔑 Binance API Credentials")
        st.markdown("""
        <div style='background:#1E2329;border:1px solid #2B3139;border-radius:10px;
                    padding:14px 18px;margin-bottom:16px;font-size:12px;color:#848E9C'>
        💡 Use a <b style='color:#F0B90B'>Read-Only</b> API key for safety.
        Go to
        <a href='https://www.binance.com/en/my/settings/api-management'
           target='_blank' style='color:#F0B90B'>Binance → API Management</a>
        and enable <b>Read Info</b> only.
        </div>
        """, unsafe_allow_html=True)

        new_key = st.text_input(
            "BINANCE_API_KEY",
            value=cur_key,
            type="password",
            placeholder="Paste your Binance API Key here",
        )
        new_secret = st.text_input(
            "BINANCE_SECRET_KEY",
            value=cur_secret,
            type="password",
            placeholder="Paste your Binance Secret Key here",
        )
        st.markdown("")
        submitted = st.form_submit_button("💾 Save Binance Keys", use_container_width=True, type="primary")

    if submitted:
        if new_key.strip() and new_secret.strip():
            try:
                write_env({
                    "BINANCE_API_KEY":    new_key.strip(),
                    "BINANCE_SECRET_KEY": new_secret.strip(),
                    "USE_MOCK_DATA":      "false",
                })
                # Reload env vars + modules so keys take effect in this process
                load_dotenv(override=True)
                importlib.reload(_src_config)
                importlib.reload(_src_fetcher)
                # Clear all caches + session, go to dashboard
                st.cache_data.clear()
                st.session_state.clear()
                st.session_state["_page"] = "dashboard"
                st.session_state["_keys_saved"] = True
                st.balloons()
                st.rerun()
            except Exception as exc:
                st.error(f"Failed to save: {exc}")
        else:
            st.warning("Both fields are required.")

    st.markdown("")

    # ── Groq AI credentials ───────────────────────────────────────────────────
    st.markdown("### 🤖 Groq API Key (for AI Chat)")
    with st.form("groq_form"):
        st.markdown("""
        <div style='background:#1E2329;border:1px solid #2B3139;border-radius:10px;
                    padding:14px 18px;margin-bottom:16px;font-size:12px;color:#848E9C'>
        Powers the <b style='color:#9945FF'>💬 AI Chat</b> on the dashboard.
        Get a free key at
        <a href='https://console.groq.com/keys'
           target='_blank' style='color:#F0B90B'>Groq Console → API Keys</a>
        (free tier: 30 req/min, 6000 tokens/min).
        </div>
        """, unsafe_allow_html=True)

        new_groq = st.text_input(
            "GROQ_API_KEY",
            value=cur_groq,
            type="password",
            placeholder="Paste your Groq API Key here",
        )
        st.markdown("")
        groq_submitted = st.form_submit_button("💾 Save Groq Key", use_container_width=True, type="primary")

    if groq_submitted:
        if new_groq.strip():
            try:
                write_env({"GROQ_API_KEY": new_groq.strip()})
                st.success("✅ Groq key saved! AI Chat is now active.")
                time.sleep(0.8)
                st.rerun()
            except Exception as exc:
                st.error(f"Failed to save: {exc}")
        else:
            st.warning("Please paste a Groq API key.")

    st.markdown("")

    # ── Tax Report Binance credentials ────────────────────────────────────────
    cur_tax_key    = env.get("TAX_BINANCE_API_KEY", "")
    cur_tax_secret = env.get("TAX_BINANCE_SECRET_KEY", "")

    st.markdown("### 📋 Tax Report API Key")
    with st.form("tax_api_form"):
        st.markdown("""
        <div style='background:#1E2329;border:1px solid #2B3139;border-radius:10px;
                    padding:14px 18px;margin-bottom:16px;font-size:12px;color:#848E9C'>
        💡 Use a separate <b style='color:#F0B90B'>Read-Only</b> API key for the Tax Report page.
        Leave blank to use the Dashboard key above.<br>
        Go to
        <a href='https://www.binance.com/en/my/settings/api-management'
           target='_blank' style='color:#F0B90B'>Binance → API Management</a>
        and create a new key with <b>Read Info</b> only.
        </div>
        """, unsafe_allow_html=True)

        new_tax_key = st.text_input(
            "TAX_BINANCE_API_KEY",
            value=cur_tax_key,
            type="password",
            placeholder="Paste Tax API Key (or leave blank)",
        )
        new_tax_secret = st.text_input(
            "TAX_BINANCE_SECRET_KEY",
            value=cur_tax_secret,
            type="password",
            placeholder="Paste Tax Secret Key (or leave blank)",
        )
        st.markdown("")
        tax_submitted = st.form_submit_button("💾 Save Tax Keys", use_container_width=True, type="primary")

    if tax_submitted:
        try:
            write_env({
                "TAX_BINANCE_API_KEY":    new_tax_key.strip(),
                "TAX_BINANCE_SECRET_KEY": new_tax_secret.strip(),
            })
            load_dotenv(override=True)
            st.success("✅ Tax API key saved to .env!")
            time.sleep(0.8)
            st.rerun()
        except Exception as exc:
            st.error(f"Failed to save: {exc}")

    st.markdown("")
    st.markdown("### 📋 Current Status")
    col_key, col_secret, col_groq, col_tax = st.columns(4)
    with col_key:
        if cur_key:
            st.markdown(
                f'<div class="card"><div class="kpi-label">Binance API Key</div>'
                f'<div class="kpi-value kpi-green" style="font-size:13px">'
                f'✅ Set ({cur_key[:8]}...)</div></div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<div class="card"><div class="kpi-label">Binance API Key</div>'
                '<div class="kpi-value kpi-red" style="font-size:13px">❌ Not set</div></div>',
                unsafe_allow_html=True,
            )
    with col_secret:
        if cur_secret:
            st.markdown(
                f'<div class="card"><div class="kpi-label">Binance Secret</div>'
                f'<div class="kpi-value kpi-green" style="font-size:13px">'
                f'✅ Set ({cur_secret[:4]}...)</div></div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<div class="card"><div class="kpi-label">Binance Secret</div>'
                '<div class="kpi-value kpi-red" style="font-size:13px">❌ Not set</div></div>',
                unsafe_allow_html=True,
            )
    with col_groq:
        if cur_groq:
            st.markdown(
                f'<div class="card"><div class="kpi-label">Groq AI Key</div>'
                f'<div class="kpi-value kpi-green" style="font-size:13px">'
                f'✅ Set ({cur_groq[:8]}...)</div></div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<div class="card"><div class="kpi-label">Groq AI Key</div>'
                '<div class="kpi-value" style="font-size:13px;color:#848E9C">⬜ Not set</div></div>',
                unsafe_allow_html=True,
            )
    with col_tax:
        if cur_tax_key:
            st.markdown(
                f'<div class="card"><div class="kpi-label">Tax API Key</div>'
                f'<div class="kpi-value kpi-green" style="font-size:13px">'
                f'✅ Set ({cur_tax_key[:8]}...)</div></div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<div class="card"><div class="kpi-label">Tax API Key</div>'
                '<div class="kpi-value" style="font-size:13px;color:#848E9C">⬜ Using Dashboard key</div></div>',
                unsafe_allow_html=True,
            )

    st.markdown("")
    st.divider()
    st.caption("OpenClaw Portfolio Brain · github.com/namtrung99/openclaw-portfolio-brain · #AIBinance")
    st.stop()


# ─────────────────────────────────────────────────────────────────────────────
#  Page: Tax Report  (loader must be defined before the page block)
# ─────────────────────────────────────────────────────────────────────────────

@st.cache_data(ttl=3600, show_spinner=False)
def load_tax_data(year: int) -> dict:
    """Fetch tax data for a given year using TAX_BINANCE_API_KEY only."""
    _env = read_env()
    api_k = _env.get("TAX_BINANCE_API_KEY", "").strip()
    sec_k = _env.get("TAX_BINANCE_SECRET_KEY", "").strip()
    if not api_k or not sec_k:
        return {"error": "TAX_BINANCE_API_KEY not configured. Go to ⚙️ Settings to add it."}
    return fetch_tax_data(year, api_key=api_k, secret_key=sec_k)


if st.session_state.get("_page") == "tax":
    _t_l, _t_r = st.columns([5, 1])
    with _t_l:
        st.markdown("## 📋 Tax Report")
        st.caption(
            "Summarises your Binance activity for a given calendar year: "
            "deposits, withdrawals, spot-to-spot converts and realised P&L from trade history."
        )
    with _t_r:
        if st.button("← Dashboard", key="_back_dash_tax", use_container_width=True):
            st.session_state["_page"] = "dashboard"
            st.rerun()

    st.divider()

    # ── Year selector ─────────────────────────────────────────────────────────
    _cur_year = datetime.datetime.utcnow().year
    _tax_col1, _tax_col2, _tax_col3 = st.columns([2, 3, 3])
    with _tax_col1:
        tax_year = st.selectbox(
            "📅 Tax Year",
            options=list(range(_cur_year, _cur_year - 5, -1)),
            index=0,
            key="_tax_year",
        )

    # ── Which key is being used ───────────────────────────────────────────────
    _env_tax = read_env()
    _tax_k = _env_tax.get("TAX_BINANCE_API_KEY", "")
    if _tax_k:
        st.info(f"🔑 Using dedicated Tax API key: `{_tax_k[:8]}...`  ·  Change in ⚙️ Settings")
    else:
        st.error("⚠️ TAX_BINANCE_API_KEY not set — go to ⚙️ Settings to add your Tax API key.")

    # ── Load / Fetch ──────────────────────────────────────────────────────────
    _tax_load_col, _tax_clear_col = st.columns([3, 1])
    with _tax_load_col:
        load_tax_btn = st.button(
            f"📥 Load {tax_year} Tax Data",
            use_container_width=True,
            type="primary",
            key="_load_tax_btn",
        )
    with _tax_clear_col:
        if st.button("🗑 Clear Cache", use_container_width=True, key="_clear_tax_cache"):
            load_tax_data.clear()
            st.success("Cache cleared.")

    # ── Trigger fetch ─────────────────────────────────────────────────────────
    _tax_state_key = f"_tax_data_{tax_year}"
    if load_tax_btn:
        with st.spinner(f"Fetching {tax_year} data from Binance… this may take 10–30 seconds."):
            try:
                _td = load_tax_data(tax_year)
                st.session_state[_tax_state_key] = _td
            except Exception as _e:
                st.error(f"❌ Failed to fetch tax data: {_e}")

    _tax_data: dict = st.session_state.get(_tax_state_key, {})

    if _tax_data.get("error"):
        st.error(f"❌ {_tax_data['error']}")
        st.stop()

    if not _tax_data:
        st.markdown(
            '<div style="background:#1E2329;border:1px solid #2B3139;border-radius:12px;'
            'padding:40px;text-align:center;color:#848E9C;margin-top:24px">'
            '<div style="font-size:32px;margin-bottom:12px">📋</div>'
            f'<b style="color:#F0B90B">Select a year and click "Load {tax_year} Tax Data"</b><br>'
            '<span style="font-size:12px">Data is cached for 1 hour per year</span>'
            '</div>',
            unsafe_allow_html=True,
        )
        st.stop()

    # ─────────────────────────────────────────────────────────────────────────
    #  Parse loaded data
    # ─────────────────────────────────────────────────────────────────────────
    _deps  = _tax_data.get("deposits",    [])
    _withs = _tax_data.get("withdrawals", [])
    _convs = _tax_data.get("converts",   [])
    _p2ps  = _tax_data.get("p2p",        [])
    _spots = _tax_data.get("spot_trades", [])

    # Build DataFrames
    def _ms_to_dt(ms):
        try:
            return datetime.datetime.utcfromtimestamp(int(ms) / 1000)
        except Exception:
            return None

    # Deposits
    _df_dep = pd.DataFrame(_deps) if _deps else pd.DataFrame(
        columns=["insertTime", "coin", "amount", "network", "status", "address", "txId"])
    if not _df_dep.empty:
        _df_dep["datetime"] = _df_dep["insertTime"].apply(_ms_to_dt)
        _df_dep["amount"]   = pd.to_numeric(_df_dep.get("amount", 0), errors="coerce").fillna(0)
        _df_dep = _df_dep.sort_values("datetime", ascending=False)

    # Withdrawals
    _df_wit = pd.DataFrame(_withs) if _withs else pd.DataFrame(
        columns=["applyTime", "coin", "amount", "transactionFee", "network", "status", "address", "txId"])
    if not _df_wit.empty:
        _df_wit["datetime"]       = _df_wit["applyTime"].apply(
            lambda x: datetime.datetime.utcfromtimestamp(x / 1000)
            if isinstance(x, (int, float)) else pd.to_datetime(x, errors="coerce")
        )
        _df_wit["amount"]         = pd.to_numeric(_df_wit.get("amount", 0),         errors="coerce").fillna(0)
        _df_wit["transactionFee"] = pd.to_numeric(_df_wit.get("transactionFee", 0), errors="coerce").fillna(0)
        _df_wit = _df_wit.sort_values("datetime", ascending=False)

    # Converts
    _df_conv = pd.DataFrame(_convs) if _convs else pd.DataFrame(
        columns=["createTime", "fromAsset", "fromAmount", "toAsset", "toAmount", "ratio", "orderStatus"])
    if not _df_conv.empty:
        _df_conv["datetime"]    = _df_conv["createTime"].apply(_ms_to_dt)
        _df_conv["fromAmount"]  = pd.to_numeric(_df_conv.get("fromAmount",  0), errors="coerce").fillna(0)
        _df_conv["toAmount"]    = pd.to_numeric(_df_conv.get("toAmount",    0), errors="coerce").fillna(0)
        _df_conv["ratio"]       = pd.to_numeric(_df_conv.get("ratio",       0), errors="coerce").fillna(0)
        _df_conv = _df_conv.sort_values("datetime", ascending=False)

    # ── Aggregate KPIs ────────────────────────────────────────────────────────
    _total_deposited  = _df_dep["amount"].sum()  if not _df_dep.empty  else 0.0
    _total_withdrawn  = _df_wit["amount"].sum()  if not _df_wit.empty  else 0.0
    _total_withdw_fee = _df_wit["transactionFee"].sum() if not _df_wit.empty else 0.0
    _n_dep   = len(_df_dep)
    _n_with  = len(_df_wit)
    _n_conv  = len(_df_conv)

    # P2P
    _df_p2p = pd.DataFrame(_p2ps) if _p2ps else pd.DataFrame()
    _n_p2p = len(_df_p2p)
    _p2p_buy_amt = 0.0
    _p2p_sell_amt = 0.0
    if not _df_p2p.empty:
        _df_p2p["totalPrice"] = pd.to_numeric(_df_p2p.get("totalPrice", 0), errors="coerce").fillna(0)
        _df_p2p["amount"]     = pd.to_numeric(_df_p2p.get("amount", 0), errors="coerce").fillna(0)
        _df_p2p["unitPrice"]  = pd.to_numeric(_df_p2p.get("unitPrice", 0), errors="coerce").fillna(0)
        _df_p2p["createTime"] = pd.to_numeric(_df_p2p.get("createTime", 0), errors="coerce")
        _df_p2p["datetime"]   = _df_p2p["createTime"].apply(
            lambda x: datetime.datetime.utcfromtimestamp(x / 1000) if x > 0 else None)
        for _, r in _df_p2p.iterrows():
            if r.get("_tradeType") == "BUY":
                _p2p_buy_amt += r["totalPrice"]
            else:
                _p2p_sell_amt += r["totalPrice"]

    # Spot trades
    _df_spot_tax = pd.DataFrame(_spots) if _spots else pd.DataFrame()
    _n_spot = len(_df_spot_tax)
    _spot_buy_total = 0.0
    _spot_sell_total = 0.0
    if not _df_spot_tax.empty:
        _df_spot_tax["quoteQty"] = pd.to_numeric(_df_spot_tax.get("quoteQty", 0), errors="coerce").fillna(0)
        _df_spot_tax["time_dt"]  = _df_spot_tax["time"].apply(
            lambda x: datetime.datetime.utcfromtimestamp(x / 1000) if x else None)
        for _, r in _df_spot_tax.iterrows():
            if r.get("isBuyer"):
                _spot_buy_total += r["quoteQty"]
            else:
                _spot_sell_total += r["quoteQty"]

    # Net flow
    _net_flow = _total_deposited - _total_withdrawn

    # ── KPI Cards — Row 1 ────────────────────────────────────────────────────
    st.markdown(f"### 📊 {tax_year} Summary")

    def _kpi(col, label, value, sub="", color="kpi-white"):
        col.markdown(
            f'<div class="card"><div class="kpi-label">{label}</div>'
            f'<div class="kpi-value {color}">{value}</div>'
            f'<div style="color:#848E9C;font-size:10px;margin-top:2px">{sub}</div></div>',
            unsafe_allow_html=True,
        )

    _k1, _k2, _k3, _k4 = st.columns(4)
    _kpi(_k1, "📥 Deposits",  f"{_n_dep} txns", f"across {_df_dep['coin'].nunique() if not _df_dep.empty else 0} coins", "kpi-green")
    _kpi(_k2, "📤 Withdrawals", f"{_n_with} txns", f"fees: ~${_total_withdw_fee:,.4f}", "kpi-red")
    _kpi(_k3, "🔄 Converts",  f"{_n_conv} swaps", "", "kpi-gold")
    _kpi(_k4, "🤝 P2P Trades", f"{_n_p2p} trades",
         f"Buy ${_p2p_buy_amt:,.0f} / Sell ${_p2p_sell_amt:,.0f}" if _n_p2p else "none",
         "kpi-gold" if _n_p2p else "")
    st.markdown("")

    # ── KPI Cards — Row 2 ────────────────────────────────────────────────────
    _k5, _k6, _k7, _k8 = st.columns(4)
    _kpi(_k5, "🛒 Spot Buys",  f"${_spot_buy_total:,.0f}", f"{sum(1 for _,r in _df_spot_tax.iterrows() if r.get('isBuyer')) if not _df_spot_tax.empty else 0} trades", "kpi-green")
    _kpi(_k6, "💰 Spot Sells", f"${_spot_sell_total:,.0f}", f"{sum(1 for _,r in _df_spot_tax.iterrows() if not r.get('isBuyer')) if not _df_spot_tax.empty else 0} trades", "kpi-red")
    _spot_net = _spot_sell_total - _spot_buy_total
    _kpi(_k7, "📊 Spot Net P&L (est.)", f"${_spot_net:+,.0f}", "sells - buys (USDT)", "kpi-green" if _spot_net >= 0 else "kpi-red")
    _kpi(_k8, "📈 Total Spot Trades", f"{_n_spot:,}", f"{_df_spot_tax['_symbol'].nunique() if not _df_spot_tax.empty and '_symbol' in _df_spot_tax.columns else 0} pairs")

    st.markdown("")
    st.markdown(
        '<div style="background:#1E2329;border:1px solid #2B3139;border-radius:10px;'
        'padding:12px 18px;font-size:12px;color:#848E9C;margin-bottom:8px">'
        '⚠️ <b style="color:#F0B90B">Disclaimer:</b> Amounts are shown in their native crypto units '
        '(not USD) unless Binance returns USDT/BUSD amounts. '
        'Consult a qualified tax professional for official reporting. '
        'This tool is for informational purposes only.'
        '</div>',
        unsafe_allow_html=True,
    )

    st.divider()

    # ── Deposits Table ────────────────────────────────────────────────────────
    with st.expander(f"📥 Deposits — {_n_dep} records", expanded=_n_dep > 0):
        if _df_dep.empty:
            st.info("No deposits found for this period.")
        else:
            _show_dep = _df_dep[["datetime", "coin", "amount", "network", "status", "txId"]].copy()
            _show_dep.columns = ["Date (UTC)", "Coin", "Amount", "Network", "Status", "TxID"]
            _show_dep["Date (UTC)"] = _show_dep["Date (UTC)"].astype(str)
            st.dataframe(_show_dep, use_container_width=True, hide_index=True)

            # Summary by coin
            _dep_by_coin = (
                _df_dep.groupby("coin")["amount"]
                .agg(["sum", "count"])
                .reset_index()
                .rename(columns={"coin": "Coin", "sum": "Total Amount", "count": "Txns"})
                .sort_values("Total Amount", ascending=False)
            )
            st.markdown("**By Coin:**")
            st.dataframe(_dep_by_coin, use_container_width=True, hide_index=True)

            st.download_button(
                "⬇️ Export Deposits CSV",
                data=_show_dep.to_csv(index=False).encode(),
                file_name=f"deposits_{tax_year}.csv",
                mime="text/csv",
            )

    # ── Withdrawals Table ─────────────────────────────────────────────────────
    with st.expander(f"📤 Withdrawals — {_n_with} records", expanded=_n_with > 0):
        if _df_wit.empty:
            st.info("No withdrawals found for this period.")
        else:
            _show_wit = _df_wit[["datetime", "coin", "amount", "transactionFee", "network", "status", "txId"]].copy()
            _show_wit.columns = ["Date (UTC)", "Coin", "Amount", "Fee", "Network", "Status", "TxID"]
            _show_wit["Date (UTC)"] = _show_wit["Date (UTC)"].astype(str)
            st.dataframe(_show_wit, use_container_width=True, hide_index=True)

            _wit_by_coin = (
                _df_wit.groupby("coin")
                .agg(total_amount=("amount", "sum"), total_fee=("transactionFee", "sum"), txns=("amount", "count"))
                .reset_index()
                .rename(columns={"coin": "Coin", "total_amount": "Total Amount", "total_fee": "Total Fees", "txns": "Txns"})
                .sort_values("Total Amount", ascending=False)
            )
            st.markdown("**By Coin:**")
            st.dataframe(_wit_by_coin, use_container_width=True, hide_index=True)

            st.download_button(
                "⬇️ Export Withdrawals CSV",
                data=_show_wit.to_csv(index=False).encode(),
                file_name=f"withdrawals_{tax_year}.csv",
                mime="text/csv",
            )

    # ── Converts Table ────────────────────────────────────────────────────────
    with st.expander(f"🔄 Converts / Swaps — {_n_conv} records", expanded=_n_conv > 0):
        if _df_conv.empty:
            st.info("No convert trades found for this period.")
        else:
            _cols_conv = [c for c in ["datetime", "fromAsset", "fromAmount", "toAsset", "toAmount", "ratio", "orderStatus"] if c in _df_conv.columns]
            _show_conv = _df_conv[_cols_conv].copy()
            _show_conv.columns = [{"datetime": "Date (UTC)", "fromAsset": "From", "fromAmount": "From Amt",
                                    "toAsset": "To", "toAmount": "To Amt", "ratio": "Rate",
                                    "orderStatus": "Status"}.get(c, c) for c in _cols_conv]
            _show_conv["Date (UTC)"] = _show_conv["Date (UTC)"].astype(str)
            st.dataframe(_show_conv, use_container_width=True, hide_index=True)

            st.download_button(
                "⬇️ Export Converts CSV",
                data=_show_conv.to_csv(index=False).encode(),
                file_name=f"converts_{tax_year}.csv",
                mime="text/csv",
            )

    # ── P2P Trades Table ──────────────────────────────────────────────────────
    with st.expander(f"🤝 P2P Trades — {_n_p2p} records", expanded=_n_p2p > 0):
        if _df_p2p.empty:
            st.info("No P2P trades found for this period.")
        else:
            _p2p_cols = []
            for c in ["datetime", "_tradeType", "asset", "amount", "unitPrice", "totalPrice", "fiat", "counterPartNickName", "orderStatus"]:
                if c in _df_p2p.columns:
                    _p2p_cols.append(c)
            _show_p2p = _df_p2p[_p2p_cols].copy() if _p2p_cols else _df_p2p.copy()
            _col_map = {"datetime": "Date (UTC)", "_tradeType": "Side", "asset": "Crypto",
                        "amount": "Amount", "unitPrice": "Price", "totalPrice": "Total (Fiat)",
                        "fiat": "Fiat", "counterPartNickName": "Counterparty", "orderStatus": "Status"}
            _show_p2p.columns = [_col_map.get(c, c) for c in _show_p2p.columns]
            if "Date (UTC)" in _show_p2p.columns:
                _show_p2p["Date (UTC)"] = _show_p2p["Date (UTC)"].astype(str)
            st.dataframe(_show_p2p, use_container_width=True, hide_index=True)
            st.download_button(
                "⬇️ Export P2P CSV",
                data=_show_p2p.to_csv(index=False).encode(),
                file_name=f"p2p_{tax_year}.csv",
                mime="text/csv",
            )

    # ── Spot Trade History Table ──────────────────────────────────────────────
    with st.expander(f"🛒 Spot Trade History — {_n_spot} trades", expanded=_n_spot > 0):
        if _df_spot_tax.empty:
            st.info("No spot trades found for this period.")
        else:
            _spot_rows = []
            for _, t in _df_spot_tax.iterrows():
                _spot_rows.append({
                    "Date (UTC)": t["time_dt"].strftime("%Y-%m-%d %H:%M") if t.get("time_dt") else "—",
                    "Pair":       t.get("_symbol", "?"),
                    "Side":       "BUY" if t.get("isBuyer") else "SELL",
                    "Qty":        f"{float(t.get('qty', 0)):.6f}",
                    "Price":      f"${float(t.get('price', 0)):,.6f}",
                    "Total":      f"${float(t.get('quoteQty', 0)):,.2f}",
                    "Fee":        f"{float(t.get('commission', 0)):.6f} {t.get('commissionAsset', '')}",
                })
            _df_spot_show = pd.DataFrame(_spot_rows)
            st.dataframe(
                _df_spot_show.style.map(
                    lambda v: "color:#0ECB81;font-weight:600" if v == "BUY"
                    else ("color:#F6465D;font-weight:600" if v == "SELL" else ""),
                    subset=["Side"]),
                use_container_width=True, hide_index=True,
                height=min(35 + len(_spot_rows) * 35, 500),
            )

            # Summary by pair
            _spot_by_pair = (
                _df_spot_tax.groupby("_symbol")["quoteQty"]
                .agg(["sum", "count"])
                .reset_index()
                .rename(columns={"_symbol": "Pair", "sum": "Total Volume (USDT)", "count": "Trades"})
                .sort_values("Total Volume (USDT)", ascending=False)
            )
            st.markdown("**By Pair:**")
            st.dataframe(_spot_by_pair, use_container_width=True, hide_index=True)

            st.download_button(
                "⬇️ Export Spot Trades CSV",
                data=_df_spot_show.to_csv(index=False).encode(),
                file_name=f"spot_trades_{tax_year}.csv",
                mime="text/csv",
            )

    # ── Timeline chart ────────────────────────────────────────────────────────
    _events = []
    for _, row in _df_dep.iterrows():
        _events.append({"date": row["datetime"], "type": "Deposit",  "coin": row.get("coin","?"), "amount": row["amount"]})
    for _, row in _df_wit.iterrows():
        _events.append({"date": row["datetime"], "type": "Withdraw", "coin": row.get("coin","?"), "amount": -row["amount"]})

    if _events:
        _df_events = pd.DataFrame(_events).dropna(subset=["date"])
        _df_events["month"] = _df_events["date"].dt.to_period("M").astype(str)
        _monthly = _df_events.groupby(["month", "type"])["amount"].sum().reset_index()

        _fig_tl = px.bar(
            _monthly,
            x="month", y="amount", color="type",
            color_discrete_map={"Deposit": "#0ECB81", "Withdraw": "#F6465D"},
            barmode="relative",
            title=f"{tax_year} Monthly Deposit / Withdrawal Flow",
            labels={"month": "Month", "amount": "Net Amount (native units)", "type": ""},
        )
        _fig_tl.update_layout(
            plot_bgcolor="#181A20", paper_bgcolor="#181A20",
            font_color="#EAECEF", title_font_color="#F0B90B",
            legend=dict(bgcolor="#1E2329"),
        )
        st.plotly_chart(_fig_tl, use_container_width=True)

    st.divider()
    st.caption("OpenClaw Portfolio Brain · Tax data sourced from Binance API · For reference only")
    st.stop()


# ─────────────────────────────────────────────────────────────────────────────
#  Cached data loaders
# ─────────────────────────────────────────────────────────────────────────────

@st.cache_data(ttl=60, show_spinner=False)
def load_wallet(use_mock: bool) -> tuple:
    raw  = fetch_portfolio(use_mock=use_mock)
    snap = aggregate(raw, policy=DEFAULT_POLICY)
    plan = generate_plan(snap, policy=DEFAULT_POLICY)
    return raw, snap, plan


@st.cache_data(ttl=300, show_spinner=False)
def load_trades(assets_key: str, prices_key: str, use_mock: bool) -> dict:
    return fetch_cost_basis(
        json.loads(assets_key),
        json.loads(prices_key),
        use_mock=use_mock,
    )


# ─────────────────────────────────────────────────────────────────────────────
#  Session state management
# ─────────────────────────────────────────────────────────────────────────────

USE_MOCK = False  # always real API when key is present

# First run without API key → redirect to settings with welcome banner
if not has_api_key and "snap" not in st.session_state:
    st.session_state["_first_run"] = True
    st.session_state["_page"] = "settings"
    st.rerun()

# Reset session when switching data modes (shouldn't happen, but guard it)
if st.session_state.get("_data_mode") != USE_MOCK:
    st.session_state.clear()
    st.session_state["_data_mode"] = USE_MOCK

# Auto-refresh every 60 seconds
now  = time.time()
last = st.session_state.get("_loaded_at", now)
if now - last >= 60 and "snap" in st.session_state and not refresh:
    load_wallet.clear()
    st.session_state.pop("snap", None)
    st.rerun()

# Load wallet on first run or manual refresh
if "snap" not in st.session_state or refresh:
    with st.spinner("Loading wallet data..."):
        try:
            raw, snap, plan = load_wallet(USE_MOCK)
            st.session_state.update({
                "raw":        raw,
                "snap":       snap,
                "plan":       plan,
                "trades":     None,
                "_err":       None,
                "_loaded_at": time.time(),
            })
        except Exception as exc:
            st.session_state["_err"] = str(exc)

if st.session_state.get("_err"):
    st.error(f"❌ API Error: {st.session_state['_err']}")
    st.info("👉 Go to **⚙️ API Settings** in the sidebar to configure your Binance API keys.")
    st.stop()

raw  = st.session_state["raw"]
snap = st.session_state["snap"]
plan = st.session_state["plan"]
loaded_at = datetime.datetime.fromtimestamp(
    st.session_state.get("_loaded_at", now)
).strftime("%H:%M:%S")


# ─────────────────────────────────────────────────────────────────────────────
#  Page: Dashboard header
# ─────────────────────────────────────────────────────────────────────────────

if st.session_state.pop("_keys_saved", False):
    st.success("✅ API keys saved and loaded — showing your live portfolio!")

st.markdown("## 🧠 Portfolio Brain — Wallet Overview")
st.caption(f"Binance Spot · Futures · Earn  |  Live API  |  {loaded_at}  |  auto-refresh 60s")

# Quick-nav shortcut row
_hdr_l, _hdr_tax, _hdr_r = st.columns([5, 1, 1])
with _hdr_tax:
    if st.button("📋 Tax Report", key="_goto_tax", use_container_width=True):
        st.session_state["_page"] = "tax"
        st.rerun()
with _hdr_r:
    if st.button("⚙️ Settings", key="_goto_settings", use_container_width=True):
        st.session_state["_page"] = "settings"
        st.rerun()
st.markdown("")


# ─────────────────────────────────────────────────────────────────────────────
#  Section: Wallet breakdown (4 KPI cards)
# ─────────────────────────────────────────────────────────────────────────────

total_val    = snap.total_equity_usdt
earn_val     = snap.earn_equity_usdt + snap.auto_invest_equity_usdt  # includes auto-invest (Binance counts it in Earn)
stable_val   = sum(abs(pos.net_value) for asset, pos in snap.positions.items() if asset in STABLE_COINS)
coin_val     = max(0.0, total_val - stable_val)

col_cash, col_coins, col_earn, col_total = st.columns(4)
_pct = lambda v: f"{v / total_val * 100:.1f}%" if total_val else "—"
render_kpi(col_cash,  "💵 Cash",            f"${stable_val:,.0f}", f"USDT & stables · {_pct(stable_val)}")
render_kpi(col_coins, "🪙 Coins",           f"${coin_val:,.0f}",   f"non-stable holdings · {_pct(coin_val)}")
render_kpi(col_earn,  "🏦 Earn",            f"${earn_val:,.0f}",   f"staking & earn · {_pct(earn_val)}")
render_kpi(col_total, "🏆 Total Portfolio", f"${total_val:,.0f}",  "all Binance accounts", "kpi-gold")
st.markdown("")


# ─────────────────────────────────────────────────────────────────────────────
#  Load trade history (non-blocking — renders after wallet cards)
# ─────────────────────────────────────────────────────────────────────────────

if st.session_state.get("trades") is None:
    placeholder = st.empty()
    with placeholder, st.spinner("Fetching trade history in background..."):
        assets_key = json.dumps(sorted(snap.positions.keys()))
        prices_key = json.dumps({a: p.price_usdt for a, p in snap.positions.items()})
        trades_data = load_trades(assets_key, prices_key, USE_MOCK)
        st.session_state["trades"] = trades_data
    placeholder.empty()
else:
    trades_data = st.session_state["trades"]

per_asset_cb = {k: v for k, v in trades_data.items() if k != "__summary__"} if trades_data else {}
cb_summary   = (trades_data.get("__summary__") or {}) if trades_data else {}


# ─────────────────────────────────────────────────────────────────────────────
#  Section: Trade summary
# ─────────────────────────────────────────────────────────────────────────────

if cb_summary.get("total_spent", 0) > 0:
    render_section("📈 Trade Summary — From Account Inception")

    total_spent    = cb_summary.get("total_spent", 0)
    total_received = cb_summary.get("total_received", 0)
    realized_pnl   = cb_summary.get("realized_pnl", 0)
    unrealized_pnl = cb_summary.get("unrealized_pnl", 0)
    net_pnl        = cb_summary.get("net_pnl", 0)

    c1, c2, c3, c4, c5 = st.columns(5)
    render_kpi(c1, "Total Spent",    f"${total_spent:,.0f}",    "all spot buys")
    render_kpi(c2, "Total Received", f"${total_received:,.0f}", "all spot sells")
    render_kpi(c3, "Realized P&L",   f"${realized_pnl:+,.0f}", "locked in from sells",   pnl_color(realized_pnl))
    render_kpi(c4, "Unrealized P&L", f"${unrealized_pnl:+,.0f}", "current vs cost basis", pnl_color(unrealized_pnl))
    render_kpi(c5, "Net P&L",        f"${net_pnl:+,.0f}",      "= realized + unrealized", pnl_color(net_pnl))
    st.markdown("")

    # ── Spot Trader Analytics ─────────────────────────────────────────────────
    render_section("📊 Spot Trader Analytics")

    # --- Compute per-asset metrics ---
    winners = []       # assets with positive total P&L
    losers = []        # assets with negative total P&L
    total_fees_usdt = 0.0
    total_trade_count = 0
    total_buy_count = 0
    total_sell_count = 0
    gross_profit = 0.0    # sum of all positive per-asset P&L
    gross_loss = 0.0      # sum of all negative per-asset P&L (absolute)

    for asset, cb in per_asset_cb.items():
        if not cb.get("trades"):
            continue
        trades_list = cb["trades"]
        asset_pnl = cb.get("realized_pnl", 0) + cb.get("unrealized_pnl", 0)
        n_trades = len(trades_list)
        n_buys = sum(1 for t in trades_list if t.get("isBuyer"))
        n_sells = n_trades - n_buys
        total_trade_count += n_trades
        total_buy_count += n_buys
        total_sell_count += n_sells

        # Fee calculation
        for t in trades_list:
            comm = float(t.get("commission", 0))
            comm_asset = t.get("commissionAsset", "")
            if comm_asset == "USDT":
                total_fees_usdt += comm
            else:
                price_map = {a: p.price_usdt for a, p in snap.positions.items()}
                total_fees_usdt += comm * price_map.get(comm_asset, 0)

        if asset_pnl > 0:
            winners.append({"asset": asset, "pnl": asset_pnl,
                            "invested": cb.get("total_invested", 0),
                            "realized": cb.get("realized_pnl", 0),
                            "unrealized": cb.get("unrealized_pnl", 0)})
            gross_profit += asset_pnl
        elif asset_pnl < 0:
            losers.append({"asset": asset, "pnl": asset_pnl,
                           "invested": cb.get("total_invested", 0),
                           "realized": cb.get("realized_pnl", 0),
                           "unrealized": cb.get("unrealized_pnl", 0)})
            gross_loss += abs(asset_pnl)

    # Sort
    winners.sort(key=lambda x: x["pnl"], reverse=True)
    losers.sort(key=lambda x: x["pnl"])

    total_assets_traded = len([a for a in per_asset_cb if per_asset_cb[a].get("trades")])
    win_count = len(winners)
    loss_count = len(losers)
    win_rate = (win_count / total_assets_traded * 100) if total_assets_traded > 0 else 0
    avg_win = (gross_profit / win_count) if win_count > 0 else 0
    avg_loss = (gross_loss / loss_count) if loss_count > 0 else 0
    profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else float("inf") if gross_profit > 0 else 0
    roi_pct = (net_pnl / total_spent * 100) if total_spent > 0 else 0
    fee_pct = (total_fees_usdt / total_spent * 100) if total_spent > 0 else 0

    # Row 1: Win Rate, ROI, Profit Factor, Fee Impact
    r1c1, r1c2, r1c3, r1c4 = st.columns(4)
    render_kpi(r1c1, "Win Rate",
               f"{win_rate:.0f}%",
               f"{win_count}W / {loss_count}L of {total_assets_traded} coins",
               "kpi-green" if win_rate >= 50 else "kpi-red")
    render_kpi(r1c2, "Overall ROI",
               f"{roi_pct:+.1f}%",
               f"net P&L / total spent",
               pnl_color(roi_pct))
    render_kpi(r1c3, "Profit Factor",
               f"{profit_factor:.2f}" if profit_factor != float("inf") else "INF",
               f"gross profit / gross loss",
               "kpi-green" if profit_factor >= 1.5 else ("kpi-gold" if profit_factor >= 1.0 else "kpi-red"))
    render_kpi(r1c4, "Total Fees Paid",
               f"${total_fees_usdt:,.0f}",
               f"{fee_pct:.2f}% of spent",
               "kpi-red" if fee_pct > 1 else "")
    st.markdown("")

    # Row 2: Avg Win, Avg Loss, Total Trades, Best Performer
    r2c1, r2c2, r2c3, r2c4 = st.columns(4)
    render_kpi(r2c1, "Avg Win",
               f"${avg_win:,.0f}",
               f"per winning coin",
               "kpi-green")
    render_kpi(r2c2, "Avg Loss",
               f"${avg_loss:,.0f}",
               f"per losing coin",
               "kpi-red")
    render_kpi(r2c3, "Total Trades",
               f"{total_trade_count:,}",
               f"{total_buy_count} buys / {total_sell_count} sells")
    best = winners[0] if winners else None
    worst = losers[0] if losers else None
    render_kpi(r2c4, "Best Performer",
               f"{best['asset']} +${best['pnl']:,.0f}" if best else "N/A",
               f"top gainer",
               "kpi-green" if best else "")
    st.markdown("")

    # Top Winners & Losers tables (side by side, balanced)
    if winners or losers:
        _tbl_height = max(len(winners), len(losers))
        _tbl_height = min(35 + _tbl_height * 35, 500)

        tw_col, tl_col = st.columns(2, gap="large")

        with tw_col:
            st.markdown(
                f'<div style="display:flex;justify-content:space-between;align-items:baseline;margin-bottom:6px">'
                f'<span style="color:#0ECB81;font-size:12px;font-weight:700;letter-spacing:.5px">'
                f'TOP WINNERS ({win_count})</span>'
                f'<span style="color:#0ECB81;font-size:12px;font-weight:600">'
                f'Gross: ${gross_profit:+,.2f}</span></div>',
                unsafe_allow_html=True,
            )
            win_rows = []
            for w in winners:
                inv = w["invested"]
                roi = (w["pnl"] / inv * 100) if inv > 0 else 0
                win_rows.append({
                    "Asset": w["asset"],
                    "P&L": f"${w['pnl']:+,.2f}",
                    "ROI": f"{roi:+.1f}%",
                    "Realized": f"${w['realized']:+,.2f}",
                    "Unrealized": f"${w['unrealized']:+,.2f}",
                })
            if win_rows:
                st.dataframe(
                    pd.DataFrame(win_rows).style
                        .map(lambda v: "color:#0ECB81" if isinstance(v, str) and "+" in v else "", subset=["P&L", "ROI"]),
                    use_container_width=True, hide_index=True, height=_tbl_height,
                )
            else:
                st.caption("No winning positions yet")

        with tl_col:
            st.markdown(
                f'<div style="display:flex;justify-content:space-between;align-items:baseline;margin-bottom:6px">'
                f'<span style="color:#F6465D;font-size:12px;font-weight:700;letter-spacing:.5px">'
                f'TOP LOSERS ({loss_count})</span>'
                f'<span style="color:#F6465D;font-size:12px;font-weight:600">'
                f'Gross: ${-gross_loss:+,.2f}</span></div>',
                unsafe_allow_html=True,
            )
            loss_rows = []
            for l in losers:
                inv = l["invested"]
                roi = (l["pnl"] / inv * 100) if inv > 0 else 0
                loss_rows.append({
                    "Asset": l["asset"],
                    "P&L": f"${l['pnl']:+,.2f}",
                    "ROI": f"{roi:+.1f}%",
                    "Realized": f"${l['realized']:+,.2f}",
                    "Unrealized": f"${l['unrealized']:+,.2f}",
                })
            if loss_rows:
                st.dataframe(
                    pd.DataFrame(loss_rows).style
                        .map(lambda v: "color:#F6465D" if isinstance(v, str) and "-" in v else "", subset=["P&L", "ROI"]),
                    use_container_width=True, hide_index=True, height=_tbl_height,
                )
            else:
                st.caption("No losing positions — impressive!")

    st.markdown("")


# ─────────────────────────────────────────────────────────────────────────────
#  Section: AI Health Score  +  Risk distribution + Allocation pie
# ─────────────────────────────────────────────────────────────────────────────

health = compute_health_score(snap, cb_summary)
col_left, col_right = st.columns(2, gap="large")

with col_left:
    render_section("🤖 AI Portfolio Health Score")

    gauge = go.Figure(go.Indicator(
        mode="gauge+number",
        value=health["score"],
        number={"suffix": "/100", "font": {"color": health["color"], "size": 36}},
        gauge={
            "axis":    {"range": [0, 100], "tickcolor": "#848E9C", "tickfont": {"color": "#848E9C", "size": 9}},
            "bar":     {"color": health["color"], "thickness": 0.28},
            "bgcolor": "#1E2329",
            "bordercolor": "#2B3139",
            "steps": [
                {"range": [0,  35], "color": "rgba(246,70,93,0.09)"},
                {"range": [35, 55], "color": "rgba(255,140,0,0.09)"},
                {"range": [55, 75], "color": "rgba(240,185,11,0.09)"},
                {"range": [75,100], "color": "rgba(14,203,129,0.09)"},
            ],
        },
        title={
            "text": (
                f'<span style="color:{health["color"]};font-size:17px;font-weight:700">'
                f'Grade {health["grade"]} — {health["label"]}</span>'
            ),
            "font": {"color": "#EAECEF"},
        },
    ))
    gauge.update_layout(
        paper_bgcolor="#1E2329",
        height=200,
        margin=dict(t=30, b=5, l=15, r=15),
    )
    st.plotly_chart(gauge, use_container_width=True)

    st.markdown('<div class="ai-box">', unsafe_allow_html=True)
    st.markdown('<span class="ai-tag">🤖 AI ANALYSIS</span>', unsafe_allow_html=True)
    for icon, message in health["tips"]:
        st.markdown(
            f"<div style='font-size:12px;margin:4px 0;color:#EAECEF'>{icon} {message}</div>",
            unsafe_allow_html=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)

with col_right:
    render_section("📊 Risk Distribution")

    safe_val = medium_val = risky_val = 0.0
    safe_cnt = medium_cnt = risky_cnt = 0
    for asset, pos in snap.positions.items():
        if abs(pos.net_value) < 0.5:
            continue
        risk = get_risk_level(asset)
        if risk == "safe":
            safe_val += abs(pos.net_value); safe_cnt += 1
        elif risk == "medium":
            medium_val += abs(pos.net_value); medium_cnt += 1
        else:
            risky_val += abs(pos.net_value); risky_cnt += 1

    rc1, rc2, rc3 = st.columns(3)
    _rpct = lambda v: f"{v / total_val * 100:.0f}%" if total_val else "—"
    render_kpi(rc1, "Safe",   f"${safe_val:,.0f}",   f"{_rpct(safe_val)} · {safe_cnt} coins",   "kpi-green")
    render_kpi(rc2, "Medium", f"${medium_val:,.0f}",  f"{_rpct(medium_val)} · {medium_cnt} coins", "kpi-gold")
    render_kpi(rc3, "Risky",  f"${risky_val:,.0f}",  f"{_rpct(risky_val)} · {risky_cnt} coins",
               "kpi-red" if (total_val and risky_val > total_val * 0.2) else "")
    st.markdown("")

    render_section("🥧 Allocation", color="#848E9C")
    alloc_rows = [
        {"Asset": asset, "Value": round(abs(pos.net_value), 2)}
        for asset, pos in snap.positions.items()
        if abs(pos.net_value) > 5
    ]
    if alloc_rows:
        df_alloc = pd.DataFrame(alloc_rows).sort_values("Value", ascending=False)
        if total_val:
            major = df_alloc[df_alloc["Value"] / total_val * 100 >= 1.5]
            minor = df_alloc[df_alloc["Value"] / total_val * 100 <  1.5]
        else:
            major = df_alloc
            minor = pd.DataFrame()
        if not minor.empty:
            df_alloc = pd.concat(
                [major, pd.DataFrame([{"Asset": "Others", "Value": minor["Value"].sum()}])],
                ignore_index=True,
            )
        else:
            df_alloc = major

        pie = px.pie(
            df_alloc, names="Asset", values="Value", hole=0.45,
            color_discrete_sequence=PIE_COLORS,
        )
        pie.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", font_color="#EAECEF",
            margin=dict(t=0, b=0, l=0, r=0), height=195,
            legend=dict(font=dict(size=10, color="#EAECEF"), bgcolor="rgba(0,0,0,0)"),
        )
        pie.update_traces(textfont_color="#0B0E11", textfont_size=10)
        st.plotly_chart(pie, use_container_width=True)


# ─────────────────────────────────────────────────────────────────────────────
#  Section: Full asset table
# ─────────────────────────────────────────────────────────────────────────────

render_section("🗂 All Assets")

table_rows = []
for asset, pos in sorted(snap.positions.items(), key=lambda x: -abs(x[1].net_value)):
    if abs(pos.net_value) < 0.5:
        continue

    risk_label = RISK_LABELS.get(get_risk_level(asset), "Risky")

    futures_str = "—"
    if pos.futures_long > 0:
        futures_str = f"+{pos.futures_long:.4f} L"
    elif pos.futures_short > 0:
        futures_str = f"-{pos.futures_short:.4f} S"

    cb = per_asset_cb.get(asset)
    if cb and cb.get("avg_cost"):
        avg_buy  = f"${cb['avg_cost']:,.4f}"
        invested = cb["total_invested"]
        upnl     = cb["unrealized_pnl"]
        pnl_str  = f"${upnl:+,.2f} ({upnl / invested * 100:+.1f}%)" if invested > 0 else "—"
    else:
        avg_buy = pnl_str = "—"

    table_rows.append({
        "Asset":   asset,
        "Risk":    risk_label,
        "Qty":     f"{pos.net_qty:.4f}",
        "Price":   f"${pos.price_usdt:,.2f}",
        "Value":   f"${abs(pos.net_value):,.2f}",
        "% Port":  f"{snap.allocation_pct.get(asset, 0):.1f}%",
        "Avg Buy": avg_buy,
        "P&L":     pnl_str,
        "Spot":    f"{pos.spot_qty:.4f}" if pos.spot_qty > 0 else "—",
        "Earn":    f"{pos.earn_qty:.4f}" if pos.earn_qty > 0 else "—",
        "Futures": futures_str,
    })

RISK_STYLE = {"Safe": "color:#0ECB81;font-weight:600", "Medium": "color:#F0B90B;font-weight:600"}

st.dataframe(
    pd.DataFrame(table_rows).style
        .map(lambda v: RISK_STYLE.get(v, "color:#F6465D;font-weight:600"), subset=["Risk"])
        .map(lambda v: "color:#0ECB81" if isinstance(v, str) and "$+" in v
             else ("color:#F6465D" if isinstance(v, str) and "$-" in v else ""),
             subset=["P&L"]),
    use_container_width=True,
    hide_index=True,
    height=360,
)


# ─────────────────────────────────────────────────────────────────────────────
#  Section: Futures open positions
# ─────────────────────────────────────────────────────────────────────────────

fut_open = [
    fp for fp in raw.get("futures_positions", [])
    if abs(float(fp.get("positionAmt", 0))) > 0
]

if fut_open:
    render_section("📈 Futures Open Positions", color="#9945FF")

    futures_rows      = []
    total_notional    = 0.0
    total_futures_pnl = 0.0

    for fp in sorted(fut_open, key=lambda x: abs(float(x.get("unRealizedProfit", 0))), reverse=True):
        symbol    = fp["symbol"]
        base      = symbol[:-4] if symbol.endswith("USDT") else symbol
        qty       = float(fp["positionAmt"])
        mark      = float(fp.get("markPrice", 0))
        entry     = float(fp.get("entryPrice", 0))
        upnl      = float(fp.get("unRealizedProfit", fp.get("unrealizedProfit", 0)))
        liq       = float(fp.get("liquidationPrice", 0))
        notional  = abs(qty) * mark
        pnl_pct   = (upnl / (abs(qty) * entry) * 100) if entry > 0 else 0

        total_notional    += notional
        total_futures_pnl += upnl

        futures_rows.append({
            "Asset":    base,
            "Side":     "Long 🟢" if qty > 0 else "Short 🔴",
            "Qty":      f"{abs(qty):.4f}",
            "Entry":    f"${entry:,.4f}",
            "Mark":     f"${mark:,.4f}",
            "Notional": f"${notional:,.2f}",
            "P&L":      f"${upnl:+,.2f} ({pnl_pct:+.1f}%)",
            "Liq":      f"${liq:,.4f}" if liq > 0.01 else "—",
            "Lev":      f"{fp.get('leverage', '—')}×",
        })

    fc1, fc2, fc3 = st.columns(3)
    render_kpi(fc1, "Positions",   str(len(futures_rows)), "open")
    render_kpi(fc2, "Notional",    f"${total_notional:,.2f}", "total exposure")
    render_kpi(fc3, "Futures P&L", f"${total_futures_pnl:+,.2f}", "unrealized", pnl_color(total_futures_pnl))
    st.markdown("")

    st.dataframe(
        pd.DataFrame(futures_rows).style
            .map(lambda v: "color:#0ECB81;font-weight:600" if "Long" in str(v)
                 else ("color:#F6465D;font-weight:600" if "Short" in str(v) else ""),
                 subset=["Side"])
            .map(lambda v: "color:#0ECB81" if isinstance(v, str) and "$+" in v
                 else ("color:#F6465D" if isinstance(v, str) and "$-" in v else ""),
                 subset=["P&L"]),
        use_container_width=True,
        hide_index=True,
    )


# ─────────────────────────────────────────────────────────────────────────────
#  Section: Binance Alpha holdings (Alpha-only, excludes graduated coins)
# ─────────────────────────────────────────────────────────────────────────────

spot_listed  = raw.get("spot_listed", set())
alpha_rows   = []

for asset, pos in sorted(snap.positions.items(), key=lambda x: -abs(x[1].net_value)):
    if asset not in BINANCE_ALPHA_COINS or abs(pos.net_value) < 0.1:
        continue
    if spot_listed and asset in spot_listed:
        continue  # graduated to regular spot — skip

    cb = per_asset_cb.get(asset)
    avg_buy = invested_str = pnl_str = "—"
    if cb and cb.get("total_invested"):
        invested   = cb["total_invested"]
        upnl       = cb["unrealized_pnl"]
        avg_buy    = f"${cb['avg_cost']:,.4f}"
        invested_str = f"${invested:,.1f}"
        pnl_str    = f"${upnl:+,.2f} ({upnl / invested * 100:+.1f}%)"

    alpha_rows.append({
        "Asset":    asset,
        "Risk":     RISK_LABELS.get(get_risk_level(asset), "Risky"),
        "Qty":      f"{pos.net_qty:.4f}",
        "Price":    f"${pos.price_usdt:,.4f}",
        "Value":    f"${abs(pos.net_value):,.2f}",
        "% Port":   f"{snap.allocation_pct.get(asset, 0):.1f}%",
        "Avg Buy":  avg_buy,
        "Invested": invested_str,
        "P&L":      pnl_str,
    })

if alpha_rows:
    render_section("🔶 Binance Alpha Holdings — Alpha Only")

    alpha_total_val = sum(
        abs(snap.positions[r["Asset"]].net_value)
        for r in alpha_rows if r["Asset"] in snap.positions
    )
    alpha_invested = sum(
        per_asset_cb[r["Asset"]]["total_invested"]
        for r in alpha_rows
        if r["Asset"] in per_asset_cb and per_asset_cb[r["Asset"]].get("total_invested")
    )
    alpha_pnl = sum(
        per_asset_cb[r["Asset"]]["unrealized_pnl"]
        for r in alpha_rows
        if r["Asset"] in per_asset_cb and per_asset_cb[r["Asset"]].get("total_invested")
    )

    a1, a2, a3 = st.columns(3)
    render_kpi(a1, "Alpha Holdings", f"${alpha_total_val:,.0f}",
               f"{alpha_total_val / total_val * 100:.1f}% · {len(alpha_rows)} coins", "kpi-gold")
    render_kpi(a2, "Invested",
               f"${alpha_invested:,.0f}" if alpha_invested else "N/A", "cost basis")
    render_kpi(a3, "P&L",
               f"${alpha_pnl:+,.0f}" if alpha_invested else "N/A",
               f"{alpha_pnl / alpha_invested * 100:+.1f}%" if alpha_invested else "",
               pnl_color(alpha_pnl) if alpha_invested else "")
    st.markdown("")

    st.dataframe(
        pd.DataFrame(alpha_rows).style
            .map(lambda v: RISK_STYLE.get(v, "color:#F6465D;font-weight:600"), subset=["Risk"])
            .map(lambda v: "color:#0ECB81" if isinstance(v, str) and "+" in v and "$" in v
                 else ("color:#F6465D" if isinstance(v, str) and "-" in v and "$" in v else ""),
                 subset=["P&L"]),
        use_container_width=True,
        hide_index=True,
    )


# ─────────────────────────────────────────────────────────────────────────────
#  Section: Per-coin trade history (fragment — only this reruns on dropdown change)
# ─────────────────────────────────────────────────────────────────────────────

assets_with_trades = sorted(a for a in per_asset_cb if per_asset_cb[a].get("trades"))

if assets_with_trades:

    @st.fragment
    def trade_history_fragment():
        render_section("🕐 Spot Trade History")

        selector_col, _ = st.columns([1, 2])
        with selector_col:
            selected_asset = st.selectbox("Select coin", options=assets_with_trades, label_visibility="collapsed")

        coin_info = per_asset_cb[selected_asset]
        trades    = coin_info.get("trades", [])

        if trades:
            h1, h2, h3, h4 = st.columns(4)
            render_kpi(h1, "Trades",         str(len(trades)),                    "total")
            render_kpi(h2, "Avg Buy",        f"${coin_info['avg_cost']:,.4f}",    "weighted")
            render_kpi(h3, "Realized P&L",   f"${coin_info['realized_pnl']:+,.2f}", "locked in", pnl_color(coin_info["realized_pnl"]))
            render_kpi(h4, "Unrealized P&L", f"${coin_info['unrealized_pnl']:+,.2f}", "vs cost",  pnl_color(coin_info["unrealized_pnl"]))
            st.markdown("")

            trade_rows = [
                {
                    "Date (UTC)": (
                        datetime.datetime.utcfromtimestamp(t["time"] / 1000).strftime("%Y-%m-%d %H:%M")
                        if t.get("time") else "—"
                    ),
                    "Side":  "BUY 🟢" if t.get("isBuyer") else "SELL 🔴",
                    "Qty":   f"{float(t.get('qty', 0)):.6f}",
                    "Price": f"${float(t.get('price', 0)):,.6f}",
                    "Total": f"${float(t.get('quoteQty', 0)):,.2f}",
                    "Fee":   f"{float(t.get('commission', 0)):.6f} {t.get('commissionAsset', '')}",
                }
                for t in sorted(trades, key=lambda x: x.get("time", 0), reverse=True)
            ]

            st.dataframe(
                pd.DataFrame(trade_rows).style
                    .map(lambda v: "color:#0ECB81;font-weight:600" if "BUY" in str(v)
                         else ("color:#F6465D;font-weight:600" if "SELL" in str(v) else ""),
                         subset=["Side"]),
                use_container_width=True,
                hide_index=True,
                height=280,
            )

    trade_history_fragment()


# ─────────────────────────────────────────────────────────────────────────────
#  Section: Futures Trade History (all trades from inception)
# ─────────────────────────────────────────────────────────────────────────────

if fut_open:
    _fut_symbols = sorted(set(fp.get("symbol", "") for fp in fut_open if fp.get("symbol")))

    if _fut_symbols:
        @st.fragment
        def futures_history_fragment():
            render_section("📈 Futures Trade History", color="#9945FF")

            _sel_col, _info_col = st.columns([1, 2])
            with _sel_col:
                _fut_selected = st.selectbox(
                    "Select futures pair",
                    options=_fut_symbols,
                    label_visibility="collapsed",
                    key="_fut_history_sel",
                )
            with _info_col:
                st.caption("Showing all trades from account inception (up to 1000 per pair)")

            if _fut_selected:
                with st.spinner(f"Loading {_fut_selected} full trade history..."):
                    _ft_data = fetch_futures_trades([_fut_selected])
                    _ft_trades = _ft_data.get(_fut_selected, [])
                    _ft_income = fetch_futures_income(symbol=_fut_selected)

                # ── Income summary (funding, realized PnL, commissions) ───────
                _funding_total = 0.0
                _realized_income = 0.0
                _commission_income = 0.0
                _transfer_total = 0.0
                for inc in _ft_income:
                    it = inc.get("incomeType", "")
                    amt = float(inc.get("income", 0))
                    if it == "FUNDING_FEE":
                        _funding_total += amt
                    elif it == "REALIZED_PNL":
                        _realized_income += amt
                    elif it == "COMMISSION":
                        _commission_income += amt
                    elif it in ("TRANSFER", "INTERNAL_TRANSFER"):
                        _transfer_total += amt

                # ── KPI row ───────────────────────────────────────────────────
                _ft_h1, _ft_h2, _ft_h3, _ft_h4, _ft_h5 = st.columns(5)
                _n_trades = len(_ft_trades)
                _ft_buys  = sum(1 for t in _ft_trades if t.get("buyer"))
                _ft_sells = _n_trades - _ft_buys
                _ft_total_pnl = sum(float(t.get("realizedPnl", 0)) for t in _ft_trades)
                _ft_total_comm = sum(float(t.get("commission", 0)) for t in _ft_trades)
                _ft_vol = sum(float(t.get("quoteQty", 0)) for t in _ft_trades)

                render_kpi(_ft_h1, "Total Trades",  f"{_n_trades:,}",
                           f"{_ft_buys} buys / {_ft_sells} sells")
                render_kpi(_ft_h2, "Realized P&L",  f"${_ft_total_pnl:+,.2f}",
                           "from closed trades",
                           "kpi-green" if _ft_total_pnl >= 0 else "kpi-red")
                render_kpi(_ft_h3, "Funding Fees",  f"${_funding_total:+,.2f}",
                           "received (+) / paid (-)",
                           "kpi-green" if _funding_total >= 0 else "kpi-red")
                render_kpi(_ft_h4, "Commissions",   f"${_ft_total_comm:,.2f}",
                           "total trading fees", "kpi-red")
                render_kpi(_ft_h5, "Volume",        f"${_ft_vol:,.0f}",
                           "total notional traded")
                st.markdown("")

                # ── Net summary banner ────────────────────────────────────────
                _net_futures = _ft_total_pnl + _funding_total - _ft_total_comm
                _net_color = "#0ECB81" if _net_futures >= 0 else "#F6465D"
                st.markdown(
                    f'<div style="background:#1E2329;border:1px solid #2B3139;border-radius:10px;'
                    f'padding:12px 18px;text-align:center;margin-bottom:12px">'
                    f'<span style="color:#848E9C;font-size:12px">Net Result (P&L + Funding - Commissions): </span>'
                    f'<span style="color:{_net_color};font-size:18px;font-weight:700">${_net_futures:+,.2f}</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

                # ── Trade table ───────────────────────────────────────────────
                if _ft_trades:
                    # Find the matching open position for entry price & leverage
                    _fp_match = next((fp for fp in fut_open if fp.get("symbol") == _fut_selected), {})
                    _entry = float(_fp_match.get("entryPrice", 0))
                    _lev = _fp_match.get("leverage", "—")
                    _liq = float(_fp_match.get("liquidationPrice", 0))

                    if _entry > 0:
                        _pos_info = st.columns(4)
                        render_kpi(_pos_info[0], "Entry Price",   f"${_entry:,.4f}", "current position")
                        render_kpi(_pos_info[1], "Leverage",      f"{_lev}×",        "current")
                        render_kpi(_pos_info[2], "Liq. Price",    f"${_liq:,.4f}" if _liq > 0.01 else "—", "liquidation")
                        _mark = float(_fp_match.get("markPrice", 0))
                        _upnl = float(_fp_match.get("unRealizedProfit", _fp_match.get("unrealizedProfit", 0)))
                        render_kpi(_pos_info[3], "Unrealized P&L", f"${_upnl:+,.2f}", "current",
                                   "kpi-green" if _upnl >= 0 else "kpi-red")
                        st.markdown("")

                    _ft_rows = [
                        {
                            "Date (UTC)": (
                                datetime.datetime.utcfromtimestamp(t["time"] / 1000).strftime("%Y-%m-%d %H:%M:%S")
                                if t.get("time") else "—"
                            ),
                            "Side":       "BUY 🟢" if t.get("buyer") else "SELL 🔴",
                            "Position":   t.get("positionSide", "BOTH"),
                            "Qty":        f"{abs(float(t.get('qty', 0))):.4f}",
                            "Price":      f"${float(t.get('price', 0)):,.4f}",
                            "Notional":   f"${float(t.get('quoteQty', 0)):,.2f}",
                            "Realized":   f"${float(t.get('realizedPnl', 0)):+,.4f}",
                            "Fee":        f"${float(t.get('commission', 0)):,.4f}",
                            "Maker":      "✓" if t.get("maker") else "",
                        }
                        for t in sorted(_ft_trades, key=lambda x: x.get("time", 0), reverse=True)
                    ]

                    st.dataframe(
                        pd.DataFrame(_ft_rows).style
                            .map(lambda v: "color:#0ECB81;font-weight:600" if "BUY" in str(v)
                                 else ("color:#F6465D;font-weight:600" if "SELL" in str(v) else ""),
                                 subset=["Side"])
                            .map(lambda v: "color:#0ECB81" if isinstance(v, str) and "$+" in v
                                 else ("color:#F6465D" if isinstance(v, str) and "$-" in v else ""),
                                 subset=["Realized"]),
                        use_container_width=True,
                        hide_index=True,
                        height=min(35 + len(_ft_rows) * 35, 500),
                    )

                    # ── Funding fee history table ─────────────────────────────
                    _funding_rows = [
                        inc for inc in _ft_income if inc.get("incomeType") == "FUNDING_FEE"
                    ]
                    if _funding_rows:
                        with st.expander(f"💰 Funding Fee History — {len(_funding_rows)} entries", expanded=False):
                            _ff_rows = [
                                {
                                    "Date (UTC)": (
                                        datetime.datetime.utcfromtimestamp(int(f.get("time", 0)) / 1000).strftime("%Y-%m-%d %H:%M")
                                    ),
                                    "Amount": f"${float(f.get('income', 0)):+,.6f}",
                                    "Asset":  f.get("asset", "USDT"),
                                }
                                for f in sorted(_funding_rows, key=lambda x: x.get("time", 0), reverse=True)
                            ]
                            st.dataframe(
                                pd.DataFrame(_ff_rows).style
                                    .map(lambda v: "color:#0ECB81" if isinstance(v, str) and "$+" in v
                                         else ("color:#F6465D" if isinstance(v, str) and "$-" in v else ""),
                                         subset=["Amount"]),
                                use_container_width=True, hide_index=True,
                                height=min(35 + len(_ff_rows) * 35, 350),
                            )
                else:
                    st.caption("No futures trades found for this pair.")

        futures_history_fragment()


# ─────────────────────────────────────────────────────────────────────────────
#  Section: Risk alerts + Rebalance + AI Insights
# ─────────────────────────────────────────────────────────────────────────────

st.markdown("")
ai_tips = generate_ai_insights(snap, cb_summary, health, fut_open)

col_alerts, col_rebalance = st.columns(2, gap="large")

with col_alerts:
    render_section("🔔 Risk Alerts")
    if not snap.risk_flags:
        render_alert("ok", "✅ Portfolio looks healthy — no alerts")
    for flag in snap.risk_flags:
        level = "danger" if flag.level == "danger" else "warn"
        icon  = "🔴" if flag.level == "danger" else "🟡"
        render_alert(level, f"{icon} <b>[{flag.asset}]</b> {flag.message}")

with col_rebalance:
    render_section("⚖️ Rebalance Suggestions")
    rebalance_actions = [s for s in plan.suggestions if s.action != "HOLD"]
    if not rebalance_actions:
        render_alert("ok", "✅ Portfolio within policy — no action needed")
    for suggestion in rebalance_actions:
        level = "ok" if suggestion.action == "BUY" else "danger"
        icon  = "🟢 BUY" if suggestion.action == "BUY" else "🔴 SELL"
        render_alert(level, f"<b>{icon} {suggestion.asset}</b>  ${suggestion.amount_usdt:,.0f} USDT — {suggestion.reason}")

# AI Insights — full width
st.markdown("")
render_section("🤖 AI Portfolio Insights", color="#9945FF")

if ai_tips:
    for level, label, message in ai_tips:
        css = {"danger": "alert-danger", "warn": "alert-warn", "ok": "alert-ok"}.get(level, "alert-warn")
        st.markdown(
            f'<div class="{css}" style="margin-bottom:8px">'
            f'<span style="font-weight:700;font-size:11px">{label}</span><br>'
            f'<span style="font-size:12px">{message}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )
else:
    render_alert("ok", "🤖 No additional recommendations — portfolio is optimally structured.")


# ─────────────────────────────────────────────────────────────────────────────
#  Section: AI Chat
# ─────────────────────────────────────────────────────────────────────────────

st.markdown("")
st.markdown(
    '<div style="background:linear-gradient(135deg,#1E2329,#161A1E);'
    'border:1px solid #627EEA40;border-radius:14px;padding:20px 24px;margin-top:12px">'
    '<div style="display:flex;align-items:center;gap:10px;margin-bottom:4px">'
    '<span style="font-size:18px">💬</span>'
    '<span style="font-size:14px;font-weight:700;color:#627EEA;letter-spacing:.3px">'
    'AI Portfolio Chat</span>'
    '<span style="background:#627EEA20;color:#627EEA;font-size:9px;font-weight:700;'
    'letter-spacing:1px;border-radius:4px;padding:2px 7px;margin-left:4px">GROQ LLAMA 3.3</span>'
    '</div>'
    '<div style="color:#5E6673;font-size:11px">Ask anything about your live portfolio</div>'
    '</div>',
    unsafe_allow_html=True,
)
st.markdown("")

groq_key = read_env().get("GROQ_API_KEY", "")

if not groq_key:
    st.markdown(
        '<div class="alert-warn" style="margin-top:8px">'
        '🤖 AI Chat is disabled — add your <b>Groq API Key</b> in '
        '<b>⚙️ API Settings</b> (sidebar) to enable it. '
        '<a href="https://console.groq.com/keys" target="_blank" '
        'style="color:#F0B90B">Get a free key →</a>'
        '</div>',
        unsafe_allow_html=True,
    )
else:
    # ── Init chat state ──────────────────────────────────────────────────────
    if "chat_messages" not in st.session_state:
        st.session_state["chat_messages"] = []
    if "_pending_q" not in st.session_state:
        st.session_state["_pending_q"] = None

    # ── Quick questions (only when chat is empty) ────────────────────────────
    if not st.session_state["chat_messages"]:
        st.markdown(
            '<div style="color:#5E6673;font-size:11px;letter-spacing:.3px;'
            'text-transform:uppercase;font-weight:600;margin-bottom:10px">'
            '⚡ Quick questions</div>',
            unsafe_allow_html=True,
        )
        suggestions = [
            "What's my biggest risk right now?",
            "Should I buy more BTC or BNB?",
            "How can I improve my health score?",
            "Which coins should I consider selling?",
            "Give me a full portfolio summary.",
            "Am I too exposed to risky altcoins?",
        ]
        q_cols = st.columns(3)
        for i, question in enumerate(suggestions):
            q_cols[i % 3].markdown('<div class="q-btn">', unsafe_allow_html=True)
            if q_cols[i % 3].button(question, key=f"_q{i}", use_container_width=True):
                st.session_state["_pending_q"] = question
            q_cols[i % 3].markdown('</div>', unsafe_allow_html=True)

    # ── Handle pending quick question (call Groq inline, no rerun) ────────────
    pending = st.session_state.pop("_pending_q", None)
    if pending:
        st.session_state["chat_messages"].append({"role": "user", "content": pending})
        with st.chat_message("user", avatar="🧑"):
            st.markdown(pending)
        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("AI is thinking..."):
                portfolio_ctx = build_portfolio_context(snap, cb_summary, health)
                reply = chat_with_groq(
                    messages=st.session_state["chat_messages"],
                    portfolio_context=portfolio_ctx,
                    api_key=groq_key,
                )
            st.markdown(reply)
        st.session_state["chat_messages"].append({"role": "assistant", "content": reply})

    # ── Conversation history ──────────────────────────────────────────────────
    if not pending:
        for msg in st.session_state["chat_messages"]:
            avatar = "🧑" if msg["role"] == "user" else "🤖"
            with st.chat_message(msg["role"], avatar=avatar):
                st.markdown(msg["content"])

    # ── Inline chat input (inside page, not floating) ─────────────────────────
    st.markdown('<div class="chat-input">', unsafe_allow_html=True)
    input_col, btn_col = st.columns([6, 1])
    with input_col:
        user_prompt = st.text_input(
            "chat", placeholder="💬 Ask about your portfolio...",
            key="_chat_input", label_visibility="collapsed",
        )
    with btn_col:
        send_clicked = st.button("🚀 Send", key="_chat_send", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    if send_clicked and user_prompt and user_prompt.strip():
        st.session_state["chat_messages"].append({"role": "user", "content": user_prompt.strip()})
        with st.chat_message("user", avatar="🧑"):
            st.markdown(user_prompt.strip())
        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("AI is thinking..."):
                portfolio_ctx = build_portfolio_context(snap, cb_summary, health)
                reply = chat_with_groq(
                    messages=st.session_state["chat_messages"],
                    portfolio_context=portfolio_ctx,
                    api_key=groq_key,
                )
            st.markdown(reply)
        st.session_state["chat_messages"].append({"role": "assistant", "content": reply})

    # ── Clear button ──────────────────────────────────────────────────────────
    if st.session_state.get("chat_messages"):
        st.markdown("")
        if st.button("🗑️ Clear conversation", key="_clear_chat"):
            st.session_state["chat_messages"] = []
            st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
#  Footer
# ─────────────────────────────────────────────────────────────────────────────

st.divider()
st.caption(
    "OpenClaw Portfolio Brain · "
    "github.com/namtrung99/openclaw-portfolio-brain · "
    "#AIBinance · Not investment advice"
)
