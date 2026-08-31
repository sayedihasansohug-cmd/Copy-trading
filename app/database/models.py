from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    Index,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def utc_now() -> datetime:
    """Return a timezone-aware UTC datetime."""
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    """Base class for all database models."""

    pass


class Token(Base):
    """
    Solana token discovered by the bot.
    """

    __tablename__ = "tokens"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    mint_address: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
        index=True,
    )

    symbol: Mapped[Optional[str]] = mapped_column(
        String(32),
        nullable=True,
    )

    name: Mapped[Optional[str]] = mapped_column(
        String(128),
        nullable=True,
    )

    decimals: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )

    market_cap_usd: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(24, 8),
        nullable=True,
    )

    liquidity_usd: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(24, 8),
        nullable=True,
    )

    volume_24h_usd: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(24, 8),
        nullable=True,
    )

    first_detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )

    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )

    token_age_seconds: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        nullable=True,
    )

    mint_authority_enabled: Mapped[Optional[bool]] = mapped_column(
        Boolean,
        nullable=True,
    )

    freeze_authority_enabled: Mapped[Optional[bool]] = mapped_column(
        Boolean,
        nullable=True,
    )

    top_holder_percent: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(8, 4),
        nullable=True,
    )

    safety_status: Mapped[str] = mapped_column(
        String(16),
        default="UNKNOWN",
        nullable=False,
    )

    is_blocked: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    block_reason: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )


class Signal(Base):
    """
    Market/news/social signal associated with a token.
    """

    __tablename__ = "signals"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    token_mint: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
    )

    source: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )

    source_type: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
    )

    title: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )

    content: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    url: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    sentiment: Mapped[Optional[str]] = mapped_column(
        String(16),
        nullable=True,
    )

    sentiment_score: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(8, 4),
        nullable=True,
    )

    relevance_score: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(8, 4),
        nullable=True,
    )

    source_quality_score: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(8, 4),
        nullable=True,
    )

    collected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )

    published_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    __table_args__ = (
        Index(
            "ix_signals_token_collected",
            "token_mint",
            "collected_at",
        ),
    )


class AIDecision(Base):
    """
    Structured decision returned by the AI layer.

    The AI does not execute trades.
    """

    __tablename__ = "ai_decisions"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    token_mint: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
    )

    decision: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
    )

    confidence: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    score: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    risk_level: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
    )

    suggested_position_percent: Mapped[Decimal] = mapped_column(
        Numeric(8, 4),
        default=Decimal("0"),
        nullable=False,
    )

    take_profit_percent: Mapped[Decimal] = mapped_column(
        Numeric(8, 4),
        default=Decimal("0"),
        nullable=False,
    )

    stop_loss_percent: Mapped[Decimal] = mapped_column(
        Numeric(8, 4),
        default=Decimal("0"),
        nullable=False,
    )

    reason: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    warnings: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    model_name: Mapped[Optional[str]] = mapped_column(
        String(128),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )


class Position(Base):
    """
    Current or historical position.
    """

    __tablename__ = "positions"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    token_mint: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
    )

    symbol: Mapped[Optional[str]] = mapped_column(
        String(32),
        nullable=True,
    )

    quantity: Mapped[Decimal] = mapped_column(
        Numeric(38, 18),
        nullable=False,
    )

    entry_price: Mapped[Decimal] = mapped_column(
        Numeric(38, 18),
        nullable=False,
    )

    current_price: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(38, 18),
        nullable=True,
    )

    position_value_usd: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(24, 8),
        nullable=True,
    )

    stop_loss_price: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(38, 18),
        nullable=True,
    )

    take_profit_price: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(38, 18),
        nullable=True,
    )

    unrealized_pnl: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(24, 8),
        nullable=True,
    )

    mode: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default="PAPER",
    )

    status: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default="OPEN",
        index=True,
    )

    opened_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )

    closed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    __table_args__ = (
        Index(
            "ix_positions_token_status",
            "token_mint",
            "status",
        ),
    )


class Trade(Base):
    """
    Every BUY/SELL execution or paper-trade simulation.
    """

    __tablename__ = "trades"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    token_mint: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
    )

    symbol: Mapped[Optional[str]] = mapped_column(
        String(32),
        nullable=True,
    )

    side: Mapped[str] = mapped_column(
        String(8),
        nullable=False,
    )

    entry_price: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(38, 18),
        nullable=True,
    )

    exit_price: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(38, 18),
        nullable=True,
    )

    amount: Mapped[Decimal] = mapped_column(
        Numeric(38, 18),
        nullable=False,
    )

    notional_usd: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(24, 8),
        nullable=True,
    )

    pnl: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(24, 8),
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="PENDING",
    )

    mode: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default="PAPER",
    )

    ai_score: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )

    ai_confidence: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )

    reason: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    tx_signature: Mapped[Optional[str]] = mapped_column(
        String(128),
        nullable=True,
        index=True,
    )

    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )

    closed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    __table_args__ = (
        Index(
            "ix_trades_token_created",
            "token_mint",
            "created_at",
        ),
    )


class DailyStat(Base):
    """
    Daily risk and performance statistics.
    """

    __tablename__ = "daily_stats"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    trading_date: Mapped[str] = mapped_column(
        String(10),
        unique=True,
        nullable=False,
        index=True,
    )

    starting_balance: Mapped[Decimal] = mapped_column(
        Numeric(24, 8),
        nullable=False,
    )

    ending_balance: Mapped[Decimal] = mapped_column(
        Numeric(24, 8),
        nullable=False,
    )

    realized_pnl: Mapped[Decimal] = mapped_column(
        Numeric(24, 8),
        default=Decimal("0"),
        nullable=False,
    )

    total_trades: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    winning_trades: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    losing_trades: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    circuit_breaker_triggered: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )


class TradeLock(Base):
    """
    Database-level lock used to protect against duplicate trades.

    This is important when the worker restarts or multiple
    execution tasks accidentally process the same token.
    """

    __tablename__ = "trade_locks"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    token_mint: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )

    lock_type: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
    )

    locked_until: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint(
            "token_mint",
            "lock_type",
            name="uq_trade_lock_token_type",
        ),
  )
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
