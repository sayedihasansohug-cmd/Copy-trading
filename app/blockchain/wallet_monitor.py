import asyncio
from sqlalchemy import select

from app.database.database import get_session
from app.database.models import Position
from app.market.token_data import get_token_data


async def check_positions_for_exit(exit_callback):
    async with get_session() as session:
        result = await session.execute(select(Position).where(Position.is_open == True))  # noqa: E712
        open_positions = result.scalars().all()

    for position in open_positions:
        token_data = await get_token_data(position.token.mint_address)
        if not token_data or token_data["price_usd"] <= 0:
            continue
        price = token_data["price_usd"]

        if price <= position.stop_loss_price:
            await exit_callback(position, price, "stop_loss")
        elif price >= position.take_profit_price:
            await exit_callback(position, price, "take_profit")


async def monitor_loop(exit_callback, interval_seconds: int = 15):
    while True:
        try:
            await check_positions_for_exit(exit_callback)
        except Exception as e:
            print(f"[wallet_monitor] error: {e}")
        await asyncio.sleep(interval_seconds)
