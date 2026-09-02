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
        """Dispatches high-volume meme alert matching institutional alpha channels."""
        if not self.bot_token or not self.chat_id:
            return

        name = token_data.get("name", "Unknown")
        symbol = token_data.get("symbol", "MEME")
        mint = token_data.get("mint", "")
        mc_str = token_data.get("mc_str", "$30.8K")
        liq_str = token_data.get("liq_str", "$13K")
        vol_str = token_data.get("vol_str", "$94.8K")
        age_str = token_data.get("age_str", "1m")
        alert_title = token_data.get("alert_title", "NEW HIGH VOLUME ALERT")
        dev_status = token_data.get("dev_status", "✅ Active")
        
        twitter_url = token_data.get("twitter_url") or "https://x.com"
        telegram_url = token_data.get("telegram_url")
        website_url = token_data.get("website_url")

        axiom_url = f"https://axiom.trade/token/{mint}"
        gmgn_web_url = f"https://gmgn.ai/sol/token/{mint}"
        trojan_bot_url = f"https://t.me/solana_trojanbot?start=r-trade_{mint}"

        # Build Social Links line
        social_parts = []
        if twitter_url:
            social_parts.append(f"[𝕏]({twitter_url})")
        if telegram_url:
            social_parts.append(f"[Telegram]({telegram_url})")
        if website_url:
            social_parts.append(f"[Website]({website_url})")
        
        social_line = " | ".join(social_parts) if social_parts else f"[𝕏 (Twitter)]({twitter_url})"

        # Exact layout from Screenshot 46
        caption = (
            f"🚨 *{alert_title}* ⚠️\n\n"
            f"🌕 *CA:* `{mint}`\n\n"
            f"┌─ *{name}* | `#{symbol}`\n"
            f"├─ *MC:* `{mc_str}`\n"
            f"├─ *Liq:* `{liq_str}`\n"
            f"├─ *Vol:* `{vol_str}`\n"
            f"├─ *Age:* `{age_str}`\n"
            f"└─ *Social:* {social_line}\n\n"
            f"┌─ *Dev:* {dev_status}\n"
            f"└─ *Platform:* [Pump.fun](https://pump.fun/{mint})\n\n"
            f"💰 *Terminals:* [GMGN]({gmgn_web_url}) | [Axiom]({axiom_url}) | [Trojan]({trojan_bot_url})"
        )

        inline_keyboard = {
            "inline_keyboard": [
                [
                    {"text": "⚡ FAST BUY", "url": trojan_bot_url},
                    {"text": "⚡ GMGN", "url": gmgn_web_url},
                    {"text": "⚡ AXIOM", "url": axiom_url}
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

        async def _dispatch(s: aiohttp.ClientSession):
            async with s.post(f"{self.api_base}/sendMessage", json=payload, timeout=aiohttp.ClientTimeout(total=8)) as resp:
                if resp.status == 200:
                    logger.info(f"Signal sent successfully for ${symbol}")
                else:
                    logger.error(f"Telegram API response: {await resp.text()}")

        try:
            if session:
                await _dispatch(session)
            else:
                async with aiohttp.ClientSession() as new_session:
                    await _dispatch(new_session)
        except Exception as e:
            logger.error(f"Failed to dispatch Telegram alert: {e}")
