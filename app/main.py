"""
Solana AI Trading Engine
========================

Current mode:
- PAPER TRADING ONLY
- No real blockchain transaction is executed
- Provides an HTTP health endpoint for Render
"""

from __future__ import annotations

import logging
import os
import sys
from typing import Any

from flask import Flask, jsonify

from app.config import (
    LIVE_TRADING,
    trading_mode,
    validate_config,
)

from app.ai.analyzer import (
    AIAnalyzer,
    AIAnalyzerError,
)


# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

logger = logging.getLogger("solana_trading_engine")


# ============================================================
# FLASK APP
# ============================================================

app = Flask(__name__)


# ============================================================
# HEALTH / STATUS
# ============================================================

@app.get("/")
def home():
    return jsonify(
        {
            "status": "online",
            "service": "Solana AI Trading Engine",
            "mode": trading_mode(),
            "live_trading": bool(LIVE_TRADING),
            "paper_trading": not bool(LIVE_TRADING),
        }
    )


@app.get("/health")
def health():
    return jsonify(
        {
            "status": "healthy",
            "service": "solana-ai-trading-engine",
            "mode": trading_mode(),
        }
    )


# ============================================================
# CONFIGURATION CHECK
# ============================================================

def startup_check() -> bool:
    try:
        validate_config()

        logger.info(
            "Trading mode: %s",
            trading_mode(),
        )

        if LIVE_TRADING:
            logger.warning(
                "LIVE_TRADING is enabled."
            )
        else:
            logger.info(
                "Paper trading mode is enabled."
            )

        return True

    except Exception as exc:
        logger.error(
            "Configuration validation failed: %s",
            exc,
        )
        return False


# ============================================================
# AI CONNECTION TEST
# ============================================================

def test_ai_connection() -> bool:
    try:
        analyzer = AIAnalyzer()

        logger.info(
            "Gemini AI analyzer initialized successfully."
        )

        logger.info(
            "Gemini model: %s",
            analyzer.model,
        )

        return True

    except AIAnalyzerError as exc:
        logger.error(
            "AI analyzer initialization failed: %s",
            exc,
        )
        return False

    except Exception as exc:
        logger.exception(
            "Unexpected AI initialization error: %s",
            exc,
        )
        return False


# ============================================================
# SAMPLE PAPER ANALYSIS
# ============================================================

def run_sample_analysis() -> None:

    sample_market_data: dict[str, Any] = {

        "token_address": "PAPER_TEST_TOKEN",
        "symbol": "TEST",
        "name": "Paper Test Token",
        "chain": "solana",

        "price": 0.001,

        "price_change_1m": 1.5,
        "price_change_5m": 4.2,
        "price_change_15m": 7.8,
        "price_change_1h": 12.5,

        "volume_1m": 1500,
        "volume_5m": 7000,
        "volume_15m": 18000,
        "volume_1h": 50000,

        "market_cap": 50000,
        "fdv": 60000,

        "liquidity_usd": 15000,

        "holders": 500,

        "top_holder_percent": 12,
        "top_10_holder_percent": 35,

        "buy_count": 120,
        "sell_count": 80,
        "buy_sell_ratio": 1.5,

        "tx_count": 200,

        "age_minutes": 30,

        "dex": "paper-test",

        "mint_authority": None,
        "freeze_authority": None,

        "lp_locked": True,
        "lp_burned": False,

        "contract_verified": True,
        "honeypot_check": True,

        "tax_buy": 0,
        "tax_sell": 0,

        "developer_holding_percent": 5,
        "insider_holding_percent": 8,

        "social_score": 0.5,
    }

    try:

        analyzer = AIAnalyzer()

        logger.info(
            "Running sample PAPER analysis..."
        )

        result = analyzer.analyze(
            sample_market_data
        )

        logger.info(
            "AI decision: %s",
            result.get("decision"),
        )

        logger.info(
            "AI confidence: %s",
            result.get("confidence"),
        )

        logger.info(
            "Risk score: %s",
            result.get("risk_score"),
        )

        logger.info(
            "Signal quality: %s",
            result.get("signal_quality"),
        )

        logger.info(
            "Sample PAPER analysis completed."
        )

    except AIAnalyzerError as exc:

        logger.error(
            "AI analysis failed: %s",
            exc,
        )

    except Exception as exc:

        logger.exception(
            "Unexpected analysis error: %s",
            exc,
        )


# ============================================================
# STARTUP
# ============================================================

def initialize_engine() -> bool:

    logger.info(
        "=========================================="
    )

    logger.info(
        "Solana AI Trading Engine starting..."
    )

    logger.info(
        "=========================================="
    )

    if not startup_check():
        logger.error(
            "Startup configuration check failed."
        )
        return False

    if not test_ai_connection():
        logger.error(
            "AI connection test failed."
        )
        return False

    run_sample_analysis()

    logger.info(
        "Engine initialization completed."
    )

    logger.info(
        "NO REAL TRADE WAS EXECUTED."
    )

    return True


# ============================================================
# MAIN
# ============================================================

def main() -> int:

    initialize_engine()

    # Render provides PORT automatically.
    port = int(
        os.environ.get(
            "PORT",
            "10000",
        )
    )

    host = "0.0.0.0"

    logger.info(
        "HTTP server starting on %s:%s",
        host,
        port,
    )

    app.run(
        host=host,
        port=port,
        debug=False,
    )

    return 0


# ============================================================
# PROGRAM ENTRY
# ============================================================

if __name__ == "__main__":
    sys.exit(
        main()
    )
