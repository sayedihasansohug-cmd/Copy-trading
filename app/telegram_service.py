from typing import Optional, Dict, Any
import aiohttp
from loguru import logger
from app.config import settings

class TelegramAlertService:
    def __init__(self):
        self.bot_token = settings.TELEGRAM_BOT_TOKEN.strip()
        self.chat_id = settings.TELEGRAM_CHAT_ID.strip()
        self.api_base = f"https://api.telegram.org/bot{self.bot_token}"

    async def send_system_message(self, text: str):
        """Dispatches operational state updates to Telegram."""
        if not self.bot_token or not self.chat_id:
            return
        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": "Markdown"
        }
        try:
            async with aiohttp.ClientSession() as session:
                await session.post(f"{self.api_base}/sendMessage", json=payload, timeout=aiohttp.ClientTimeout(total=5))
        except Exception as e:
            logger.error(f"Failed to dispatch system message: {e}")

    async def send_token_alert(self, token_data: Dict[str, Any], session: Optional[aiohttp.ClientSession] = None):
        """Sends rich photo card with Axiom, GMGN, and Trojan buttons."""
        if not self.bot_token or not self.chat_id:
            return

        name = token_data.get("name", "Unknown")
        symbol = token_data.get("symbol", "UNKNOWN")
        mint = token_data.get("mint", "")
        price_usd = token_data.get("price_usd", "0.00")
        liquidity = token_data.get("liquidity_usd", 0.0)
        volume = token_data.get("volume_24h_usd", 0.0)
        fdv = token_data.get("fdv_usd", 0.0)
        age_str = token_data.get("age_str", "Just now")
        change_5m = token_data.get("price_change_5m", 0.0)
        
        twitter_url = token_data.get("twitter_url") or "https://x.com"
        telegram_url = token_data.get("telegram_url")
        website_url = token_data.get("website_url")
        image_url = token_data.get("image_url")

        axiom_url = f"https://axiom.trade/token/{mint}"
        dex_url = token_data.get("dex_url") or f"https://dexscreener.com/solana/{mint}"
        gmgn_web_url = f"https://gmgn.ai/sol/token/{mint}"
        trojan_bot_url = f"https://t.me/solana_trojanbot?start=r-trade_{mint}"
        pump_url = f"https://pump.fun/{mint}"

        socials = []
        if twitter_url:
            socials.append(f"[𝕏]({twitter_url})")
        if telegram_url:
            socials.append(f"[TG]({telegram_url})")
        if website_url:
            socials.append(f"[WEB]({website_url})")
        social_line = " | ".join(socials) if socials else f"[𝕏 (Twitter)]({twitter_url})"

        caption = (
            f"🔴 *[PUMP]* - *{name}* | *${symbol}*\n\n"
            f"🌕 *CA:*\n`{mint}`\n\n"
            f"┌─ 🏷 *Market Cap:* `${fdv:,.1f}` | ⏳ *{age_str}*\n"
            f"├─ 💧 *Liquidity:* `${liquidity:,.1f}`\n"
            f"├─ 📊 *Volume:* `${volume:,.1f}`\n"
            f"└─ 📈 *5m Change:* `{change_5m:+.2f}%`\n\n"
            f"┌─ 🌐 *Socials:* {social_line}\n"
            f"└─ 🏷 *Tag:* `#{symbol}`"
        )

        inline_keyboard = {
            "inline_keyboard": [
                [
                    {"text": "💎 AXIOM TRADE", "url": axiom_url},
                    {"text": "⚡ FAST BUY (Trojan)", "url": trojan_bot_url}
                ],
                [
                    {"text": "📈 GMGN Terminal", "url": gmgn_web_url},
                    {"text": "📊 DexScreener", "url": dex_url}
                ],
                [
                    {"text": "💊 Pump.fun", "url": pump_url},
                    {"text": "🐦 View on X", "url": twitter_url}
                ]
            ]
        }

        async def _dispatch(s: aiohttp.ClientSession):
            if image_url and image_url.startswith("http"):
                payload = {
                    "chat_id": self.chat_id,
                    "photo": image_url,
                    "caption": caption,
                    "parse_mode": "Markdown",
                    "reply_markup": inline_keyboard
                }
                async with s.post(f"{self.api_base}/sendPhoto", json=payload, timeout=aiohttp.ClientTimeout(total=8)) as resp:
                    if resp.status == 200:
                        logger.info(f"Photo alert delivered for ${symbol}")
                        return

            text_payload = {
                "chat_id": self.chat_id,
                "text": caption,
                "parse_mode": "Markdown",
                "reply_markup": inline_keyboard,
                "disable_web_page_preview": True
            }
            async with s.post(f"{self.api_base}/sendMessage", json=text_payload, timeout=aiohttp.ClientTimeout(total=8)) as resp:
                if resp.status == 200:
                    logger.info(f"Text alert delivered for ${symbol}")

        try:
            if session:
                await _dispatch(session)
            else:
                async with aiohttp.ClientSession() as new_session:
                    await _dispatch(new_session)
        except Exception as e:
            logger.error(f"Telegram dispatch failed: {e}")
