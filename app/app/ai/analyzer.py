"""
Advanced Gemini AI analysis engine for Solana meme coins.

Responsibilities:
- Build market-analysis prompts
- Call Gemini API
- Parse strict JSON responses
- Validate AI decisions
- Apply deterministic risk gates
- Perform second-stage risk review
- Never execute real trades
"""

from __future__ import annotations

import json
import logging
from typing import Any, Mapping

import requests

from app.config import (
    GEMINI_API_KEY,
    GEMINI_MODEL,
    MIN_LIQUIDITY_USD,
    AI_BUY_THRESHOLD,
)

from app.ai.prompts import (
    SYSTEM_PROMPT,
    build_market_analysis_prompt,
    build_risk_review_prompt,
)


logger = logging.getLogger(__name__)


# ============================================================
# CONSTANTS
# ============================================================

ALLOWED_DECISIONS = {
    "BUY",
    "SELL",
    "HOLD",
    "REJECT",
}

ALLOWED_SIGNAL_QUALITY = {
    "A",
    "B",
    "C",
    "D",
    "F",
}


# ============================================================
# EXCEPTIONS
# ============================================================

class AIAnalyzerError(Exception):
    """Base exception for AI analyzer errors."""


class AIConfigurationError(AIAnalyzerError):
    """Raised when Gemini configuration is missing."""


class AIRequestError(AIAnalyzerError):
    """Raised when Gemini API request fails."""


class AIResponseError(AIAnalyzerError):
    """Raised when Gemini response is invalid."""


# ============================================================
# ANALYZER
# ============================================================

