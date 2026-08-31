"""
app/main.py
Solana AI Meme Trading Bot - Production Web Entry Point

IMPORTANT:
- Designed for Render + Gunicorn
- Root URL "/" always returns JSON
- /health provides deployment health status
- /status provides bot runtime status
- Background worker is started safely for a single Gunicorn worker
- LIVE_TRADING remains controlled by environment/config
"""

from __future__ import annotations

import logging
import os
import threading
import time
from typing import Any

from flask import Flask, jsonify

from dotenv import load_dotenv

# ---------------------------------------------------------
# ENVIRONMENT
# ---------------------------------------------------------

load_dotenv()

# ---------------------------------------------------------
# LOGGING
# ---------------------------------------------------------

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

logger = logging.getLogger("solana-ai-bot")

# ---------------------------------------------------------
# FLASK APP
# ---------------------------------------------------------

app = Flask(__name__)

# ---------------------------------------------------------
# OPTIONAL PROJECT MODULES
# ---------------------------------------------------------
#
# Lazy/fault-tolerant imports are used so that the web
# health endpoint can still come online and show the
# actual module error instead of returning "Not Found"
# or completely failing during deployment.
# ---------------------------------------------------------

MODULE_ERROR: str | None = None

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


try:
    from app.database.database import initialize_database
except Exception as exc:
    MODULE_ERROR = MODULE_ERROR or f"database import failed: {exc}"

    def initialize_database() -> None:
        return None


try:
    from app.scanner import scan_tokens
except Exception as exc:
    MODULE_ERROR = MODULE_ERROR or f"scanner import failed: {exc}"

    def scan_tokens() -> list[dict[str, Any]]:
        return []


try:
    from app.ai.analyzer import AIAnalyzer
except Exception as exc:
    MODULE_ERROR = MODULE_ERROR or f"AI analyzer import failed: {exc}"

    AIAnalyzer = None  # type: ignore


try:
    from app.trading.paper_trader import PaperTrader
except Exception as exc:
    MODULE_ERROR = MODULE_ERROR or f"paper trader import failed: {exc}"

    PaperTrader = None  # type: ignore


try:
    from app.telegram_notifier import send_message
except Exception as exc:
    MODULE_ERROR = MODULE_ERROR or f"telegram notifier import failed: {exc}"

    def send_message(text: str) -> None:
        logger.info("Telegram disabled/unavailable: %s", text)


# ---------------------------------------------------------
# RUNTIME STATE
# ---------------------------------------------------------

START_TIME = time.time()

BOT_STATUS: dict[str, Any] = {
    "status": "starting",
    "service": "Solana AI Meme Trading Bot",
    "mode": trading_mode(),
    "running": False,
    "worker_running": False,
    "ai_enabled": False,
    "scanner_enabled": False,
    "paper_trading": trading_mode() != "LIVE",
    "live_trading": trading_mode() == "LIVE",
    "last_scan": None,
    "last_error": None,
    "tokens_scanned": 0,
    "trades_executed": 0,
    "started_at": int(START_TIME),
}


# Prevent accidental duplicate background threads
_WORKER_LOCK = threading.Lock()
_WORKER_STARTED = False


# ---------------------------------------------------------
# HELPERS
# ---------------------------------------------------------

def _uptime_seconds() -> int:
    return max(0, int(time.time() - START_TIME))


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _start_background_worker_once() -> None:
    """
    Start exactly one background worker in this process.

    Render should use ONE Gunicorn worker for this architecture.
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

        logger.info("Background trading worker started.")


# ---------------------------------------------------------
# ROOT ENDPOINT
# ---------------------------------------------------------

@app.get("/")
def home():
    """
    Render/browser health endpoint.

    This prevents:
        404 Not Found

    when opening the Render service URL.
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
            "paper_trading": BOT_STATUS["paper_trading"],
            "live_trading": BOT_STATUS["live_trading"],
        }
    ), 200


# ---------------------------------------------------------
# HEALTH ENDPOINT
# ---------------------------------------------------------

@app.get("/health")
def health():
    """
    Render health endpoint.
    """

    is_healthy = (
        BOT_STATUS["status"] in {"starting", "online"}
        and BOT_STATUS["last_error"] is None
    )

    return jsonify(
        {
            "status": "healthy" if is_healthy else "degraded",
            "service": "Solana AI Meme Trading Bot",
            "mode": BOT_STATUS["mode"],
            "uptime_seconds": _uptime_seconds(),
            "worker_running": BOT_STATUS["worker_running"],
            "ai_enabled": BOT_STATUS["ai_enabled"],
            "scanner_enabled": BOT_STATUS["scanner_enabled"],
            "last_scan": BOT_STATUS["last_scan"],
            "last_error": BOT_STATUS["last_error"],
        }
    ), 200 if is_healthy else 503


