import logging
import requests

logger = logging.getLogger("solana-ai-bot")

DEXSCREENER_API = "https://api.dexscreener.com/latest/dex/tokens/"
SOLANA_BOOSTED_URL = "https://api.dexscreener.com/token-boosts/top/v1"

def scan_tokens():
    tokens = []
    try:
        response = requests.get(SOLANA_BOOSTED_URL, timeout=10)
        if response.status_code == 200:
            data = response.json()
            for item in data[:5]:  # Top 5 trending tokens
                if item.get("chainId") == "solana":
                    tokens.append({
                        "token_address": item.get("tokenAddress"),
                        "symbol": item.get("tokenAddress")[:6],
                        "price": 0.0001,  # Mock test price
                        "liquidity": 10000,
                        "volume24h": 50000
                    })
    except Exception as exc:
        logger.error("Token scanning error: %s", exc)
    return tokens
  
