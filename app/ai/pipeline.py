"""
AI trading analysis pipeline.

Flow:

Token Address
    ↓
Market Data Provider
    ↓
AI Analyzer
    ↓
Risk Review
    ↓
Final Decision

This module does NOT execute real trades.
"""

from __future__ import annotations

import logging
from typing import Any

from app.market_data import (
    SolanaMarketData,
    MarketDataError,
)

from app.ai.decision_service import (
    DecisionService,
)

logger = logging.getLogger(__name__)


class TradingPipelineError(Exception):
    """Base exception for trading pipeline errors."""


class TradingPipeline:
    """
    Connects market-data collection with the AI
    decision system.

    No real transaction is executed here.
    """

    def __init__(
        self,
        market_data_provider: SolanaMarketData | None = None,
        decision_service: DecisionService | None = None,
    ) -> None:

        self.market_data_provider = (
            market_data_provider
            or SolanaMarketData()
        )

        self.decision_service = (
            decision_service
            or DecisionService()
        )

    # ========================================================
    # PUBLIC API
    # ========================================================

    def analyze_token(
        self,
        token_address: str,
    ) -> dict[str, Any]:
        """
        Analyze one Solana token from its address.
        """

        address = token_address.strip()

        if not address:
            raise ValueError(
                "token_address cannot be empty."
            )

        logger.info(
            "Starting analysis for token: %s",
            address,
        )

        try:

            raw_market_data = (
                self.market_data_provider.get_token_data(
                    address
                )
            )

        except MarketDataError as exc:

            logger.error(
                "Market data collection failed: %s",
                exc,
            )

            raise TradingPipelineError(
                f"Unable to collect market data: {exc}"
            ) from exc

        ai_market_data = (
            self._convert_market_data(
                raw_market_data
            )
        )

        try:

            result = (
                self.decision_service.evaluate(
                    ai_market_data
                )
            )

        except Exception as exc:

            logger.exception(
                "AI decision pipeline failed."
            )

            raise TradingPipelineError(
                f"AI decision pipeline failed: {exc}"
            ) from exc

        return {
            "token_address": address,
            "market_data": ai_market_data,
            "decision": result,
        }

    # ========================================================
    # MARKET DATA CONVERSION
    # ========================================================

    @staticmethod
    def _convert_market_data(
        data: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Convert the market-data provider output into
        the field names expected by the AI analyzer.
        """

        return {
            "token_address": data.get(
                "token_address"
            ),
            "symbol": data.get(
                "base_symbol"
            ),
            "name": data.get(
                "base_name"
            ),
            "chain": data.get(
                "chain"
            ),
            "price": data.get(
                "price_usd"
            ),
            "price_change_1h": data.get(
                "price_change_24h"
            ),
            "volume_1h": data.get(
                "volume_24h"
            ),
            "volume_24h": data.get(
                "volume_24h"
            ),
            "market_cap": data.get(
                "market_cap"
            ),
            "fdv": data.get(
                "fdv"
            ),
            "liquidity_usd": data.get(
                "liquidity_usd"
            ),
            "buy_count": data.get(
                "buys_24h"
            ),
            "sell_count": data.get(
                "sells_24h"
            ),
            "pair_address": data.get(
                "pair_address"
            ),
            "dex": data.get(
                "dex"
            ),
        }


# ============================================================
# SIMPLE FUNCTION API
# ============================================================

def analyze_token(
    token_address: str,
) -> dict[str, Any]:
    """
    Convenience function for analyzing a token.
    """

    pipeline = TradingPipeline()

    return pipeline.analyze_token(
        token_address
    )
