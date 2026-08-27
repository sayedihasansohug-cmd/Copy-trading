"""
Test script for the Gemini AI analyzer.

IMPORTANT:
This script ONLY tests AI analysis.
It does NOT execute trades.
"""

from __future__ import annotations

import json
import sys

from app.ai.analyzer import AIAnalyzer


def main() -> None:
    print("=" * 60)
    print("Solana AI Analyzer Test")
    print("=" * 60)

    try:
        analyzer = AIAnalyzer()
    except Exception as exc:
        print("\n[ERROR] AI Analyzer initialization failed.")
        print(str(exc))
        sys.exit(1)

    # --------------------------------------------------------
    # TEST MARKET DATA
    # --------------------------------------------------------

    market_data = {
        "token_address": "TEST_TOKEN_ADDRESS",
        "symbol": "TEST",
        "name": "Test Token",
        "chain": "solana",

        "price": 0.001,
        "price_change_1m": 1.2,
        "price_change_5m": 4.5,
        "price_change_15m": 8.0,
        "price_change_1h": 12.5,

        "volume_1m": 5000,
        "volume_5m": 25000,
        "volume_15m": 70000,
        "volume_1h": 200000,

        "market_cap": 50000,
        "fdv": 55000,

        "liquidity": 15000,
        "liquidity_usd": 15000,

        "holders": 250,
        "top_holder_percent": 8,
        "top_10_holder_percent": 30,

        "buy_count": 120,
        "sell_count": 80,
        "buy_sell_ratio": 1.5,
        "tx_count": 200,

        "age_minutes": 30,

        "pair_address": "TEST_PAIR",
        "dex": "TEST_DEX",

        "token_created_at": None,

        "mint_authority": None,
        "freeze_authority": None,

        "lp_locked": True,
        "lp_burned": False,

        "contract_verified": False,
        "honeypot_check": True,

        "tax_buy": 0,
        "tax_sell": 0,

        "developer_holding_percent": 5,
        "insider_holding_percent": 10,

        "social_score": 0.6,

        "website": None,
        "telegram": None,
        "twitter": None,
    }

    # --------------------------------------------------------
    # RUN AI ANALYSIS
    # --------------------------------------------------------

    print("\n[INFO] Sending test market data to Gemini...")

    try:
        result = analyzer.analyze(market_data)
    except Exception as exc:
        print("\n[ERROR] AI analysis failed.")
        print(str(exc))
        sys.exit(1)

    # --------------------------------------------------------
    # PRINT RESULT
    # --------------------------------------------------------

    print("\n[OK] AI analysis completed.\n")

    print(
        json.dumps(
            result,
            indent=2,
            ensure_ascii=False,
            default=str,
        )
    )

    print("\n" + "=" * 60)
    print("TEST COMPLETED")
    print("=" * 60)


if __name__ == "__main__":
    main()
