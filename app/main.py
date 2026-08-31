"""
app/main.py
Solana AI Meme Trading Bot - Production Web Entry Point

Designed for:
- Render + Gunicorn
- Flask web entry point
- Background trading worker
- AI analysis
- Token scanner
- Paper trading
- Telegram notifications

IMPORTANT:
- LIVE_TRADING is controlled by environment/config.
- This file itself does NOT execute real blockchain transactions.
"""

from __future__ import annotations

import logging
import os
import threading
import time
from typing import Any

from dotenv import load_dotenv
from flask import Flask, jsonify


# =========================================================
# ENVIRONMENT
# =========================================================

load_dotenv()


# =========================================================
# LOGGING
# =========================================================

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

logger = logging.getLogger("solana-ai-bot")


# =========================================================
# FLASK APP
# =========================================================

app = Flask(__name__)


# =========================================================
# OPTIONAL PROJECT MODULES
# =========================================================

MODULE_ERROR: str | None = None


# ---------------------------------------------------------
# CONFIG
# ---------------------------------------------------------

try:
    from app.config import trading_mode, validate_config

except Exception as exc:
    MODULE_ERROR = f"config import failed: {exc}"

    def trading_mode() -> str:
        return (
            "LIVE"
            if os.getenv("LIVE_TRADING", "false").lower() == "true"
            else "PAPER"
        )

    def validate_config() -> None:
        return None


# ---------------------------------------------------------
# DATABASE
# ---------------------------------------------------------

try:
    from app.database.database import initialize_database

except Exception as exc:
    MODULE_ERROR = MODULE_ERROR or (
        f"database import failed: {exc}"
    )

    def initialize_database() -> None:
        return None


# ---------------------------------------------------------
# SCANNER
# ---------------------------------------------------------

try:
    from app.scanner import scan_tokens

except Exception as exc:
    MODULE_ERROR = MODULE_ERROR or (
        f"scanner import failed: {exc}"
    )

    def scan_tokens() -> list[dict[str, Any]]:
        return []


# ---------------------------------------------------------
# AI ANALYZER
# ---------------------------------------------------------

try:
    from app.ai.analyzer import AIAnalyzer

except Exception as exc:
    MODULE_ERROR = MODULE_ERROR or (
        f"AI analyzer import failed: {exc}"
    )

    AIAnalyzer = None  # type: ignore


# ---------------------------------------------------------
# PAPER TRADER
# ---------------------------------------------------------

try:
    from app.trading.paper_trader import PaperTrader

except Exception as exc:
    MODULE_ERROR = MODULE_ERROR or (
        f"paper trader import failed: {exc}"
    )

    PaperTrader = None  # type: ignore


# ---------------------------------------------------------
# TELEGRAM
# ---------------------------------------------------------

try:
    from app.telegram_notifier import send_message

except Exception as exc:
    MODULE_ERROR = MODULE_ERROR or (
        f"telegram notifier import failed: {exc}"
    )

    def send_message(text: str) -> None:
        logger.info(
            "Telegram disabled/unavailable: %s",
            text,
        )


# =========================================================
# RUNTIME STATE
# =========================================================

START_TIME = time.time()

CURRENT_MODE = trading_mode()

BOT_STATUS: dict[str, Any] = {
    "status": "starting",
    "service": "Solana AI Meme Trading Bot",
    "mode": CURRENT_MODE,
    "running": False,
    "worker_running": False,
    "ai_enabled": False,
    "scanner_enabled": False,
    "paper_trading": CURRENT_MODE != "LIVE",
    "live_trading": CURRENT_MODE == "LIVE",
    "last_scan": None,
    "last_error": MODULE_ERROR,
    "tokens_scanned": 0,
    "trades_executed": 0,
    "started_at": int(START_TIME),
}


# =========================================================
# WORKER CONTROL
# =========================================================

_WORKER_LOCK = threading.Lock()
_WORKER_STARTED = False


# =========================================================
# HELPERS
# =========================================================

def _uptime_seconds() -> int:
    """Return application uptime in seconds."""
    return max(
        0,
        int(time.time() - START_TIME),
    )


def _safe_float(
    value: Any,
    default: float = 0.0,
) -> float:
    """Safely convert a value to float."""

    try:
        return float(value)

    except (TypeError, ValueError):
        return default


def _safe_int(
    value: Any,
    default: int = 0,
) -> int:
    """Safely convert a value to int."""

    try:
        return int(value)

    except (TypeError, ValueError):
        return default


# =========================================================
# ROOT ENDPOINT
# =========================================================

