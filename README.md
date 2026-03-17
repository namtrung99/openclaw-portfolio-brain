# 🧠 OpenClaw Portfolio Brain

> **AI-powered Binance portfolio analyzer** — aggregates Spot + Futures + Earn into one dashboard,
> scores your portfolio health, gives actionable rebalance suggestions, and lets you **chat with an AI** about your portfolio.
> Built for the [Binance #AIBinance competition](https://www.binance.com/en/square/post/297854079538945) · Deadline: 2026-03-18

[![Python 3.11](https://img.shields.io/badge/python-3.11-F0B90B?logo=python&logoColor=white)](https://python.org)
[![Streamlit](https://img.shields.io/badge/streamlit-1.32+-F0B90B?logo=streamlit&logoColor=white)](https://streamlit.io)
[![Binance API](https://img.shields.io/badge/binance-api-F0B90B?logo=binance&logoColor=white)](https://binance.com)
[![Gemini](https://img.shields.io/badge/google-gemini_2.0-F0B90B?logo=google&logoColor=white)](https://aistudio.google.com)

---

## ✨ Features

| Module | What it does |
|---|---|
| 📦 **Portfolio Aggregation** | Merges Spot + USDⓈ-M Futures + Simple Earn into one USDT snapshot |
| 🤖 **AI Health Score** | Scores portfolio 0–100 across 5 risk dimensions, grades A/B/C/D |
| 🤖 **AI Insights Engine** | Rule-based AI reads 7 portfolio signals → outputs dollar-sized advice |
| 💬 **AI Chat (Gemini 2.0)** | Chat with Google Gemini about your live portfolio — ask anything |
| 📊 **Risk Distribution** | Classifies every holding as Safe / Medium / Risky with value breakdown |
| 📈 **Trade Summary** | Total spent, received, realized P&L, unrealized P&L, net P&L from inception |
| ⚖️ **Rebalance Planner** | Policy-driven Buy/Sell suggestions with exact USDT amounts |
| 🔶 **Binance Alpha Tracker** | Shows only true Alpha coins (filters out graduated-to-spot) |
| 🕐 **Trade History** | Per-coin buy/sell log with avg cost, fees, and P&L |
| 🌙 **Dark Binance Theme** | Dark UI matching Binance's color palette |
| 🔄 **Auto-refresh** | Wallet data refreshes every 60s, trades cached 5 min |

---

## 🚀 Quick Start

### Windows

```bat
REM 1. Clone repo
git clone https://github.com/namtrung99/openclaw-portfolio-brain.git
cd openclaw-portfolio-brain

REM 2. Create virtual environment
python -m venv .venv
.venv\Scripts\activate

REM 3. Install dependencies
pip install -r requirements.txt

REM 4. Run dashboard
streamlit run app.py --server.port 8502
```

Open **http://localhost:8502** in your browser.

### macOS / Linux

```bash
git clone https://github.com/namtrung99/openclaw-portfolio-brain.git
cd openclaw-portfolio-brain
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py --server.port 8502
```

---

## 🔑 API Key Setup

### Binance API Key (required)

1. Go to [Binance → API Management](https://www.binance.com/en/my/settings/api-management)
2. Create a new key — enable **Read Info** only (no trading permissions needed)
3. In the app: click **⚙️ Settings** button (top-right on dashboard) → paste key + secret → **💾 Save Binance Keys**

### Google Gemini API Key (for AI Chat)

1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey) → **Get API Key** (free tier: 15 req/min)
2. In the app: **⚙️ Settings** → paste Gemini key → **💾 Save Gemini Key**

### Or create `.env` file manually

**Windows** — create `.env` in project folder:
```
BINANCE_API_KEY=your_binance_api_key
BINANCE_SECRET_KEY=your_binance_secret_key
GEMINI_API_KEY=your_gemini_api_key
USE_MOCK_DATA=false
```

**macOS / Linux:**
```bash
cp .env.example .env
# then edit .env with your keys
```

> ⚠️ Always use a **read-only** Binance key. This app never places any orders.

---

## 🤖 AI Health Score — How It Works

Score = **0–100** composite across 5 dimensions (deterministic rule engine, no LLM):

```
Score = Stable Buffer (25pts) + Risk Mix (25pts) + Diversification (20pts)
      + P&L Health (20pts) + Futures Exposure (10pts)
```

| Dimension | Max | What's measured |
|---|---|---|
| Stable Buffer | 25 | % of portfolio in USDT/stablecoins (ideal: 15–30%) |
| Risk Mix | 25 | % of safe assets (BTC/ETH/BNB) vs risky altcoins |
| Diversification | 20 | Number of meaningful positions (ideal: 5–15) |
| P&L Health | 20 | Net P&L as % of total ever invested |
| Futures Exposure | 10 | Futures wallet as % of total (0% = max score) |

| Score | Grade | Label |
|---|---|---|
| 75–100 | **A** 🟢 | Healthy |
| 55–74 | **B** 🟡 | Moderate |
| 35–54 | **C** 🟠 | At Risk |
| 0–34  | **D** 🔴 | Danger |

---

## 💬 AI Chat

The AI Chat uses **Google Gemini 2.0 Flash** with your live portfolio injected as context.
It knows your exact holdings, P&L, health score, and can answer in **Vietnamese or English**.

**Example questions:**
- *"Tài khoản của tôi đang có vấn đề gì?"*
- *"Should I buy more BTC or BNB?"*
- *"Which coins should I sell to improve my health score?"*
- *"Give me a full portfolio review."*

> Free tier: 15 requests/minute. Get key at [aistudio.google.com](https://aistudio.google.com/app/apikey)

---

## 📁 Project Structure

```
openclaw-portfolio-brain/
├── app.py              ← Streamlit dashboard (UI + AI engine + chat)
├── main.py             ← CLI summary report
├── src/
│   ├── config.py       ← Env vars, PortfolioPolicy, STABLE_COINS
│   ├── fetcher.py      ← Async Binance API (Spot, Futures, Earn, myTrades)
│   ├── aggregator.py   ← Net exposure per coin, risk flags
│   ├── planner.py      ← Rebalance + DCA plan generator
│   ├── chatbot.py      ← Gemini 2.0 chat with portfolio context
│   └── mock_data.py    ← RISK_LEVEL map, BINANCE_ALPHA_COINS list
├── requirements.txt
├── .env                ← Your API keys (gitignored)
└── .env.example        ← Template — copy to .env and fill in keys
```

---

## 🧮 Key Formulas

```
Net Position     = spot_qty + earn_qty + futures_long − futures_short
Net Value (USDT) = net_position × current_price_usdt
Stable %         = sum(stablecoin_values) / total_equity × 100
Unrealized P&L   = current_value − (avg_cost × current_qty)
Realized P&L     = total_received_from_sells − cost_basis_of_sold
Net P&L          = realized_pnl + unrealized_pnl
AI Health Score  = Σ(5 dimension scores)  [0–100]
```

---

## 🏆 Competition Info

- **Competition**: [Binance #AIBinance](https://www.binance.com/en/square/post/297854079538945)
- **Deadline**: 2026-03-18 23:59 UTC
- **Prize**: 1st = 10 BNB
- **Participant UID**: `718475870`
- **GitHub**: [namtrung99/openclaw-portfolio-brain](https://github.com/namtrung99/openclaw-portfolio-brain)

---

**⚠️ Disclaimer:** For informational purposes only. Not investment advice. Always DYOR.
