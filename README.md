# 🧠 OpenClaw Portfolio Brain

> **Binance AI Agent Skill** — Full-stack portfolio aggregator + risk analyzer + DCA/Rebalance planner  
> Built for the [Binance #AIBinance OpenClaw competition](https://www.binance.com/en/square/post/297854079538945) · Deadline: 2026-03-18

---

## What It Does

| Feature | Description |
|---|---|
| 📦 **Portfolio Aggregation** | Merges Spot + USDⓈ-M Futures + Simple Earn into one USDT-denominated snapshot |
| ⚖️ **Net Exposure** | Per-coin net = spot_qty + earn_qty + futures_long − futures_short |
| 🔴 **Risk Flags** | Stable % too low · Concentration > limit · Margin health · High leverage |
| 📋 **Rebalance Plan** | Policy-driven Buy/Sell suggestions with amount + reason |
| 💧 **DCA Mode** | Distribute new USDT to underweight assets based on target policy |

## Quick Start

```bash
# 1. Clone
git clone https://github.com/namtrung99/openclaw-portfolio-brain.git
cd openclaw-portfolio-brain

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run CLI (mock data — no API key needed)
python main.py

# 4. Run Streamlit dashboard
streamlit run app.py

# 5. Run with DCA plan ($500 USDT)
python main.py --dca 500
```

## Use Real Binance API

```bash
cp .env.example .env
# Edit .env: set BINANCE_API_KEY, BINANCE_SECRET_KEY, USE_MOCK_DATA=false
USE_MOCK_DATA=false streamlit run app.py
```

> ⚠️ Use a **read-only** API key (no trading permissions needed).

## Project Structure

```
openclaw-portfolio-brain/
├── skills/binance/portfolio-brain/
│   └── SKILL.md          ← OpenClaw AgentSkills definition
├── src/
│   ├── config.py          ← Env vars + PortfolioPolicy dataclass
│   ├── fetcher.py         ← Async Binance API fetcher (or mock)
│   ├── aggregator.py      ← Net exposure + risk flags
│   ├── planner.py         ← DCA / Rebalance plan generator
│   └── mock_data.py       ← Realistic demo data (no API key)
├── app.py                 ← Streamlit dashboard (dark Binance UI)
├── main.py                ← CLI report
├── requirements.txt
└── .env.example
```

## Sample CLI Output

```
╔══════════════════════════════════════════════════════╗
║  🧠  OpenClaw Portfolio Brain  —  Binance AI Skill   ║
╚══════════════════════════════════════════════════════╝

──────────────────────────────────────────────────────
  📊 PORTFOLIO SUMMARY
──────────────────────────────────────────────────────
  Total Equity     :    $62,847.50 USDT
  ├─ Spot          :    $54,127.00
  ├─ Earn          :     $6,520.00
  └─ Futures       :     $1,200.00  (uPnL +320.50)
  Stable %         :         8.3%

──────────────────────────────────────────────────────
  ⚠️  RISK FLAGS
──────────────────────────────────────────────────────
  🟡 [STABLE] Stable allocation 8.3% < minimum 10%
  🟡 [BTC] BTC at 71.0% exceeds policy max 45%

──────────────────────────────────────────────────────
  📋 REBALANCE PLAN
──────────────────────────────────────────────────────
  🔴 SELL  BTC    $16,394.00  Trim to target 37.5%
  🟢 BUY   ETH     $5,219.00  ETH underweight 3.2%
  🟢 BUY   STABLE  $8,127.00  Add USDT buffer
```

## OpenClaw Skill Integration

```bash
# Add to your OpenClaw agent
npx skills add https://github.com/namtrung99/openclaw-portfolio-brain

# Set API keys in openclaw.json or env
export BINANCE_API_KEY=your_key
export BINANCE_SECRET_KEY=your_secret
```

Then ask your OpenClaw agent:
- *"Show my portfolio"*
- *"What are my risk flags?"*
- *"Generate a rebalance plan"*
- *"DCA $500 into underweight assets"*

---

**⚠️ Disclaimer:** For informational purposes only. Not investment advice. DYOR. See [Binance Terms](https://www.binance.com/en/terms) and [Risk Warning](https://www.binance.com/en/risk-warning).
