import base64
from typing import Dict, Any
import aiohttp
from solders.keypair import Keypair
from solders.transaction import VersionedTransaction
from solana.rpc.async_api import AsyncClient
from loguru import logger
from app.config import settings

class SolanaManager:
    JUPITER_QUOTE_URL = "https://quote-api.jup.ag/v6/quote"
    JUPITER_SWAP_URL = "https://quote-api.jup.ag/v6/swap"

    def __init__(self):
        self.rpc_client = AsyncClient(settings.SOLANA_RPC_URL)
        self.wallet = Keypair.from_base58_string(settings.SOLANA_PRIVATE_KEY)

    @property
    def public_key_str(self) -> str:
        return str(self.wallet.pubkey())

    async def get_swap_quote(self, input_mint: str, output_mint: str, amount_lamports: int) -> Dict[str, Any]:
        params = {
            "inputMint": input_mint,
            "outputMint": output_mint,
            "amount": str(amount_lamports),
            "slippageBps": str(settings.SLIPPAGE_BPS)
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(self.JUPITER_QUOTE_URL, params=params, timeout=aiohttp.ClientTimeout(total=8)) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    raise RuntimeError(f"Jupiter Quote API error: {text}")
                return await resp.json()

    async def build_and_send_swap(self, quote_response: Dict[str, Any]) -> str:
        payload = {
            "quoteResponse": quote_response,
            "userPublicKey": self.public_key_str,
            "wrapAndUnwrapSol": True,
            "prioritizationFeeLamports": "auto"
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(self.JUPITER_SWAP_URL, json=payload, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    raise RuntimeError(f"Jupiter Swap API error: {text}")
                swap_data = await resp.json()

        swap_tx_base64 = swap_data.get("swapTransaction")
        if not swap_tx_base64:
            raise ValueError("No swap transaction payload in response")

        tx_bytes = base64.b64decode(swap_tx_base64)
        versioned_tx = VersionedTransaction.from_bytes(tx_bytes)

        # Sign the transaction
        signature = self.wallet.sign_message(versioned_tx.message.to_bytes())
        signed_tx = VersionedTransaction.populate(versioned_tx.message, [signature])

        # Submit transaction
        tx_response = await self.rpc_client.send_raw_transaction(bytes(signed_tx))
        tx_hash = str(tx_response.value)
        logger.info(f"Transaction submitted successfully. Hash: {tx_hash}")
        return tx_hash
