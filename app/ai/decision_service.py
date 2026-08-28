"""
Advanced AI decision orchestration layer.

Responsibilities:
- Run first-stage AI market analysis.
- Apply deterministic risk gates.
- Run second-stage independent risk review.
- Produce one final normalized decision.
- Never execute real trades.
- Never access or use private wallet keys.
"""

from __future__ import annotations

import logging
from typing import Any, Mapping

from app.ai.analyzer import (
    AIAnalyzer,
    AIAnalyzerError,
)

logger = logging.getLogger(__name__)


ALLOWED_DECISIONS = {
    "BUY",
    "SELL",
    "HOLD",
    "REJECT",
}


class DecisionServiceError(Exception):
    """Base exception for decision service errors."""


class DecisionService:
    """
    High-level AI decision orchestration service.

    Flow:

        market_data
             |
             v
        AI market analysis
             |
             v
        deterministic risk gates
             |
             v
        second-stage risk review
             |
             v
        final decision

    IMPORTANT:
    This class NEVER executes a trade.
    """

    def __init__(
        self,
        analyzer: AIAnalyzer | None = None,
    ) -> None:
        self.analyzer = analyzer or AIAnalyzer()

    # ============================================================
    # PUBLIC API
    # ============================================================

    def evaluate(
        self,
        market_data: Mapping[str, Any],
    ) -> dict[str, Any]:
        """
        Perform the complete AI decision pipeline.

        Parameters
        ----------
        market_data:
            Market information for one token.

        Returns
        -------
        dict[str, Any]
            Final normalized decision.
        """

        if not isinstance(market_data, Mapping):
            raise TypeError(
                "market_data must be a mapping/dictionary."
            )

        logger.info(
            "Starting AI evaluation."
        )

        # --------------------------------------------------------
        # Stage 1: AI market analysis
        # --------------------------------------------------------

        try:
            ai_decision = self.analyzer.analyze(
                market_data
            )

        except AIAnalyzerError as exc:
            logger.exception(
                "Primary AI analysis failed."
            )

            return self._build_failure_result(
                reason=(
                    "Primary AI analysis failed: "
                    f"{exc}"
                )
            )

        # --------------------------------------------------------
        # Stage 2: basic decision validation
        # --------------------------------------------------------

        first_decision = str(
            ai_decision.get(
                "decision",
                "REJECT",
            )
        ).upper()

        if first_decision not in ALLOWED_DECISIONS:
            first_decision = "REJECT"

        ai_decision["decision"] = first_decision

        # --------------------------------------------------------
        # Stage 3: hard-stop check
        # --------------------------------------------------------

        if first_decision == "REJECT":
            return self._finalize(
                ai_decision=ai_decision,
                risk_review={
                    "approved": False,
                    "final_decision": "REJECT",
                    "risk_score": ai_decision.get(
                        "risk_score",
                        1.0,
                    ),
                    "reason": (
                        "Primary deterministic risk "
                        "gates rejected the opportunity."
                    ),
                    "critical_risks": (
                        ai_decision.get(
                            "warnings",
                            [],
                        )
                    ),
                    "warnings": [],
                    "required_conditions": [],
                    "max_position_percent": None,
                },
            )

        # --------------------------------------------------------
        # Stage 4: second-stage risk review
        # --------------------------------------------------------

        try:
            risk_review = self.analyzer.risk_review(
                market_data=market_data,
                ai_decision=ai_decision,
            )

        except AIAnalyzerError as exc:
            logger.exception(
                "Second-stage risk review failed."
            )

            return self._build_failure_result(
                reason=(
                    "Second-stage risk review failed: "
                    f"{exc}"
                ),
                ai_decision=ai_decision,
            )

        # --------------------------------------------------------
        # Stage 5: final decision
        # --------------------------------------------------------

        return self._finalize(
            ai_decision=ai_decision,
            risk_review=risk_review,
        )

    # ============================================================
    # FINALIZATION
    # ============================================================

    @staticmethod
    def _finalize(
        ai_decision: Mapping[str, Any],
        risk_review: Mapping[str, Any],
    ) -> dict[str, Any]:
        """
        Combine first-stage analysis and second-stage review.

        The second-stage reviewer has veto power.

        A BUY is allowed only when:
        - AI decision is BUY
        - risk review approves it
        - final decision is BUY
        - risk score is <= 0.85
        """

        decision = str(
            ai_decision.get(
                "decision",
                "REJECT",
            )
        ).upper()

        review_decision = str(
            risk_review.get(
                "final_decision",
                "REJECT",
            )
        ).upper()

        approved = bool(
            risk_review.get(
                "approved",
                False,
            )
        )

        risk_score = _safe_float(
            risk_review.get(
                "risk_score",
                ai_decision.get(
                    "risk_score",
                    1.0,
                ),
            )
        )

        warnings = _string_list(
            ai_decision.get(
                "warnings",
                [],
            )
        )

        review_warnings = _string_list(
            risk_review.get(
                "warnings",
                [],
            )
        )

        critical_risks = _string_list(
            risk_review.get(
                "critical_risks",
                [],
            )
        )

        required_conditions = _string_list(
            risk_review.get(
                "required_conditions",
                [],
            )
        )

        warnings.extend(
            review_warnings
        )

        warnings.extend(
            critical_risks
        )

        # --------------------------------------------------------
        # Absolute veto rules
        # --------------------------------------------------------

        if decision == "REJECT":
            approved = False
            review_decision = "REJECT"

        if review_decision == "REJECT":
            approved = False

        if risk_score > 0.85:
            approved = False
            review_decision = "REJECT"

            warnings.append(
                "Final risk score exceeds the "
                "maximum approval threshold."
            )

        # --------------------------------------------------------
        # BUY requires BOTH stages to agree.
        # --------------------------------------------------------

        if decision == "BUY":
            if not approved:
                final_decision = "HOLD"
            elif review_decision != "BUY":
                final_decision = "HOLD"
            else:
                final_decision = "BUY"

        # --------------------------------------------------------
        # SELL decisions are never converted into BUY.
        # --------------------------------------------------------

        elif decision == "SELL":
            if review_decision == "SELL" and approved:
                final_decision = "SELL"
            else:
                final_decision = "HOLD"

        # --------------------------------------------------------
        # HOLD remains HOLD unless explicitly rejected.
        # --------------------------------------------------------

        elif decision == "HOLD":
            final_decision = "HOLD"

        else:
            final_decision = "REJECT"

        # --------------------------------------------------------
        # Safety rule:
        # no approval for non-BUY decisions.
        # --------------------------------------------------------

        final_approved = (
            approved
            and final_decision in {
                "BUY",
                "SELL",
            }
        )

        return {
            "decision": final_decision,
            "approved": final_approved,

            "confidence": _safe_float(
                ai_decision.get(
                    "confidence",
                    0.0,
                )
            ),

            "risk_score": risk_score,

            "signal_quality": str(
                ai_decision.get(
                    "signal_quality",
                    "F",
                )
            ).upper(),

            "entry_score": ai_decision.get(
                "entry_score"
            ),

            "liquidity_score": ai_decision.get(
                "liquidity_score"
            ),

            "momentum_score": ai_decision.get(
                "momentum_score"
            ),

            "volume_score": ai_decision.get(
                "volume_score"
            ),

            "holder_score": ai_decision.get(
                "holder_score"
            ),

            "safety_score": ai_decision.get(
                "safety_score"
            ),

            "reasons": _string_list(
                ai_decision.get(
                    "reasons",
                    [],
                )
            ),

            "warnings": _unique_strings(
                warnings
            ),

            "invalidating_conditions": _string_list(
                ai_decision.get(
                    "invalidating_conditions",
                    [],
                )
            ),

            "critical_risks": critical_risks,

            "required_conditions": (
                required_conditions
            ),

            "max_position_percent": (
                _safe_optional_float(
                    risk_review.get(
                        "max_position_percent"
                    )
                )
            ),

            "risk_review_reason": str(
                risk_review.get(
                    "reason",
                    "",
                )
            ).strip(),

            "stage_1_decision": decision,

            "stage_2_decision": review_decision,

            "stage_2_approved": approved,
        }

    # ============================================================
    # FAILURE RESULT
    # ============================================================

    @staticmethod
    def _build_failure_result(
        reason: str,
        ai_decision: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Return a safe failure result.

        Failure always means REJECT.
        """

        decision = dict(
            ai_decision or {}
        )

        return {
            "decision": "REJECT",
            "approved": False,
            "confidence": _safe_float(
                decision.get(
                    "confidence",
                    0.0,
                )
            ),
            "risk_score": 1.0,
            "signal_quality": "F",

            "entry_score": decision.get(
                "entry_score"
            ),

            "liquidity_score": decision.get(
                "liquidity_score"
            ),

            "momentum_score": decision.get(
                "momentum_score"
            ),

            "volume_score": decision.get(
                "volume_score"
            ),

            "holder_score": decision.get(
                "holder_score"
            ),

            "safety_score": decision.get(
                "safety_score"
            ),

            "reasons": [],
            "warnings": [
                reason
            ],

            "invalidating_conditions": [
                "AI pipeline failure"
            ],

            "critical_risks": [
                "Decision pipeline failed."
            ],

            "required_conditions": [],

            "max_position_percent": None,

            "risk_review_reason": reason,

            "stage_1_decision": "REJECT",

            "stage_2_decision": "REJECT",

            "stage_2_approved": False,
        }


# ================================================================
# HELPERS
# ================================================================

def _safe_float(
    value: Any,
    default: float = 0.0,
) -> float:
    """
    Convert a value to float safely.
    """

    try:
        if value is None:
            return default

        return float(value)

    except (
        TypeError,
        ValueError,
    ):
        return default


def _safe_optional_float(
    value: Any,
) -> float | None:
    """
    Convert a value to float or return None.
    """

    if value is None:
        return None

    try:
        return float(value)

    except (
        TypeError,
        ValueError,
    ):
        return None


def _string_list(
    value: Any,
) -> list[str]:
    """
    Normalize arbitrary list-like data into strings.
    """

    if value is None:
        return []

    if isinstance(
        value,
        str,
    ):
        text = value.strip()

        if not text:
            return []

        return [text]

    if not isinstance(
        value,
        (list, tuple, set),
    ):
        return [
            str(value).strip()
        ]

    result: list[str] = []

    for item in value:
        text = str(
            item
        ).strip()

        if text:
            result.append(
                text
            )

    return result


def _unique_strings(
    values: list[str],
) -> list[str]:
    """
    Remove duplicate strings while
    preserving their original order.
    """

    result: list[str] = []
    seen: set[str] = set()

    for value in values:
        text = str(
            value
        ).strip()

        if not text:
            continue

        if text in seen:
            continue

        seen.add(
            text
        )

        result.append(
            text
        )

    return result
