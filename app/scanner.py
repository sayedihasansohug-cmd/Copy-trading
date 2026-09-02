import time
from typing import List, Dict, Any, Set, Optional
import aiohttp
from loguru import logger
from app.config import settings

class MarketNarrativeScanner:
    DEX_BOOSTS_URL = "https://api.dexscreener.com/token-boosts/top/v1"
    DEX_PROFILES_URL = "https://api.dexscreener.com/token-profiles/latest/v1"
    DEX_PAIR_URL = "https://api.dexscreener.com/latest/dex/tokens/"

    def __init__(self):
        self.seen_mints: Set[str] = set()

    def _calculate_age(self, created_at_ms: Optional[int]) -> str:
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
        endpoints = [self.DEX_BOOSTS_URL, self.DEX_PROFILES_URL]

        for url in endpoints:
            try:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=8)) as resp:
                    if resp.status != 200:
                        continue
                    raw_data = await resp.json()
                    
                    # Normalize list
                    items = []
                    if isinstance(raw_data, list):
                        items = raw_data
                    elif isinstance(raw_data, dict):
                        items = raw_data.get("tokens") or raw_data.get("pairs") or []

                    for profile in items:
                        if not isinstance(profile, dict):
                            continue
                            
                        # Ensure Solana token
                        chain_id = profile.get("chainId") or "solana"
                        if chain_id != "solana":
                            continue

                        mint = profile.get("tokenAddress")
                        if not mint or mint in self.seen_mints:
                            continue

                        # Extract Links
                        links = profile.get("links") or []
                        twitter_url = None
                        telegram_url = None
                        website_url = None

                        if isinstance(links, list):
                            for link in links:
                                if isinstance(link, dict):
                                    url_str = link.get("url", "")
                                    link_type = link.get("type", "").lower()
                                    if "x.com" in url_str or "twitter.com" in url_str or link_type == "twitter":
                                        twitter_url = url_str
                                    elif "t.me" in url_str or link_type == "telegram":
                                        telegram_url = url_str
                                    elif link_type == "website" or url_str.startswith("http"):
                                        website_url = url_str

                        # Fetch pair market liquidity
                        pair_data = await self.fetch_token_pair_data(session, mint)
                        if not pair_data:
                            continue

                        # Check pair info links as fallback
                        if not twitter_url:
                            info_links = pair_data.get("info", {}).get("socials") or []
                            for s in info_links:
                                if s.get("type") == "twitter":
                                    twitter_url = s.get("url")

                        liquidity = float(pair_data.get("liquidity", {}).get("usd", 0) or 0)
                        volume_24h = float(pair_data.get("volume", {}).get("h24", 0) or 0)
                        fdv = float(pair_data.get("fdv", 0) or 0)
                        price_usd = pair_data.get("priceUsd", "0.00")
                        change_5m = float(pair_data.get("priceChange", {}).get("m5", 0) or 0)
                        created_at = pair_data.get("pairCreatedAt")

                        # Mark as seen so duplicates are prevented
                        self.seen_mints.add(mint)
                        if len(self.seen_mints) > 1500:
                            self.seen_mints.pop()

                        token_info = {
                            "name": pair_data.get("baseToken", {}).get("name", "Unknown"),
                            "symbol": pair_data.get("baseToken", {}).get("symbol", "MEME"),
                            "mint": mint,
                            "price_usd": price_usd,
                            "liquidity_usd": liquidity,
                            "volume_24h_usd": volume_24h,
                            "fdv_usd": fdv,
                            "age_str": self._calculate_age(created_at),
                            "price_change_5m": change_5m,
                            "image_url": profile.get("header") or profile.get("icon") or pair_data.get("info", {}).get("imageUrl") or "",
                            "twitter_url": twitter_url or f"https://x.com/search?q={mint}",
                            "telegram_url": telegram_url,
                            "website_url": website_url,
                            "dex_url": pair_data.get("url", f"https://dexscreener.com/solana/{mint}")
                        }
                        qualified_tokens.append(token_info)

            except Exception as e:
                logger.debug(f"Scan iteration notice: {e}")

        return qualified_tokens
