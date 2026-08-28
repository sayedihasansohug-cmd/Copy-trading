"""
Integration test for the Solana AI trading pipeline.

This test does NOT execute real trades.
"""

from __future__ import annotations

import unittest
from unittest.mock import patch

from app.ai.pipeline import TradingPipeline


class TradingPipelineTests(unittest.TestCase):

    @patch(
        "app.ai.pipeline.SolanaMarketData.get_token_data"
    )
    @patch(
        "app.ai.pipeline.DecisionService.evaluate"
    )
    def test_analyze_token(
        self,
        mock_evaluate,
        mock_market_data,
    ) -> None:

        mock_market_data.return_value = {
            "token_address": "TEST_TOKEN",
            "chain": "solana",
            "base_symbol": "TEST",
            "base_name": "Test Token",
            "pair_address": "TEST_PAIR",
            "dex": "test-dex",
            "price_usd": 0.001,
            "liquidity_usd": 50000,
            "market_cap": 250000,
            "fdv": 300000,
            "volume_24h": 100000,
            "price_change_24h": 10,
            "buys_24h": 500,
            "sells_24h": 300,
        }

        mock_evaluate.return_value = {
            "analysis": {
                "decision": "BUY",
                "confidence": 0.80,
                "risk_score": 0.40,
            },
            "risk_review": {
                "approved": True,
                "final_decision": "BUY",
                "risk_score": 0.40,
            },
            "final": {
                "decision": "BUY",
                "approved": True,
            },
        }

        pipeline = TradingPipeline()

        result = pipeline.analyze_token(
            "TEST_TOKEN"
        )

        self.assertIn(
            "token_address",
            result,
        )

        self.assertIn(
            "market_data",
            result,
        )

        self.assertIn(
            "decision",
            result,
        )

        self.assertEqual(
            result["token_address"],
            "TEST_TOKEN",
        )

        self.assertEqual(
            result["decision"]["final"]["decision"],
            "BUY",
        )

        mock_market_data.assert_called_once_with(
            "TEST_TOKEN"
        )

        mock_evaluate.assert_called_once()


if __name__ == "__main__":
    unittest.main()
