"""
Advanced Gemini AI analysis engine for Solana meme coins.

Responsibilities
----------------
1. Build market-analysis prompts.
2. Call Gemini API.
3. Parse strict JSON responses.
4. Validate AI decisions.
5. Apply deterministic risk gates.
6. Perform second-stage risk review.
7. Never execute real trades.

IMPORTANT
---------
This module ONLY performs analysis.

It does NOT:
- connect to a wallet
- sign transactions
- send transactions
- buy tokens
- sell tokens
"""

from __future__ import annotations

import json
import logging
import time
from typing import Any, Mapping

import requests

from app.config import (
    AI_BUY_THRESHOLD,
    GEMINI_API_KEY,
    GEMINI_MODEL,
    MIN_LIQUIDITY_USD,
)

from app.ai.prompts import (
    SYSTEM_PROMPT,
    build_market_analysis_prompt,
    build_risk_review_prompt,
)


logger = logging.getLogger(__name__)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def _clamp(val: Any, min_val: float = 0.0, max_val: float = 1.0) -> float:
    """Clamp a value between min_val and max_val."""
    try:
        f_val = float(val)
        return max(min_val, min(f_val, max_val))
    except (TypeError, ValueError):
        return min_val


def _optional_float(val: Any) -> float | None:
    """Safely convert value to optional float."""
    if val is None:
        return None
    try:
        return float(val)
    except (TypeError, ValueError):
        return None


# ============================================================================
# CONSTANTS
# ============================================================================

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


DEFAULT_TIMEOUT_SECONDS = 30

MAX_RETRIES = 3

RETRYABLE_STATUS_CODES = {
    408,
    409,
    429,
    500,
    502,
    503,
    504,
}


DEFAULT_SCORE_FIELDS = (
    "entry_score",
    "liquidity_score",
    "momentum_score",
    "volume_score",
    "holder_score",
    "safety_score",
)


# ============================================================================
# EXCEPTIONS
# ============================================================================


class AIAnalyzerError(Exception):
    """Base exception for AI analyzer errors."""


class AIConfigurationError(AIAnalyzerError):
    """Raised when Gemini configuration is missing or invalid."""


class AIRequestError(AIAnalyzerError):
    """Raised when the Gemini API request fails."""


class AIResponseError(AIAnalyzerError):
    """Raised when Gemini returns an invalid response."""


# ============================================================================
# AI ANALYZER
# ============================================================================


