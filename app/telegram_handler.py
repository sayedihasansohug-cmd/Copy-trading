"""
Telegram message handler for the Solana AI trading engine.

This module:
- Receives Telegram messages
- Extracts Solana token addresses
- Sends token addresses to the analysis pipeline
- Does NOT execute real trades
"""

from __future__ import annotations

import logging
import re
from typing import Any

from app.ai.pipeline import TradingPipeline


logger = logging.getLogger(__name__)


# Solana addresses are normally 32-44 characters
# using the Base58 character set.
SOLANA_ADDRESS_PATTERN = re.compile(
    r"(?<![1-9A-HJ-NP-Za-km-z])"
    r"[1-9A-HJ-NP-Za-km-z]{32,44}"
    r"(?![1-9A-HJ-NP-Za-km-z])"
)


class TelegramHandler:
    """
    Processes incoming Telegram messages.

    This class only analyzes tokens.
    It does not buy or sell anything.
    """

    def __init__(
        self,
        pipeline: TradingPipeline | None = None,
    ) -> None:

        self.pipeline = (
            pipeline
            or TradingPipeline()
        )

    # ========================================================
    # MESSAGE PROCESSING
    # ========================================================

    def process_message(
        self,
        message: str,
    ) -> dict[str, Any]:

        if not isinstance(
            message,
            str,
        ):
            raise TypeError(
                "message must be a string."
            )

        text = message.strip()

        if not text:
            return {
                "found": False,
                "reason": "Empty message.",
            }

        token_address = (
            self.extract_token_address(text)
        )

        if token_address is None:
            return {
                "found": False,
                "reason": (
                    "No Solana token address found."
                ),
            }

        logger.info(
            "Solana token detected: %s",
            token_address,
        )

        result = self.pipeline.analyze_token(
            token_address
        )

        return {
            "found": True,
            "token_address": token_address,
            "result": result,
        }

    # ========================================================
    # ADDRESS EXTRACTION
    # ========================================================

    @staticmethod
    def extract_token_address(
        message: str,
    ) -> str | None:

        matches = SOLANA_ADDRESS_PATTERN.findall(
            message
        )

        if not matches:
            return None

        # Use the first valid-looking Solana address.
        return matches[0]


# ============================================================
# SIMPLE FUNCTION API
# ============================================================

def process_telegram_message(
    message: str,
) -> dict[str, Any]:
    """
    Process one Telegram message.
    """

    handler = TelegramHandler()

    return handler.process_message(
        message
    )
