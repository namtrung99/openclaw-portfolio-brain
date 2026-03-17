"""
chatbot.py — AI Portfolio Chatbot powered by Groq (free, fast inference).
Builds a compact portfolio context and sends multi-turn conversations
to Groq's LLaMA 3.3 70B model, returning full text replies.
"""
from __future__ import annotations

import time as _time
from typing import Any

# ── Client-side rate limiter ──────────────────────────────────────────────────
_last_call_ts: float = 0.0
_MIN_INTERVAL: float = 2.0  # seconds between calls

# ─────────────────────────────────────────────────────────────────────────────
#  System prompt template
# ─────────────────────────────────────────────────────────────────────────────

_SYSTEM_TEMPLATE = """\
You are an expert crypto portfolio advisor for a Binance user.
Answer questions about their live portfolio concisely and helpfully.

RULES:
- Reference real numbers from the portfolio context below.
- Give actionable, specific advice (amounts, percentages, coin names).
- Be direct — one brief "not financial advice" disclaimer max.
- Use markdown: bold key numbers, bullet points for lists.
- If a coin is not in their portfolio, say so.
- Respond in the same language the user writes (Vietnamese or English).

CURRENT PORTFOLIO:
{portfolio_context}
"""

# ─────────────────────────────────────────────────────────────────────────────
#  Portfolio context builder
# ─────────────────────────────────────────────────────────────────────────────

def build_portfolio_context(snap: Any, cb_summary: dict, health: dict) -> str:
    """
    Serialize the live portfolio snapshot into a compact text block
    that fits comfortably in a system prompt.
    """
    total = snap.total_equity_usdt or 1.0

    # Top holdings
    top_positions = sorted(
        [(a, p) for a, p in snap.positions.items() if abs(p.net_value) > 1],
        key=lambda x: -abs(x[1].net_value),
    )[:12]

    holdings_lines = "\n".join(
        f"  - {asset}: ${abs(pos.net_value):,.0f} ({abs(pos.net_value) / total * 100:.1f}%)"
        f"  qty={pos.net_qty:.4f}  price=${pos.price_usdt:,.2f}"
        for asset, pos in top_positions
    )

    # P&L
    total_spent    = cb_summary.get("total_spent", 0)
    net_pnl        = cb_summary.get("net_pnl", 0)
    realized_pnl   = cb_summary.get("realized_pnl", 0)
    unrealized_pnl = cb_summary.get("unrealized_pnl", 0)
    pnl_pct        = net_pnl / total_spent * 100 if total_spent > 0 else 0

    # Stable buffer
    stable_pct = snap.stable_pct

    # Health
    grade       = health.get("grade", "?")
    score       = health.get("score", 0)
    health_label = health.get("label", "")

    context = f"""\
Total portfolio value : ${total:,.2f} USDT
Health score          : {score}/100 (Grade {grade} — {health_label})
Stable buffer         : {stable_pct:.1f}%
Futures wallet        : ${snap.futures_wallet_usdt:,.2f} USDT

TOP HOLDINGS:
{holdings_lines}

P&L SUMMARY:
  Total invested  : ${total_spent:,.2f}
  Realized P&L    : ${realized_pnl:+,.2f}
  Unrealized P&L  : ${unrealized_pnl:+,.2f}
  Net P&L         : ${net_pnl:+,.2f} ({pnl_pct:+.1f}%)
"""
    return context


# ─────────────────────────────────────────────────────────────────────────────
#  Groq chat
# ─────────────────────────────────────────────────────────────────────────────

def chat_with_groq(
    messages: list[dict],
    portfolio_context: str,
    api_key: str,
) -> str:
    """
    Send the conversation history to Groq (LLaMA 3.3 70B) and return the reply.

    Args:
        messages:          List of {"role": "user"|"assistant", "content": "..."} dicts.
        portfolio_context: Output of build_portfolio_context().
        api_key:           Groq API key.

    Returns:
        The model's text reply, or an error message string.
    """
    try:
        from groq import Groq
    except ImportError:
        return "`groq` package not installed. Run `pip install groq`."

    global _last_call_ts

    # Client-side rate limit
    elapsed = _time.time() - _last_call_ts
    if elapsed < _MIN_INTERVAL:
        _time.sleep(_MIN_INTERVAL - elapsed)

    MAX_RETRIES = 2
    # Keep last 6 messages to control token usage
    recent = messages[-6:] if len(messages) > 6 else messages

    system_prompt = _SYSTEM_TEMPLATE.format(portfolio_context=portfolio_context)

    groq_messages = [{"role": "system", "content": system_prompt}]
    for msg in recent:
        groq_messages.append({
            "role": msg["role"],  # user / assistant — same as Groq expects
            "content": msg["content"],
        })

    for attempt in range(MAX_RETRIES):
        try:
            client = Groq(api_key=api_key)
            _last_call_ts = _time.time()

            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=groq_messages,
                max_tokens=1024,
                temperature=0.7,
            )
            text = response.choices[0].message.content
            return text or "_(no response)_"

        except Exception as exc:
            error_str = str(exc)
            is_rate_limit = "429" in error_str or "rate" in error_str.lower()

            if is_rate_limit and attempt < MAX_RETRIES - 1:
                _time.sleep(10)
                continue

            if "invalid_api_key" in error_str.lower() or "authentication" in error_str.lower():
                return "Invalid Groq API key. Please update it in Settings."
            if is_rate_limit:
                return "Groq rate limit reached. Please wait a moment and try again."
            return f"Groq error: {error_str[:150]}"

    return "Could not get a response. Please try again."
