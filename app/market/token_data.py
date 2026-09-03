import time
from typing import List, Dict, Any, Optional
import aiohttp
from loguru import logger

class TokenDataFetcher:
    DEX_SEARCH_URL = "https://api.dexscreener.com/latest/dex/search?q=SOL"
    DEX_PROFILES_URL = "https://api.dexscreener.com/token-profiles/latest/v1"
    DEX_BOOSTS_URL = "https://api.dexscreener.com/token-boosts/latest/v1"
    DEX_TOKEN_URL = "https://api.dexscreener.com/latest/dex/tokens/"
    RUGCHECK_API_URL = "https://api.rugcheck.xyz/v1/tokens/"

    @classmethod
    async def get_market_candidates(cls, session: aiohttp.ClientSession) -> List[str]:
        """Collects candidate mint addresses from live boosted and profiled streams."""
        mints = set()
        endpoints = [cls.DEX_BOOSTS_URL, cls.DEX_PROFILES_URL]

        for url in endpoints:
            try:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        items = data if isinstance(data, list) else data.get("tokens", [])
                        for item in items:
                            if item.get("chainId") == "solana":
                                mint = item.get("tokenAddress")
                                if mint:
                                    mints.add(mint)
            except Exception as e:
                logger.debug(f"Candidate stream error: {e}")

        try:
            async with session.get(cls.DEX_SEARCH_URL, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    pairs = data.get("pairs") or []
                    for p in pairs[:30]:
                        if p.get("chainId") == "solana":
                            mint = p.get("baseToken", {}).get("address")
                            if mint:
                                mints.add(mint)
        except Exception as e:
            logger.debug(f"Search API error: {e}")

        return list(mints)

    @classmethod
    async def fetch_token_metrics(cls, session: aiohttp.ClientSession, mint: str) -> Optional[Dict[str, Any]]:
        """Fetches comprehensive pair, social narrative, and on-chain metrics."""
        url = f"{cls.DEX_TOKEN_URL}{mint}"
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                if resp.status != 200:
                    return None
                data = await resp.json()
                pairs = data.get("pairs") or []
                sol_pairs = [p for p in pairs if p.get("chainId") == "solana"]
                if not sol_pairs:
                    return None

                sol_pairs.sort(key=lambda x: float(x.get("liquidity", {}).get("usd", 0) or 0), reverse=True)
                pair = sol_pairs[0]

                created_at_ms = pair.get("pairCreatedAt")
                now_ms = int(time.time() * 1000)
                age_minutes = round((now_ms - created_at_ms) / 60000, 1) if created_at_ms else 0.0

                txns = pair.get("txns", {})
                tx_5m = txns.get("m5", {})
                buys_5m = int(tx_5m.get("buys", 0))
                sells_5m = int(tx_5m.get("sells", 0))
                total_tx_5m = buys_5m + sells_5m
                ratio_5m = round(buys_5m / max(1, sells_5m), 2)

                vol = pair.get("volume", {})
                vol_5m = float(vol.get("m5", 0.0))
                vol_1h = float(vol.get("h1", 0.0))
                vol_24h = float(vol.get("h24", 0.0))

                price_change = pair.get("priceChange", {})
                m5_change = float(price_change.get("m5", 0.0))
                m15_change = float(price_change.get("m15", 0.0))
                h1_change = float(price_change.get("h1", 0.0))

                liquidity_usd = float(pair.get("liquidity", {}).get("usd", 0.0))
                fdv = float(pair.get("fdv", 0.0) or pair.get("marketCap", 0.0))

                # Extract verified social presence & narrative
                info = pair.get("info", {})
                socials = info.get("socials", [])
                twitter_url = next((s.get("url") for s in socials if s.get("type") == "twitter"), None)
                telegram_url = next((s.get("url") for s in socials if s.get("type") == "telegram"), None)
                websites = info.get("websites", [])
                website_url = websites[0].get("url") if websites else None

                # Safety report
                safety_report = await cls.fetch_safety_check(session, mint)

                return {
                    "token_address": mint,
                    "symbol": pair.get("baseToken", {}).get("symbol", "UNKNOWN"),
                    "name": pair.get("baseToken", {}).get("name", "Unknown Token"),
                    "price_usd": pair.get("priceUsd", "0.00"),
                    "age_minutes": age_minutes,
                    "liquidity_usd": liquidity_usd,
                    "market_cap": fdv,
                    "volume_5m": vol_5m,
                    "volume_1h": vol_1h,
                    "volume_24h": vol_24h,
                    "price_change_5m": m5_change,
                    "price_change_15m": m15_change,
                    "price_change_1h": h1_change,
                    "buys_5m": buys_5m,
                    "sells_5m": sells_5m,
                    "tx_count_5m": total_tx_5m,
                    "buy_sell_ratio_5m": ratio_5m,
                    "dex_url": pair.get("url", f"https://dexscreener.com/solana/{mint}"),
                    "dex": pair.get("dexId", "raydium"),
                    "socials": {
                        "has_socials": bool(twitter_url or telegram_url or website_url),
                        "twitter_url": twitter_url,
                        "telegram_url": telegram_url,
                        "website_url": website_url,
                        "description": pair.get("baseToken", {}).get("name", "")
                    },
                    "safety": safety_report
                }
        except Exception as e:
            logger.debug(f"Metrics fetch error for {mint}: {e}")
            return None

    @classmethod
    async def fetch_safety_check(cls, session: aiohttp.ClientSession, mint: str) -> Dict[str, Any]:
        """Fetches RugCheck token risk parameters."""
        url = f"{cls.RUGCHECK_API_URL}{mint}/report/summary"
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=4)) as resp:
                if resp.status == 200:
                    report = await resp.json()
                    risks = report.get("risks", [])
                    has_freeze = any("freeze" in r.get("name", "").lower() for r in risks)
                    has_mint = any("mint" in r.get("name", "").lower() for r in risks)
                    score = report.get("score", 0)
                    return {
                        "is_safe": score < 1500 and not has_freeze and not has_mint,
                        "score": score,
                        "has_freeze_authority": has_freeze,
                        "has_mint_authority": has_mint,
                    }
        except Exception:
            pass
        return {
            "is_safe": True,
            "score": 0,
            "has_freeze_authority": False,
            "has_mint_authority": False,
              }
