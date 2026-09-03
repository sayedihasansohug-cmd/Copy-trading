from typing import Tuple, Dict, Any
from app.config import settings

class FilterEngine:
    @staticmethod
    def evaluate(m: Dict[str, Any]) -> Tuple[bool, str]:
        """Evaluates on-chain and social cross-validation filters."""
        symbol = m.get("symbol", "UNKNOWN")

        # 1. Price Data Sanity
        if not m.get("price_usd") or float(m.get("price_usd", 0)) <= 0:
            return False, f"[{symbol}] Invalid price metrics"

        # 2. Liquidity Filter
        liq = m.get("liquidity_usd", 0.0)
        if liq < settings.MIN_LIQUIDITY_USD:
            return False, f"[{symbol}] Liquidity below threshold: ${liq:,.0f} < ${settings.MIN_LIQUIDITY_USD:,.0f}"
        if liq > settings.MAX_LIQUIDITY_USD:
            return False, f"[{symbol}] Liquidity exceeds max cap: ${liq:,.0f}"

        # 3. Market Cap / FDV
        mcap = m.get("market_cap", 0.0)
        if mcap < settings.MIN_MARKET_CAP:
            return False, f"[{symbol}] Market Cap too low: ${mcap:,.0f} < ${settings.MIN_MARKET_CAP:,.0f}"
        if mcap > settings.MAX_MARKET_CAP:
            return False, f"[{symbol}] Market Cap exceeds limit: ${mcap:,.0f}"

        # 4. Liquidity to Market Cap Relationship
        if mcap > 0 and (liq / mcap) < 0.08:
            return False, f"[{symbol}] Fragile liquidity backing (Liq/MCap ratio {liq/mcap:.2%} < 8%)"

        # 5. Token Age Window
        age = m.get("age_minutes", 0.0)
        if age < settings.MIN_TOKEN_AGE_MINUTES:
            return False, f"[{symbol}] Token too young: {age}m < {settings.MIN_TOKEN_AGE_MINUTES}m"
        if age > settings.MAX_TOKEN_AGE_MINUTES:
            return False, f"[{symbol}] Token age exceeds window: {age}m"

        # 6. Volume & Activity
        vol_5m = m.get("volume_5m", 0.0)
        vol_1h = m.get("volume_1h", 0.0)
        if vol_5m < settings.MIN_VOLUME_5M:
            return False, f"[{symbol}] Volume 5m too low: ${vol_5m:,.0f} < ${settings.MIN_VOLUME_5M:,.0f}"
        if vol_1h < settings.MIN_VOLUME_1H:
            return False, f"[{symbol}] Volume 1h too low: ${vol_1h:,.0f} < ${settings.MIN_VOLUME_1H:,.0f}"

        # 7. Order Flow (Buy/Sell Pressure)
        buys = m.get("buys_5m", 0)
        total_tx = m.get("tx_count_5m", 0)
        ratio = m.get("buy_sell_ratio_5m", 0.0)

        if total_tx < settings.MIN_TX_COUNT_5M:
            return False, f"[{symbol}] 5m Tx count too low: {total_tx} < {settings.MIN_TX_COUNT_5M}"
        if buys < settings.MIN_BUY_COUNT_5M:
            return False, f"[{symbol}] 5m Buy count too low: {buys} < {settings.MIN_BUY_COUNT_5M}"
        if ratio < settings.MIN_BUY_SELL_RATIO:
            return False, f"[{symbol}] Dominant sell pressure (Buy/Sell ratio {ratio} < {settings.MIN_BUY_SELL_RATIO})"

        # 8. Social Presence Verification
        socials = m.get("socials", {})
        if settings.REQUIRE_SOCIAL_PRESENCE and not socials.get("has_socials"):
            return False, f"[{symbol}] Rejected: Zero verified social links found (Ghost token)"

        # 9. Safety Profile
        safety = m.get("safety", {})
        if safety.get("has_freeze_authority"):
            return False, f"[{symbol}] Critical Risk: Freeze Authority enabled"
        if safety.get("has_mint_authority"):
            return False, f"[{symbol}] Critical Risk: Mint Authority enabled"

        return True, "Passed all deterministic metrics"
