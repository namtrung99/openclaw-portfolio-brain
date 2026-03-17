---
name: portfolio-brain
description: >
  Aggregates your full Binance portfolio across Spot balances, USDⓈ-M Futures
  positions (with unrealized PnL, mark price), and Simple Earn holdings into a
  single USD-denominated snapshot. Calculates net exposure per coin, concentration
  risk, leverage alerts, and generates DCA/Rebalance trade plans based on your
  target policy.
metadata:
  version: 0.1.0
  author: namtrung99
  openclaw:
    requires:
      env: ["BINANCE_API_KEY", "BINANCE_SECRET_KEY"]
    primaryEnv: "BINANCE_API_KEY"
    emoji: "🧠"
license: MIT
---

# 🧠 Binance Portfolio Brain Skill

> **AI-powered portfolio aggregator + risk analyzer + DCA/Rebalance planner for Binance.**

## Overview

| Source         | Data Fetched                                             |
|----------------|----------------------------------------------------------|
| Spot           | All non-zero balances + USDT value                       |
| USDⓈ-M Futures | Open positions, mark price, unrealized PnL, leverage     |
| Simple Earn    | Flexible + Locked holdings (USDT-equivalent)             |
| Market         | Live mark/spot prices for valuation                      |

## Quick Reference

| Natural Language Command            | What it does                                          |
|-------------------------------------|-------------------------------------------------------|
| `Show my portfolio`                 | Full snapshot: equity, allocation, top positions      |
| `What are my risk flags?`           | Concentration > limit, stable %, margin health        |
| `Generate rebalance plan`           | Buy/Sell suggestions to reach target policy           |
| `What is my BTC net exposure?`      | Spot + Futures long/short net in BTC + USDT           |
| `DCA plan for this week`            | Distribute available stable to underweight assets     |

## Authentication

**Base URLs:**
- Spot/Earn: `https://api.binance.com`
- Futures:   `https://fapi.binance.com`

**Environment Variables Required:**
```
BINANCE_API_KEY=your_api_key_here
BINANCE_SECRET_KEY=your_secret_key_here
```
> ⚠️ Use a **read-only** API key (Enable Read only; disable trading/withdrawal).

## Endpoints Used

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/v3/account` | ✅ | Spot balances |
| GET | `/api/v3/ticker/price` | ❌ | Spot prices |
| GET | `/sapi/v1/simple-earn/flexible/position` | ✅ | Flexible Earn positions |
| GET | `/sapi/v1/simple-earn/locked/position` | ✅ | Locked Earn positions |
| GET | `/fapi/v3/account` | ✅ | Futures wallet + margin summary |
| GET | `/fapi/v3/positionRisk` | ✅ | Open futures positions |
| GET | `/fapi/v1/premiumIndex` | ❌ | Mark price + funding rate |

## Signing Requests
1. Build query string with all params + `timestamp` (Unix ms)
2. Sign with `HMAC-SHA256` using `BINANCE_SECRET_KEY`
3. Append `&signature=<hex_digest>`
4. Add header: `X-MBX-APIKEY: <BINANCE_API_KEY>`
5. User-Agent: `binance-portfolio-brain/0.1.0 (Skill)`

## Security Notes
- API Key display: show first 5 + last 4 chars only: `su1Qc...8akf`
- Secret Key: always fully masked: `***...aws1`
- All signals are for **reference only** — not investment advice.
