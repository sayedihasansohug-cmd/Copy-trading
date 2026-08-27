"""
AI prompt definitions for the Solana meme-coin trading engine.

This module contains:
- System instructions
- Market-analysis prompt builder
- Strict JSON response schema
- Risk-aware decision instructions

IMPORTANT:
This module does NOT execute trades.
It only prepares prompts for the AI decision layer.
"""

from __future__ import annotations

import json
from typing import Any, Mapping


# ---------------------------------------------------------------------------
# AI RESPONSE SCHEMA
# ---------------------------------------------------------------------------

AI_RESPONSE_SCHEMA: dict[str, Any] = {
    "decision": "BUY | SELL | HOLD | REJECT",
    "confidence": 0.0,
    "risk_score": 0.0,
    "signal_quality": "A | B | C | D | F",
    "entry_score": 0.0,
    "liquidity_score": 0.0,
    "momentum_score": 0.0,
    "volume_score": 0.0,
    "holder_score": 0.0,
    "safety_score": 0.0,
    "recommended_entry": None,
    "stop_loss_percent": None,
    "take_profit_percent": None,
    "max_position_percent": None,
    "time_horizon_minutes": None,
    "reasons": [],
    "warnings": [],
    "invalidating_conditions": [],
}


# ---------------------------------------------------------------------------
# SYSTEM PROMPT
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """
You are an advanced crypto market-analysis engine specializing in
high-risk Solana meme coins.

Your job is to analyze supplied market and token data and return a
STRICTLY STRUCTURED trading analysis.

You are NOT allowed to invent missing market data.

You must distinguish between:

1. Facts supplied by the data
2. Reasonable market inference
3. Unknown information

If important information is missing, reduce confidence and increase risk.

You must NEVER guarantee profit.

You must NEVER claim that a trade is certain to win.

You must prioritize capital preservation over trade frequency.

Your possible decisions are:

BUY
SELL
HOLD
REJECT

Use REJECT when the token appears unsafe, data quality is insufficient,
liquidity is inadequate, manipulation risk is excessive, or important
risk controls fail.

For BUY decisions:

- Do not assume the token will rise.
- Evaluate liquidity.
- Evaluate volume.
- Evaluate momentum.
- Evaluate holder concentration when available.
- Evaluate token safety information when available.
- Evaluate market-cap/liquidity relationship.
- Look for abnormal volume or possible manipulation.
- Consider whether entry conditions are already extended.
- Define invalidating conditions.
- Define stop-loss and take-profit levels only when sufficient data exists.
- Never recommend risking the entire portfolio.

For SELL decisions:

- Determine whether momentum or market structure has deteriorated.
- Consider liquidity and exit risk.
- Consider whether the position should be reduced rather than completely
  closed when appropriate.

For HOLD decisions:

- Explain what information or market condition is missing.
- Specify what would cause a transition to BUY or SELL.

For REJECT decisions:

- Clearly identify the main risk factors.
- Do not recommend entering the position.

CONFIDENCE RULES:

confidence must be between 0.0 and 1.0.

Confidence is NOT probability of profit.

A high confidence score means the supplied evidence strongly supports
the analytical conclusion, not that the trade is guaranteed to succeed.

RISK SCORE:

risk_score must be between 0.0 and 1.0.

0.0 = comparatively low risk
1.0 = extremely high risk

For meme coins, high risk is normal. Do not artificially assign a low
risk score simply because momentum is strong.

SCORING:

entry_score       = quality of current entry
liquidity_score   = quality of available liquidity
momentum_score    = strength and consistency of momentum
volume_score      = quality of volume
holder_score      = holder distribution quality
safety_score      = token/security quality

All scores must be between 0.0 and 1.0.

SIGNAL QUALITY:

A = exceptionally strong setup
B = good setup
C = mixed/uncertain setup
D = weak setup
F = unacceptable setup

IMPORTANT:

Never create fake values for unavailable fields.

If data is unavailable, use null where appropriate and explain it in
warnings.

RETURN ONLY VALID JSON.

Do not use Markdown.

Do not add explanations outside the JSON object.
"""


# ---------------------------------------------------------------------------
# MARKET DATA PROMPT
# ---------------------------------------------------------------------------

def build_market_analysis_prompt(
    market_data: Mapping[str, Any],
) -> str:
    """
    Build a structured market-analysis prompt.

    Parameters
    ----------
    market_data:
        Dictionary containing market/token information.

    Returns
    -------
    str
        Prompt to send to the AI model.
    """

    if not isinstance(market_data, Mapping):
        raise TypeError("market_data must be a mapping/dictionary")

    clean_data = _sanitize_market_data(market_data)

    payload = json.dumps(
        clean_data,
        ensure_ascii=False,
        indent=2,
        default=str,
    )

    return f"""
Analyze the following Solana token using the rules provided in the
system instructions.

MARKET DATA:

{payload}

ANALYSIS REQUIREMENTS:

1. Determine whether the supplied data is sufficient.
2. Evaluate liquidity.
3. Evaluate volume and volume consistency.
4. Evaluate price momentum.
5. Evaluate market-cap/liquidity relationship.
6. Evaluate holder distribution if supplied.
7. Evaluate token safety information if supplied.
8. Look for signs of abnormal activity or possible manipulation.
9. Determine whether the current entry is already overextended.
10. Produce a risk-adjusted decision.
11. Define invalidating conditions.
12. Never invent missing data.
13. Return ONLY the required JSON object.

REQUIRED JSON STRUCTURE:

{json.dumps(AI_RESPONSE_SCHEMA, indent=2)}
""".strip()


