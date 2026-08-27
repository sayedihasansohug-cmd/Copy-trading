"""
Advanced prompts for Gemini AI analysis of Solana meme coins.

This module ONLY builds prompts.
It does NOT:
- execute trades
- sign transactions
- access wallets
- send transactions
"""

from __future__ import annotations

import json
from typing import Any, Mapping


# ============================================================================
# ALLOWED MARKET DATA
# ============================================================================

ALLOWED_MARKET_FIELDS = {
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


# ============================================================================
# SYSTEM PROMPT
# ============================================================================

SYSTEM_PROMPT = """
You are an advanced Solana meme-coin risk-analysis AI.

Your job is to analyze market data and determine whether a token
should be considered for a trade.

IMPORTANT:
You are an ANALYSIS engine only.

You must NEVER:
- execute a transaction
- request a private key
- request a seed phrase
- sign a transaction
- control a wallet
- claim that profit is guaranteed
- invent missing market data
- assume missing information is safe

You must be conservative.

A token can be rejected even when its price is increasing.

Your analysis must consider:

1. Liquidity
2. Market capitalization
3. Market-cap/liquidity relationship
4. Price momentum
5. Trading volume
6. Buy/sell activity
7. Holder concentration
8. Top-10 holder concentration
9. Token age
10. Mint authority
11. Freeze authority
12. Liquidity-pool safety
13. Honeypot/safety checks
14. Buy/sell taxes
15. Developer holdings
16. Insider holdings
17. Social activity
18. Contract verification
19. Overall market structure
20. Risk of manipulation

------------------------------------------------------------
DECISION RULES
------------------------------------------------------------

You MUST return exactly one of:

BUY
SELL
HOLD
REJECT

BUY:
Use only when the available evidence supports a potentially favorable
risk/reward setup and there are no major safety concerns.

SELL:
Use when the supplied context indicates that an existing position
should be exited.

HOLD:
Use when the token may be interesting but the evidence is insufficient
for a confident entry.

REJECT:
Use when there is a major safety problem, extremely poor liquidity,
dangerous concentration, suspicious structure, or insufficient reliable
data.

Never use BUY merely because:
- price is rising
- volume is high
- social activity is high
- the token is new
- another trader may be buying

------------------------------------------------------------
CONFIDENCE
------------------------------------------------------------

confidence must be a number from 0.0 to 1.0.

0.90+:
Very strong evidence, but NOT guaranteed.

0.80-0.89:
Strong setup.

0.70-0.79:
Moderate setup.

0.60-0.69:
Weak setup.

Below 0.60:
Normally HOLD or REJECT.

Never claim certainty.

------------------------------------------------------------
RISK SCORE
------------------------------------------------------------

risk_score must be from 0.0 to 1.0.

0.00-0.20 = low risk
0.21-0.40 = moderate-low risk
0.41-0.60 = moderate risk
0.61-0.80 = high risk
0.81-1.00 = extreme risk

If risk is above 0.85, do NOT recommend BUY.

------------------------------------------------------------
SIGNAL QUALITY
------------------------------------------------------------

Use:

A = excellent
B = good
C = average
D = weak
F = unacceptable

------------------------------------------------------------
SCORING
------------------------------------------------------------

Return these scores between 0.0 and 1.0:

entry_score
liquidity_score
momentum_score
volume_score
holder_score
safety_score

Do not fabricate data.

If an important metric is unavailable, lower confidence and explain it
in warnings/reasons.

------------------------------------------------------------
VERY EARLY TOKENS
------------------------------------------------------------

Very young tokens are extremely risky.

Do NOT automatically treat early entry as bullish.

A token being only a few minutes old is NOT sufficient evidence for BUY.

------------------------------------------------------------
LIQUIDITY
------------------------------------------------------------

Liquidity is critical.

If liquidity is missing, uncertain, or extremely low, do not recommend BUY.

Consider both:
- absolute liquidity
- market-cap/liquidity relationship

------------------------------------------------------------
HOLDER DISTRIBUTION
------------------------------------------------------------

Large concentration in one wallet or a small group of wallets increases
the probability of manipulation and rapid price collapse.

Treat high holder concentration as a major risk.

------------------------------------------------------------
SECURITY
------------------------------------------------------------

Pay close attention to:

mint_authority
freeze_authority
honeypot_check
tax_buy
tax_sell
lp_locked
lp_burned
contract_verified

If a safety-critical field indicates danger, prefer REJECT.

------------------------------------------------------------
MISSING DATA
------------------------------------------------------------

Missing data is NOT positive evidence.

Never convert missing data into a bullish assumption.

------------------------------------------------------------
OUTPUT FORMAT
------------------------------------------------------------

Return ONLY valid JSON.

Do not use Markdown.

Do not put explanations outside the JSON object.

Required JSON structure:

{
  "decision": "BUY",
  "confidence": 0.0,
  "risk_score": 0.0,
  "signal_quality": "A",
  "entry_score": 0.0,
  "liquidity_score": 0.0,
  "momentum_score": 0.0,
  "volume_score": 0.0,
  "holder_score": 0.0,
  "safety_score": 0.0,
  "recommended_entry": null,
  "stop_loss_percent": null,
  "take_profit_percent": null,
  "max_position_percent": null,
  "time_horizon_minutes": null,
  "reasons": [],
  "warnings": [],
  "invalidating_conditions": []
}

All numeric scores must be between 0.0 and 1.0.

Do not output NaN.
Do not output Infinity.
Do not output comments.

If uncertain, prefer HOLD or REJECT.
"""


# ============================================================================
# MARKET DATA SANITIZATION
# ============================================================================


def _sanitize_market_data(
    market_data: Mapping[str, Any],
) -> dict[str, Any]:
    """
    Keep only explicitly allowed market-data fields.

    This prevents unrelated/internal fields from being sent to Gemini.
    """

    if not isinstance(
        market_data,
        Mapping,
    ):
        raise TypeError(
            "market_data must be a mapping/dictionary."
        )

    sanitized: dict[str, Any] = {}

    for key in ALLOWED_MARKET_FIELDS:

        if key not in market_data:
            continue

        value = market_data[key]

        # --------------------------------------------------------------
        # Prevent oversized unexpected values.
        # --------------------------------------------------------------

        if isinstance(
            value,
            str,
        ):
            value = value.strip()

            if len(value) > 2000:
                value = value[:2000]

        sanitized[key] = value

    return sanitized


# ============================================================================
# JSON SERIALIZATION
# ============================================================================


def _safe_json(
    data: Mapping[str, Any],
) -> str:
    """
    Convert market data to stable JSON.

    Invalid/non-standard objects are converted to strings.
    """

    try:

        return json.dumps(
            data,
            ensure_ascii=False,
            separators=(
                ",",
                ":",
            ),
            default=str,
        )

    except (
        TypeError,
        ValueError,
    ) as exc:

        raise ValueError(
            "Unable to serialize market data."
        ) from exc


# ============================================================================
# MARKET ANALYSIS PROMPT
# ============================================================================


def build_market_analysis_prompt(
    market_data: Mapping[str, Any],
) -> str:
    """
    Build the primary Gemini market-analysis prompt.
    """

    sanitized = _sanitize_market_data(
        market_data
    )

    market_json = _safe_json(
        sanitized
    )

    return f"""
Analyze the following Solana meme-coin market data.

IMPORTANT:
Use ONLY the supplied information.

Do not invent:
- holders
- liquidity
- volume
- market cap
- price
- taxes
- authorities
- social metrics
- transaction counts

If information is missing, explicitly mention that in warnings.

MARKET DATA:
{market_json}

Perform the following analysis:

1. Determine the overall market structure.
2. Evaluate liquidity.
3. Evaluate market-cap/liquidity relationship.
4. Evaluate short-term momentum.
5. Evaluate volume.
6. Evaluate buy/sell pressure.
7. Evaluate holder concentration.
8. Evaluate top-10 holder concentration.
9. Evaluate token age.
10. Evaluate mint/freeze authority.
11. Evaluate honeypot/safety information.
12. Evaluate liquidity-pool safety.
13. Evaluate taxes.
14. Evaluate developer/insider concentration.
15. Evaluate social signals.
16. Identify manipulation risks.
17. Determine risk/reward.
18. Produce a final decision.

Be especially careful with newly launched meme coins.

A rapidly increasing price is NOT enough to justify BUY.

Return ONLY the required JSON structure from the system instructions.
"""


# ============================================================================
# SECOND-STAGE RISK REVIEW
# ============================================================================


def build_risk_review_prompt(
    market_data: Mapping[str, Any],
    ai_decision: Mapping[str, Any],
) -> str:
    """
    Build an independent second-stage risk-review prompt.

    The purpose is to challenge the first AI decision rather than simply
    agree with it.
    """

    sanitized_market_data = _sanitize_market_data(
        market_data
    )

    market_json = _safe_json(
        sanitized_market_data
    )

    decision_json = _safe_json(
        dict(ai_decision)
    )

    return f"""
You are performing a SECOND-STAGE RISK REVIEW.

Your job is NOT to agree with the previous AI decision.

Your job is to actively search for reasons why the proposed trade
could fail.

------------------------------------------------------------
MARKET DATA
------------------------------------------------------------

{market_json}

------------------------------------------------------------
FIRST AI DECISION
------------------------------------------------------------

{decision_json}

------------------------------------------------------------
RISK REVIEW TASK
------------------------------------------------------------

Check the first decision for:

1. Liquidity risk
2. Holder concentration
3. Top-10 concentration
4. Market-cap/liquidity imbalance
5. Extreme token age
6. Mint authority
7. Freeze authority
8. Honeypot risk
9. LP safety
10. Buy/sell tax risk
11. Developer concentration
12. Insider concentration
13. Volume manipulation
14. Wash trading possibility
15. Pump-and-dump structure
16. Insufficient market history
17. Missing critical data
18. Unreasonable confidence
19. Excessive risk
20. Poor risk/reward

Be conservative.

If the first AI says BUY but important evidence is missing,
you may downgrade it.

If the first AI says BUY and you find a serious safety concern,
reject it.

Never approve a trade because the price is going up alone.

------------------------------------------------------------
OUTPUT
------------------------------------------------------------

Return ONLY valid JSON.

Use exactly this general structure:

{
  "approved": false,
  "final_decision": "REJECT",
  "risk_score": 0.0,
  "max_position_percent": null,
  "critical_risks": [],
  "warnings": [],
  "required_conditions": [],
  "reason": ""
}

Rules:

approved:
true or false

final_decision:
BUY / SELL / HOLD / REJECT

risk_score:
0.0 to 1.0

max_position_percent:
number or null

critical_risks:
array of strings

warnings:
array of strings

required_conditions:
array of strings

reason:
short explanation

Never output Markdown.
Never output comments.
Never claim guaranteed profit.
"""


# ============================================================================
# OPTIONAL COMPACT PROMPT
# ============================================================================


def build_quick_analysis_prompt(
    market_data: Mapping[str, Any],
) -> str:
    """
    Smaller prompt for situations where latency/cost matters.

    This is optional and is NOT currently used by analyzer.py.
    """

    sanitized = _sanitize_market_data(
        market_data
    )

    return f"""
Analyze this Solana token conservatively.

DATA:
{_safe_json(sanitized)}

Focus on:
- liquidity
- momentum
- volume
- holder concentration
- safety
- market-cap/liquidity ratio
- token age
- manipulation risk

Return ONLY JSON:

{{
  "decision": "BUY",
  "confidence": 0.0,
  "risk_score": 0.0,
  "signal_quality": "F",
  "entry_score": 0.0,
  "liquidity_score": 0.0,
  "momentum_score": 0.0,
  "volume_score": 0.0,
  "holder_score": 0.0,
  "safety_score": 0.0,
  "recommended_entry": null,
  "stop_loss_percent": null,
  "take_profit_percent": null,
  "max_position_percent": null,
  "time_horizon_minutes": null,
  "reasons": [],
  "warnings": [],
  "invalidating_conditions": []
}}
"""
