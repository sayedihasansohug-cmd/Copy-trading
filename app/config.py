from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    PORT: int = Field(default=10000, description="Web server port")
    
    # Telegram Configuration
    TELEGRAM_BOT_TOKEN: str = Field(..., description="Telegram bot authentication token")
    TELEGRAM_CHAT_ID: str = Field(..., description="Target Telegram channel or user ID")

    # Scanner & Filtering Configuration
    MIN_LIQUIDITY_USD: float = Field(default=3000.0, description="Minimum pool liquidity required in USD")
    MIN_VOLUME_24H_USD: float = Field(default=5000.0, description="Minimum 24h trading volume in USD")
    MIN_MARKET_CAP_USD: float = Field(default=8000.0, description="Minimum FDV / Market Cap in USD")
    SCAN_INTERVAL_SECONDS: int = Field(default=10, description="Interval between scanner cycles in seconds")

settings = Settings()
