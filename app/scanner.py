import time
from typing import List, Dict, Any, Set, Optional
import aiohttp
from loguru import logger
from app.config import settings

class MarketNarrativeScanner:
    DEX_PROFILES_URL = "https://api.dexscreener.com/token-profiles/latest/v1"
    DEX_PAIR_URL = "https://api.dexscreener.com/latest/dex/tokens/"

    def __init__(self):
        self.seen_mints: Set[str] = set()

    def _calculate_age(self, created_at_ms: Optional[int]) -> str:
        """Calculates human-readable time elapsed since pair creation."""
        if not created_at_ms:
            return "New launch"
        elapsed_seconds = max(0, int(time.time() - (created_at_ms / 1000)))
        if elapsed_seconds < 60:
            return f"{elapsed_seconds}s ago"
        elif elapsed_seconds < 3600:
            return f"{elapsed_seconds // 60}m ago"
        elif elapsed_seconds < 86400:
            return f"{elapsed_seconds // 3600}h ago"
        return f"{elapsed_seconds // 86400}d ago"

    async def fetch_token_pair_data(self, session: aiohttp.ClientSession, mint: str) -> Optional[Dict[str, Any]]:
        url = f"{self.DEX_PAIR_URL}{mint}"
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    pairs = data.get("pairs") or []
                    sol_pairs = [p for p in pairs if p.get("chainId") == "solana"]
                    if sol_pairs:
                        sol_pairs.sort(key=lambda x: float(x.get("liquidity", {}).get("usd", 0) or 0), reverse=True)
                        return sol_pairs[0]
        except Exception as e:
            logger.debug(f"Pair fetch failed for {mint}: {e}")
        return None

    async def scan_latest_viral_tokens(self, session: aiohttp.ClientSession) -> List[Dict[str, Any]]:
        qualified_tokens = []

        try:
            async with session.get(self.DEX_PROFILES_URL, timeout=aiohttp.ClientTimeout(total=8)) as resp:
                if resp.status != 200:
                    return qualified_tokens
                profiles = await resp.json()
                if not isinstance(profiles, list):
                    return qualified_tokens

            for profile in profiles:
                if profile.get("chainId") != "solana":
                    continue

                mint = profile.get("tokenAddress")
                if not mint or mint in self.seen_mints:
                    continue

                # Extract Social Links
                links = profile.get("links") or []
                twitter_url = None
                telegram_url = None
                website_url = None

                for link in links:
                    url_str = link.get("url", "")
                    link_type = link.get("type", "").lower()
                    if "x.com" in url_str or "twitter.com" in url_str or link_type == "twitter":
                        twitter_url = url_str
                    elif "t.me" in url_str or link_type == "telegram":
                        telegram_url = url_str
                    elif link_type == "website" or url_str.startswith("http"):
                        website_url = url_str

                # Ensure verified X / Twitter presence
                if not twitter_url:
                    continue

                pair_data = await self.fetch_token_pair_data(session, mint)
                if not pair_data:
                    continue

                liquidity = float(pair_data.get("liquidity", {}).get("usd", 0) or 0)
                volume_24h = float(pair_data.get("volume", {}).get("h24", 0) or 0)
                fdv = float(pair_data.get("fdv", 0) or 0)
                price_usd = pair_data.get("priceUsd", "0.00")
                change_5m = float(pair_data.get("priceChange", {}).get("m5", 0) or 0)
                created_at = pair_data.get("pairCreatedAt")

                # Filter: Ensure minimum market thresholds
                if (liquidity < settings.MIN_LIQUIDITY_USD or 
                    volume_24h < settings.MIN_VOLUME_24H_USD):
                    continue

                self.seen_mints.add(mint)
                if len(self.seen_mints) > 1000:
                    self.seen_mints.pop()

                token_info = {
                    "name": pair_data.get("baseToken", {}).get("name", "Unknown Token"),
                    "symbol": pair_data.get("baseToken", {}).get("symbol", "MEME"),
                    "mint": mint,
                    "price_usd": price_usd,
                    "liquidity_usd": liquidity,
                    "volume_24h_usd": volume_24h,
                    "fdv_usd": fdv,
                    "age_str": self._calculate_age(created_at),
                    "price_change_5m": change_5m,
                    "image_url": profile.get("header") or profile.get("icon") or "",
                    "twitter_url": twitter_url,
                    "telegram_url": telegram_url,
                    "website_url": website_url,
                    "dex_url": pair_data.get("url", f"https://dexscreener.com/solana/{mint}")
                }
                qualified_tokens.append(token_info)

        except Exception as e:
            logger.error(f"Error in narrative scan: {e}")

        return qualified_tokens
