"""
AI prompt definitions for the Solana meme-coin trading engine.

This module:
- Defines the AI system prompt
- Builds market-analysis prompts
- Builds risk-review prompts
- Sanitizes market data
- Defines the expected AI response schema

This module does NOT execute trades.
"""

from __future__ import annotations

import json
from typing import Any, Mapping


# ============================================================
# AI RESPONSE SCHEMA
# ============================================================

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


# ============================================================
# SYSTEM PROMPT
# ============================================================

SYSTEM_PROMPT = """
You are an advanced crypto market-analysis engine specializing in
high-risk Solana meme coins.

Your task is to analyze only the market and token data supplied to you.

You must never invent missing information.

You must distinguish between:

1. Supplied facts
2. Reasonable market inference
3. Unknown information

If important information is missing:
- reduce confidence
- increase risk
- explain the missing information in warnings

Never guarantee profit.

Never claim that a trade is certain to succeed.

Capital preservation is more important than trade frequency.

Allowed decisions:

BUY
SELL
HOLD
REJECT

Use REJECT when:
- liquidity is inadequate
- token safety is questionable
- manipulation risk is excessive
- critical information is missing
- risk controls fail
- the available evidence is insufficient

For BUY decisions evaluate:

- liquidity
- trading volume
- momentum
- holder concentration
- token safety
- market-cap/liquidity relationship
- abnormal activity
- possible manipulation
- entry extension
- risk/reward
- invalidating conditions

Never recommend risking the entire portfolio.

For SELL decisions evaluate:

- deterioration in momentum
- deterioration in market structure
- liquidity and exit risk
- whether reducing the position is preferable to a complete exit

For HOLD decisions:

- explain what information is missing
- explain what market condition would justify BUY
- explain what market condition would justify SELL

For REJECT decisions:

- clearly explain the major risks
- do not recommend entering the position

CONFIDENCE:

confidence must be between 0.0 and 1.0.

Confidence is NOT the probability of profit.

RISK SCORE:

risk_score must be between 0.0 and 1.0.

0.0 = comparatively lower risk
1.0 = extremely high risk

For meme coins, high risk is normal.

SCORING:

entry_score = quality of current entry
liquidity_score = quality of available liquidity
momentum_score = strength and consistency of momentum
volume_score = quality of trading volume
holder_score = quality of holder distribution
safety_score = token/security quality

All available scores must be between 0.0 and 1.0.

If a score cannot be calculated because data is unavailable,
return null and explain why in warnings.

SIGNAL QUALITY:

A = exceptionally strong setup
B = good setup
C = mixed or uncertain setup
D = weak setup
F = unacceptable setup

Never create fake values.

Return ONLY valid JSON.

Do not use Markdown.

Do not add explanations outside the JSON object.
"""


# ============================================================
# MARKET ANALYSIS PROMPT
# ============================================================

def build_market_analysis_prompt(
    market_data: Mapping[str, Any],
) -> str:
    """
    Build a structured market-analysis prompt.
    """

    if not isinstance(market_data, Mapping):
        raise TypeError(
            "market_data must be a mapping/dictionary."
        )

    clean_data = _sanitize_market_data(
        market_data
    )

    payload = json.dumps(
        clean_data,
        ensure_ascii=False,
        indent=2,
        default=str,
    )

    schema = json.dumps(
        AI_RESPONSE_SCHEMA,
        ensure_ascii=False,
        indent=2,
    )

    return f"""
Analyze the following Solana token using the system instructions.

MARKET DATA:

{payload}

ANALYSIS REQUIREMENTS:

1. Determine whether the supplied data is sufficient.
2. Evaluate liquidity.
3. Evaluate volume.
4. Evaluate volume consistency when possible.
5. Evaluate price momentum.
6. Evaluate market-cap/liquidity relationship.
7. Evaluate holder distribution if supplied.
8. Evaluate token safety information if supplied.
9. Look for abnormal activity or possible manipulation.
10. Determine whether the current entry is overextended.
11. Produce a risk-adjusted decision.
12. Define invalidating conditions.
13. Never invent missing information.
14. Return ONLY valid JSON.

REQUIRED JSON STRUCTURE:

{schema}
""".strip()


# ============================================================
# MARKET DATA SANITIZATION
# ============================================================

def _sanitize_market_data(
    market_data: Mapping[str, Any],
) -> dict[str, Any]:
    """
    Keep only approved market-data fields.
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
        "volume_24h",
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


# ============================================================
# RISK REVIEW PROMPT
# ============================================================

def build_risk_review_prompt(
    market_data: Mapping[str, Any],
    ai_decision: Mapping[str, Any],
) -> str:
    """
    Build a second-stage independent risk-review prompt.
    """

    if not isinstance(market_data, Mapping):
        raise TypeError(
            "market_data must be a mapping/dictionary."
        )

    if not isinstance(ai_decision, Mapping):
        raise TypeError(
            "ai_decision must be a mapping/dictionary."
        )

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

Do NOT blindly approve the proposed decision.

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

If critical information is missing, do not assume it is safe.

Return ONLY valid JSON using this structure:

{{
    "approved": false,
    "final_decision": "BUY | SELL | HOLD | REJECT",
    "risk_score": 0.0,
    "max_position_percent": null,
    "critical_risks": [],
    "warnings": [],
    "required_conditions": [],
    "reason": ""
}}
""".strip()


# ============================================================
# PAPER-TRADING PROMPT
# ============================================================

def build_paper_trade_prompt(
    market_data: Mapping[str, Any],
    decision: Mapping[str, Any],
) -> str:
    """
    Build a prompt for evaluating a hypothetical paper trade.

    This function does NOT execute a real transaction.
    """

    if not isinstance(market_data, Mapping):
        raise TypeError(
            "market_data must be a mapping/dictionary."
        )

    if not isinstance(decision, Mapping):
        raise TypeError(
            "decision must be a mapping/dictionary."
        )

    market_payload = json.dumps(
        _sanitize_market_data(market_data),
        ensure_ascii=False,
        indent=2,
        default=str,
    )

    decision_payload = json.dumps(
        dict(decision),
        ensure_ascii=False,
        indent=2,
        default=str,
    )

    return f"""
Evaluate this hypothetical paper-trading opportunity.

MARKET DATA:

{market_payload}

AI DECISION:

{decision_payload}

Determine whether the proposed paper trade satisfies the
risk-management requirements.

This is a PAPER TRADE only.

Do not assume real execution.

Return ONLY valid JSON:

{{
    "paper_trade_allowed": false,
    "entry_price": null,
    "stop_loss_price": null,
    "take_profit_price": null,
    "position_percent": null,
    "risk_reward_ratio": null,
    "reason": "",
    "warnings": []
}}
""".strip()


# ============================================================
# REQUIRED RESPONSE FIELDS
# ============================================================

def get_required_response_fields() -> tuple[str, ...]:
    """
    Return all required top-level AI response fields.
    """

    return tuple(
        AI_RESPONSE_SCHEMA.keys()
    )
