import os

from dotenv import load_dotenv


# Load variables from .env when running locally.
load_dotenv()


def _get_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)

    if value is None:
        return default

    return value.strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def _get_int(name: str, default: int) -> int:
    value = os.getenv(name)

    if value is None or value.strip() == "":
        return default

    try:
        return int(value)
    except ValueError:
        return default


def _get_float(name: str, default: float) -> float:
    value = os.getenv(name)

    if value is None or value.strip() == "":
        return default

    try:
        return float(value)
    except ValueError:
        return default


# ============================================================
# AI
# ============================================================

GEMINI_API_KEY = os.getenv(
    "GEMINI_API_KEY",
    "",
)

GEMINI_MODEL = os.getenv(
    "GEMINI_MODEL",
    "gemini-3.7-flash",
)


# ============================================================
# SOLANA
# ============================================================

SOLANA_RPC_URL = os.getenv(
    "SOLANA_RPC_URL",
    "https://api.mainnet-beta.solana.com",
)

SOLANA_PRIVATE_KEY = os.getenv(
    "SOLANA_PRIVATE_KEY",
    "",
)


# ============================================================
# JUPITER
# ============================================================

JUPITER_API_KEY = os.getenv(
    "JUPITER_API_KEY",
    "",
)

JUPITER_QUOTE_URL = os.getenv(
    "JUPITER_QUOTE_URL",
    "https://api.jup.ag/swap/v1/quote",
)

JUPITER_SWAP_URL = os.getenv(
    "JUPITER_SWAP_URL",
    "https://api.jup.ag/swap/v1/swap",
)


# ============================================================
# DATABASE
# ============================================================

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite+aiosqlite:///./trading.db",
)


# ============================================================
# TRADING MODE
# ============================================================

# CRITICAL:
# Paper trading is the default.
# Live trading must be explicitly enabled.
LIVE_TRADING = _get_bool(
    "LIVE_TRADING",
    False,
)


# ============================================================
# RISK MANAGEMENT
# ============================================================

MAX_POSITION_USD = _get_float(
    "MAX_POSITION_USD",
    25.0,
)

MAX_DAILY_LOSS_USD = _get_float(
    "MAX_DAILY_LOSS_USD",
    25.0,
)

MAX_OPEN_POSITIONS = _get_int(
    "MAX_OPEN_POSITIONS",
    3,
)

TAKE_PROFIT_PERCENT = _get_float(
    "TAKE_PROFIT_PERCENT",
    20.0,
)

STOP_LOSS_PERCENT = _get_float(
    "STOP_LOSS_PERCENT",
    10.0,
)

MAX_SLIPPAGE_BPS = _get_int(
    "MAX_SLIPPAGE_BPS",
    100,
)


# ============================================================
# MARKET FILTERS
# ============================================================

MIN_LIQUIDITY_USD = _get_float(
    "MIN_LIQUIDITY_USD",
    10000.0,
)

MIN_VOLUME_24H_USD = _get_float(
    "MIN_VOLUME_24H_USD",
    25000.0,
)

AI_BUY_THRESHOLD = _get_int(
    "AI_BUY_THRESHOLD",
    80,
)

SCAN_INTERVAL_SECONDS = _get_int(
    "SCAN_INTERVAL_SECONDS",
    30,
)

TOKEN_COOLDOWN_MINUTES = _get_int(
    "TOKEN_COOLDOWN_MINUTES",
    60,
)

MAX_CANDIDATES_PER_SCAN = _get_int(
    "MAX_CANDIDATES_PER_SCAN",
    10,
)


# ============================================================
# PAPER TRADING
# ============================================================

PAPER_START_BALANCE_USD = _get_float(
    "PAPER_START_BALANCE_USD",
    500.0,
)


# ============================================================
# TELEGRAM
# ============================================================

TELEGRAM_BOT_TOKEN = os.getenv(
    "TELEGRAM_BOT_TOKEN",
    "",
)

TELEGRAM_CHAT_ID = os.getenv(
    "TELEGRAM_CHAT_ID",
    "",
)


# ============================================================
# VALIDATION
# ============================================================

def validate_config() -> None:
    """
    Validate critical configuration before starting the bot.

    Paper trading does not require private keys or API secrets.
    """

    if MAX_POSITION_USD <= 0:
        raise ValueError(
            "MAX_POSITION_USD must be greater than zero."
        )

    if MAX_DAILY_LOSS_USD <= 0:
        raise ValueError(
            "MAX_DAILY_LOSS_USD must be greater than zero."
        )

    if MAX_OPEN_POSITIONS <= 0:
        raise ValueError(
            "MAX_OPEN_POSITIONS must be greater than zero."
        )

    if TAKE_PROFIT_PERCENT <= 0:
        raise ValueError(
            "TAKE_PROFIT_PERCENT must be greater than zero."
        )

    if STOP_LOSS_PERCENT <= 0:
        raise ValueError(
            "STOP_LOSS_PERCENT must be greater than zero."
        )

    if MAX_SLIPPAGE_BPS < 0:
        raise ValueError(
            "MAX_SLIPPAGE_BPS cannot be negative."
        )

    if MIN_LIQUIDITY_USD < 0:
        raise ValueError(
            "MIN_LIQUIDITY_USD cannot be negative."
        )

    if MIN_VOLUME_24H_USD < 0:
        raise ValueError(
            "MIN_VOLUME_24H_USD cannot be negative."
        )

    if not 0 <= AI_BUY_THRESHOLD <= 100:
        raise ValueError(
            "AI_BUY_THRESHOLD must be between 0 and 100."
        )

    if SCAN_INTERVAL_SECONDS < 5:
        raise ValueError(
            "SCAN_INTERVAL_SECONDS must be at least 5."
        )

    if MAX_CANDIDATES_PER_SCAN <= 0:
        raise ValueError(
            "MAX_CANDIDATES_PER_SCAN must be greater than zero."
        )

    # Live mode requires a private key.
    # We intentionally do NOT require it in paper mode.
    if LIVE_TRADING and not SOLANA_PRIVATE_KEY:
        raise ValueError(
            "LIVE_TRADING=true requires "
            "SOLANA_PRIVATE_KEY."
        )


def trading_mode() -> str:
    """
    Return the current execution mode.
    """

    if LIVE_TRADING:
        return "LIVE"

    return "PAPER"
