from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    solana_rpc_url: str = "https://api.devnet.solana.com"
    solana_ws_url: str = "wss://api.devnet.solana.com"
    wallet_private_key: str
    network: str = "devnet"

    anthropic_api_key: str
    ai_model: str = "claude-sonnet-4-6"

    telegram_bot_token: str
    telegram_chat_id: str

    max_position_size_sol: float = 0.1
    max_daily_loss_sol: float = 0.3
    max_open_positions: int = 3
    stop_loss_percent: float = 20
    take_profit_percent: float = 50
    slippage_bps: int = 100

    dexscreener_api: str = "https://api.dexscreener.com/latest/dex"
    jupiter_quote_api: str = "https://quote-api.jup.ag/v6"

    database_url: str = "sqlite+aiosqlite:///./trading_bot.db"

    @property
    def is_mainnet(self) -> bool:
        return self.network == "mainnet-beta"


settings = Settings()
