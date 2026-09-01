from typing import Optional, Dict, Any
import aiohttp
from loguru import logger

class TokenDataFetcher:
    DEX_TOKEN_URL = "https://api.dexscreener.com/latest/dex/tokens/"
    DEX_SEARCH_URL = "https://api.dexscreener.com/latest/dex/search?q="

    @classmethod
    async def get_pair_by_address(cls, mint_address: str) -> Optional[Dict[str, Any]]:
        url = f"{cls.DEX_TOKEN_URL}{mint_address}"
        return await cls._fetch_solana_pair(url)

    @classmethod
    async def get_pair_by_ticker(cls, ticker: str) -> Optional[Dict[str, Any]]:
        url = f"{cls.DEX_SEARCH_URL}{ticker}"
        return await cls._fetch_solana_pair(url)

    @classmethod
    async def _fetch_solana_pair(cls, url: str) -> Optional[Dict[str, Any]]:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                    if response.status != 200:
                        return None
                    data = await response.json()
                    pairs = data.get("pairs") or []
                    sol_pairs = [p for p in pairs if p.get("chainId") == "solana"]
                    if not sol_pairs:
                        return None
                    sol_pairs.sort(key=lambda p: float(p.get("liquidity", {}).get("usd", 0) or 0), reverse=True)
                    return sol_pairs[0]
        except Exception as e:
            logger.error(f"Failed to fetch DexScreener data: {e}")
            return None
