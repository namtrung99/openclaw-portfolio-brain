"""
config.py — Load environment variables and define default portfolio policy.
"""
import os
from dataclasses import dataclass, field
from typing import Dict, Tuple
from dotenv import load_dotenv

load_dotenv()

# ── Binance API credentials ────────────────────────────────────────────────────
BINANCE_API_KEY    = os.getenv("BINANCE_API_KEY", "")
BINANCE_SECRET_KEY = os.getenv("BINANCE_SECRET_KEY", "")
USE_MOCK_DATA      = os.getenv("USE_MOCK_DATA", "true").lower() == "true"

# ── API base URLs ──────────────────────────────────────────────────────────────
SPOT_BASE_URL    = "https://api.binance.com"
FUTURES_BASE_URL = "https://fapi.binance.com"
USER_AGENT       = "binance-portfolio-brain/0.1.0 (Skill)"

# ── Stable coins list ──────────────────────────────────────────────────────────
STABLE_COINS = {"USDT", "USDC", "BUSD", "DAI", "TUSD", "FDUSD"}


@dataclass
class PortfolioPolicy:
    """
    Target allocation policy (min%, max%) per asset or category.
    Planner will generate Buy/Sell suggestions to bring portfolio within these bounds.
    """
    # (min_pct, max_pct) — as fractions of total equity, e.g. 0.35 = 35%
    allocations: Dict[str, Tuple[float, float]] = field(default_factory=lambda: {
        "BTC":      (0.30, 0.45),   # Bitcoin
        "ETH":      (0.10, 0.25),   # Ethereum
        "BNB":      (0.05, 0.10),   # BNB
        "STABLE":   (0.15, 0.25),   # All stablecoins combined
    })
    max_single_alt_pct: float = 0.08       # Any single alt ≤ 8%
    min_stable_pct:     float = 0.10       # Alert if stable < 10%
    max_futures_leverage: float = 5.0      # Alert if effective leverage > 5×
    margin_health_threshold: float = 0.30  # Alert if available/total margin < 30%


# Default policy instance
DEFAULT_POLICY = PortfolioPolicy()
