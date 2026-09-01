import datetime as dt
from sqlalchemy import String, Float, Integer, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Token(Base):
    __tablename__ = "tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    mint_address: Mapped[str] = mapped_column(String, unique=True, index=True)
    symbol: Mapped[str] = mapped_column(String, default="")
    name: Mapped[str] = mapped_column(String, default="")
    first_seen_at: Mapped[dt.datetime] = mapped_column(DateTime, default=dt.datetime.utcnow)

    positions: Mapped[list["Position"]] = relationship(back_populates="token")


class Position(Base):
    __tablename__ = "positions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    token_id: Mapped[int] = mapped_column(ForeignKey("tokens.id"))
    token: Mapped["Token"] = relationship(back_populates="positions")

    entry_price_sol: Mapped[float] = mapped_column(Float)
    amount_tokens: Mapped[float] = mapped_column(Float)
    sol_invested: Mapped[float] = mapped_column(Float)
    stop_loss_price: Mapped[float] = mapped_column(Float)
    take_profit_price: Mapped[float] = mapped_column(Float)

    is_open: Mapped[bool] = mapped_column(Boolean, default=True)
    opened_at: Mapped[dt.datetime] = mapped_column(DateTime, default=dt.datetime.utcnow)
    closed_at: Mapped[dt.datetime | None] = mapped_column(DateTime, nullable=True)
    exit_price_sol: Mapped[float | None] = mapped_column(Float, nullable=True)
    realized_pnl_sol: Mapped[float | None] = mapped_column(Float, nullable=True)


class TradeLog(Base):
    __tablename__ = "trade_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    timestamp: Mapped[dt.datetime] = mapped_column(DateTime, default=dt.datetime.utcnow)
    mint_address: Mapped[str] = mapped_column(String)
    side: Mapped[str] = mapped_column(String)
    amount_sol: Mapped[float] = mapped_column(Float)
    tx_signature: Mapped[str | None] = mapped_column(String, nullable=True)
    success: Mapped[bool] = mapped_column(Boolean, default=False)
    error_message: Mapped[str | None] = mapped_column(String, nullable=True)
    ai_reasoning: Mapped[str | None] = mapped_column(String, nullable=True)
