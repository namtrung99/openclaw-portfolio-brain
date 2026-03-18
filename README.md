# OpenClaw Portfolio Brain

> **AI-powered Binance portfolio analyzer** — aggregates Spot + Futures + Earn + Funding + Auto-Invest into one dashboard,
> scores your portfolio health, gives actionable rebalance suggestions, and lets you **chat with an AI** about your portfolio.
> Built for the [Binance #AIBinance competition](https://www.binance.com/en/square/post/297854079538945) - Deadline: 2026-03-18

[![Python 3.11](https://img.shields.io/badge/python-3.11-F0B90B?logo=python&logoColor=white)](https://python.org)
[![Streamlit](https://img.shields.io/badge/streamlit-1.32+-F0B90B?logo=streamlit&logoColor=white)](https://streamlit.io)
[![Binance API](https://img.shields.io/badge/binance-api-F0B90B?logo=binance&logoColor=white)](https://binance.com)
[![Groq](https://img.shields.io/badge/groq-llama_3.3_70B-F0B90B?logo=meta&logoColor=white)](https://console.groq.com)
[![Docker](https://img.shields.io/badge/docker-ready-F0B90B?logo=docker&logoColor=white)](https://www.docker.com/products/docker-desktop/)

---

## Features

| Module | What it does |
|---|---|
| **Wallet Overview** | 5 KPI cards: Cash, Coins (spot+earn), Earn, Futures (wallet+uPnL), Total |
| **P2P Lifetime Summary** | Total USDT deposited/withdrawn via P2P from inception, VND & USD breakdown |
| **Portfolio Aggregation** | Merges Spot + Futures + Earn + Funding Wallet + Auto-Invest into one USDT snapshot |
| **All Assets Table** | Spot+earn holdings only (no futures notional inflation), correct % allocation |
| **AI Health Score** | Scores portfolio 0-100 across 5 risk dimensions, grades A/B/C/D |
| **AI Insights Engine** | Rule-based AI reads 7 portfolio signals and outputs dollar-sized advice |
| **AI Chat (Groq LLaMA 3.3)** | Chat with AI about your live portfolio — ask anything, free and fast |
| **Risk Distribution** | Classifies every holding as Safe / Medium / Risky with value breakdown |
| **Spot Trader Analytics** | Win Rate, ROI, Profit Factor, Fees, Avg Win/Loss, Best Performer |
| **Trade Summary** | Total spent, received, realized P&L, unrealized P&L, net P&L from inception |
| **Rebalance Planner** | Policy-driven Buy/Sell suggestions with exact USDT amounts |
| **Binance Alpha Tracker** | Shows only true Alpha coins (filters out graduated-to-spot) |
| **Spot Trade History** | Per-coin buy/sell log with avg cost, fees, and P&L |
| **Futures Trade History** | 365-day income API across all traded symbols (37+), full P&L + funding breakdown |
| **Futures Open Positions** | Entry price, leverage, liquidation price, unrealized P&L |
| **Tax Report** | Annual deposits, withdrawals, converts, P2P trades (VND/USD), spot trades + CSV |
| **Server Time Sync** | Auto-corrects machine clock drift vs Binance server (handles 72s+ offset) |
| **Dark Binance Theme** | Dark UI matching Binance's color palette |
| **Auto-refresh** | Wallet data refreshes every 60s, trades cached 5 min |
| **Docker Support** | One-command run on any machine — Windows, macOS, Linux |

---

## Dashboard Layout

```
Portfolio Brain — Wallet Overview
  ├── 5 KPI Cards: Cash | Coins (spot+earn) | Earn | Futures (wallet+uPnL) | Total
  ├── P2P Lifetime Summary — USDT nap/rut, VND & USD breakdown, all-time orders
  ├── Trade Summary (spent, received, realized P&L, unrealized P&L, net P&L)
  ├── Spot Trader Analytics (Win Rate, ROI, Profit Factor, Fees, Avg Win/Loss)
  ├── Top Winners / Top Losers
  ├── All Assets (spot+earn only, % allocation = spot+earn total)
  ├── Futures Open Positions
  ├── AI Health Score (gauge + risk distribution + allocation pie)
  ├── Futures Trade History (365d income all symbols, per-symbol detail)
  ├── Risk Alerts + Rebalance Suggestions
  ├── AI Portfolio Insights
  ├── Binance Alpha Tracker
  ├── Spot Trade History (per-coin with avg cost + P&L)
  └── AI Chat (Groq LLaMA 3.3 70B)

Tax Report (separate page via sidebar or dashboard button)
  ├── Deposits: count + coins + USDT equivalent
  ├── Withdrawals: count + total fees
  ├── Converts / Swaps
  ├── P2P Trades: VND buy/sell + USD buy/sell breakdown
  ├── Spot Buys ($) | Spot Sells ($) | Net P&L | Total Trades
  └── All sections exportable to CSV

Settings (separate page)
  ├── Binance API Key (main dashboard)
  ├── Groq API Key (AI Chat)
  └── Tax Report API Key (dedicated read-only key, never used on main dashboard)
```

---

## Quick Start

> **Recommended:** Use Docker — works on Windows, macOS, and Linux without installing Python or any dependencies.
> If you don't have Docker, see the [Docker Setup Guide](#docker-setup-guide) section below.

---

### Option 1 — Docker (recommended, works on any machine)

**Step 1:** Install Docker — see [Docker Setup Guide](#docker-setup-guide) below if you've never used it.

**Step 2:** Clone the repo and create your `.env` file:

**Windows (Command Prompt or PowerShell):**
```bat
git clone https://github.com/namtrung99/openclaw-portfolio-brain.git
cd openclaw-portfolio-brain
copy .env.example .env
notepad .env
```

**macOS / Linux:**
```bash
git clone https://github.com/namtrung99/openclaw-portfolio-brain.git
cd openclaw-portfolio-brain
cp .env.example .env
nano .env
```

**Step 3:** Fill in your API keys in `.env`:
```
BINANCE_API_KEY=your_binance_api_key_here
BINANCE_SECRET_KEY=your_binance_secret_key_here
GROQ_API_KEY=your_groq_api_key_here
USE_MOCK_DATA=false
```

**Step 4:** Start the app:
```bash
docker compose up -d
```

Open **http://localhost:8502** in your browser. Done!

**Useful Docker commands:**
```bash
docker compose up -d        # start in background
docker compose down         # stop
docker compose logs -f      # view live logs
docker compose up -d --build  # rebuild after code changes
```

---

### Option 2 — Python (Windows)

Requires Python 3.11+ — download from [python.org](https://www.python.org/downloads/) if not installed.

```bat
git clone https://github.com/namtrung99/openclaw-portfolio-brain.git
cd openclaw-portfolio-brain
copy .env.example .env
notepad .env
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py --server.port 8502
```

Open **http://localhost:8502** in your browser.

---

### Option 3 — Python (macOS / Linux)

```bash
git clone https://github.com/namtrung99/openclaw-portfolio-brain.git
cd openclaw-portfolio-brain
cp .env.example .env
nano .env
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py --server.port 8502
```

---

## Docker Setup Guide

Docker lets you run apps in isolated containers — no need to install Python, pip, or manage dependencies.

### Install Docker on Windows

1. Go to **https://www.docker.com/products/docker-desktop/**
2. Click **"Download for Windows"** and run the installer
3. During install, make sure **"Use WSL 2"** is checked (recommended)
4. After install, open **Docker Desktop** from Start Menu — wait for the whale icon in the taskbar to stop animating
5. Open **PowerShell** or **Command Prompt** and verify:
   ```bat
   docker --version
   docker compose version
   ```
   You should see version numbers — Docker is ready.

> **Windows requirement:** Windows 10/11 with WSL 2 enabled. If you see a WSL error during install, run in PowerShell as Administrator:
> ```powershell
> wsl --install
> ```
> Then restart your computer and try again.

### Install Docker on macOS

1. Go to **https://www.docker.com/products/docker-desktop/**
2. Choose **"Download for Mac"** — pick Apple Silicon (M1/M2/M3) or Intel depending on your Mac
3. Open the downloaded `.dmg` file, drag Docker to Applications
4. Launch Docker from Applications — wait for the whale icon in the menu bar to stop animating
5. Verify in Terminal:
   ```bash
   docker --version
   docker compose version
   ```

### Install Docker on Linux (Ubuntu/Debian)

```bash
# Install Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# Log out and back in, then verify
docker --version
docker compose version
```

### What is Docker?

Docker packages the app and all its dependencies (Python, libraries, configs) into a **container** — like a mini virtual machine that runs identically on any computer. No more "works on my machine" problems.

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

## How to Use

### Step 1 — Add your API keys

When you open the app for the first time, you'll be taken directly to **Settings**.
Add your Binance API key and Groq API key, then click **Save**.
The dashboard will load automatically — no restart needed.

### Step 2 — Read the Dashboard

The dashboard is organized from **top to bottom** by importance:

| Section | What to look at |
|---|---|
| **Wallet Overview** (top) | 5 cards: Cash, Coins (spot+earn), Earn, Futures (wallet+uPnL), Total |
| **P2P Lifetime Summary** | Total USDT deposited/withdrawn via P2P, VND & USD breakdown |
| **Trade Summary** | How much you've spent, received, and your overall P&L since account creation |
| **Spot Trader Analytics** | Win Rate, ROI, Profit Factor — tells you *why* you're winning or losing |
| **AI Health Score** | Grade A–D — overall portfolio risk score with tips |
| **Risk Distribution** | How much of your money is in Safe vs Risky assets |
| **All Assets table** | Every spot+earn coin with price, value, avg cost, and P&L (no futures notional) |
| **Futures Trade History** | Full income history across all 37+ traded symbols (365-day window) |
| **Spot Trade History** | Pick any coin to see every buy/sell you've made |
| **Risk Alerts** | Automatic warnings if something is wrong |
| **Rebalance Suggestions** | Exact BUY/SELL amounts to optimize your allocation |
| **AI Insights** | AI reads 7 signals and gives dollar-specific advice |
| **Tax Report** | Annual summary: deposits, withdrawals, converts, P2P (VND/USD), spot trades |
| **AI Chat** | Ask the AI anything about your portfolio |

### Step 3 — Understand your P&L

```
Are you profitable? Check: Net P&L (Trade Summary)
Which coins are making you money? Check: Top Winners (Trader Analytics)
Which coins are dragging you down? Check: Top Losers (Trader Analytics)
Is your portfolio risky? Check: Health Score + Risk Distribution
What should I do next? Check: AI Insights + Rebalance Suggestions
Need personalized advice? Ask the AI Chat
```

### Step 4 — Use the AI Chat

Click the chat box at the bottom of the dashboard and ask anything (Vietnamese or English):
- *"Tài khoản của tôi đang lãi hay lỗ?"*
- *"Coin nào tôi nên bán?"*
- *"My stable buffer is too low, what should I buy?"*
- *"Give me a full portfolio review."*

### Step 5 — Refresh data

- Data auto-refreshes every **60 seconds**
- Click **Refresh Data** in the sidebar to force an immediate reload
- Trade history is cached for **5 minutes** (trades don't change every second)

---

## Dashboard Metrics — Detailed Explanation

### 1. Wallet Overview (5 KPI Cards)

| Metric | Definition | Formula |
|---|---|---|
| **Cash** | Total stablecoin value (Spot + Earn only) | `Cash = SUM(spot_value + earn_value)` for `{USDT, USDC, BUSD, FDUSD, DAI, TUSD}` |
| **Coins** | Total non-stablecoin value (Spot + Earn only) | `Coins = SUM(spot_value + earn_value)` for non-stablecoins |
| **Earn** | Total value locked in Earn products | `Earn = earn_equity + earn_interest_gap + auto_invest_equity` |
| **Futures** | Futures wallet + unrealized P&L | `Futures = futures_wallet_usdt + futures_unrealized_pnl` |
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

### 8. Per-Asset Position Detail (All Assets Table)

The All Assets table uses **spot+earn only** to avoid futures notional inflation:

| Field | Formula |
|---|---|
| Holding Qty | `spot_qty + earn_qty` (NOT net — excludes futures) |
| Holding Value | `spot_value + earn_value` |
| % Port | `holding_value / total_spot_earn_value * 100` |
| Futures | Shown separately as `+qty L` or `-qty S` |
| Avg Cost | `total_buy_cost / total_buy_qty` (from trade history) |
| Unrealized P&L | `holding_value - (holding_qty * avg_cost)` |
| Realized P&L | `total_sell_revenue - (total_sell_qty * avg_cost)` |

> **Why spot+earn only?** If you hold 0.047 BTC long on futures, the old `net_value` calculation inflated BTC's value
> by the full notional (0.047 × $102k = $4.8k). The All Assets table now correctly shows only what you *physically hold*.

---

### 9. P2P Lifetime Summary

Sweeps your entire P2P C2C order history from 2021-01-01 to now in 29-day windows.

| Metric | Description |
|---|---|
| **USDT Deposited** | Total USDT you *received* from P2P buy orders (fiat → USDT) |
| **USDT Withdrawn** | Total USDT you *spent* on P2P sell orders (USDT → fiat) |
| **Net USDT Flow** | Deposited - Withdrawn (positive = net depositor) |
| **VND Spent** | Total Vietnamese Dong paid for USDT across all buy orders |
| **VND Received** | Total VND received from USDT sell orders |
| **USD Spent/Received** | Same breakdown for USD-denominated P2P trades |
| **Total Orders** | Count of all completed P2P orders |

Data is cached for 30 minutes. Use the **Refresh** button to force reload.

---

### 10. Futures Trade History

Uses `/fapi/v1/income` (365-day window) instead of `/fapi/v1/userTrades` which Binance purges for inactive pairs.

| Feature | Details |
|---|---|
| **Symbols covered** | All historically traded symbols (37+), not just currently open positions |
| **History depth** | 365 days via 7-day sliding windows with 0.35s sleep (rate-limit safe) |
| **Income types** | REALIZED_PNL, FUNDING_FEE, COMMISSION, TRANSFER |
| **Full flat table** | All entries sorted newest-first, color-coded by type, CSV export |
| **Per-symbol detail** | Dropdown to inspect P&L + funding + commissions for any symbol |
| **KPIs** | Total Realized P&L, Funding Fees, Commissions, Net Result |

> **Note:** Binance purges `/fapi/v1/userTrades` for pairs with no activity after ~3 months. The income API retains 365 days of data regardless.

---


### 11. Rebalance Planner

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

### 12. Tax Report

Annual tax summary (separate page, uses a dedicated read-only API key).

| Section | Details |
|---|---|
| **Deposits** | Count of fiat/crypto deposits with USDT equivalent |
| **Withdrawals** | Count + total withdrawal fees |
| **Converts/Swaps** | All Binance Convert transactions |
| **P2P Trades** | Buy/sell counts + amounts broken down by VND and USD |
| **Spot Buys** | Total USD spent buying coins (uses `fromId` pagination — no 24h limit) |
| **Spot Sells** | Total USD received selling coins |
| **Net Spot P&L** | Sells - Buys |
| **Total Trades** | All spot trades count |

> **Important:** Binance `/api/v3/myTrades` has a 24-hour max window when using `startTime`/`endTime`.
> We use `fromId` pagination instead (no time filter) to get all historical trades correctly.

CSV export available for all sections.

---

### 13. Binance Alpha Tracker

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
|-- app.py              <- Streamlit dashboard (UI, AI engine, chat, all pages)
|-- main.py             <- CLI summary report
|-- Dockerfile          <- Docker image definition
|-- docker-compose.yml  <- One-command Docker run
|-- .dockerignore       <- Files excluded from Docker build
|-- src/
|   |-- config.py       <- Env vars, PortfolioPolicy, STABLE_COINS
|   |-- fetcher.py      <- All Binance API fetchers:
|   |                      fetch_portfolio()          -- Spot, Futures, Earn, Funding, Auto-Invest
|   |                      fetch_futures_income()     -- 365-day income via 7-day windows
|   |                      fetch_futures_all_symbols()-- All historically traded symbols
|   |                      fetch_p2p_lifetime()       -- P2P history from 2021, all fiat currencies
|   |                      fetch_tax_data()           -- Annual tax summary (asyncio.gather)
|   |                      _fetch_spot_trades_tax()   -- fromId pagination, no 24h limit
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
# Wallet KPI Cards (5 cards, spot+earn only for holdings)
Cash (Stable)    = SUM(spot_value + earn_value) for stablecoins
Coins            = SUM(spot_value + earn_value) for non-stablecoins
Earn             = SUM(earn_value) across all assets
Futures          = futures_wallet_usdt + futures_unrealized_pnl
Total            = Cash + Coins + Earn + Futures

# All Assets Table (spot+earn only, NO futures notional inflation)
Holding Value    = spot_value + earn_value
Holding Qty      = spot_qty + earn_qty
% Port           = holding_value / SUM(all holding_values) * 100

# Full Portfolio Aggregation
Total Portfolio  = Spot + Earn + Earn_Interest_Gap + Futures_Wallet + Futures_uPnL

# P2P Lifetime Summary
Net USDT Flow    = usdt_bought - usdt_sold
                   (bought = USDT you received from fiat; sold = USDT you sent back to fiat)

# Trade Analytics
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
- **Participant UID**: `38021960`
- **GitHub**: [namtrung99/openclaw-portfolio-brain](https://github.com/namtrung99/openclaw-portfolio-brain)

---

**Disclaimer:** For informational purposes only. Not investment advice. Always DYOR.
