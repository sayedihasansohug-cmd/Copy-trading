import json
import re
from typing import Dict, Any, Optional
import google.generativeai as genai
from loguru import logger
from app.config import settings
from app.ai.prompts import ANALYSIS_SYSTEM_PROMPT

class AIAnalyzer:
    def __init__(self):
        clean_key = settings.GEMINI_API_KEY.strip().strip("'").strip('"')
        genai.configure(api_key=clean_key)
        self.models_to_try = ["gemini-1.5-flash", "gemini-1.5-flash-latest", "gemini-1.5-pro", "gemini-pro"]

    def _clean_json(self, text: str) -> str:
        cleaned = text.strip()
        if "```" in cleaned:
            match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", cleaned)
            if match:
                cleaned = match.group(1).strip()
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start != -1 and end != -1 and end > start:
            return cleaned[start:end + 1]
        return cleaned

    async def analyze_token(self, metrics: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        socials = metrics.get("socials", {})
        
        prompt = (
            f"Analyze on-chain structure and viral narrative confirmation for this Solana token:\n\n"
            f"Token: ${metrics.get('symbol')} ({metrics.get('name')})\n"
            f"Mint: {metrics.get('token_address')}\n"
            f"Price: ${metrics.get('price_usd')} (5m: {metrics.get('price_change_5m'):+.2f}%, 15m: {metrics.get('price_change_15m'):+.2f}%)\n"
            f"Age: {metrics.get('age_minutes')} minutes\n"
            f"Liquidity USD: ${metrics.get('liquidity_usd'):,.0f}\n"
            f"Market Cap: ${metrics.get('market_cap'):,.0f}\n"
            f"Volume 5m: ${metrics.get('volume_5m'):,.0f} | 1h: ${metrics.get('volume_1h'):,.0f}\n"
            f"Orderflow 5m: {metrics.get('buys_5m')} Buys / {metrics.get('sells_5m')} Sells (Ratio: {metrics.get('buy_sell_ratio_5m')})\n"
            f"Total Txns 5m: {metrics.get('tx_count_5m')}\n"
            f"Verified Social Presence: Twitter={'YES' if socials.get('twitter_url') else 'NO'}, "
            f"Telegram={'YES' if socials.get('telegram_url') else 'NO'}, Website={'YES' if socials.get('website_url') else 'NO'}\n"
            f"Safety: FreezeAuth={metrics.get('safety', {}).get('has_freeze_authority')}, MintAuth={metrics.get('safety', {}).get('has_mint_authority')}\n"
        )

        for model_name in self.models_to_try:
            try:
                model = genai.GenerativeModel(
                    model_name=model_name,
                    system_instruction=ANALYSIS_SYSTEM_PROMPT,
                    generation_config={"response_mime_type": "application/json", "temperature": 0.1}
                )
                response = await model.generate_content_async(prompt)
                raw_text = response.text.strip()
                cleaned = self._clean_json(raw_text)
                return json.loads(cleaned)
            except Exception as e:
                logger.debug(f"Model {model_name} evaluation failed: {e}")
                continue

        logger.error(f"All AI analysis models failed for ${metrics.get('symbol')}")
        return None
