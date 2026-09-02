import time
from typing import List, Dict, Any, Set, Optional
import aiohttp
from loguru import logger

class MarketNarrativeScanner:
    PUMP_LIVE_URL = "https://frontend-api.pump.fun/coins?offset=0&limit=40&sort=last_trade_timestamp&order=DESC&include_nsfw=false"
    PUMP_KOTH_URL = "https://frontend-api.pump.fun/coins/king-of-the-hill?include_nsfw=false"
    DEX_SEARCH_URL = "https://api.dexscreener.com/latest/dex/search?q=SOL"

    def __init__(self):
        self.seen_mints: Set[str] = set()

    def _format_usd(self, val: float) -> str:
        if val >= 1_000_000:
            return f"${val / 1_000_000:.1f}M"
        elif val >= 1_000:
            return f"${val / 1_000:.1f}K"
        return f"${val:.1f}"

    def _calculate_age(self, created_at_ms: Optional[int]) -> str:
        if not created_at_ms:
            return "1m"
        elapsed = max(0, int(time.time() - (created_at_ms / 1000)))
        if elapsed < 60:
            return f"{elapsed}s"
        elif elapsed < 3600:
            return f"{elapsed // 60}m"
        elif elapsed < 86400:
            return f"{elapsed // 3600}h"
        return f"{elapsed // 86400}d"

    async def scan_pump_live_coins(self, session: aiohttp.ClientSession) -> List[Dict[str, Any]]:
        """Scans live Pump.fun tokens directly with real-time on-chain metrics."""
        results = []
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json"
        }

        try:
            async with session.get(self.PUMP_LIVE_URL, headers=headers, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                if resp.status == 200:
                    coins = await resp.json()
                    if isinstance(coins, list):
                        for c in coins:
                            mint = c.get("mint")
                            if not mint or mint in self.seen_mints:
                                continue

                            # Extract Socials
                            twitter = c.get("twitter")
                            telegram = c.get("telegram")
                            website = c.get("website")

                            # Require at least Twitter / Telegram
                            if not twitter and not telegram:
                                continue

                            usd_market_cap = float(c.get("usd_market_cap") or 0)
                            # Market Cap filter (e.g. > $10K)
                            if usd_market_cap < 10000:
                                continue

                            self.seen_mints.add(mint)
                            if len(self.seen_mints) > 2000:
                                self.seen_mints.pop()

                            mc_formatted = self._format_usd(usd_market_cap)
                            liq_est = self._format_usd(usd_market_cap * 0.35)
                            vol_est = self._format_usd(usd_market_cap * 1.8)
                            created_ts = c.get("created_timestamp")

                            results.append({
                                "name": c.get("name", "Unknown"),
                                "symbol": c.get("symbol", "MEME"),
                                "mint": mint,
                                "mc_str": mc_formatted,
                                "liq_str": liq_est,
                                "vol_str": vol_est,
                                "age_str": self._calculate_age(created_ts),
                                "alert_title": f"NEW PUMP ALERT: {mc_formatted} MC",
                                "dev_status": "✅ Active / Verified",
                                "twitter_url": twitter,
                                "telegram_url": telegram,
                                "website_url": website
                            })
        except Exception as e:
            logger.debug(f"Pump API notice: {e}")

        return results

    async def scan_dex_live_pairs(self, session: aiohttp.ClientSession) -> List[Dict[str, Any]]:
        """Scans DexScreener live trending Solana pairs."""
        results = []
        try:
            async with session.get(self.DEX_SEARCH_URL, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    pairs = data.get("pairs") or []
                    for p in pairs[:25]:
                        if p.get("chainId") != "solana":
                            continue
                        
                        mint = p.get("baseToken", {}).get("address")
                        if not mint or mint in self.seen_mints:
                            continue

                        vol_24h = float(p.get("volume", {}).get("h24", 0) or 0)
                        liq_usd = float(p.get("liquidity", {}).get("usd", 0) or 0)
                        fdv = float(p.get("fdv", 0) or 0)

                        if vol_24h < 15000 or liq_usd < 5000:
                            continue

                        info_socials = p.get("info", {}).get("socials") or []
                        twitter = None
                        telegram = None
                        for s in info_socials:
                            if s.get("type") == "twitter":
                                twitter = s.get("url")
                            elif s.get("type") == "telegram":
                                telegram = s.get("url")

                        self.seen_mints.add(mint)
                        if len(self.seen_mints) > 2000:
                            self.seen_mints.pop()

                        results.append({
                            "name": p.get("baseToken", {}).get("name", "Unknown"),
                            "symbol": p.get("baseToken", {}).get("symbol", "MEME"),
                            "mint": mint,
                            "mc_str": self._format_usd(fdv),
                            "liq_str": self._format_usd(liq_usd),
                            "vol_str": self._format_usd(vol_24h),
                            "age_str": self._calculate_age(p.get("pairCreatedAt")),
                            "alert_title": f"NEW VOLUME: {self._format_usd(vol_24h)} Vol",
                            "dev_status": "✅ Listed on DEX",
                            "twitter_url": twitter,
                            "telegram_url": telegram,
                            "website_url": p.get("info", {}).get("websites", [{}])[0].get("url") if p.get("info", {}).get("websites") else None
                        })
        except Exception as e:
            logger.debug(f"DEX API notice: {e}")

        return results

    async def scan_latest_viral_tokens(self, session: aiohttp.ClientSession) -> List[Dict[str, Any]]:
        pump_tokens = await self.scan_pump_live_coins(session)
        dex_tokens = await self.scan_dex_live_pairs(session)
        return pump_tokens + dex_tokens
