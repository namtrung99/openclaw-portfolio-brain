"""
chatbot.py — AI Portfolio Chatbot powered by Google Gemini.
Builds a rich portfolio context string and sends multi-turn conversations
to Gemini 2.0 Flash, returning streamed or full text replies.
"""
from __future__ import annotations

import time as _time
from typing import Any

# ─────────────────────────────────────────────────────────────────────────────
#  System prompt template
# ─────────────────────────────────────────────────────────────────────────────

_SYSTEM_TEMPLATE = """\
You are an expert crypto portfolio advisor for a Binance user.
Your job is to answer questions about their live portfolio concisely and helpfully.

RULES:
- Always reference real numbers from the portfolio context provided.
- Give actionable, specific advice (amounts, percentages, coin names).
- Be direct — no fluff, no disclaimers beyond one brief "not financial advice" at the end.
- Format responses with markdown: bold key numbers, bullet points for lists.
- If asked about a coin not in the portfolio, answer generically but remind the user it's not in their holdings.
- Respond in the same language the user writes in (Vietnamese or English).

CURRENT PORTFOLIO SNAPSHOT:
{portfolio_context}
"""

# ─────────────────────────────────────────────────────────────────────────────
#  Portfolio context builder
# ─────────────────────────────────────────────────────────────────────────────

def build_portfolio_context(snap: Any, cb_summary: dict, health: dict) -> str:
    """
    Serialize the live portfolio snapshot into a compact text block
    that fits comfortably in a Gemini system prompt.
    """
    total = snap.total_equity_usdt or 1.0

    # Top holdings
    top_positions = sorted(
        [(a, p) for a, p in snap.positions.items() if abs(p.net_value) > 1],
        key=lambda x: -abs(x[1].net_value),
    )[:15]

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
#  Gemini chat
# ─────────────────────────────────────────────────────────────────────────────

def chat_with_gemini(
    messages: list[dict],
    portfolio_context: str,
    api_key: str,
) -> str:
    """
    Send the full conversation history to Gemini 2.0 Flash and return the reply.

    Args:
        messages:          List of {"role": "user"|"assistant", "content": "..."} dicts.
        portfolio_context: Output of build_portfolio_context().
        api_key:           Google Gemini API key.

    Returns:
        The model's text reply, or an error message string.
    """
    try:
        from google import genai
        from google.genai import types
    except ImportError:
        return "❌ `google-genai` package not installed. Run `pip install google-genai`."

    MAX_RETRIES = 3
    for attempt in range(MAX_RETRIES):
        try:
            client = genai.Client(api_key=api_key)

            system_prompt = _SYSTEM_TEMPLATE.format(portfolio_context=portfolio_context)

            # Convert session messages → Gemini Contents
            contents: list[types.Content] = []
            for msg in messages:
                role = "user" if msg["role"] == "user" else "model"
                contents.append(
                    types.Content(role=role, parts=[types.Part(text=msg["content"])])
                )

            response = client.models.generate_content(
                model="gemini-2.0-flash",
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    max_output_tokens=1024,
                    temperature=0.7,
                ),
                contents=contents,
            )
            return response.text or "_(no response)_"

        except Exception as exc:
            error_str = str(exc)
            is_rate_limit = "429" in error_str or "quota" in error_str.lower() or "rate" in error_str.lower()
            if is_rate_limit and attempt < MAX_RETRIES - 1:
                _time.sleep(3 * (2 ** attempt))  # 3s, 6s, 12s backoff
                continue
            if "API_KEY_INVALID" in error_str or "API key" in error_str.lower():
                return "❌ Invalid Gemini API key. Please check your key in ⚙️ Settings."
            if is_rate_limit:
                return "⚠️ Gemini rate limit — retried 3 times. Please wait 30s and try again."
            return f"❌ Error: {error_str}"

    return "❌ Unexpected error."
