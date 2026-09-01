import httpx
from app.config import settings


class TokenSafetyError(Exception):
    pass


async def get_token_data(mint_address: str) -> dict | None:
    url = f"{settings.dexscreener_api}/tokens/{mint_address}"
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(url)
        if resp.status_code != 200:
            return None
        data = resp.json()
        pairs = data.get("pairs") or []
        if not pairs:
            return None
        pair = max(pairs, key=lambda p: float(p.get("liquidity", {}).get("usd", 0) or 0))
        return {
            "mint": mint_address,
            "symbol": pair.get("baseToken", {}).get("symbol"),
            "price_usd": float(pair.get("priceUsd", 0) or 0),
            "liquidity_usd": float(pair.get("liquidity", {}).get("usd", 0) or 0),
            "volume_24h_usd": float(pair.get("volume", {}).get("h24", 0) or 0),
            "price_change_5m": float(pair.get("priceChange", {}).get("m5", 0) or 0),
            "price_change_1h": float(pair.get("priceChange", {}).get("h1", 0) or 0),
            "created_at_ms": pair.get("pairCreatedAt"),
            "dex": pair.get("dexId"),
            "fdv": float(pair.get("fdv", 0) or 0),
        }


def passes_safety_filter(token: dict, min_liquidity_usd: float = 5000,
                          min_volume_24h_usd: float = 2000) -> tuple[bool, str]:
    if token["liquidity_usd"] < min_liquidity_usd:
        return False, f"liquidity too low (${token['liquidity_usd']:.0f})"
    if token["volume_24h_usd"] < min_volume_24h_usd:
        return False, f"24h volume too low (${token['volume_24h_usd']:.0f})"
    if token["fdv"] > 0 and token["liquidity_usd"] / token["fdv"] < 0.02:
        return False, "liquidity/FDV ratio suspiciously low (possible rug setup)"
    if token["price_change_5m"] > 300:
        return False, "already pumped >300% in 5m — likely too late to enter"
    return True, "ok"
