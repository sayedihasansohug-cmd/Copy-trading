from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Solana Configuration
    SOLANA_RPC_URL: str = Field(default="https://api.mainnet-beta.solana.com", description="Solana Mainnet RPC URL")
    SOLANA_PRIVATE_KEY: str = Field(..., description="Base58 private key of the trading wallet")

    # Google Gemini API Configuration (Gemini API Key)
    GEMINI_API_KEY: str = Field(..., description="Google Gemini API Key")

    # Social Sentiment / Twitter
    TWITTER_BEARER_TOKEN: str = Field(default="", description="Twitter Bearer Token (Optional)")

    # Telegram Alert Configuration
    TELEGRAM_BOT_TOKEN: str = Field(..., description="Telegram bot authentication token")
    TELEGRAM_CHAT_ID: str = Field(..., description="Target Telegram channel/user ID")

    # Trading Execution Parameters
    TRADE_AMOUNT_SOL: float = Field(default=0.05, description="Amount of SOL allocated per trade")
    SLIPPAGE_BPS: int = Field(default=300, description="Slippage tolerance in basis points (300 = 3%)")
    TAKE_PROFIT_PCT: float = Field(default=60.0, description="Target profit percentage")
    STOP_LOSS_PCT: float = Field(default=20.0, description="Maximum allowed loss percentage")
    TRAILING_STOP_PCT: float = Field(default=12.0, description="Trailing stop percentage from peak price")
    MIN_LIQUIDITY_USD: float = Field(default=5000.0, description="Minimum pool liquidity required in USD")
    MAX_MARKET_CAP_USD: float = Field(default=10000000.0, description="Maximum FDV allowed for entry")

settings = Settings()
