from __future__ import annotations

import unittest

from app.market_data import SolanaMarketData


class MarketDataHelperTests(unittest.TestCase):

    def test_select_best_pair(self) -> None:

        pairs = [
            {
                "chainId": "solana",
                "liquidity": {
                    "usd": 1000,
                },
            },
            {
                "chainId": "solana",
                "liquidity": {
                    "usd": 5000,
                },
            },
        ]

        result = SolanaMarketData._select_best_pair(
            pairs
        )

        self.assertIsNotNone(result)

        self.assertEqual(
            result["liquidity"]["usd"],
            5000,
        )

    def test_select_best_pair_empty(self) -> None:

        result = SolanaMarketData._select_best_pair(
            []
        )

        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