# ---------------------------------------------------------
# STATUS ENDPOINT
# ---------------------------------------------------------

@app.get("/status")
def status():
    """
    Detailed bot status.
    """

    return jsonify(
        {
            **BOT_STATUS,
            "uptime_seconds": _uptime_seconds(),
        }
    ), 200


# ---------------------------------------------------------
# SIMPLE API INFO ENDPOINT
# ---------------------------------------------------------

@app.get("/api")
def api_info():
    return jsonify(
        {
            "service": "Solana AI Meme Trading Bot",
            "status": "online",
            "endpoints": {
                "home": "/",
                "health": "/health",
                "status": "/status",
                "api": "/api",
            },
        }
    ), 200


# ---------------------------------------------------------
# BACKGROUND TRADING WORKER
# ---------------------------------------------------------

def background_worker() -> None:
    """
    Main background engine.

    Flow:

        Validate configuration
              ↓
        Initialize database
              ↓
        Scanner
              ↓
        AI Analyzer
              ↓
        Risk Review
              ↓
        Paper Trader
              ↓
        Telegram notification
    """

    BOT_STATUS["status"] = "starting"
    BOT_STATUS["worker_running"] = True

    try:
        # ---------------------------------------------
        # CONFIG VALIDATION
        # ---------------------------------------------

        try:
            validate_config()
            logger.info("Configuration validation completed.")
        except Exception as exc:
            logger.exception("Configuration validation failed.")
            BOT_STATUS["last_error"] = f"Configuration error: {exc}"

        # ---------------------------------------------
        # DATABASE
        # ---------------------------------------------

        try:
            initialize_database()
            logger.info("Database initialization completed.")
        except Exception as exc:
            logger.exception("Database initialization failed.")
            BOT_STATUS["last_error"] = f"Database error: {exc}"

        # ---------------------------------------------
        # AI ENGINE
        # ---------------------------------------------

        analyzer = None

        if AIAnalyzer is not None:
            try:
                analyzer = AIAnalyzer()
                BOT_STATUS["ai_enabled"] = True
                logger.info("AI analyzer initialized.")
            except Exception as exc:
                logger.exception("AI analyzer initialization failed.")
                BOT_STATUS["ai_enabled"] = False
                BOT_STATUS["last_error"] = f"AI initialization error: {exc}"

        # ---------------------------------------------
        # PAPER TRADER
        # ---------------------------------------------

        trader = None

        if PaperTrader is not None:
            try:
                starting_balance = _safe_float(
                    os.getenv("PAPER_START_BALANCE_USD", "100.0"),
                    100.0,
                )

                trader = PaperTrader(
                    starting_balance=starting_balance
                )

                logger.info(
                    "Paper trader initialized with balance: $%.2f",
                    starting_balance,
                )

            except Exception as exc:
                logger.exception("Paper trader initialization failed.")
                BOT_STATUS["last_error"] = (
                    f"Trader initialization error: {exc}"
                )

        BOT_STATUS["scanner_enabled"] = True
        BOT_STATUS["status"] = "online"
        BOT_STATUS["running"] = True

        logger.info(
            "Trading engine online | mode=%s",
            BOT_STATUS["mode"],
        )

        # ---------------------------------------------
        # MAIN LOOP
        # ---------------------------------------------

        scan_interval = max(
            5,
            int(os.getenv("SCAN_INTERVAL_SECONDS", "30")),
        )

        while True:

            scan_started = time.time()

            try:

                # -----------------------------------------
                # SCAN
                # -----------------------------------------

                tokens = scan_tokens()

                if tokens is None:
                    tokens = []

                BOT_STATUS["tokens_scanned"] += len(tokens)
                BOT_STATUS["last_scan"] = int(time.time())
                BOT_STATUS["last_error"] = None

                logger.info(
                    "Scanner returned %d token(s).",
                    len(tokens),
                )

                # -----------------------------------------
                # PROCESS EACH TOKEN
                # -----------------------------------------

                for market_data in tokens:

                    if not isinstance(market_data, dict):
                        continue

                    token_address = market_data.get("token_address")

                    if not token_address:
                        continue

                    symbol = (
                        market_data.get("symbol")
                        or token_address[:6]
                    )

                    # -------------------------------------
                    # AI ANALYSIS
                    # -------------------------------------

                    if analyzer is None:
                        continue

                    try:
                        decision = analyzer.analyze(
                            market_data
                        )

                    except Exception as exc:
                        logger.exception(
                            "AI analysis failed for %s",
                            symbol,
                        )
                        continue

                    # -------------------------------------
                    # RISK REVIEW
                    # -------------------------------------

                    try:
                        review = analyzer.risk_review(
                            market_data,
                            decision,
                        )

                    except Exception as exc:
                        logger.exception(
                            "Risk review failed for %s",
                            symbol,
                        )
                        continue

                    if not isinstance(review, dict):
                        continue

                    final_decision = str(
                        review.get(
                            "final_decision",
                            decision.get("decision", "HOLD")
                            if isinstance(decision, dict)
                            else "HOLD",
                        )
                    ).upper()

                    approved = bool(
                        review.get("approved", False)
                    )

                    confidence = _safe_float(
                        decision.get("confidence", 0)
                        if isinstance(decision, dict)
                        else 0
                    )

                    logger.info(
                        "AI | %s | decision=%s | approved=%s | confidence=%.4f",
                        symbol,
                        final_decision,
                        approved,
                        confidence,
                    )

                    # -------------------------------------
                    # BUY
                    # -------------------------------------

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

                        try:
                            balance = _safe_float(
                                trader.get_balance()
                                if hasattr(
                                    trader,
                                    "get_balance",
                                )
                                else trader.balance,
                                0.0,
                            )
                        except Exception:
                            balance = 0.0

                        usd_amount = min(
                            balance,
                            max_position,
                        )

                        if usd_amount <= 0:
                            logger.warning(
                                "No available paper balance for %s",
                                symbol,
                            )
                            continue

                        # ---------------------------------
                        # PRICE
                        # ---------------------------------

                        price = _safe_float(
                            market_data.get("price"),
                            0.0,
                        )

                        if price <= 0:
                            logger.warning(
                                "Invalid price for %s",
                                symbol,
                            )
                            continue

                        # ---------------------------------
                        # PAPER BUY
                        # ---------------------------------

                        try:
                            success = trader.buy(
                                token_address,
                                symbol,
                                confidence,
                                usd_amount,
                            )
                        except TypeError:
                            # Compatibility fallback for
                            # traders expecting price.
                            try:
                                success = trader.buy(
                                    token_address,
                                    symbol,
                                    price,
                                    usd_amount,
                                )
                            except Exception as exc:
                                logger.exception(
                                    "BUY failed for %s",
                                    symbol,
                                )
                                continue

                        if success:
                            BOT_STATUS["trades_executed"] += 1

                            logger.info(
                                "BUY executed | %s | $%.2f",
                                symbol,
                                usd_amount,
                            )

                            try:
                                send_message(
                                    f"🟢 BUY {symbol}\n"
                                    f"Amount: ${usd_amount:.2f}\n"
                                    f"Confidence: {confidence:.2%}\n"
                                    f"Mode: {BOT_STATUS['mode']}"
                                )
                            except Exception:
                                logger.exception(
                                    "Telegram BUY notification failed."
                                )

                    # -------------------------------------
                    # SELL
                    # -------------------------------------

                    elif final_decision == "SELL":

                        if trader is None:
                            continue

                        price = _safe_float(
                            market_data.get("price"),
                            0.0,
                        )

                        if price <= 0:
                            continue

                        try:
                            pnl = trader.sell(
                                token_address,
                                price,
                            )

                        except Exception:
                            logger.exception(
                                "SELL failed for %s",
                                symbol,
                            )
                            continue

                        if pnl is not False:

                            BOT_STATUS["trades_executed"] += 1

                            logger.info(
                                "SELL executed | %s | PNL=$%.4f",
                                symbol,
                                _safe_float(pnl),
                            )

                            try:
                                send_message(
                                    f"🔴 SELL {symbol}\n"
                                    f"PNL: ${_safe_float(pnl):.4f}\n"
                                    f"Mode: {BOT_STATUS['mode']}"
                                )
                            except Exception:
                                logger.exception("Telegram SELL notification failed")
                                    message = "Telegram SELL notification"
