import datetime as dt
from sqlalchemy import select, func

from app.config import settings
from app.database.database import get_session
from app.database.models import Position, TradeLog


class RiskCheckFailed(Exception):
    pass


async def get_open_position_count() -> int:
    async with get_session() as session:
        result = await session.execute(
            select(func.count()).select_from(Position).where(Position.is_open == True)  # noqa: E712
        )
        return result.scalar_one()


async def get_today_realized_pnl() -> float:
    today_start = dt.datetime.combine(dt.date.today(), dt.time.min)
    async with get_session() as session:
        result = await session.execute(
            select(func.coalesce(func.sum(Position.realized_pnl_sol), 0.0))
            .where(Position.closed_at >= today_start)
        )
        return result.scalar_one()


async def has_open_position_for(mint_address: str) -> bool:
    async with get_session() as session:
        result = await session.execute(
            select(Position)
            .join(Position.token)
            .where(Position.is_open == True)  # noqa: E712
        )
        positions = result.scalars().all()
        return any(p.token.mint_address == mint_address for p in positions)


async def check_can_open_position(mint_address: str, sol_amount: float) -> None:
    if sol_amount > settings.max_position_size_sol:
        raise RiskCheckFailed(
            f"position size {sol_amount} SOL exceeds max {settings.max_position_size_sol} SOL"
        )

    open_count = await get_open_position_count()
    if open_count >= settings.max_open_positions:
        raise RiskCheckFailed(f"already at max open positions ({settings.max_open_positions})")

    if await has_open_position_for(mint_address):
        raise RiskCheckFailed("already holding a position in this token")

    today_pnl = await get_today_realized_pnl()
    if today_pnl <= -abs(settings.max_daily_loss_sol):
        raise RiskCheckFailed(
            f"daily loss limit hit ({today_pnl:.4f} SOL) — trading paused until tomorrow"
        )


def calc_stop_loss_price(entry_price: float) -> float:
    return entry_price * (1 - settings.stop_loss_percent / 100)


def calc_take_profit_price(entry_price: float) -> float:
    return entry_price * (1 + settings.take_profit_percent / 100)