class AIAnalyzer:
    """
    Gemini-powered AI decision layer.

    IMPORTANT:
    This class DOES NOT execute trades.

    It only:
    - analyzes supplied market data
    - returns BUY / SELL / HOLD / REJECT
    - applies deterministic risk protection
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        timeout: int = 30,
    ) -> None:

        self.api_key = (
            api_key
            or GEMINI_API_KEY
        )

        self.model = (
            model
            or GEMINI_MODEL
        )

        self.timeout = timeout

        self.api_url = (
            "https://generativelanguage.googleapis.com/"
            "v1beta/models/"
            f"{self.model}:generateContent"
        )

        self._validate_configuration()

    # ========================================================
    # CONFIGURATION
    # ========================================================

    def _validate_configuration(self) -> None:

        if not self.api_key:
            raise AIConfigurationError(
                "GEMINI_API_KEY is not configured."
            )

        if not self.model:
            raise AIConfigurationError(
                "GEMINI_MODEL is not configured."
            )

    # ========================================================
    # PUBLIC ANALYSIS
    # ========================================================

    def analyze(
        self,
        market_data: Mapping[str, Any],
    ) -> dict[str, Any]:
        """
        Analyze one Solana token.

        This method never executes a trade.
        """

        if not isinstance(
            market_data,
            Mapping,
        ):
            raise TypeError(
                "market_data must be a mapping/dictionary."
            )

        prompt = build_market_analysis_prompt(
            market_data
        )

        raw_response = self._call_gemini(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=prompt,
        )

        decision = self._parse_json_response(
            raw_response
        )

        validated = self._validate_decision(
            decision
        )

        validated = self._apply_risk_gates(
            market_data,
            validated,
        )

        return validated

    # ========================================================
    # SECOND-STAGE RISK REVIEW
    # ========================================================

    def risk_review(
        self,
        market_data: Mapping[str, Any],
        ai_decision: Mapping[str, Any],
    ) -> dict[str, Any]:
        """
        Perform an independent second-stage risk review.

        This does not execute trades.
        """

        prompt = build_risk_review_prompt(
            market_data,
            ai_decision,
        )

        raw_response = self._call_gemini(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=prompt,
        )

        result = self._parse_json_response(
            raw_response
        )

        return self._validate_risk_review(
            result
        )

    # ========================================================
    # GEMINI API
    # ========================================================

    def _call_gemini(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> str:

        headers = {
            "x-goog-api-key": self.api_key,
            "Content-Type": "application/json",
        }

        payload = {
            "systemInstruction": {
                "parts": [
                    {
                        "text": system_prompt,
                    }
                ]
            },
            "contents": [
                {
                    "role": "user",
                    "parts": [
                        {
                            "text": user_prompt,
                        }
                    ],
                }
            ],
            "generationConfig": {
    "responseMimeType": "application/json",
            },
        }

        try:

            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=self.timeout,
            )

        except requests.RequestException as exc:

            logger.exception(
                "Gemini API request failed."
            )

            raise AIRequestError(
                f"Gemini API request failed: {exc}"
            ) from exc

        if response.status_code >= 400:

            raise AIRequestError(
                "Gemini API returned HTTP "
                f"{response.status_code}: "
                f"{response.text[:1000]}"
            )

        try:

            data = response.json()

        except ValueError as exc:

            raise AIResponseError(
                "Gemini API returned invalid JSON."
            ) from exc

        content = self._extract_gemini_content(
            data
        )

        if not content:

            raise AIResponseError(
                "Gemini returned an empty response."
            )

        return content

    # ========================================================
    # GEMINI RESPONSE EXTRACTION
    # ========================================================

    @staticmethod
    def _extract_gemini_content(
        response: Mapping[str, Any],
    ) -> str:

        candidates = response.get(
            "candidates"
        )

        if not isinstance(
            candidates,
            list,
        ):
            return ""

        if not candidates:
            return ""

        first = candidates[0]

        if not isinstance(
            first,
            Mapping,
        ):
            return ""

        content = first.get(
            "content"
        )

        if not isinstance(
            content,
            Mapping,
        ):
            return ""

        parts = content.get(
            "parts"
        )

        if not isinstance(
            parts,
            list,
        ):
            return ""

        text_parts: list[str] = []

        for part in parts:

            if not isinstance(
                part,
                Mapping,
            ):
                continue

            text = part.get(
                "text"
            )

            if isinstance(
                text,
                str,
            ):
                text_parts.append(
                    text
                )

        return "".join(
            text_parts
        ).strip()

    # ========================================================
    # JSON PARSER
    # ========================================================

    @staticmethod
    def _parse_json_response(
        raw_response: str,
    ) -> dict[str, Any]:

        text = raw_response.strip()

        # Remove Markdown code fences if Gemini
        # accidentally returns them.
        if text.startswith("```"):

            lines = text.splitlines()

            if lines:
                lines = lines[1:]

            if (
                lines
                and lines[-1].strip() == "```"
            ):
                lines = lines[:-1]

            text = "\n".join(
                lines
            ).strip()

        try:

            data = json.loads(
                text
            )

        except json.JSONDecodeError as exc:

            # Try to recover the JSON object.
            start = text.find("{")
            end = text.rfind("}")

            if start >= 0 and end > start:

                candidate = text[
                    start:end + 1
                ]

                try:

                    data = json.loads(
                        candidate
                    )

                except json.JSONDecodeError:

                    raise AIResponseError(
                        "Gemini response is not valid JSON."
                    ) from exc

            else:

                raise AIResponseError(
                    "Gemini response does not contain JSON."
                ) from exc

        if not isinstance(
            data,
            dict,
        ):

            raise AIResponseError(
                "Gemini response must be a JSON object."
            )

        return data

    # ========================================================
    # DECISION VALIDATION
    # ========================================================

    @staticmethod
    def _validate_decision(
        decision: Mapping[str, Any],
    ) -> dict[str, Any]:

        result = dict(
            decision
        )

        decision_name = str(
            result.get(
                "decision",
                "REJECT",
            )
        ).upper()

        if (
            decision_name
            not in ALLOWED_DECISIONS
        ):
            decision_name = "REJECT"

        result["decision"] = (
            decision_name
        )

        result["confidence"] = _clamp(
            result.get(
                "confidence"
            ),
            0.0,
            1.0,
        )

        result["risk_score"] = _clamp(
            result.get(
                "risk_score"
            ),
            0.0,
            1.0,
        )

        quality = str(
            result.get(
                "signal_quality",
                "F",
            )
        ).upper()

        if (
            quality
            not in ALLOWED_SIGNAL_QUALITY
        ):
            quality = "F"

        result["signal_quality"] = (
            quality
        )

                score_fields = (
            "entry_score",
            "liquidity_score",
            "momentum_score",
            "volume_score",
            "holder_score",
            "safety_score",
        )

        for field in score_fields:

            value = result.get(field)

            if value is None:
                result[field] = None
            else:
                result[field] = _clamp(
                    value,
                    0.0,
                    1.0,
                )

        result.setdefault(
            "reasons",
            [],
        )

        result.setdefault(
            "warnings",
            [],
        )

        result.setdefault(
            "invalidating_conditions",
            [],
        )

        return result
        result.setdefault(
            "warnings",
            [],
        )

        result.setdefault(
            "invalidating_conditions",
            [],
        )

        return result

    # ========================================================
    # DETERMINISTIC RISK GATES
    # ========================================================

    @staticmethod
    def _apply_risk_gates(
        market_data: Mapping[str, Any],
        decision: dict[str, Any],
    ) -> dict[str, Any]:

        warnings = list(
            decision.get(
                "warnings"
            ) or []
        )

        decision_name = (
            decision["decision"]
        )

        liquidity = _to_float(
            market_data.get(
                "liquidity_usd"
            )
        )

        if liquidity is None:

            liquidity = _to_float(
                market_data.get(
                    "liquidity"
                )
            )

        market_cap = _to_float(
            market_data.get(
                "market_cap"
            )
        )

        top_holder = _to_float(
            market_data.get(
                "top_holder_percent"
            )
        )

        age_minutes = _to_float(
            market_data.get(
                "age_minutes"
            )
        )

        # ----------------------------------------------------
        # Minimum liquidity
        # ----------------------------------------------------

        if (
            decision_name == "BUY"
            and liquidity is not None
            and liquidity < MIN_LIQUIDITY_USD
        ):

            warnings.append(
                "Liquidity is below the minimum safety threshold."
            )

            decision_name = "REJECT"

        # ----------------------------------------------------
        # Holder concentration
        # ----------------------------------------------------

        if (
            decision_name == "BUY"
            and top_holder is not None
            and top_holder > 25
        ):

            warnings.append(
                "Top holder concentration is excessive."
            )

            decision_name = "REJECT"

        # ----------------------------------------------------
        # Extremely new token
        # ----------------------------------------------------

        if (
            decision_name == "BUY"
            and age_minutes is not None
            and age_minutes < 2
        ):

            warnings.append(
                "Token is extremely new; insufficient history."
            )

            decision_name = "HOLD"

        # ----------------------------------------------------
        # Market cap / liquidity
        # ----------------------------------------------------

        if (
            decision_name == "BUY"
            and market_cap is not None
            and liquidity is not None
            and liquidity > 0
        ):

            ratio = (
                market_cap
                / liquidity
            )

            if ratio > 500:

                warnings.append(
                    "Market-cap to liquidity ratio is extremely high."
                )

                decision_name = "REJECT"

        # ----------------------------------------------------
        # Low confidence
        # ----------------------------------------------------

        if (
            decision_name == "BUY"
            and decision["confidence"] < (AI_BUY_THRESHOLD / 100)
        ):

            warnings.append(
                "AI confidence is below the BUY safety threshold."
            )

            decision_name = "HOLD"

        # ----------------------------------------------------
        # Excessive risk
        # ----------------------------------------------------

        if (
            decision_name == "BUY"
            and decision["risk_score"] > 0.85
        ):

            warnings.append(
                "Risk score is too high for automatic approval."
            )

            decision_name = "REJECT"

        decision["decision"] = (
            decision_name
        )

        decision["warnings"] = (
            _unique_strings(
                warnings
            )
        )

        return decision

    # ========================================================
    # RISK REVIEW VALIDATION
    # ========================================================

    @staticmethod
    def _validate_risk_review(
        result: Mapping[str, Any],
    ) -> dict[str, Any]:

        output = dict(
            result
        )

        approved = output.get(
            "approved",
            False,
        )

        if isinstance(
            approved,
            str,
        ):
            approved = (
                approved.lower()
                in {
                    "true",
                    "1",
                    "yes",
                }
            )

        output["approved"] = bool(
            approved
        )

        final_decision = str(
            output.get(
                "final_decision",
                "REJECT",
            )
        ).upper()

        if (
            final_decision
            not in ALLOWED_DECISIONS
        ):
            final_decision = "REJECT"

        output["final_decision"] = (
            final_decision
        )

        output["risk_score"] = _clamp(
            output.get(
                "risk_score"
            ),
            0.0,
            1.0,
        )

        output.setdefault(
            "max_position_percent",
            None,
        )

        output.setdefault(
            "critical_risks",
            [],
        )

        output.setdefault(
            "warnings",
            [],
        )

        output.setdefault(
            "required_conditions",
            [],
        )

        output.setdefault(
            "reason",
            "",
        )

        # Never approve REJECT.
        if (
            final_decision
            == "REJECT"
        ):
            output["approved"] = False

        # Never approve extremely risky result.
        if (
            output["risk_score"]
            > 0.85
        ):
            output["approved"] = False

        return output


# ============================================================
# HELPERS
# ============================================================

def _to_float(
    value: Any,
) -> float | None:

    if value is None:
        return None

    try:

        return float(
            value
        )

    except (
        TypeError,
        ValueError,
    ):

        return None


def _clamp(
    value: Any,
    minimum: float,
    maximum: float,
) -> float:

    number = _to_float(
        value
    )

    if number is None:
        return minimum

    return max(
        minimum,
        min(
            maximum,
            number,
        ),
    )


def _unique_strings(
    values: list[Any],
) -> list[str]:

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
