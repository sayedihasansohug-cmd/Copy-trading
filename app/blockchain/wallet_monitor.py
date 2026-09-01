from solders.pubkey import Pubkey
from app.blockchain.solana import SolanaManager
from loguru import logger

class WalletMonitor:
    def __init__(self, solana_manager: SolanaManager):
        self.solana = solana_manager

    async def get_sol_balance(self) -> float:
        try:
            pubkey = Pubkey.from_string(self.solana.public_key_str)
            resp = await self.solana.rpc_client.get_balance(pubkey)
            return resp.value / 1e9
        except Exception as e:
            logger.error(f"Failed to fetch SOL balance: {e}")
            return 0.0
