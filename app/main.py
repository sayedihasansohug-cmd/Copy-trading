"""
app/main.py
Solana AI Meme Trading Bot - Render/Gunicorn
"""

from __future__ import annotations

import logging
import os
import threading
import time
from typing import Any

from flask import Flask, jsonify
from dotenv import load_dotenv

load_dotenv()

# --------------------------------------------------
# LOGGING
# --------------------------------------------------

logging.basicConfig(
    level=getattr(
        logging,
        os.getenv("LOG_LEVEL", "INFO").upper(),
        logging.INFO,
    ),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

logger = logging.getLogger("solana-ai-bot")

# --------------------------------------------------
# FLASK
# --------------------------------------------------

app = Flask(__name__)

# --------------------------------------------------
# OPTIONAL MODULE IMPORTS
# --------------------------------------------------

MODULE_ERROR = None

try:
    from app.config import trading_mode, validate_config, GEMINI_API_KEY
except Exception as exc:
    MODULE_ERROR = f"config: {exc}"
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

    def trading_mode():
        return (
            "LIVE"
            if os.getenv("LIVE_TRADING", "false").lower() == "true"
            else "PAPER"
        )

    def validate_config():
        pass


try:
    from app.database.database import initialize_database
except Exception as exc:
    MODULE_ERROR = MODULE_ERROR or f"database: {exc}"

    def initialize_database():
        pass


try:
    from app.scanner import scan_tokens
except Exception as exc:
    MODULE_ERROR = MODULE_ERROR or f"scanner: {exc}"

    def scan_tokens():
        return []


try:
    from app.ai.analyzer import AIAnalyzer
except Exception as exc:
    MODULE_ERROR = MODULE_ERROR or f"AI analyzer: {exc}"
    AIAnalyzer = None


try:
    from app.trading.paper_trader import PaperTrader
except Exception as exc:
    MODULE_ERROR = MODULE_ERROR or f"paper trader: {exc}"
    PaperTrader = None


try:
    from app.telegram_notifier import send_message
except Exception as exc:
    MODULE_ERROR = MODULE_ERROR or f"telegram: {exc}"

    def send_message(text):
        logger.info("Telegram unavailable: %s", text)


# --------------------------------------------------
# STATE
# --------------------------------------------------

START_TIME = time.time()
_WORKER_STARTED = False
_WORKER_LOCK = threading.Lock()

MODE = trading_mode()

BOT_STATUS = {
    "status": "starting",
    "service": "Solana AI Meme Trading Bot",
    "mode": MODE,
    "running": False,
    "worker_running": False,
    "ai_enabled": False,
    "scanner_enabled": False,
    "paper_trading": MODE != "LIVE",
    "live_trading": MODE == "LIVE",
    "last_scan": None,
    "last_error": MODULE_ERROR,
    "tokens_scanned": 0,
    "trades_executed": 0,
    "started_at": int(START_TIME),
}


# --------------------------------------------------
# HELPERS
# --------------------------------------------------

def safe_float(value: Any, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def safe_int(value: Any, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def uptime():
    return int(time.time() - START_TIME)


# --------------------------------------------------
# ROUTES
# --------------------------------------------------

@app.get("/")
def home():
    return jsonify({
        "status": "online",
        "service": BOT_STATUS["service"],
        "mode": BOT_STATUS["mode"],
        "uptime_seconds": uptime(),
        "worker_running": BOT_STATUS["worker_running"],
        "ai_enabled": BOT_STATUS["ai_enabled"],
        "scanner_enabled": BOT_STATUS["scanner_enabled"],
        "paper_trading": BOT_STATUS["paper_trading"],
        "live_trading": BOT_STATUS["live_trading"],
    })


@app.get("/health")
def health():
    healthy = BOT_STATUS["status"] in {"starting", "online"}

    return jsonify({
        "status": "healthy" if healthy else "degraded",
        "service": BOT_STATUS["service"],
        "mode": BOT_STATUS["mode"],
        "uptime_seconds": uptime(),
        "worker_running": BOT_STATUS["worker_running"],
        "ai_enabled": BOT_STATUS["ai_enabled"],
        "scanner_enabled": BOT_STATUS["scanner_enabled"],
        "last_scan": BOT_STATUS["last_scan"],
        "last_error": BOT_STATUS["last_error"],
    }), 200 if healthy else 503


@app.get("/status")
def status():
    return jsonify({
        **BOT_STATUS,
        "uptime_seconds": uptime(),
    })


@app.get("/api")
def api_info():
    return jsonify({
        "service": BOT_STATUS["service"],
        "status": "online",
        "endpoints": [
            "/",
            "/health",
            "/status",
            "/api",
        ],
    })


# --------------------------------------------------
# TELEGRAM HELPERS
# --------------------------------------------------

def notify_buy(symbol, amount, confidence):
    try:
        send_message(
            f"🟢 BUY {symbol}\n"
            f"Amount: ${amount:.2f}\n"
            f"Confidence: {confidence:.2%}\n"
            f"Mode: {BOT_STATUS['mode']}"
        )
    except Exception:
        logger.exception("Telegram BUY notification failed")


def notify_sell(symbol, pnl):
    try:
        send_message(
            f"🔴 SELL {symbol}\n"
            f"PNL: ${pnl:.4f}\n"
            f"Mode: {BOT_STATUS['mode']}"
        )
    except Exception:
        logger.exception("Telegram SELL notification failed")


# --------------------------------------------------
# BUY
# --------------------------------------------------

def execute_buy(trader, token, symbol, confidence, price):
    if trader is None:
        return False

    try:
        balance = (
            trader.get_balance()
            if hasattr(trader, "get_balance")
            else trader.balance
        )
    except Exception:
        balance = 0

    balance = safe_float(balance)

    max_position = safe_float(
        os.getenv("MAX_POSITION_USD", "10"),
        10,
    )

    amount = min(balance, max_position)

    if amount <= 0:
        logger.warning("No paper balance for %s", symbol)
        return False

    try:
        result = trader.buy(
            token,
            symbol,
            confidence,
            amount,
        )
    except TypeError:
        try:
            result = trader.buy(
                token,
                symbol,
                price,
                amount,
            )
        except Exception:
            logger.exception("BUY failed: %s", symbol)
            return False
    except Exception:
        logger.exception("BUY failed: %s", symbol)
        return False

    if result:
        BOT_STATUS["trades_executed"] += 1
        logger.info(
            "BUY executed | %s | $%.2f",
            symbol,
            amount,
        )
        notify_buy(symbol, amount, confidence)

    return bool(result)


# --------------------------------------------------
# SELL
# --------------------------------------------------

def execute_sell(trader, token, symbol, price):
    if trader is None or price <= 0:
        return False

    try:
        pnl = trader.sell(token, price)
    except Exception:
        logger.exception("SELL failed: %s", symbol)
        return False

    if pnl is not False and pnl is not None:
        pnl = safe_float(pnl)

        BOT_STATUS["trades_executed"] += 1

        logger.info(
            "SELL executed | %s | PNL=$%.4f",
            symbol,
            pnl,
        )

        notify_sell(symbol, pnl)
        return True

    return False


# --------------------------------------------------
# TOKEN PROCESSOR
# --------------------------------------------------

def process_token(market_data, analyzer, trader):
    if not isinstance(market_data, dict):
        return

    token = market_data.get("token_address")
    if not token:
        return

    symbol = market_data.get("symbol") or token[:6]

    price = safe_float(
        market_data.get("price"),
        0,
    )

    if analyzer is None:
        return

    # AI Analysis
    try:
        decision = analyzer.analyze(market_data)
    except Exception:
        logger.exception("AI analysis failed: %s", symbol)
        return

    # Risk review
    try:
        review = analyzer.risk_review(
            market_data,
            decision,
        )
    except Exception:
        logger.exception("Risk review failed: %s", symbol)
        return

    if not isinstance(review, dict):
        return

    if isinstance(decision, dict):
        default_decision = decision.get(
            "decision",
            "HOLD",
        )
        confidence = safe_float(
            decision.get("confidence", 0)
        )
    else:
        default_decision = "HOLD"
        confidence = 0

    final_decision = str(
        review.get(
            "final_decision",
            default_decision,
        )
    ).upper()

    approved = bool(
        review.get("approved", False)
    )

    logger.info(
        "AI | %s | decision=%s | approved=%s | confidence=%.2f",
        symbol,
        final_decision,
        approved,
        confidence,
    )

    # BUY
    if (
        final_decision == "BUY"
        and approved
        and price > 0
    ):
        execute_buy(
            trader,
            token,
            symbol,
            confidence,
            price,
        )

    # SELL
    elif final_decision == "SELL":
        execute_sell(
            trader,
            token,
            symbol,
            price,
        )


# --------------------------------------------------
# BACKGROUND WORKER
# --------------------------------------------------

def background_worker():
    BOT_STATUS["worker_running"] = True
    BOT_STATUS["status"] = "starting"

    try:
        # Config
        try:
            validate_config()
            logger.info("Configuration OK")
        except Exception as exc:
            BOT_STATUS["last_error"] = f"Config error: {exc}"
            logger.exception("Configuration validation failed")

        # Database
        try:
            initialize_database()
            logger.info("Database OK")
        except Exception as exc:
            BOT_STATUS["last_error"] = f"Database error: {exc}"
            logger.exception("Database initialization failed")

        # AI Initialization Check
        analyzer = None

        if AIAnalyzer is not None and GEMINI_API_KEY:
            try:
                analyzer = AIAnalyzer()
                BOT_STATUS["ai_enabled"] = True
                logger.info("AI analyzer successfully initialized & ready.")
            except Exception as exc:
                BOT_STATUS["last_error"] = f"AI error: {exc}"
                BOT_STATUS["ai_enabled"] = False
                logger.exception("AI initialization failed")
        else:
            if not GEMINI_API_KEY:
                logger.warning("GEMINI_API_KEY is missing! AI feature disabled.")
            if AIAnalyzer is None:
                logger.warning("AIAnalyzer module could not be imported.")

        # Trader
        trader = None

        if PaperTrader is not None:
            try:
                balance = safe_float(
                    os.getenv(
                        "PAPER_START_BALANCE_USD",
                        "500",
                    ),
                    500,
                )

                trader = PaperTrader(
                    starting_balance=balance
                )

                logger.info(
                    "Paper trader ready | balance=$%.2f",
                    balance,
                )
            except Exception as exc:
                BOT_STATUS["last_error"] = (
                    f"Trader error: {exc}"
                )
                logger.exception(
                    "Paper trader initialization failed"
                )

        BOT_STATUS["scanner_enabled"] = True
        BOT_STATUS["status"] = "online"
        BOT_STATUS["running"] = True

        logger.info(
            "Trading engine online | mode=%s",
            BOT_STATUS["mode"],
        )

        interval = max(
            5,
            safe_int(
                os.getenv(
                    "SCAN_INTERVAL_SECONDS",
                    "30",
                ),
                30,
            ),
        )

        while True:
            try:
                tokens = scan_tokens()

                if not tokens:
                    tokens = []

                BOT_STATUS["tokens_scanned"] += len(tokens)
                BOT_STATUS["last_scan"] = int(time.time())

                logger.info(
                    "Scanner returned %d token(s)",
                    len(tokens),
                )

                for market_data in tokens:
                    try:
                        process_token(
                            market_data,
                            analyzer,
                            trader,
                        )
                    except Exception:
                        logger.exception(
                            "Token processing failed"
                        )

            except Exception as exc:
                BOT_STATUS["last_error"] = (
                    f"Scanner error: {exc}"
                )
                logger.exception(
                    "Scanner cycle failed"
                )

            time.sleep(interval)

    except Exception as exc:
        BOT_STATUS["status"] = "degraded"
        BOT_STATUS["running"] = False
        BOT_STATUS["last_error"] = (
            f"Fatal worker error: {exc}"
        )
        logger.exception(
            "Fatal background worker error"
        )

    finally:
        BOT_STATUS["worker_running"] = False
        BOT_STATUS["running"] = False


# --------------------------------------------------
# START WORKER ONCE
# --------------------------------------------------

def start_worker_once():
    global _WORKER_STARTED

    with _WORKER_LOCK:
        if _WORKER_STARTED:
            return

        _WORKER_STARTED = True

        thread = threading.Thread(
            target=background_worker,
            name="trading-worker",
            daemon=True,
        )

        thread.start()

        logger.info(
            "Background worker started"
        )


# Start worker when Gunicorn imports app
start_worker_once()


# --------------------------------------------------
# LOCAL DEVELOPMENT
# --------------------------------------------------

if __name__ == "__main__":
    port = safe_int(
        os.getenv("PORT", "5000"),
        5000,
    )

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False,
        use_reloader=False,
    )
