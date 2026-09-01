from typing import Tuple, Dict, Any, Optional
from loguru import logger
from app.config import settings

class RiskManager:
    @staticmethod
    def evaluate_token(pair_data: Optional[Dict[str, Any]]) -> Tuple[bool, str]:
        if not pair_data:
            return False, "Token pair not found or has no Solana market."

        liquidity_usd = float(pair_data.get("liquidity", {}).get("usd", 0) or 0)
        fdv = float(pair_data.get("fdv", 0) or 0)
        volume_24h = float(pair_data.get("volume", {}).get("h24", 0) or 0)

        # 1. Liquidity Threshold
        if liquidity_usd < settings.MIN_LIQUIDITY_USD:
            return False, f"Low liquidity: ${liquidity_usd:,.2f} < ${settings.MIN_LIQUIDITY_USD:,.2f}"

        # 2. Maximum FDV Check
        if fdv > settings.MAX_MARKET_CAP_USD:
            return False, f"Market cap too high: ${fdv:,.2f} > ${settings.MAX_MARKET_CAP_USD:,.2f}"

        # 3. Minimum Volume Check
        if volume_24h < 500:
            return False, "Volume insufficient for trade execution."

        # 4. Flash Dump Guard
        price_drop_5m = float(pair_data.get("priceChange", {}).get("m5", 0) or 0)
        if price_drop_5m < -50.0:
            return False, f"Sudden price collapse detected: {price_drop_5m}%"

        logger.info(f"Risk checks passed for {pair_data.get('baseToken', {}).get('symbol')}")
        return True, "Risk validation successful."
