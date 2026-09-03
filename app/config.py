from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    PORT: int = Field(default=10000)
    
    # Telegram Configuration
    TELEGRAM_BOT_TOKEN: str = Field(...)
    TELEGRAM_CHAT_ID: str = Field(...)

    # AI Configuration (Gemini API)
    GEMINI_API_KEY: str = Field(...)

    # Optional Twitter API (If available)
    TWITTER_BEARER_TOKEN: str = Field(default="")

    # Scanner Timers
    SCAN_INTERVAL_SECONDS: int = Field(default=15)
    SIGNAL_COOLDOWN_MINUTES: int = Field(default=60)

    # Liquidity Filters (USD)
    MIN_LIQUIDITY_USD: float = Field(default=8000.0)
    MAX_LIQUIDITY_USD: float = Field(default=500000.0)

    # Volume & Transaction Activity
    MIN_VOLUME_5M: float = Field(default=3000.0)
    MIN_VOLUME_1H: float = Field(default=15000.0)
    MIN_TX_COUNT_5M: int = Field(default=25)
    MIN_BUY_COUNT_5M: int = Field(default=15)
    MIN_BUY_SELL_RATIO: float = Field(default=1.2)

    # Market Cap / FDV (USD)
    MIN_MARKET_CAP: float = Field(default=15000.0)
    MAX_MARKET_CAP: float = Field(default=3000000.0)

    # Token Age Filters (Minutes)
    MIN_TOKEN_AGE_MINUTES: float = Field(default=3.0)
    MAX_TOKEN_AGE_MINUTES: float = Field(default=1440.0)

    # Quality & Virality Scoring Gates
    MIN_AI_SCORE: int = Field(default=75)
    MIN_CONFIDENCE: int = Field(default=75)
    MIN_VIRAL_SCORE: int = Field(default=60)
    REQUIRE_SOCIAL_PRESENCE: bool = Field(default=True)

    # Strict Zero-Trading Safeguard
    LIVE_TRADING: bool = Field(default=False)

settings = Settings()
