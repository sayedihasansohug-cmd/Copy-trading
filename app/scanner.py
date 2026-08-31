import logging
import requests

logger = logging.getLogger("solana-ai-bot")

DEXSCREENER_URL = "https://api.dexscreener.com/latest/dex/search?q=solana"

def scan_tokens():
    tokens = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    try:
        response = requests.get(DEXSCREENER_URL, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            pairs = data.get("pairs", [])
            for pair in pairs[:10]:
                if pair.get("chainId") == "solana":
                    base_token = pair.get("baseToken", {})
                    addr = base_token.get("address")
                    if addr:
                        tokens.append({
                            "token_address": addr,
                            "symbol": base_token.get("symbol", "UNKNOWN"),
                            "price": float(pair.get("priceUsd", 0.0001)),
                            "liquidity": float(pair.get("liquidity", {}).get("usd", 0)),
                            "volume24h": float(pair.get("volume", {}).get("h24", 0))
                        })
    except Exception as exc:
        logger.error("Scan exception: %s", exc)

    # Backup candidate tokens if API fails
    if not tokens:
        tokens = [
            {
                "token_address": "So11111111111111111111111111111111111111112",
                "symbol": "SOL_PRO",
                "price": 0.00025,
                "liquidity": 45000,
                "volume24h": 150000
            }
        ]

    logger.info("Scanner fetched %d token(s)", len(tokens))
    return tokens
  
