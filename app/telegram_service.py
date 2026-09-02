from typing import Optional, Dict, Any
import aiohttp
from loguru import logger
from app.config import settings

class TelegramAlertService:
    def __init__(self):
        self.bot_token = settings.TELEGRAM_BOT_TOKEN.strip()
        self.chat_id = settings.TELEGRAM_CHAT_ID.strip()
        self.api_base = f"https://api.telegram.org/bot{self.bot_token}"

    async def send_token_alert(self, token_data: Dict[str, Any], session: Optional[aiohttp.ClientSession] = None):
        """Sends rich formatted alert with inline buttons to Telegram."""
        if not self.bot_token or not self.chat_id:
            logger.warning("Telegram credentials not configured. Skipping alert.")
            return

        name = token_data.get("name", "Unknown")
        symbol = token_data.get("symbol", "UNKNOWN")
        mint = token_data.get("mint", "N/A")
        price = token_data.get("price_usd", "0.00")
        liquidity = token_data.get("liquidity_usd", 0.0)
        volume = token_data.get("volume_24h_usd", 0.0)
        fdv = token_data.get("fdv_usd", 0.0)
        description = token_data.get("description", "No narrative provided.")
        
        twitter_url = token_data.get("twitter_url") or "https://x.com"
        dex_url = token_data.get("dex_url") or f"https://dexscreener.com/solana/{mint}"
        gmgn_url = f"https://gmgn.ai/sol/token/{mint}"
        pump_url = f"https://pump.fun/{mint}"
        solscan_url = f"https://solscan.io/token/{mint}"

        caption = (
            f"🚀 *VIRAL SOLANA MEME DETECTED*\n\n"
            f"🪙 *Asset:* *{name}* (`${symbol}`)\n"
            f"💵 *Price:* `${price}`\n"
            f"💧 *Liquidity:* `${liquidity:,.0f}`\n"
            f"📊 *24h Volume:* `${volume:,.0f}`\n"
            f"🏷 *Market Cap / FDV:* `${fdv:,.0f}`\n\n"
            f"📝 *Narrative / X Story:*\n_{description[:220]}_\n\n"
            f"📍 *Contract Address:*\n`{mint}`"
        )

        inline_keyboard = {
            "inline_keyboard": [
                [
                    {"text": "📈 GMGN Terminal", "url": gmgn_url},
                    {"text": "📊 DexScreener", "url": dex_url}
                ],
                [
                    {"text": "🐦 View on X (Twitter)", "url": twitter_url},
                    {"text": "💊 Pump.fun", "url": pump_url}
                ],
                [
                    {"text": "🔍 Solscan Explorer", "url": solscan_url}
                ]
            ]
        }

        payload = {
            "chat_id": self.chat_id,
            "text": caption,
            "parse_mode": "Markdown",
            "reply_markup": inline_keyboard,
            "disable_web_page_preview": True
        }

        endpoint = f"{self.api_base}/sendMessage"
        
        async def _dispatch(s: aiohttp.ClientSession):
            async with s.post(endpoint, json=payload, timeout=aiohttp.ClientTimeout(total=8)) as resp:
                if resp.status == 200:
                    logger.info(f"Telegram alert dispatched successfully for ${symbol}")
                else:
                    err_msg = await resp.text()
                    logger.error(f"Telegram API responded with {resp.status}: {err_msg}")

        try:
            if session:
                await _dispatch(session)
            else:
                async with aiohttp.ClientSession() as new_session:
                    await _dispatch(new_session)
        except Exception as e:
            logger.error(f"Failed to send Telegram alert: {e}")
