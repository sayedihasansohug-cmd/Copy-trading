"""
Solana AI Trading Engine
========================

Purpose:
- Startup configuration validation
- Gemini AI analyzer initialization
- Safe paper-trading analysis
- Health/status endpoint
- Graceful error handling

IMPORTANT:
This version is PAPER TRADING ONLY.
No real Solana transaction is created, signed, or submitted.
"""

from __future__ import annotations

import logging
import os
import sys
import time
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
# APPLICATION INFO
# ============================================================

APP_NAME = "Solana AI Trading Engine"
APP_VERSION = "1.0.0"

# Force-safe mode.
# Even if an environment variable accidentally enables live
# trading, this file will refuse to run live trades.
PAPER_ONLY = True


# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format=(
        "%(asctime)s | "
        "%(levelname)s | "
        "%(name)s | "
        "%(message)s"
    ),
)

logger = logging.getLogger("solana_trading_engine")


# ============================================================
# FLASK HEALTH SERVER
# ============================================================

app = Flask(__name__)


@app.get("/")
def home():
    """
    Basic application status page.
    """

    return jsonify(
        {
            "application": APP_NAME,
            "version": APP_VERSION,
            "status": "online",
            "trading_mode": trading_mode(),
            "paper_only": PAPER_ONLY,
            "live_trading_config": bool(LIVE_TRADING),
            "real_trades_enabled": False,
        }
    )


@app.get("/health")
def health():
    """
    Health check endpoint for Render.
    """

    return jsonify(
        {
            "status": "healthy",
            "application": APP_NAME,
            "paper_only": True,
            "real_trades_enabled": False,
        }
    )


@app.get("/status")
def status():
    """
    Detailed engine status.
    """

    return jsonify(
        {
            "application": APP_NAME,
            "version": APP_VERSION,
            "trading_mode": trading_mode(),
            "paper_only": PAPER_ONLY,
            "configured_live_trading": bool(LIVE_TRADING),
            "real_trade_execution": False,
            "ai_analyzer": "available",
        }
    )


# ============================================================
# STARTUP CHECK
# ============================================================

def startup_check() -> bool:
    """
    Validate configuration before starting the engine.
    """

    logger.info("Running startup configuration check...")

    try:
        validate_config()

    except Exception as exc:
        logger.error(
            "Configuration validation failed: %s",
            exc,
        )
        return False

    logger.info(
        "Trading mode reported by config: %s",
        trading_mode(),
    )

    # --------------------------------------------------------
    # HARD SAFETY CHECK
    # --------------------------------------------------------

    if PAPER_ONLY and LIVE_TRADING:

        logger.error(
            "SAFETY STOP: LIVE_TRADING is enabled, "
            "but this main.py is configured as PAPER ONLY."
        )

        logger.error(
            "No real transaction will be executed."
        )

        return False

    logger.info(
        "Paper trading safety mode: ENABLED"
    )

    logger.info(
        "Real trade execution: DISABLED"
    )

    return True


# ============================================================
# AI CONNECTION TEST
# ============================================================

