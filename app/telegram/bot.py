import os
import requests
import logging

logger = logging.getLogger("solana-ai-bot")

class TelegramBot:
    def __init__(self):
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID")

    def send_alert(self, token_symbol: str, action: str, score: int, reason: str):
        if not self.bot_token or not self.chat_id:
            logger.warning("Telegram configuration missing.")
            return False

        message = (
            f"🚀 <b>AI TRADING ALERT</b> 🚀\n\n"
            f"<b>Token:</b> ${token_symbol}\n"
            f"<b>Action:</b> {action}\n"
            f"<b>AI Score:</b> {score}/100\n"
            f"<b>Reasoning:</b> {reason}"
        )

        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": "HTML"
        }

        try:
            res = requests.post(url, json=payload, timeout=5)
            return res.status_code == 200
        except Exception as exc:
            logger.error("Failed sending Telegram alert: %s", exc)
            return False
          
