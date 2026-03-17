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

# Cost basis: how much USDT was spent to acquire each asset (0 = fully airdropped)
MOCK_COST_BASIS = {
    "BTC":  42000.0,   # total USDT spent buying BTC
    "ETH":  6200.0,
    "BNB":  3100.0,
    "SOL":  0.0,       # fully airdropped / earned free
    "USDT": 1800.0,
    "USDC": 320.0,
}

# Airdrop quantities per asset (qty received for free)
MOCK_AIRDROP_QTY = {
    "SOL":  28.0,     # 100% airdrop
    "BNB":  2.0,      # partial airdrop
    "ETH":  0.5,      # from Earn rewards
}

# Risk classification
# "safe"   = BTC, ETH, BNB, stablecoins (large cap, well-established)
# "medium" = top-50 altcoins by market cap
# "risky"  = small/mid-cap alts, new coins, meme coins
RISK_LEVEL = {
    # Stablecoins -> always safe
    "USDT":  "safe", "USDC": "safe", "BUSD": "safe",
    "FDUSD": "safe", "DAI":  "safe", "TUSD": "safe",
    # Top-tier
    "BTC":   "safe", "ETH":  "safe", "BNB":  "safe",
    # Top-20 large-cap alts
    "SOL":   "medium", "XRP":  "medium", "ADA":  "medium",
    "DOGE":  "medium", "SHIB": "medium", "TRX":  "medium",
    "TON":   "medium", "AVAX": "medium", "LINK": "medium",
    "DOT":   "medium", "MATIC":"medium", "POL":  "medium",
    "LTC":   "medium", "UNI":  "medium", "ATOM": "medium",
    "NEAR":  "medium", "APT":  "medium", "ARB":  "medium",
    "OP":    "medium", "SUI":  "medium",
    # Everything else = risky by default (see get_risk_level())
}

# Keep MOCK_RISK_LEVEL as alias for backward compat
MOCK_RISK_LEVEL = RISK_LEVEL


# ── Binance Alpha program coins ──────────────────────────────────────────────
# Source: coinmarketcap.com/view/binance-alpha/ (381 tokens as of Mar 2026)
# Binance Alpha = early-access tokens available on Binance Alpha portal
# NOT the same as regular Binance spot listings
BINANCE_ALPHA_COINS = {
    # ── User wallet confirmed Alpha holdings ──
    "BERA",      # Berachain
    "LISTA",     # Lista DAO
    "PROVE",     # Proven
    "NFP",       # NFPrompt
    "AEVO",      # Aevo Exchange
    "TOWNS",     # Towns Protocol
    "MITO",      # Mitosis
    "C",         # C token
    "ENA",       # Ethena
    "SIGN",      # Sign Protocol
    "HAEDAL",    # Haedal Protocol
    "TST",       # The Standard Token
    "KMNO",      # Kamino Finance
    "IP",        # Story Protocol
    "LAYER",     # Solayer
    "WAL",       # Walrus
    "INIT",      # Initia
    "PARTI",     # Particle Network
    "NIL",       # =nil; Foundation
    "DOOD",      # Doodles
    # ── Other confirmed Binance Alpha tokens (CMC) ──
    "ATH",       # Aethir
    "GRASS",     # Grass
    "VVV",       # Venice Token
    "FARTCOIN",  # Fartcoin
    "PIPPIN",    # Pippin
    "SKR",       # Seeker (Solana Mobile)
    "DEGEN",     # Degen (Base)
    "FLUID",     # Fluid (Instadapp)
    "AERO",      # Aerodrome Finance
    "SPX",       # SPX6900
    "ZETA",      # ZetaChain
    "DRIFT",     # Drift Protocol
    "PEAQ",      # peaq network
    "SAFE",      # Safe
    "SQD",       # Subsquid
    "KGEN",      # KGeN
    "CARV",      # CARV Protocol
    "POKT",      # Pocket Network
    "IRYS",      # Irys
    "ARC",       # AI Rig Complex
    "ZORA",      # ZORA
    "TAIKO",     # Taiko
    "MOG",       # Mog Coin
    "POPCAT",    # Popcat (SOL)
    "MOODENG",   # Moo Deng
    "MEW",       # cat in a dogs world
    "SOON",      # SOON
    "ALCH",      # Alchemist AI
    "GWEI",      # ETHGas
    "ALEO",      # Aleo
    "VELO",      # Velo
    "RAVE",      # RaveDAO
    "BTW",       # Bitway
    "COAI",      # ChainOpera AI
    "MERL",      # Merlin Chain
    "BTR",       # Bitlayer
    "BEAT",      # Audiera
    "RIVER",     # River
    "UAI",       # UnifAI Network
    "ICNT",      # Impossible Cloud Network
    "YZY",       # YZY MONEY
}

def get_risk_level(asset: str) -> str:
    """Get risk level for an asset. Defaults to 'risky' for unknown coins."""
    from src.config import STABLE_COINS
    if asset in STABLE_COINS:
        return "safe"
    return RISK_LEVEL.get(asset, "risky")

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