def test_ai_connection() -> bool:
    """
    Initialize the AI analyzer.

    No trading transaction is performed here.
    """

    logger.info(
        "Testing AI analyzer..."
    )

    try:

        analyzer = AIAnalyzer()

        logger.info(
            "AI analyzer initialized successfully."
        )

        logger.info(
            "AI model: %s",
            getattr(
                analyzer,
                "model",
                "unknown",
            ),
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
# SAMPLE MARKET DATA
# ============================================================

def get_sample_market_data() -> dict[str, Any]:
    """
    Return safe test market data.

    This data is completely artificial.
    """

    return {
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

        "liquidity": 15000,
        "liquidity_usd": 15000,

        "holders": 500,

        "top_holder_percent": 12,
        "top_10_holder_percent": 35,

        "buy_count": 120,
        "sell_count": 80,
        "buy_sell_ratio": 1.5,

        "tx_count": 200,

        "age_minutes": 30,

        "pair_address": "PAPER_TEST_PAIR",
        "dex": "paper-test",

        "token_created_at": None,

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

        "website": None,
        "telegram": None,
        "twitter": None,
    }


# ============================================================
# SAMPLE AI ANALYSIS
# ============================================================

def run_sample_analysis() -> bool:
    """
    Perform one AI analysis using artificial market data.

    IMPORTANT:
    This function NEVER executes a trade.
    """

    logger.info(
        "------------------------------------------"
    )

    logger.info(
        "Starting paper analysis..."
    )

    logger.info(
        "No real wallet will be used."
    )

    logger.info(
        "No real transaction will be submitted."
    )

    try:

        analyzer = AIAnalyzer()

        market_data = get_sample_market_data()

        result = analyzer.analyze(
            market_data
        )

        # ----------------------------------------------------
        # Extract results safely
        # ----------------------------------------------------

        decision = result.get(
            "decision",
            "UNKNOWN",
        )

        confidence = result.get(
            "confidence",
            0,
        )

        risk_score = result.get(
            "risk_score",
            0,
        )

        signal_quality = result.get(
            "signal_quality",
            0,
        )

        entry_score = result.get(
            "entry_score",
            0,
        )

        liquidity_score = result.get(
            "liquidity_score",
            0,
        )

        momentum_score = result.get(
            "momentum_score",
            0,
        )

        volume_score = result.get(
            "volume_score",
            0,
        )

        holder_score = result.get(
            "holder_score",
            0,
        )

        safety_score = result.get(
            "safety_score",
            0,
        )

        # ----------------------------------------------------
        # Log result
        # ----------------------------------------------------

        logger.info(
            "AI DECISION       : %s",
            decision,
        )

        logger.info(
            "CONFIDENCE        : %s",
            confidence,
        )

        logger.info(
            "RISK SCORE        : %s",
            risk_score,
        )

        logger.info(
            "SIGNAL QUALITY    : %s",
            signal_quality,
        )

        logger.info(
            "ENTRY SCORE       : %s",
            entry_score,
        )

        logger.info(
            "LIQUIDITY SCORE   : %s",
            liquidity_score,
        )

        logger.info(
            "MOMENTUM SCORE    : %s",
            momentum_score,
        )

        logger.info(
            "VOLUME SCORE      : %s",
            volume_score,
        )

        logger.info(
            "HOLDER SCORE      : %s",
            holder_score,
        )

        logger.info(
            "SAFETY SCORE      : %s",
            safety_score,
        )

        # ----------------------------------------------------
        # Reasons
        # ----------------------------------------------------

        reasons = result.get(
            "reasons",
            [],
        )

        if isinstance(reasons, list):

            for reason in reasons[:10]:

                logger.info(
                    "REASON: %s",
                    reason,
                )

        # ----------------------------------------------------
        # Warnings
        # ----------------------------------------------------

        warnings = result.get(
            "warnings",
            [],
        )

        if isinstance(warnings, list):

            for warning in warnings[:10]:

                logger.warning(
                    "WARNING: %s",
                    warning,
                )

        logger.info(
            "Paper analysis completed successfully."
        )

        logger.info(
            "------------------------------------------"
        )

        return True

    except AIAnalyzerError as exc:

        logger.error(
            "AI analysis failed: %s",
            exc,
        )

        return False

    except Exception as exc:

        logger.exception(
            "Unexpected analysis error: %s",
            exc,
        )

        return False


# ============================================================
# ENGINE STARTUP
# ============================================================

def initialize_engine() -> bool:
    """
    Complete engine initialization.

    Returns:
        True if startup succeeds.
        False if startup fails.
    """

    logger.info(
        "=========================================="
    )

    logger.info(
        "%s",
        APP_NAME,
    )

    logger.info(
        "Version: %s",
        APP_VERSION,
    )

    logger.info(
        "=========================================="
    )

    # --------------------------------------------------------
    # 1. Configuration
    # --------------------------------------------------------

    if not startup_check():

        logger.error(
            "Startup configuration check failed."
        )

        return False

    # --------------------------------------------------------
    # 2. AI
    # --------------------------------------------------------

    if not test_ai_connection():

        logger.error(
            "AI connection test failed."
        )

        return False

    # --------------------------------------------------------
    # 3. Paper analysis
    # --------------------------------------------------------

    if not run_sample_analysis():

        logger.error(
            "Sample paper analysis failed."
        )

        return False

    # --------------------------------------------------------
    # Complete
    # --------------------------------------------------------

    logger.info(
        "=========================================="
    )

    logger.info(
        "ENGINE INITIALIZED SUCCESSFULLY"
    )

    logger.info(
        "Trading mode: PAPER"
    )

    logger.info(
        "Real transactions: DISABLED"
    )

    logger.info(
        "=========================================="
    )

    return True


# ============================================================
# WORKER MODE
# ============================================================

def run_worker() -> None:
    """
    Run the engine as a long-running worker.

    Currently this is only a safe startup/heartbeat loop.
    No real trading is performed.
    """

    logger.info(
        "Starting paper-trading worker..."
    )

    if not initialize_engine():

        logger.error(
            "Engine initialization failed."
        )

        sys.exit(1)

    logger.info(
        "Worker is running."
    )

    while True:

        try:

            logger.info(
                "Engine heartbeat | "
                "mode=PAPER | "
                "real_trades=False",
            )

            time.sleep(60)

        except KeyboardInterrupt:

            logger.info(
                "Shutdown requested."
            )

            break

        except Exception as exc:

            logger.exception(
                "Worker error: %s",
                exc,
            )

            time.sleep(10)


# ============================================================
# MAIN
# ============================================================

def main() -> int:
    """
    Local/worker entry point.
    """

    logger.info(
        "Starting Solana AI Trading Engine..."
    )

    success = initialize_engine()

    if not success:

        logger.error(
            "Application startup failed."
        )

        return 1

    logger.info(
        "Application startup completed."
    )

    logger.info(
        "No real trade was executed."
    )

    return 0


# ============================================================
# PROGRAM ENTRY
# ============================================================

if __name__ == "__main__":

    # Worker mode can be enabled with:
    #
    # RUN_WORKER=true
    #
    # Otherwise perform one startup test and exit.

    run_worker_enabled = (
        os.getenv(
            "RUN_WORKER",
            "false",
        ).lower()
        == "true"
    )

    if run_worker_enabled:

        run_worker()

    else:

        sys.exit(
            main()
        )