@app.get("/")
def home():
    """
    Main Render/browser endpoint.

    Prevents:
        404 Not Found
    """

    return jsonify(
        {
            "status": "online",
            "service": "Solana AI Meme Trading Bot",
            "mode": BOT_STATUS["mode"],
            "message": "Bot is running.",
            "uptime_seconds": _uptime_seconds(),
            "worker_running": BOT_STATUS["worker_running"],
            "ai_enabled": BOT_STATUS["ai_enabled"],
            "scanner_enabled": BOT_STATUS["scanner_enabled"],
            "paper_trading": BOT_STATUS["paper_trading"],
            "live_trading": BOT_STATUS["live_trading"],
        }
    ), 200


# =========================================================
# HEALTH ENDPOINT
# =========================================================

@app.get("/health")
def health():
    """
    Render health endpoint.
    """

    is_healthy = (
        BOT_STATUS["status"] in {
            "starting",
            "online",
        }
        and BOT_STATUS["last_error"] is None
    )

    return jsonify(
        {
            "status": (
                "healthy"
                if is_healthy
                else "degraded"
            ),
            "service": "Solana AI Meme Trading Bot",
            "mode": BOT_STATUS["mode"],
            "uptime_seconds": _uptime_seconds(),
            "worker_running": BOT_STATUS["worker_running"],
            "ai_enabled": BOT_STATUS["ai_enabled"],
            "scanner_enabled": BOT_STATUS[
                "scanner_enabled"
            ],
            "last_scan": BOT_STATUS["last_scan"],
            "last_error": BOT_STATUS["last_error"],
        }
    ), 200 if is_healthy else 503


# =========================================================
# STATUS ENDPOINT
# =========================================================

@app.get("/status")
def status():
    """
    Detailed bot runtime status.
    """

    return jsonify(
        {
            **BOT_STATUS,
            "uptime_seconds": _uptime_seconds(),
        }
    ), 200


# =========================================================
# API INFO
# =========================================================

@app.get("/api")
def api_info():
    """
    Basic API information.
    """

    return jsonify(
        {
            "service": "Solana AI Meme Trading Bot",
            "status": "online",
            "mode": BOT_STATUS["mode"],
            "endpoints": {
                "home": "/",
                "health": "/health",
                "status": "/status",
                "api": "/api",
            },
        }
    ), 200


# =========================================================
# BACKGROUND WORKER STARTER
# =========================================================

def _start_background_worker_once() -> None:
    """
    Start exactly one background worker in this process.

    Recommended Render configuration:
        Gunicorn workers = 1
    """

    global _WORKER_STARTED

    with _WORKER_LOCK:

        if _WORKER_STARTED:
            return

        _WORKER_STARTED = True

        worker = threading.Thread(
            target=background_worker,
            name="trading-worker",
            daemon=True,
        )

        worker.start()

        logger.info(
            "Background trading worker started."
        )


# =========================================================
# BACKGROUND TRADING WORKER
# =========================================================

