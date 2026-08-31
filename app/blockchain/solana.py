import logging

logger = logging.getLogger("solana-ai-bot")

class SolanaClient:
    def __init__(self, rpc_url="https://api.mainnet-beta.solana.com"):
        self.rpc_url = rpc_url

    def get_token_info(self, token_address):
        logger.info("Fetching on-chain info for token: %s", token_address)
        return {"status": "success", "address": token_address}
      
