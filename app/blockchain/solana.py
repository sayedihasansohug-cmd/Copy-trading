import logging

logger = logging.getLogger("solana-ai-bot")

class SolanaClient:
    def __init__(self, rpc_url="https://api.mainnet-beta.solana.com"):
        self.rpc_url = rpc_url

    def get_token_info(self, token_address):
        logger.info("Fetching on-chain info for token: %s", token_address)
        return {"status": "success", "address": token_address}
      
import base58
from solders.keypair import Keypair
from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Confirmed

from app.config import settings


class SolanaConnection:
    def __init__(self):
        self.client = AsyncClient(settings.solana_rpc_url, commitment=Confirmed)
        self.keypair = self._load_keypair()

    @staticmethod
    def _load_keypair() -> Keypair:
        raw = base58.b58decode(settings.wallet_private_key)
        return Keypair.from_bytes(raw)

    @property
    def public_key(self) -> str:
        return str(self.keypair.pubkey())

    async def get_sol_balance(self) -> float:
        resp = await self.client.get_balance(self.keypair.pubkey())
        return resp.value / 1_000_000_000

    async def close(self):
        await self.client.close()


solana_conn = SolanaConnection()
