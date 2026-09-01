import httpx
import base64
from solders.transaction import VersionedTransaction
from solders.commitment_config import CommitmentLevel
from solana.rpc.types import TxOpts

from app.config import settings
from app.blockchain.solana import solana_conn

SOL_MINT = "So11111111111111111111111111111111111111112"
LAMPORTS_PER_SOL = 1_000_000_000


class SwapError(Exception):
    pass


async def get_quote(input_mint: str, output_mint: str, amount_lamports: int) -> dict:
    url = f"{settings.jupiter_quote_api}/quote"
    params = {
        "inputMint": input_mint,
        "outputMint": output_mint,
        "amount": amount_lamports,
        "slippageBps": settings.slippage_bps,
    }
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(url, params=params)
        if resp.status_code != 200:
            raise SwapError(f"quote failed: {resp.text}")
        return resp.json()


async def execute_swap(input_mint: str, output_mint: str, amount_lamports: int) -> str:
    quote = await get_quote(input_mint, output_mint, amount_lamports)

    async with httpx.AsyncClient(timeout=15) as client:
        swap_resp = await client.post(
            f"{settings.jupiter_quote_api}/swap",
            json={
                "quoteResponse": quote,
                "userPublicKey": solana_conn.public_key,
                "wrapAndUnwrapSol": True,
                "dynamicComputeUnitLimit": True,
                "prioritizationFeeLamports": "auto",
            },
        )
        if swap_resp.status_code != 200:
            raise SwapError(f"swap build failed: {swap_resp.text}")
        swap_tx_b64 = swap_resp.json()["swapTransaction"]

    raw_tx = VersionedTransaction.from_bytes(base64.b64decode(swap_tx_b64))
    signed_tx = VersionedTransaction(raw_tx.message, [solana_conn.keypair])

    result = await solana_conn.client.send_raw_transaction(
        bytes(signed_tx),
        opts=TxOpts(skip_preflight=False, preflight_commitment=CommitmentLevel.Confirmed),
    )
    signature = str(result.value)

    confirmed = await solana_conn.client.confirm_transaction(result.value, commitment=CommitmentLevel.Confirmed)
    if confirmed.value[0].err is not None:
        raise SwapError(f"transaction failed on-chain: {confirmed.value[0].err}")

    return signature


async def buy_token(mint_address: str, sol_amount: float) -> str:
    lamports = int(sol_amount * LAMPORTS_PER_SOL)
    return await execute_swap(SOL_MINT, mint_address, lamports)


async def sell_token(mint_address: str, token_amount_lamports: int) -> str:
    return await execute_swap(mint_address, SOL_MINT, token_amount_lamports)
