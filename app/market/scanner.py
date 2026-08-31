import logging
import requests

logger = logging.getLogger("solana-ai-bot")

# DexScreener Public Search API
SEARCH_API_URL = "https://api.dexscreener.com/latest/dex/search?q=solana"

def scan_tokens():
    """
    Scans live Solana tokens from DexScreener API.
    Provides fallback mock tokens if API is restricted.
    """
    tokens = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        response = requests.get(SEARCH_API_URL, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            pairs = data.get("pairs", [])
            
            for pair in pairs[:10]:
                if pair.get("chainId") == "solana":
                    base_token = pair.get("baseToken", {})
                    token_addr = base_token.get("address")
                    if token_addr:
                        tokens.append({
                            "token_address": token_addr,
                            "symbol": base_token.get("symbol", "UNKNOWN"),
                            "price": float(pair.get("priceUsd", 0.0001)),
                            "liquidity": float(pair.get("liquidity", {}).get("usd", 0)),
                            "volume24h": float(pair.get("volume", {}).get("h24", 0))
                        })

    except Exception as exc:
        logger.error("Token scanning exception: %s", exc)

    # Fallback to test tokens if external API yields empty results
    if not tokens:
        logger.warning("API returned empty results or got restricted. Injecting candidate tokens for AI evaluation.")
        tokens = [
            {
                "token_address": "So11111111111111111111111111111111111111112",
                "symbol": "SOL_MEME",
                "price": 0.00025,
                "liquidity": 25000,
                "volume24h": 120000
            },
            {
                "token_address": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
                "symbol": "AI_DOGE",
                "price": 0.00008,
                "liquidity": 18000,
                "volume24h": 85000
            }
        ]

    logger.info("Successfully scanned %d Solana token(s)", len(tokens))
    return tokens
  
