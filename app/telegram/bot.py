from typing import Dict, Any, Optional
import aiohttp
from loguru import logger
from app.config import settings

class TelegramNotifier:
    def __init__(self):
        self.bot_token = settings.TELEGRAM_BOT_TOKEN.strip()
        self.chat_id = settings.TELEGRAM_CHAT_ID.strip()
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"

    def _format_usd(self, val: float) -> str:
        if val >= 1_000_000:
            return f"${val / 1_000_000:.1f}M"
        elif val >= 1_000:
            return f"${val / 1_000:.1f}K"
        return f"${val:.2f}"

    async def send_signal(self, metrics: Dict[str, Any], ai: Dict[str, Any], session: Optional[aiohttp.ClientSession] = None):
        """Sends rich Telegram alert card with viral narrative metrics & on-chain cross-validation."""
        if not self.bot_token or not self.chat_id:
            return

        symbol = metrics.get("symbol", "UNKNOWN")
        mint = metrics.get("token_address", "N/A")
        scores = ai.get("scores", {})
        viral = ai.get("viral_analysis", {})

        reasons = "\n".join([f"• {r}" for r in ai.get("reasons", [])]) or "• Strong volume and liquidity alignment"
        warnings = "\n".join([f"• {w}" for w in ai.get("warnings", [])]) or "• High volatility asset"
        invalidations = "\n".join([f"• {i}" for i in ai.get("invalidating_conditions", [])]) or "• Buy/sell pressure falls"

        risk_val = ai.get("risk_score", 50)
        risk_label = "Low" if risk_val < 35 else ("Medium" if risk_val < 70 else "High")

        viral_score = viral.get("viral_score", "UNAVAILABLE")
        social_momentum = viral.get("social_momentum", "MEDIUM")
        narrative = viral.get("narrative", "Solana Meme Narrative")
        social_growth = viral.get("social_growth", "Organic community growth")
        engagement = viral.get("engagement", "Verified social links active")
        on_chain_conf = viral.get("on_chain_confirmation", "PASS")

        socials = metrics.get("socials", {})
        twitter_link = socials.get("twitter_url") or "https://x.com"

        text = (
            f"🚨 *SOLANA MEME RADAR*\n\n"
            f"🪙 *TOKEN:* `${symbol}`\n\n"
            f"📍 *CA:*\n`{mint}`\n\n"
            f"💰 *Market Cap:* {self._format_usd(metrics.get('market_cap', 0))}\n"
            f"💧 *Liquidity:* {self._format_usd(metrics.get('liquidity_usd', 0))}\n"
            f"📊 *Volume 5M:* {self._format_usd(metrics.get('volume_5m', 0))}\n"
            f"📈 *5M:* `{metrics.get('price_change_5m', 0.0):+.1f}%`\n"
            f"📈 *15M:* `{metrics.get('price_change_15m', 0.0):+.1f}%`\n"
            f"🟢 *Buys:* `{metrics.get('buys_5m', 0)}`\n"
            f"🔴 *Sells:* `{metrics.get('sells_5m', 0)}`\n"
            f"⚖️ *Buy/Sell:* `{metrics.get('buy_sell_ratio_5m', 1.0):.2f}`\n"
            f"⏱️ *Age:* `{metrics.get('age_minutes', 0):.0f} min`\n\n"
            f"━━━━━━━━━━━━━━\n\n"
            f"🔥 *VIRAL SCORE:* `{viral_score}/100`\n"
            f"📈 *SOCIAL MOMENTUM:* `{social_momentum}`\n"
            f"🧠 *NARRATIVE:* _{narrative}_\n"
            f"👥 *SOCIAL GROWTH:* {social_growth}\n"
            f"💬 *ENGAGEMENT:* {engagement}\n"
            f"🔗 *ON-CHAIN CONFIRMATION:* `{on_chain_conf}`\n\n"
            f"━━━━━━━━━━━━━━\n\n"
            f"⭐ *Overall Score:* `{ai.get('overall_score', 0)}/100`\n"
            f"🎯 *Signal:* `{ai.get('decision', 'BUY_WATCH')}`\n"
            f"🧠 *Confidence:* `{ai.get('confidence', 0)}%`\n"
            f"⚠️ *Risk:* `{risk_label} ({risk_val}/100)`\n\n"
            f"💧 *Liquidity Score:* `{scores.get('liquidity_score', 0)}`\n"
            f"📈 *Momentum Score:* `{scores.get('momentum_score', 0)}`\n"
            f"📊 *Volume Score:* `{scores.get('volume_score', 0)}`\n"
            f"👥 *Holder Score:* `{scores.get('holder_score', 0)}`\n"
            f"🔐 *Safety Score:* `{scores.get('safety_score', 0)}`\n\n"
            f"━━━━━━━━━━━━━━\n\n"
            f"🧠 *WHY:*\n{reasons}\n\n"
            f"⚠️ *WARNINGS:*\n{warnings}\n\n"
            f"❌ *INVALIDATION:*\n{invalidations}\n\n"
            f"🔗 *CA:*\n`{mint}`\n\n"
            f"⚠️ *MANUAL REVIEW REQUIRED*\n"
            f"_This is NOT financial advice and NOT an automatic trade._"
        )

        inline_keyboard = {
            "inline_keyboard": [
                [
                    {"text": "📈 GMGN Terminal", "url": f"https://gmgn.ai/sol/token/{mint}"},
                    {"text": "📊 DexScreener", "url": metrics.get("dex_url", f"https://dexscreener.com/solana/{mint}")}
                ],
                [
                    {"text": "💎 Axiom Trade", "url": f"https://axiom.trade/token/{mint}"},
                    {"text": "🐦 View on X", "url": twitter_link}
                ]
            ]
        }

        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": "Markdown",
            "reply_markup": inline_keyboard,
            "disable_web_page_preview": True
        }

        async def _send(s: aiohttp.ClientSession):
            async with s.post(self.api_url, json=payload, timeout=aiohttp.ClientTimeout(total=8)) as resp:
                if resp.status == 200:
                    logger.info(f"[TELEGRAM] Signal dispatched for ${symbol}")
                else:
                    logger.error(f"[TELEGRAM] Error {resp.status}: {await resp.text()}")

        try:
            if session:
                await _send(session)
            else:
                async with aiohttp.ClientSession() as s:
                    await _send(s)
        except Exception as e:
            logger.error(f"[TELEGRAM] Dispatch failed: {e}")
