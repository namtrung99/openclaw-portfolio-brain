# 🧠 OpenClaw Portfolio Brain

> **AI-powered Binance portfolio analyzer** — aggregates Spot + Futures + Earn into one dashboard,  
> scores your portfolio health with an AI engine, and gives actionable rebalance suggestions.  
> Built for the [Binance #AIBinance competition](https://www.binance.com/en/square/post/297854079538945) · Deadline: 2026-03-18

[![Python 3.11](https://img.shields.io/badge/python-3.11-F0B90B?logo=python&logoColor=white)](https://python.org)
[![Streamlit](https://img.shields.io/badge/streamlit-1.32+-F0B90B?logo=streamlit&logoColor=white)](https://streamlit.io)
[![Binance API](https://img.shields.io/badge/binance-api-F0B90B?logo=binance&logoColor=white)](https://binance.com)

---

## 🎥 Live Demo

> 🌐 [http://localhost:8502](http://localhost:8502) — run locally with your own API key  
> 📁 [GitHub](https://github.com/namtrung99/openclaw-portfolio-brain)

---

## ✨ Features

| Module | What it does |
|---|---|
| 📦 **Portfolio Aggregation** | Merges Spot + USDⓈ-M Futures + Simple Earn into one USDT snapshot |
| 🤖 **AI Health Score** | Scores your portfolio 0–100 across 5 dimensions, grades A/B/C/D |
| 🤖 **AI Insights Engine** | Rule-based AI that reads portfolio signals → outputs specific, dollar-sized advice |
| 📊 **Risk Distribution** | Classifies every holding as Safe / Medium / Risky with value breakdown |
| 📈 **Trade Summary** | Total spent, received, realized P&L, unrealized P&L, net P&L from inception |
| ⚖️ **Rebalance Planner** | Policy-driven Buy/Sell suggestions with exact USDT amounts |
| 🔶 **Binance Alpha Tracker** | Shows only true Alpha coins (filters out graduated-to-spot) |
| 🕐 **Trade History** | Per-coin buy/sell log with avg cost, fees, and P&L |
| 🌙 **Dark Binance Theme** | Pixel-perfect dark UI matching Binance's color palette |
| 🔄 **Auto-refresh** | Wallet data refreshes every 60s, trades cached 5 min |

---

## 🤖 AI Health Score — How It Works

The Health Score is a **0–100 composite score** computed across 5 independent dimensions.  
No LLM is used — the AI engine is a deterministic rule system that mirrors how a professional risk manager thinks.

```
Score = Stable Buffer (25pts) + Risk Mix (25pts) + Diversification (20pts)
      + P&L Health (20pts) + Futures Exposure (10pts)
```

### Scoring Breakdown

#### 1. Stable Buffer — max 25 pts
Measures what % of your portfolio is in USDT/stablecoins.

| Range | Score | Reason |
|---|---|---|
| 15% – 30% | **25** ✅ | Ideal buffer: enough to buy dips, not too much idle |
| 10% – 15% | 15 ⚠️ | Below recommended — add USDT |
| > 40% | 15 ⚠️ | Too conservative — capital not working |
| < 10% | 5 🔴 | Danger zone — no dry powder if market drops |

#### 2. Risk Mix — max 25 pts
Measures the ratio of **safe assets** (BTC, ETH, BNB, stables) in your portfolio.

| Safe % | Score | Reason |
|---|---|---|
| ≥ 50% | **25** ✅ | Well protected, solid base |
| 30–50% | 15 ⚠️ | Moderate — watch altcoin exposure |
| < 30% | 5 🔴 | High volatility risk |

#### 3. Diversification — max 20 pts
Counts positions worth > $10 USDT.

| Positions | Score | Reason |
|---|---|---|
| 5 – 15 | **20** ✅ | Optimal: enough spread, not over-diversified |
| < 5 | 10 ⚠️ | Too concentrated in few assets |
| > 15 | 10 ⚠️ | Hard to manage, returns diluted |

#### 4. P&L Health — max 20 pts
Net P&L as % of total amount ever invested.

| Net P&L % | Score | Reason |
|---|---|---|
| ≥ 0% | **20** ✅ | In profit overall |
| −25% to 0% | 12 ⚠️ | Moderate loss — manageable |
| −50% to −25% | 6 🔴 | Significant drawdown |
| < −50% | 2 🔴 | Heavy loss — review strategy |

#### 5. Futures Exposure — max 10 pts
Futures wallet as % of total portfolio.

| Futures % | Score | Reason |
|---|---|---|
| 0% (no position) | **10** ✅ | No leverage risk |
| < 10% | **10** ✅ | Low leverage — acceptable |
| 10–25% | 6 ⚠️ | Moderate — monitor liquidation prices |
| > 25% | 2 🔴 | High leverage — dangerous in volatile market |

### Grades

| Score | Grade | Label |
|---|---|---|
| 75–100 | **A** 🟢 | Healthy |
| 55–74 | **B** 🟡 | Moderate |
| 35–54 | **C** 🟠 | At Risk |
| 0–34 | **D** 🔴 | Danger |

---

## 🤖 AI Insights Engine

Beyond the score, the AI Insights Engine generates **specific, dollar-sized recommendations** by analyzing:

- **Stable buffer shortage** → tells you exactly how much USDT to move
- **Concentration risk** → names the asset, shows exact loss scenario (e.g. "if BTC drops 30%, you lose $X")
- **P&L context** → different advice for -10% vs -50% drawdown
- **Futures over-leverage** → flags when notional exposure exceeds 30% of portfolio
- **Altcoin overweight** → warns when risky assets exceed 40% of portfolio
- **Positive feedback** → when portfolio is healthy, suggests profit-taking levels

---

## 🚀 Quick Start

```bash
# 1. Clone
git clone https://github.com/namtrung99/openclaw-portfolio-brain.git
cd openclaw-portfolio-brain

# 2. Create virtualenv and install
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 3. Run dashboard
streamlit run app.py --server.port 8502
```

Open `http://localhost:8502` → click **⚙️ API Settings** in sidebar → paste your Binance API keys → Save.

---

## 🔑 API Key Setup

1. Go to [Binance → API Management](https://www.binance.com/en/my/settings/api-management)
2. Create a new API key — enable **Read Info** only (no trading permissions needed)
3. In the app: sidebar → **⚙️ API Settings** → paste key + secret → **💾 Save Keys**

Or manually create `.env`:
```env
BINANCE_API_KEY=your_api_key_here
BINANCE_SECRET_KEY=your_secret_key_here
USE_MOCK_DATA=false
```

> ⚠️ Always use a **read-only** key. This app never places orders.

---

## 📁 Project Structure

```
openclaw-portfolio-brain/
├── app.py                 ← Streamlit dashboard (dark Binance UI + AI engine)
├── main.py                ← CLI report
├── src/
│   ├── config.py          ← Env vars, PortfolioPolicy, STABLE_COINS
│   ├── fetcher.py         ← Async Binance API (Spot + Futures + Earn + myTrades)
│   ├── aggregator.py      ← Net exposure per coin, risk flags
│   ├── planner.py         ← Rebalance + DCA plan generator
│   └── mock_data.py       ← RISK_LEVEL map, BINANCE_ALPHA_COINS list
├── requirements.txt
├── .env                   ← Your API keys (gitignored)
└── .env.example
```

---

## 🧮 Key Formulas

```
Net Position     = spot_qty + earn_qty + futures_long − futures_short
Net Value (USDT) = net_position × current_price_usdt
Stable %         = sum(stablecoin_values) / total_equity × 100
Unrealized P&L   = current_value − (avg_cost × current_qty)
Realized P&L     = total_received_from_sells − cost_of_sold_coins
Net P&L          = realized_pnl + unrealized_pnl
AI Health Score  = Σ(5 dimension scores)  [0–100]
```

---

## 🏆 Competition Info

- **Competition**: [Binance #AIBinance OpenClaw Skills](https://www.binance.com/en/square/post/297854079538945)
- **Deadline**: 2026-03-18 23:59 UTC
- **Prize**: 1st = 10 BNB
- **Participant UID**: `718475870`
- **GitHub**: [namtrung99/openclaw-portfolio-brain](https://github.com/namtrung99/openclaw-portfolio-brain)

---

**⚠️ Disclaimer:** For informational purposes only. Not investment advice. DYOR.  
See [Binance Terms](https://www.binance.com/en/terms) and [Risk Warning](https://www.binance.com/en/risk-warning).
