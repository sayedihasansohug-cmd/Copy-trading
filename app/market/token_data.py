import requests
import logging

logger = logging.getLogger("solana-ai-bot")

def get_detailed_token_data(token_address: str) -> dict:
    url = f"https://api.dexscreener.com/latest/dex/tokens/{token_address}"
    try:
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            data = res.json()
            pairs = data.get("pairs", [])
            if pairs:
                p = pairs[0]
                return {
                    "token_address": token_address,
                    "symbol": p.get("baseToken", {}).get("symbol", "UNKNOWN"),
                    "price": float(p.get("priceUsd", 0.0)),
                    "liquidity": float(p.get("liquidity", {}).get("usd", 0.0)),
                    "volume24h": float(p.get("volume", {}).get("h24", 0.0))
                }
    except Exception as exc:
        logger.error("Error fetching token details: %s", exc)
    return {}
  
