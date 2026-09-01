from loguru import logger
from app.blockchain.solana import SolanaManager
from app.config import settings

WSOL_MINT = "So11111111111111111111111111111111111111112"

class TradeExecutor:
    def __init__(self):
        self.solana = SolanaManager()

    async def execute_buy(self, token_mint: str, sol_amount: float) -> str:
        logger.info(f"Initiating BUY for mint: {token_mint} with {sol_amount} SOL")
        lamports = int(sol_amount * 1_000_000_000)
        quote = await self.solana.get_swap_quote(
            input_mint=WSOL_MINT,
            output_mint=token_mint,
            amount_lamports=lamports
        )
        return await self.solana.build_and_send_swap(quote)

    async def execute_sell(self, token_mint: str, raw_units: int) -> str:
        logger.info(f"Initiating SELL for mint: {token_mint} with units: {raw_units}")
        quote = await self.solana.get_swap_quote(
            input_mint=token_mint,
            output_mint=WSOL_MINT,
            amount_lamports=raw_units
        )
        return await self.solana.build_and_send_swap(quote)
