import asyncio
from datetime import datetime
from sqlalchemy import select
from loguru import logger
from app.database.database import AsyncSessionLocal
from app.database.models import Position
from app.market.token_data import TokenDataFetcher
from app.trading.executor import TradeExecutor
from app.telegram.bot import TelegramNotifier
from app.config import settings

class PositionManager:
    def __init__(self):
        self.executor = TradeExecutor()
        self.notifier = TelegramNotifier()

    async def register_position(self, token_mint: str, symbol: str, entry_price: float, token_amount: float, sol_invested: float, tx_hash: str):
        async with AsyncSessionLocal() as session:
            pos = Position(
                token_mint=token_mint,
                symbol=symbol,
                entry_price_usd=entry_price,
                highest_price_usd=entry_price,
                token_amount=token_amount,
                sol_invested=sol_invested,
                buy_tx_hash=tx_hash,
                is_active=True
            )
            session.add(pos)
            await session.commit()
            logger.info(f"Position saved for {symbol} at ${entry_price}")

    async def monitor_positions_loop(self):
        while True:
            try:
                async with AsyncSessionLocal() as session:
                    stmt = select(Position).where(Position.is_active == True)
                    result = await session.execute(stmt)
                    active_positions = result.scalars().all()

                    for pos in active_positions:
                        await self._process_active_position(session, pos)

            except Exception as e:
                logger.error(f"Error in position tracking cycle: {e}")

            await asyncio.sleep(10)

    async def _process_active_position(self, session, pos: Position):
        pair = await TokenDataFetcher.get_pair_by_address(pos.token_mint)
        if not pair:
            return

        current_price = float(pair.get("priceUsd", 0) or 0)
        if current_price <= 0:
            return

        if current_price > pos.highest_price_usd:
            pos.highest_price_usd = current_price
            await session.commit()

        pnl_pct = ((current_price - pos.entry_price_usd) / pos.entry_price_usd) * 100.0
        drawdown_pct = ((pos.highest_price_usd - current_price) / pos.highest_price_usd) * 100.0

        should_close = False
        reason = ""

        if pnl_pct >= settings.TAKE_PROFIT_PCT:
            should_close = True
            reason = f"Take-Profit Reached (+{pnl_pct:.2f}%)"
        elif pnl_pct <= -settings.STOP_LOSS_PCT:
            should_close = True
            reason = f"Stop-Loss Triggered ({pnl_pct:.2f}%)"
        elif drawdown_pct >= settings.TRAILING_STOP_PCT and pnl_pct > 15.0:
            should_close = True
            reason = f"Trailing-Stop Triggered (Peak Drop -{drawdown_pct:.2f}%)"

        if should_close:
            await self._close_position(session, pos, current_price, pnl_pct, reason)

    async def _close_position(self, session, pos: Position, close_price: float, pnl_pct: float, reason: str):
        logger.info(f"Closing position {pos.symbol}: {reason}")
        try:
            raw_units = int(pos.token_amount * 1_000_000)
            tx_hash = await self.executor.execute_sell(pos.token_mint, raw_units)

            pos.is_active = False
            pos.sell_tx_hash = tx_hash
            pos.closed_at = datetime.utcnow()
            await session.commit()

            msg = (
                f"🚨 *POSITION CLOSED*\n\n"
                f"🪙 *Token:* {pos.symbol}\n"
                f"💡 *Trigger:* {reason}\n"
                f"📊 *PnL:* {pnl_pct:+.2f}%\n"
                f"💵 *Exit Price:* ${close_price:.6f}\n\n"
                f"🔗 [Solscan](https://solscan.io/tx/{tx_hash})"
            )
            await self.notifier.send_alert(msg)
        except Exception as e:
            logger.error(f"Failed to sell position {pos.symbol}: {e}")