# ---------------------------------------------------------------------------
# DATA SANITIZATION
# ---------------------------------------------------------------------------

def _sanitize_market_data(
    market_data: Mapping[str, Any],
) -> dict[str, Any]:
    """
    Normalize incoming market data before sending it to the AI.

    This prevents accidental leakage of arbitrary internal fields and
    keeps the AI input predictable.
    """

    allowed_fields = {
        "token_address",
        "symbol",
        "name",
        "chain",
        "price",
        "price_change_1m",
        "price_change_5m",
        "price_change_15m",
        "price_change_1h",
        "volume_1m",
        "volume_5m",
        "volume_15m",
        "volume_1h",
        "market_cap",
        "fdv",
        "liquidity",
        "liquidity_usd",
        "holders",
        "top_holder_percent",
        "top_10_holder_percent",
        "buy_count",
        "sell_count",
        "buy_sell_ratio",
        "tx_count",
        "age_minutes",
        "pair_address",
        "dex",
        "token_created_at",
        "mint_authority",
        "freeze_authority",
        "lp_locked",
        "lp_burned",
        "contract_verified",
        "honeypot_check",
        "tax_buy",
        "tax_sell",
        "developer_holding_percent",
        "insider_holding_percent",
        "social_score",
        "website",
        "telegram",
        "twitter",
    }

    sanitized: dict[str, Any] = {}

    for key in allowed_fields:
        if key in market_data:
            sanitized[key] = market_data[key]

    return sanitized


# ---------------------------------------------------------------------------
# RISK REVIEW PROMPT
# ---------------------------------------------------------------------------

def build_risk_review_prompt(
    market_data: Mapping[str, Any],
    ai_decision: Mapping[str, Any],
) -> str:
    """
    Create a second-stage risk-review prompt.

    This can later be used as a separate safety layer before paper/live
    execution.
    """

    market_payload = json.dumps(
        _sanitize_market_data(market_data),
        ensure_ascii=False,
        indent=2,
        default=str,
    )

    decision_payload = json.dumps(
        dict(ai_decision),
        ensure_ascii=False,
        indent=2,
        default=str,
    )

    return f"""
Perform an independent risk review of the proposed AI decision.

MARKET DATA:

{market_payload}

PROPOSED AI DECISION:

{decision_payload}

Your job is NOT to blindly approve the decision.

Check for:

- insufficient liquidity
- excessive holder concentration
- suspicious volume
- extreme price extension
- abnormal buy/sell imbalance
- possible manipulation
- token safety problems
- missing critical information
- unreasonable stop-loss
- unreasonable take-profit
- excessive portfolio exposure
- poor risk/reward
- inconsistent AI reasoning

Return ONLY valid JSON using this structure:

{{
    "approved": true,
    "final_decision": "BUY | SELL | HOLD | REJECT",
    "risk_score": 0.0,
    "max_position_percent": null,
    "critical_risks": [],
    "warnings": [],
    "required_conditions": [],
    "reason": ""
}}
""".strip()


# ---------------------------------------------------------------------------
# PAPER-TRADING PROMPT
# ---------------------------------------------------------------------------

def build_paper_trade_prompt(
    market_data: Mapping[str, Any],
    decision: Mapping[str, Any],
) -> str:
    """
    Build a prompt for evaluating a hypothetical paper trade.

    This does NOT execute a real transaction.
    """

    return f"""
Evaluate this hypothetical paper-trading opportunity.

MARKET DATA:
{json.dumps(_sanitize_market_data(market_data), indent=2, default=str)}

AI DECISION:
{json.dumps(dict(decision), indent=2, default=str)}

Determine whether the proposed paper trade satisfies the analytical
requirements.

Return ONLY valid JSON:

{{
    "paper_trade_allowed": true,
    "entry_price": null,
    "stop_loss_price": null,
    "take_profit_price": null,
    "position_percent": null,
    "risk_reward_ratio": null,
    "reason": "",
    "warnings": []
}}
""".strip()


# ---------------------------------------------------------------------------
# RESPONSE VALIDATION
# ---------------------------------------------------------------------------

def get_required_response_fields() -> tuple[str, ...]:
    """
    Return the required top-level fields expected from the AI.
    """

    return tuple(AI_RESPONSE_SCHEMA.keys())
