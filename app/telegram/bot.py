import aiohttp
from loguru import logger
from app.config import settings

class TelegramNotifier:
    def __init__(self):
        self.endpoint = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"

    async def send_alert(self, message: str):
        payload = {
            "chat_id": settings.TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "Markdown",
            "disable_web_page_preview": True
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.endpoint, json=payload, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                    if resp.status != 200:
                        logger.warning(f"Telegram returned non-200 status: {resp.status}")
        except Exception as e:
            logger.error(f"Failed to send Telegram notification: {e}")
