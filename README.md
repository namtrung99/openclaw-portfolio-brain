# OpenClaw Portfolio Brain

> **AI-powered Binance portfolio analyzer** — aggregates Spot + Futures + Earn + Funding + Auto-Invest into one dashboard,
> scores your portfolio health, gives actionable rebalance suggestions, and lets you **chat with an AI** about your portfolio.
> Built for the [Binance #AIBinance competition](https://www.binance.com/en/square/post/297854079538945) - Deadline: 2026-03-18

[![Python 3.11](https://img.shields.io/badge/python-3.11-F0B90B?logo=python&logoColor=white)](https://python.org)
[![Streamlit](https://img.shields.io/badge/streamlit-1.32+-F0B90B?logo=streamlit&logoColor=white)](https://streamlit.io)
[![Binance API](https://img.shields.io/badge/binance-api-F0B90B?logo=binance&logoColor=white)](https://binance.com)
[![Groq](https://img.shields.io/badge/groq-llama_3.3_70B-F0B90B?logo=meta&logoColor=white)](https://console.groq.com)

---

## Features

| Module | What it does |
|---|---|
| **Portfolio Aggregation** | Merges Spot + Futures + Earn + Funding Wallet + Auto-Invest into one USDT snapshot |
| **AI Health Score** | Scores portfolio 0-100 across 5 risk dimensions, grades A/B/C/D |
| **AI Insights Engine** | Rule-based AI reads 7 portfolio signals and outputs dollar-sized advice |
| **AI Chat (Groq LLaMA 3.3)** | Chat with AI about your live portfolio — ask anything, free and fast |
| **Risk Distribution** | Classifies every holding as Safe / Medium / Risky with value breakdown |
| **Trade Summary** | Total spent, received, realized P&L, unrealized P&L, net P&L from inception |
| **Rebalance Planner** | Policy-driven Buy/Sell suggestions with exact USDT amounts |
| **Binance Alpha Tracker** | Shows only true Alpha coins (filters out graduated-to-spot) |
| **Trade History** | Per-coin buy/sell log with avg cost, fees, and P&L |
| **Server Time Sync** | Auto-corrects machine clock drift vs Binance server (handles 72s+ offset) |
| **Dark Binance Theme** | Dark UI matching Binance's color palette |
| **Auto-refresh** | Wallet data refreshes every 60s, trades cached 5 min |

---

## Quick Start

### Windows

```bat
git clone https://github.com/namtrung99/openclaw-portfolio-brain.git
cd openclaw-portfolio-brain
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
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

## API Key Setup

### Binance API Key (required)

1. Go to [Binance API Management](https://www.binance.com/en/my/settings/api-management)
2. Create a new key — enable **Read Info** only (no trading permissions needed)
3. In the app: click **Settings** button (top-right) -> paste key + secret -> **Save Binance Keys**

### Groq API Key (for AI Chat)

1. Go to [Groq Console](https://console.groq.com/keys) -> **Create API Key** (free tier: 30 req/min)
2. In the app: **Settings** -> paste Groq key -> **Save Groq Key**

### Or create .env file manually

```
BINANCE_API_KEY=your_binance_api_key
BINANCE_SECRET_KEY=your_binance_secret_key
GROQ_API_KEY=your_groq_api_key
USE_MOCK_DATA=false
```

> Always use a **read-only** Binance key. This app never places any orders.

---

## Dashboard Metrics — Detailed Explanation

### 1. Wallet Overview (4 KPI Cards)

| Metric | Definition | Formula |
|---|---|---|
| **Cash** | Total value of all stablecoin holdings across Spot + Earn + Funding | `Cash = SUM(qty * 1.0)` for all assets in `{USDT, USDC, BUSD, FDUSD, DAI, TUSD}` |
| **Coins** | Total value of all non-stablecoin holdings | `Coins = Total Portfolio - Cash` |
| **Earn** | Total value of all Earn products (Flexible + Locked + accrued interest + Auto-Invest) | `Earn = earn_equity + earn_interest_gap + auto_invest_equity` |
| **Total Portfolio** | Total value of all Binance accounts combined | See formula below |

**Total Portfolio formula:**

```
Total Portfolio = Spot Equity + Earn Equity + Earn Interest Gap
                + Futures Wallet Balance + Futures Unrealized PnL

Where:
  Spot Equity        = SUM(spot_qty[asset] * price[asset]) for all assets
                       (includes Funding Wallet + Auto-Invest holdings)
  Earn Equity        = SUM(earn_qty[asset] * price[asset]) for all Earn positions
  Earn Interest Gap  = max(0, earn_account_total - Earn Equity)
                       (accrued interest not reflected in LD* token balances)
  Futures Wallet     = totalWalletBalance from Binance Futures API
  Futures uPnL       = totalUnrealizedProfit from Binance Futures API
```

**Data sources aggregated:**

| Source | Binance API | Included in |
|---|---|---|
| Spot Account | `GET /api/v3/account` | Spot Equity |
| Simple Earn Flexible | `GET /sapi/v1/simple-earn/flexible/position` | Earn Equity |
| Simple Earn Locked | `GET /sapi/v1/simple-earn/locked/position` | Earn Equity |
| Simple Earn Account | `GET /sapi/v1/simple-earn/account` | Earn Interest Gap |
| Futures Account | `GET /fapi/v3/account` | Futures Wallet + uPnL |
| Funding Wallet | `POST /sapi/v1/asset/get-funding-asset` | Spot Equity |
| Auto-Invest Plans | `GET /sapi/v1/lending/auto-invest/plan/id` | Spot Equity (also shown in Earn card) |

---

### 2. Trade Summary (5 KPI Cards)

Calculated from all historical spot trades (`/api/v3/myTrades`) across all held + previously-held assets.

| Metric | Definition | Formula |
|---|---|---|
| **Total Spent** | Sum of USDT spent on all buy trades (including fees) | `Total Spent = SUM(quoteQty + commission_usdt)` for all `isBuyer=true` trades |
| **Total Received** | Sum of USDT received from all sell trades (minus fees) | `Total Received = SUM(quoteQty - commission_usdt)` for all `isBuyer=false` trades |
| **Realized P&L** | Profit/loss already locked in from completed sell trades | `Realized P&L = SUM(sell_revenue - cost_of_sold)` per asset, where `cost_of_sold = sell_qty * avg_cost` |
| **Unrealized P&L** | Paper profit/loss on currently held positions | `Unrealized P&L = SUM(current_value - remaining_cost)` per asset, where `current_value = net_qty * current_price`, `remaining_cost = net_qty * avg_cost` |
| **Net P&L** | Overall profit/loss (realized + paper) | `Net P&L = Realized P&L + Unrealized P&L` |

**Average cost calculation (per asset):**

```
avg_cost = total_buy_cost / total_buy_qty
  where total_buy_cost = SUM(quoteQty + commission_usdt) for all buys
  and   total_buy_qty  = SUM(qty) for all buys
```

Note: `Net P&L != Total Received - Total Spent` because unrealized P&L on open positions is not captured by received/spent.

---

### 3. Spot Trader Analytics (8 KPI Cards + Top Winners/Losers)

Deep analysis metrics designed for spot traders to understand **why** they are winning or losing, and which coins are driving their results.

**Row 1 — Performance metrics:**

| Metric | Definition | Formula |
|---|---|---|
| **Win Rate** | % of traded coins that are currently profitable | `Win Rate = winners / total_assets_traded * 100` where a "winner" has `realized_pnl + unrealized_pnl > 0` |
| **Overall ROI** | Return on investment across all trades | `ROI = Net P&L / Total Spent * 100` |
| **Profit Factor** | How much you earn per dollar lost — key risk metric | `Profit Factor = Gross Profit / Gross Loss` where Gross Profit = SUM of all positive per-coin P&L, Gross Loss = SUM of all negative per-coin P&L |
| **Total Fees Paid** | Cumulative trading fees in USDT | `Fees = SUM(commission * price)` for all trades, shown as $ and as % of total spent |

**Row 2 — Efficiency metrics:**

| Metric | Definition | Formula |
|---|---|---|
| **Avg Win** | Average profit per winning coin | `Avg Win = Gross Profit / number_of_winners` |
| **Avg Loss** | Average loss per losing coin | `Avg Loss = Gross Loss / number_of_losers` |
| **Total Trades** | Total number of individual trades executed | Count of all buy + sell trades across all assets |
| **Best Performer** | The single coin with highest total P&L | Top 1 sorted by `realized_pnl + unrealized_pnl` |

**Interpreting Profit Factor:**

| Profit Factor | Meaning |
|---|---|
| > 2.0 | Excellent — strong edge |
| 1.5 - 2.0 | Good — profitable system |
| 1.0 - 1.5 | Marginal — barely profitable |
| < 1.0 | Losing — gross losses exceed gains |

**Top Winners / Top Losers tables:**

Shows the 8 best and 8 worst performing coins side-by-side with:
- Per-coin P&L ($), ROI (%), Realized P&L, Unrealized P&L
- Helps identify: which coins drive profit, which are dragging you down, and where to cut losses

---

### 4. AI Health Score (Gauge + Analysis)

A **deterministic 0-100 composite score** across 5 risk dimensions (rule engine, no LLM):

```
Health Score = Stable Buffer + Risk Mix + Diversification + P&L Health + Futures Exposure
```

| Dimension | Max Pts | What it measures | Scoring |
|---|---|---|---|
| **Stable Buffer** | 25 | % of portfolio in stablecoins | 25 if 15-30%, 15 if 10-15% or >40%, 5 otherwise |
| **Risk Mix** | 25 | % of portfolio in "safe" assets (BTC/ETH/BNB/stables) | 25 if safe >= 50%, 15 if safe >= 30%, 5 otherwise |
| **Diversification** | 20 | Number of positions worth > $10 | 20 if 5-15 positions, 10 if <5 or >15 |
| **P&L Health** | 20 | Net P&L as % of total spent | 20 if >= 0%, 12 if >= -25%, 6 if >= -50%, 2 otherwise |
| **Futures Exposure** | 10 | Futures wallet as % of total portfolio | 10 if no futures or <10%, 6 if <25%, 2 otherwise |

**Grade mapping:**

| Score Range | Grade | Status |
|---|---|---|
| 75-100 | **A** | Healthy |
| 55-74 | **B** | Moderate |
| 35-54 | **C** | At Risk |
| 0-34 | **D** | Danger |

---

### 5. Risk Distribution (Donut Chart + Table)

Every asset is classified into one of three risk tiers:

| Tier | Assets | Criteria |
|---|---|---|
| **Safe** | USDT, USDC, BUSD, FDUSD, DAI, TUSD, BTC, ETH, BNB | Stablecoins + top-3 by market cap |
| **Medium** | SOL, XRP, ADA, DOGE, SHIB, TRX, TON, AVAX, LINK, DOT, MATIC, POL, LTC, UNI, ATOM, NEAR, APT, ARB, OP, SUI | Top-20 large-cap altcoins |
| **Risky** | Everything else | Small-cap altcoins, memecoins, Alpha tokens |

**Per-tier calculation:**

```
Safe Value   = SUM(|net_value|) for all assets where risk_level = "safe"
Medium Value = SUM(|net_value|) for all assets where risk_level = "medium"
Risky Value  = SUM(|net_value|) for all assets where risk_level = "risky"
Tier %       = Tier Value / (Safe + Medium + Risky) * 100
```

---

### 6. Allocation Pie Chart

Shows top holdings as % of total portfolio:

```
Allocation % (per asset) = |net_value| / total_equity * 100
  where net_value = (spot_qty + earn_qty + futures_long - futures_short) * price
```

---

### 7. AI Insights Engine

Rule-based analysis that reads 7 portfolio signals and generates actionable advice with dollar amounts:

| Signal | Trigger | Action Suggested |
|---|---|---|
| Stable buffer critical | stable_pct < 10% | Convert $X altcoins to USDT (target 20%) |
| Stable buffer low | stable_pct < 15% | Add ~$X more in USDT |
| Over-conservative | stable_pct > 45% | Deploy $X into BTC/BNB |
| Concentration risk | Single non-safe asset > 40% | Trim to 25%, free $X |
| Risky concentration | Single risky asset > 25% | Reduce to under 10% |
| Heavy losses | Net P&L < -30% | Avoid panic selling, focus on high-conviction |
| High futures leverage | Futures notional > 30% of portfolio | Reduce positions or add margin |
| Risky altcoin overweight | Risky assets > 40% | Target under 20% speculative |
| Over-diversified | > 20 positions | Focus on best 10-15 ideas |

---

### 8. Per-Asset Position Detail

| Field | Formula |
|---|---|
| Net Qty | `spot_qty + earn_qty + futures_long - futures_short` |
| Net Value | `net_qty * current_price` |
| Spot Value | `spot_qty * price_usdt` |
| Earn Value | `earn_qty * price_usdt` |
| Avg Cost | `total_buy_cost / total_buy_qty` (from trade history) |
| Unrealized P&L | `current_value - (net_qty * avg_cost)` |
| Realized P&L | `total_sell_revenue - (total_sell_qty * avg_cost)` |

---

### 9. Rebalance Planner

Policy-driven suggestions based on target allocations:

```
Default Policy:
  BTC:  15-35% of portfolio
  ETH:  10-25%
  BNB:  10-25%
  Minimum stable buffer: 10%
  Max single alt: 15%
  Max futures leverage: 10x
```

Generates BUY/SELL suggestions with exact USDT amounts to reach target allocation.

---

### 10. Binance Alpha Tracker

Filters your holdings to show only Binance Alpha program tokens (early-access coins not yet on regular spot).
Uses a curated list of 60+ confirmed Alpha tokens from CoinMarketCap.

Shows per-coin: quantity, current value, P&L, risk classification.

---

## Server Time Sync

The app automatically syncs with Binance server time on startup.
This handles machine clock drift (tested up to 72+ seconds offset).

```
Algorithm:
  1. GET /api/v3/time -> server_time_ms
  2. offset = server_time_ms - local_time_ms
  3. All signed requests use: timestamp = local_time + offset
  4. recvWindow = 30000ms for extra tolerance
```

---

## AI Chat

The AI Chat uses **Groq's LLaMA 3.3 70B** (free, fast inference) with your live portfolio injected as context.
It knows your exact holdings, P&L, health score, and can answer in **Vietnamese or English**.

**Example questions:**
- "Tai khoan cua toi dang co van de gi?"
- "Should I buy more BTC or BNB?"
- "Which coins should I sell to improve my health score?"
- "Give me a full portfolio review."

> Free tier: 30 requests/minute. Get key at [console.groq.com](https://console.groq.com/keys)

---

## Project Structure

```
openclaw-portfolio-brain/
|-- app.py              <- Streamlit dashboard (UI + AI engine + chat)
|-- main.py             <- CLI summary report
|-- src/
|   |-- config.py       <- Env vars, PortfolioPolicy, STABLE_COINS
|   |-- fetcher.py      <- Async Binance API (Spot, Futures, Earn, Funding, Auto-Invest, myTrades)
|   |-- aggregator.py   <- Net exposure per coin, risk flags, earn interest correction
|   |-- planner.py      <- Rebalance + DCA plan generator
|   |-- chatbot.py      <- Groq LLaMA 3.3 chat with portfolio context
|   |-- mock_data.py    <- RISK_LEVEL map, BINANCE_ALPHA_COINS list
|-- requirements.txt
|-- .env                <- Your API keys (gitignored)
|-- .env.example        <- Template -- copy to .env and fill in keys
```

---

## Key Formulas Summary

```
Net Position     = spot_qty + earn_qty + futures_long - futures_short
Net Value (USDT) = net_position * current_price_usdt
Stable %         = SUM(stablecoin_values) / total_equity * 100

Total Portfolio  = Spot + Earn + Earn_Interest_Gap + Futures_Wallet + Futures_uPnL

Avg Cost         = total_buy_cost / total_buy_qty
Unrealized P&L   = current_value - (net_qty * avg_cost)
Realized P&L     = sell_revenue - (sell_qty * avg_cost)
Net P&L          = Realized + Unrealized

AI Health Score  = Stable(25) + RiskMix(25) + Diversification(20) + PnL(20) + Futures(10)

Win Rate         = winners / total_coins_traded * 100
ROI              = Net P&L / Total Spent * 100
Profit Factor    = Gross Profit / Gross Loss
Avg Win          = Gross Profit / number_of_winners
Avg Loss         = Gross Loss / number_of_losers
```

---

## Competition Info

- **Competition**: [Binance #AIBinance](https://www.binance.com/en/square/post/297854079538945)
- **Deadline**: 2026-03-18 23:59 UTC
- **Prize**: 1st = 10 BNB
- **Participant UID**: `718475870`
- **GitHub**: [namtrung99/openclaw-portfolio-brain](https://github.com/namtrung99/openclaw-portfolio-brain)

---

**Disclaimer:** For informational purposes only. Not investment advice. Always DYOR.
