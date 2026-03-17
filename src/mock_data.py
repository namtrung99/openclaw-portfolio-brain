"""
mock_data.py — Realistic mock portfolio data for demo (no API key needed).
Simulates: BTC/ETH heavy portfolio with some Futures positions and Earn.
"""

MOCK_SPOT_ACCOUNT = {
    "accountType": "SPOT",
    "balances": [
        {"asset": "BTC",   "free": "0.52",    "locked": "0.00"},
        {"asset": "ETH",   "free": "3.80",    "locked": "0.00"},
        {"asset": "BNB",   "free": "12.50",   "locked": "0.00"},
        {"asset": "SOL",   "free": "28.00",   "locked": "0.00"},
        {"asset": "USDT",  "free": "1480.00", "locked": "0.00"},
        {"asset": "USDC",  "free": "320.00",  "locked": "0.00"},
    ]
}

MOCK_FUTURES_ACCOUNT = {
    "totalWalletBalance":    "1200.00",
    "totalUnrealizedProfit": "320.50",
    "totalMarginBalance":    "1520.50",
    "availableBalance":      "680.00",
    "totalMaintMargin":      "210.00",
    "assets": [
        {"asset": "USDT", "walletBalance": "1200.00", "unrealizedProfit": "320.50"}
    ]
}

MOCK_FUTURES_POSITIONS = [
    {
        "symbol":           "BTCUSDT",
        "positionSide":     "BOTH",
        "positionAmt":      "0.10",        # Long 0.10 BTC
        "entryPrice":       "80000.00",
        "markPrice":        "84200.00",
        "unRealizedProfit": "420.00",
        "notional":         "8420.00",
        "leverage":         "3",
        "isolatedMargin":   "0",
        "liquidationPrice": "55000.00",
        "marginType":       "cross",
    },
    {
        "symbol":           "ETHUSDT",
        "positionSide":     "BOTH",
        "positionAmt":      "-1.00",       # Short 1.0 ETH
        "entryPrice":       "2100.00",
        "markPrice":        "1995.00",
        "unRealizedProfit": "105.00",
        "notional":         "1995.00",
        "leverage":         "2",
        "isolatedMargin":   "0",
        "liquidationPrice": "3200.00",
        "marginType":       "cross",
    },
    {
        "symbol":           "SOLUSDT",
        "positionSide":     "BOTH",
        "positionAmt":      "10.00",       # Long 10 SOL
        "entryPrice":       "135.00",
        "markPrice":        "148.50",
        "unRealizedProfit": "135.00",
        "notional":         "1485.00",
        "leverage":         "2",
        "isolatedMargin":   "0",
        "liquidationPrice": "68.00",
        "marginType":       "cross",
    },
]

MOCK_EARN_FLEXIBLE = {
    "rows": [
        {"asset": "USDT", "totalAmount": "500.00",  "latestAnnualPercentageRate": "0.0312", "canRedeem": True},
        {"asset": "ETH",  "totalAmount": "0.50",    "latestAnnualPercentageRate": "0.0180", "canRedeem": True},
        {"asset": "BNB",  "totalAmount": "2.00",    "latestAnnualPercentageRate": "0.0095", "canRedeem": True},
    ]
}

MOCK_EARN_LOCKED = {
    "rows": [
        {"asset": "BNB",  "amount": "5.00",   "annualInterestRate": "0.0420", "redeemDate": "2026-04-15"},
        {"asset": "USDT", "amount": "200.00", "annualInterestRate": "0.0580", "redeemDate": "2026-03-30"},
    ]
}

MOCK_MARK_PRICES = {
    "BTCUSDT": "84200.00",
    "ETHUSDT": "1995.00",
    "BNBUSDT": "582.00",
    "SOLUSDT": "148.50",
    "USDTUSDT": "1.00",
    "USDCUSDT": "1.00",
}

MOCK_SPOT_PRICES = {
    "BTC":   84200.0,
    "ETH":   1995.0,
    "BNB":   582.0,
    "SOL":   148.5,
    "USDT":  1.0,
    "USDC":  1.0,
    "FDUSD": 1.0,
    "BUSD":  1.0,
}