def background_worker() -> None:
    """
    Main trading engine.

    Flow:

        Configuration
             ↓
        Database
             ↓
        Scanner
             ↓
        AI Analyzer
             ↓
        Risk Review
             ↓
        Paper Trader
             ↓
        Telegram
    """

    BOT_STATUS["status"] = "starting"
    BOT_STATUS["worker_running"] = True

    try:

        # =================================================
        # CONFIGURATION
        # =================================================

        try:

            validate_config()

            logger.info(
                "Configuration validation completed."
            )

        except Exception as exc:

            logger.exception(
                "Configuration validation failed."
            )

            BOT_STATUS["last_error"] = (
                f"Configuration error: {exc}"
            )


        # =================================================
        # DATABASE
        # =================================================

        try:

            initialize_database()

            logger.info(
                "Database initialization completed."
            )

        except Exception as exc:

            logger.exception(
                "Database initialization failed."
            )

            BOT_STATUS["last_error"] = (
                f"Database error: {exc}"
            )


        # =================================================
        # AI ENGINE
        # =================================================

        analyzer = None

        if AIAnalyzer is not None:

            try:

                analyzer = AIAnalyzer()

                BOT_STATUS["ai_enabled"] = True

                logger.info(
                    "AI analyzer initialized."
                )

            except Exception as exc:

                logger.exception(
                    "AI analyzer initialization failed."
                )

                BOT_STATUS["ai_enabled"] = False

                BOT_STATUS["last_error"] = (
                    f"AI initialization error: {exc}"
                )


        # =================================================
        # PAPER TRADER
        # =================================================

        trader = None

        if PaperTrader is not None:

            try:

                starting_balance = _safe_float(
                    os.getenv(
                        "PAPER_START_BALANCE_USD",
                        "100.0",
                    ),
                    100.0,
                )

                trader = PaperTrader(
                    starting_balance=starting_balance
                )

                logger.info(
                    "Paper trader initialized "
                    "with balance: $%.2f",
                    starting_balance,
                )

            except Exception as exc:

                logger.exception(
                    "Paper trader initialization failed."
                )

                BOT_STATUS["last_error"] = (
                    f"Trader initialization error: {exc}"
                )


        # =================================================
        # ENGINE READY
        # =================================================

        BOT_STATUS["scanner_enabled"] = True
        BOT_STATUS["status"] = "online"
        BOT_STATUS["running"] = True

        logger.info(
            "Trading engine online | mode=%s",
            BOT_STATUS["mode"],
        )


        # =================================================
        # SCAN INTERVAL
        # =================================================

        try:

            scan_interval = max(
                5,
                _safe_int(
                    os.getenv(
                        "SCAN_INTERVAL_SECONDS",
                        "30",
                    ),
                    30,
                ),
            )

        except Exception:

            scan_interval = 30


        logger.info(
            "Scan interval: %s seconds",
            scan_interval,
        )


        # =================================================
        # MAIN LOOP
        # =================================================

        while True:

            scan_started = time.time()

            try:

                # =========================================
                # SCAN TOKENS
                # =========================================

                tokens = scan_tokens()

                if tokens is None:
                    tokens = []

                if not isinstance(tokens, list):
                    logger.warning(
                        "Scanner returned unexpected type: %s",
                        type(tokens).__name__,
                    )

                    tokens = []

                BOT_STATUS["tokens_scanned"] += len(
                    tokens
                )

                BOT_STATUS["last_scan"] = int(
                    time.time()
                )

                BOT_STATUS["last_error"] = None

                logger.info(
                    "Scanner returned %d token(s).",
                    len(tokens),
                )


                # =========================================
                # PROCESS TOKENS
                # =========================================

                for market_data in tokens:

                    if not isinstance(
                        market_data,
                        dict,
                    ):
                        continue


                    # -------------------------------------
                    # TOKEN ADDRESS
                    # -------------------------------------

                    token_address = market_data.get(
                        "token_address"
                    )

                    if not token_address:
                        continue


                    # -------------------------------------
                    # SYMBOL
                    # -------------------------------------

                    symbol = (
                        market_data.get("symbol")
                        or str(token_address)[:6]
                    )


                    # =====================================
                    # AI ANALYSIS
                    # =====================================

                    if analyzer is None:

                        logger.warning(
                            "AI analyzer unavailable; "
                            "skipping %s",
                            symbol,
                        )

                        continue


                    try:

                        decision = analyzer.analyze(
                            market_data
                        )

                    except Exception:

                        logger.exception(
                            "AI analysis failed for %s",
                            symbol,
                        )

                        continue


                    # =====================================
                    # RISK REVIEW
                    # =====================================

                    try:

                        review = analyzer.risk_review(
                            market_data,
                            decision,
                        )

                    except Exception:

                        logger.exception(
                            "Risk review failed for %s",
                            symbol,
                        )

                        continue


                    if not isinstance(
                        review,
                        dict,
                    ):
                        continue


                    # =====================================
                    # FINAL DECISION
                    # =====================================

                    default_decision = "HOLD"

                    if isinstance(
                        decision,
                        dict,
                    ):
                        default_decision = str(
                            decision.get(
                                "decision",
                                "HOLD",
                            )
                        )


                    final_decision = str(
                        review.get(
                            "final_decision",
                            default_decision,
                        )
                    ).upper()


                    approved = bool(
                        review.get(
                            "approved",
                            False,
                        )
                    )


                    # =====================================
                    # CONFIDENCE
                    # =====================================

                    if isinstance(
                        decision,
                        dict,
                    ):
                        confidence = _safe_float(
                            decision.get(
                                "confidence",
                                0,
                            ),
                            0.0,
                        )
                    else:
                        confidence = 0.0


                    logger.info(
                        "AI | %s | decision=%s | "
                        "approved=%s | confidence=%.4f",
                        symbol,
                        final_decision,
                        approved,
                        confidence,
                    )


                    # =====================================
                    # BUY
                    # =====================================

                    if (
                        final_decision == "BUY"
                        and approved
                        and trader is not None
                    ):

                        max_position = _safe_float(
                            os.getenv(
                                "MAX_POSITION_USD",
                                "10.0",
                            ),
                            10.0,
                        )


                        # ---------------------------------
                        # BALANCE
                        # ---------------------------------

                        try:

                            if hasattr(
                                trader,
                                "get_balance",
                            ):
                                current_balance = (
                                    trader.get_balance()
                                )

                            else:
                                current_balance = (
                                    trader.balance
                                )

                            balance = _safe_float(
                                curre
