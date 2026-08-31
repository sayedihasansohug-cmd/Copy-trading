from sqlalchemy import select

from app.database.database import get_session
from app.database.models import Token, Position
from app.trading.risk_manager import calc_stop_loss_price, calc_take_profit_price


async def get_or_create_token(mint_address: str, symbol: str = "", name: str = "") -> Token:
    async with get_session() as session:
        result = await session.execute(select(Token).where(Token.mint_address == mint_address))
        token = result.scalar_one_or_none()
        if token:
            return token
        token = Token(mint_address=mint_address, symbol=symbol, name=name)
        session.add(token)
        await session.flush()
        await session.refresh(token)
        return token


async def open_position(mint_address: str, entry_price: float, amount_tokens: float,
                         sol_invested: float, symbol: str = "") -> Position:
    token = await get_or_create_token(mint_address, symbol=symbol)
    async with get_session() as session:
        position = Position(
            token_id=token.id,
            entry_price_sol=entry_price,
            amount_tokens=amount_tokens,
            sol_invested=sol_invested,
            stop_loss_price=calc_stop_loss_price(entry_price),
            take_profit_price=calc_take_profit_price(entry_price),
            is_open=True,
        )
        session.add(position)
        await session.flush()
        await session.refresh(position)
        return position


async def close_position(position_id: int, exit_price: float) -> Position:
    import datetime as dt
    async with get_session() as session:
        result = await session.execute(select(Position).where(Position.id == position_id))
        position = result.scalar_one()
        position.is_open = False
        position.closed_at = dt.datetime.utcnow()
        position.exit_price_sol = exit_price
        position.realized_pnl_sol = (exit_price - position.entry_price_sol) * position.amount_tokens
        await session.flush()
        await session.refresh(position)
        return position