class AIAnalyzer:
    """
    Gemini-powered AI decision layer.

    This class NEVER executes trades.

    It only:
        - analyzes supplied market data
        - returns BUY / SELL / HOLD / REJECT
        - applies deterministic risk protection
        - performs optional second-stage risk review
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        timeout: int = DEFAULT_TIMEOUT_SECONDS,
        max_retries: int = MAX_RETRIES,
    ) -> None:

        self.api_key = (
            api_key
            if api_key is not None
            else GEMINI_API_KEY
        )

        self.model = (
            model
            if model is not None
            else GEMINI_MODEL
        )

        self.timeout = max(
            5,
            int(timeout),
        )

        self.max_retries = max(
            0,
            int(max_retries),
        )

        self.api_url = (
            "https://generativelanguage.googleapis.com/"
            "v1beta/models/"
            f"{self.model}:generateContent"
        )

        self.session = requests.Session()

        self._validate_configuration()

    # ========================================================================
    # CONFIGURATION
    # ========================================================================

    def _validate_configuration(self) -> None:
        """Validate Gemini configuration."""

        if not self.api_key:
            raise AIConfigurationError(
                "GEMINI_API_KEY is not configured."
            )

        if not isinstance(self.api_key, str):
            raise AIConfigurationError(
                "GEMINI_API_KEY must be a string."
            )

        if not self.model:
            raise AIConfigurationError(
                "GEMINI_MODEL is not configured."
            )

        if not isinstance(self.model, str):
            raise AIConfigurationError(
                "GEMINI_MODEL must be a string."
            )

    # ========================================================================
    # PUBLIC ANALYSIS
    # ========================================================================

    def analyze(
        self,
        market_data: Mapping[str, Any],
    ) -> dict[str, Any]:
        """
        Analyze one Solana token.

        Returns a validated decision dictionary.

        This method NEVER executes a trade.
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

        parsed_response = self._parse_json_response(
            raw_response
        )

        validated_response = self._validate_decision(
            parsed_response
        )

        final_response = self._apply_risk_gates(
            market_data=market_data,
            decision=validated_response,
        )

        return final_response

    # ========================================================================
    # SECOND-STAGE RISK REVIEW
    # ========================================================================

    def risk_review(
        self,
        market_data: Mapping[str, Any],
        ai_decision: Mapping[str, Any],
    ) -> dict[str, Any]:
        """
        Perform a second-stage AI risk review.

        This does NOT execute trades.
        """

        if not isinstance(
            market_data,
            Mapping,
        ):
            raise TypeError(
                "market_data must be a mapping/dictionary."
            )

        if not isinstance(
            ai_decision,
            Mapping,
        ):
            raise TypeError(
                "ai_decision must be a mapping/dictionary."
            )

        prompt = build_risk_review_prompt(
            market_data,
            ai_decision,
        )

        raw_response = self._call_gemini(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=prompt,
        )

        parsed_response = self._parse_json_response(
            raw_response
        )

        return self._validate_risk_review(
            parsed_response
        )

    # ========================================================================
    # GEMINI API
    # ========================================================================

    def _call_gemini(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> str:
        """
        Call Gemini generateContent API.

        Includes:
            - connection reuse
            - timeout protection
            - retry for temporary errors
            - 429 handling
            - 5xx handling
            - JSON response mode
        """

        if not system_prompt:
            raise AIRequestError(
                "System prompt is empty."
            )

        if not user_prompt:
            raise AIRequestError(
                "User prompt is empty."
            )

        headers = {
            "x-goog-api-key": self.api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        payload = {
            "systemInstruction": {
                "parts": [
                    {
                        "text": str(system_prompt),
                    }
                ]
            },
            "contents": [
                {
                    "role": "user",
                    "parts": [
                        {
                            "text": str(user_prompt),
                        }
                    ],
                }
            ],
            "generationConfig": {
                "responseMimeType": "application/json",
                "temperature": 0.1,
                "maxOutputTokens": 2000,
            },
        }

        last_error: Exception | None = None

        for attempt in range(
            self.max_retries + 1
        ):

            try:
                response = self.session.post(
                    self.api_url,
                    headers=headers,
                    json=payload,
                    timeout=self.timeout,
                )

            except requests.Timeout as exc:

                last_error = exc

                logger.warning(
                    "Gemini request timeout. "
                    "Attempt %s/%s",
                    attempt + 1,
                    self.max_retries + 1,
                )

                if attempt >= self.max_retries:
                    raise AIRequestError(
                        "Gemini API request timed out."
                    ) from exc

                self._sleep_before_retry(
                    attempt
                )

                continue

            except requests.RequestException as exc:

                last_error = exc

                logger.warning(
                    "Gemini network error. "
                    "Attempt %s/%s: %s",
                    attempt + 1,
                    self.max_retries + 1,
                    exc,
                )

                if attempt >= self.max_retries:
                    raise AIRequestError(
                        f"Gemini network request failed: {exc}"
                    ) from exc

                self._sleep_before_retry(
                    attempt
                )

                continue

            # --------------------------------------------------------------
            # SUCCESS
            # --------------------------------------------------------------

            if 200 <= response.status_code < 300:

                try:
                    data = response.json()

                except ValueError as exc:

                    raise AIResponseError(
                        "Gemini returned invalid JSON."
                    ) from exc

                content = self._extract_gemini_content(
                    data
                )

                if not content:

                    raise AIResponseError(
                        "Gemini returned an empty response."
                    )

                return content

            # --------------------------------------------------------------
            # RETRYABLE HTTP ERROR
            # --------------------------------------------------------------

            if response.status_code in RETRYABLE_STATUS_CODES:

                last_error = AIRequestError(
                    "Gemini API temporary HTTP error "
                    f"{response.status_code}: "
                    f"{response.text[:500]}"
                )

                logger.warning(
                    "Gemini temporary HTTP error %s. "
                    "Attempt %s/%s",
                    response.status_code,
                    attempt + 1,
                    self.max_retries + 1,
                )

                if attempt >= self.max_retries:
                    raise last_error

                self._sleep_before_retry(
                    attempt
                )

                continue

            # --------------------------------------------------------------
            # PERMANENT HTTP ERROR
            # --------------------------------------------------------------

            raise AIRequestError(
                "Gemini API returned HTTP "
                f"{response.status_code}: "
                f"{response.text[:1000]}"
            )

        raise AIRequestError(
            f"Gemini request failed: {last_error}"
        )

    # ========================================================================
    # RETRY BACKOFF
    # ========================================================================

    @staticmethod
    def _sleep_before_retry(
        attempt: int,
    ) -> None:
        """
        Small exponential backoff.

        1st retry: 0.5 sec
        2nd retry: 1.0 sec
        3rd retry: 2.0 sec
        """

        delay = min(
            2.0,
            0.5 * (2**attempt),
        )

        time.sleep(delay)

    # ========================================================================
    # GEMINI RESPONSE EXTRACTION
    # ========================================================================

    @staticmethod
    def _extract_gemini_content(
        response: Mapping[str, Any],
    ) -> str:
        """
        Extract text from Gemini response.
        """

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

        first_candidate = candidates[0]

        if not isinstance(
            first_candidate,
            Mapping,
        ):
            return ""

        content = first_candidate.get(
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

    # ========================================================================
    # JSON PARSER
    # ========================================================================

    @staticmethod
    def _parse_json_response(
        raw_response: str,
    ) -> dict[str, Any]:
        """
        Parse Gemini JSON response.
        """

        if not isinstance(
            raw_response,
            str,
        ):
            raise AIResponseError(
                "Gemini response must be a string."
            )

        text = raw_response.strip()

        if not text:
            raise AIResponseError(
                "Gemini response is empty."
            )

        # Remove Markdown code fences
        if text.startswith("```"):
            lines = text.splitlines()
            if lines:
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            text = "\n".join(lines).strip()

        try:
            data = json.loads(text)
        except json.JSONDecodeError as original_error:
            start = text.find("{")
            end = text.rfind("}")

            if start < 0 or end <= start:
                raise AIResponseError(
                    "Gemini response does not contain a valid JSON object."
                ) from original_error

            candidate = text[start : end + 1]

            try:
                data = json.loads(candidate)
            except json.JSONDecodeError as exc:
                raise AIResponseError(
                    "Gemini response is not valid JSON."
                ) from exc

        if not isinstance(data, dict):
            raise AIResponseError(
                "Gemini response must be a JSON object."
            )

        return data

    # ========================================================================
    # DECISION VALIDATION
    # ========================================================================

    @staticmethod
    def _validate_decision(
        decision: Mapping[str, Any],
    ) -> dict[str, Any]:
        """
        Validate and normalize AI decision.
        """

        if not isinstance(decision, Mapping):
            raise AIResponseError("AI decision must be a JSON object.")

        result = dict(decision)

        # Decision
        decision_name = str(result.get("decision", "REJECT")).strip().upper()
        if decision_name not in ALLOWED_DECISIONS:
            decision_name = "REJECT"
        result["decision"] = decision_name

        # Confidence & Risk
        result["confidence"] = _clamp(result.get("confidence"), 0.0, 1.0)
        result["risk_score"] = _clamp(result.get("risk_score"), 0.0, 1.0)

        # Signal quality
        quality = str(result.get("signal_quality", "F")).strip().upper()
        if quality not in ALLOWED_SIGNAL_QUALITY:
            quality = "F"
        result["signal_quality"] = quality

        # Score fields
        for field in DEFAULT_SCORE_FIELDS:
            value = result.get(field)
            result[field] = None if value is None else _clamp(value, 0.0, 1.0)

        # Trade planning fields
        result["recommended_entry"] = _optional_float(result.get("recommended_entry"))
        result["stop_loss_percent"] = _optional_float(result.get("stop_loss_percent"))
        result["take_profit_percent"] = _optional_float(result.get("take_profit_percent"))
        result["reasoning"] = str(result.get("reasoning", "")).strip()

        return result

    @staticmethod
    def _validate_risk_review(
        review: Mapping[str, Any],
    ) -> dict[str, Any]:
        """Validate second-stage risk review structure."""
        if not isinstance(review, Mapping):
            raise AIResponseError("Risk review must be a JSON object.")

        result = dict(review)
        result["approved"] = bool(result.get("approved", False))
        result["risk_level"] = str(result.get("risk_level", "HIGH")).strip().upper()
        result["reasoning"] = str(result.get("reasoning", "")).strip()
        return result

    # ========================================================================
    # DETERMINISTIC RISK GATES
    # ========================================================================

    @staticmethod
    def _apply_risk_gates(
        market_data: Mapping[str, Any],
        decision: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Hard safety checks that override AI decisions.
        """
        liquidity = _optional_float(market_data.get("liquidity_usd")) or 0.0
        confidence = decision.get("confidence", 0.0) * 100

        # Override BUY decision if deterministic rules fail
        if decision["decision"] == "BUY":
            if liquidity < MIN_LIQUIDITY_USD:
                decision["decision"] = "REJECT"
                decision["reasoning"] += f" [GATE REJECT: Liquidity ${liquidity} < Min ${MIN_LIQUIDITY_USD}]"
            elif confidence < AI_BUY_THRESHOLD:
                decision["decision"] = "REJECT"
                decision["reasoning"] += f" [GATE REJECT: Confidence {confidence}% < Threshold {AI_BUY_THRESHOLD}%]"

        return decision
              
import json
import anthropic

from app.config import settings
from app.ai.prompts import ANALYSIS_SYSTEM_PROMPT, build_analysis_prompt

client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)


async def analyze_signal(signal: dict, token_data: dict) -> dict:
    prompt = build_analysis_prompt(signal, token_data)
    try:
        response = await client.messages.create(
            model=settings.ai_model,
            max_tokens=300,
            system=ANALYSIS_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
        text = "".join(
            block.text for block in response.content if block.type == "text"
        ).strip()
        text = text.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        result = json.loads(text)
    except (json.JSONDecodeError, anthropic.APIError, Exception) as e:
        return {
            "decision": "skip",
            "confidence": 0,
            "reasoning": f"analysis failed, defaulting to skip: {e}",
            "red_flags": ["ai_error"],
        }

    if result.get("confidence", 0) > 75:
        result["confidence"] = 75

    return result
