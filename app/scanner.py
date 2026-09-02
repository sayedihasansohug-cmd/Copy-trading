from typing import List, Dict, Any, Set, Optional
import aiohttp
from loguru import logger
from app.config import settings

class MarketNarrativeScanner:
    DEX_PROFILES_URL = "https://api.dexscreener.com/token-profiles/latest/v1"
    DEX_BOOSTS_URL = "https://api.dexscreener.com/token-boosts/top/v1"
    DEX_PAIR_URL = "https://api.dexscreener.com/latest/dex/tokens/"

    def __init__(self):
        self.seen_mints: Set[str] = set()

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
            logger.debug(f"Error fetching pair for {mint}: {e}")
        return None

    async def scan_latest_viral_tokens(self, session: aiohttp.ClientSession) -> List[Dict[str, Any]]:
        """Scans DexScreener for verified Solana tokens with active X/Twitter narratives."""
        qualified_tokens = []

        try:
            async with session.get(self.DEX_PROFILES_URL, timeout=aiohttp.ClientTimeout(total=8)) as resp:
                if resp.status != 200:
                    logger.warning(f"Profiles endpoint returned status {resp.status}")
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

                links = profile.get("links") or []
                twitter_url = None
                for link in links:
                    url_str = link.get("url", "")
                    link_type = link.get("type", "").lower()
                    if "x.com" in url_str or "twitter.com" in url_str or link_type == "twitter":
                        twitter_url = url_str
                        break

                # Filter: Require verified X / Twitter link
                if not twitter_url:
                    continue

                pair_data = await self.fetch_token_pair_data(session, mint)
                if not pair_data:
                    continue

                liquidity = float(pair_data.get("liquidity", {}).get("usd", 0) or 0)
                volume_24h = float(pair_data.get("volume", {}).get("h24", 0) or 0)
                fdv = float(pair_data.get("fdv", 0) or 0)
                price_usd = pair_data.get("priceUsd", "0.00")

                # Apply quality & risk thresholds
                if (liquidity < settings.MIN_LIQUIDITY_USD or 
                    volume_24h < settings.MIN_VOLUME_24H_USD or 
                    fdv < settings.MIN_MARKET_CAP_USD):
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
                    "description": profile.get("description", "Viral narrative circulating on X / Solana."),
                    "icon_url": profile.get("icon", ""),
                    "twitter_url": twitter_url,
                    "dex_url": pair_data.get("url", f"https://dexscreener.com/solana/{mint}")
                }
                qualified_tokens.append(token_info)

        except Exception as e:
            logger.error(f"Error during narrative scanning: {e}")

        return qualified_tokens
