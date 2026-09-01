from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Position(Base):
    __tablename__ = "positions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    token_mint = Column(String(64), unique=True, index=True, nullable=False)
    symbol = Column(String(32), nullable=False)
    entry_price_usd = Column(Float, nullable=False)
    highest_price_usd = Column(Float, nullable=False)
    token_amount = Column(Float, nullable=False)
    sol_invested = Column(Float, nullable=False)
    is_active = Column(Boolean, default=True, index=True)
    buy_tx_hash = Column(String(128), nullable=False)
    sell_tx_hash = Column(String(128), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    closed_at = Column(DateTime, nullable=True)
