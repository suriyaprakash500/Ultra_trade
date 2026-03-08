"""
Trading Autopilot — Database Models.

Defines both SQLAlchemy ORM models (for persistence) and Pydantic schemas
(for API serialization). Every table uses UUID primary keys for portability.
"""

from __future__ import annotations

import uuid
from datetime import datetime, UTC
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import (
    Column,
    DateTime,
    Float,
    Integer,
    String,
    Text,
    Boolean,
    Enum as SAEnum,
)
from sqlalchemy.orm import DeclarativeBase


# ════════════════════════════════════════════════════════════════════
#  Enumerations
# ════════════════════════════════════════════════════════════════════

class OrderSide(str, Enum):
    """Buy or sell."""
    BUY = "BUY"
    SELL = "SELL"


class OrderType(str, Enum):
    """Order pricing type."""
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    SL = "SL"
    SL_M = "SL-M"


class OrderStatus(str, Enum):
    """Lifecycle status of an order."""
    PENDING = "PENDING"
    OPEN = "OPEN"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"


class ProductType(str, Enum):
    """Kite product types."""
    CNC = "CNC"      # Cash & Carry (delivery)
    MIS = "MIS"      # Margin Intraday Squareoff
    NRML = "NRML"    # Normal (F&O)


class TradingMode(str, Enum):
    """Paper vs live trading."""
    PAPER = "paper"
    LIVE = "live"


class SentimentLevel(str, Enum):
    """AI-determined sentiment."""
    VERY_BULLISH = "very_bullish"
    BULLISH = "bullish"
    NEUTRAL = "neutral"
    BEARISH = "bearish"
    VERY_BEARISH = "very_bearish"


class SafetyLayerResult(str, Enum):
    """Result of a safety layer check."""
    PASSED = "PASSED"
    BLOCKED = "BLOCKED"
    WARNING = "WARNING"


# ════════════════════════════════════════════════════════════════════
#  SQLAlchemy Base
# ════════════════════════════════════════════════════════════════════

class Base(DeclarativeBase):
    """Base class for all ORM models."""
    pass


# ════════════════════════════════════════════════════════════════════
#  ORM Models (Database Tables)
# ════════════════════════════════════════════════════════════════════

class OrderRecord(Base):
    """Persisted order (paper or live)."""

    __tablename__ = "orders"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    symbol = Column(String, nullable=False, index=True)
    exchange = Column(String, default="NSE")
    side = Column(SAEnum(OrderSide), nullable=False)
    order_type = Column(SAEnum(OrderType), default=OrderType.MARKET)
    product = Column(SAEnum(ProductType), default=ProductType.CNC)
    quantity = Column(Integer, nullable=False)
    price = Column(Float, default=0.0)
    trigger_price = Column(Float, default=0.0)
    status = Column(SAEnum(OrderStatus), default=OrderStatus.PENDING)
    trading_mode = Column(SAEnum(TradingMode), default=TradingMode.PAPER)
    kite_order_id = Column(String, nullable=True)
    reason = Column(Text, nullable=True)
    ai_confidence = Column(Float, default=0.0)
    stop_loss = Column(Float, nullable=True)
    take_profit = Column(Float, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))


class PositionRecord(Base):
    """Current open position in the portfolio."""

    __tablename__ = "positions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    symbol = Column(String, nullable=False, index=True, unique=True)
    exchange = Column(String, default="NSE")
    quantity = Column(Integer, default=0)
    average_price = Column(Float, default=0.0)
    current_price = Column(Float, default=0.0)
    pnl = Column(Float, default=0.0)
    pnl_pct = Column(Float, default=0.0)
    sector = Column(String, nullable=True)
    stop_loss = Column(Float, nullable=True)
    take_profit = Column(Float, nullable=True)
    trading_mode = Column(SAEnum(TradingMode), default=TradingMode.PAPER)
    opened_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))


class TradeRecord(Base):
    """Completed trade (for performance tracking)."""

    __tablename__ = "trades"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    order_id = Column(String, nullable=False)
    symbol = Column(String, nullable=False, index=True)
    side = Column(SAEnum(OrderSide), nullable=False)
    quantity = Column(Integer, nullable=False)
    entry_price = Column(Float, nullable=False)
    exit_price = Column(Float, nullable=True)
    pnl = Column(Float, default=0.0)
    pnl_pct = Column(Float, default=0.0)
    reason = Column(Text, nullable=True)
    exit_reason = Column(String, nullable=True)
    ai_confidence = Column(Float, default=0.0)
    duration_minutes = Column(Integer, default=0)
    trading_mode = Column(SAEnum(TradingMode), default=TradingMode.PAPER)
    entered_at = Column(DateTime, default=lambda: datetime.now(UTC))
    exited_at = Column(DateTime, nullable=True)


class NewsRecord(Base):
    """Processed news item with AI analysis."""

    __tablename__ = "news"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String, nullable=False)
    source = Column(String, nullable=False)
    url = Column(String, nullable=True)
    content_summary = Column(Text, nullable=True)
    sentiment = Column(SAEnum(SentimentLevel), default=SentimentLevel.NEUTRAL)
    sentiment_score = Column(Float, default=0.0)  # -2.0 to +2.0
    impact_level = Column(String, default="low")   # critical, high, medium, low
    affected_symbols = Column(Text, nullable=True)  # JSON list of symbols
    ai_confidence = Column(Float, default=0.0)
    processed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))


class DailyMetrics(Base):
    """Daily performance metrics snapshot."""

    __tablename__ = "daily_metrics"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    date = Column(String, nullable=False, unique=True, index=True)
    total_pnl = Column(Float, default=0.0)
    total_pnl_pct = Column(Float, default=0.0)
    win_count = Column(Integer, default=0)
    loss_count = Column(Integer, default=0)
    win_rate = Column(Float, default=0.0)
    avg_win = Column(Float, default=0.0)
    avg_loss = Column(Float, default=0.0)
    largest_win = Column(Float, default=0.0)
    largest_loss = Column(Float, default=0.0)
    portfolio_value = Column(Float, default=0.0)
    cash_balance = Column(Float, default=0.0)
    max_drawdown = Column(Float, default=0.0)
    sharpe_ratio = Column(Float, default=0.0)
    trades_executed = Column(Integer, default=0)
    safety_triggers = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))


# ════════════════════════════════════════════════════════════════════
#  Pydantic Schemas (API Serialization)
# ════════════════════════════════════════════════════════════════════

class OrderCreate(BaseModel):
    """Schema for creating a new order via API."""
    symbol: str
    exchange: str = "NSE"
    side: OrderSide
    order_type: OrderType = OrderType.MARKET
    product: ProductType = ProductType.CNC
    quantity: int
    price: float = 0.0
    trigger_price: float = 0.0
    reason: Optional[str] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None


class OrderResponse(BaseModel):
    """Schema for order API responses."""
    id: str
    symbol: str
    exchange: str
    side: OrderSide
    order_type: OrderType
    product: ProductType
    quantity: int
    price: float
    status: OrderStatus
    trading_mode: TradingMode
    reason: Optional[str] = None
    ai_confidence: float = 0.0
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PositionResponse(BaseModel):
    """Schema for position API responses."""
    id: str
    symbol: str
    exchange: str
    quantity: int
    average_price: float
    current_price: float
    pnl: float
    pnl_pct: float
    sector: Optional[str] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    trading_mode: TradingMode
    opened_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PortfolioSummary(BaseModel):
    """Aggregated portfolio snapshot."""
    total_value: float = 0.0
    cash_balance: float = 0.0
    invested_value: float = 0.0
    total_pnl: float = 0.0
    total_pnl_pct: float = 0.0
    positions_count: int = 0
    day_pnl: float = 0.0
    trading_mode: TradingMode = TradingMode.PAPER


class TradeIdea(BaseModel):
    """AI-generated trade recommendation."""
    symbol: str
    side: OrderSide
    reason: str
    confidence: float = Field(ge=0.0, le=100.0)
    suggested_entry: float
    stop_loss: float
    take_profit: float
    position_size: int
    risk_reward_ratio: float
    time_horizon: str = "1-3 days"
    news_catalysts: list[str] = []


class NewsAnalysis(BaseModel):
    """Processed news analysis result."""
    title: str
    source: str
    sentiment: SentimentLevel
    sentiment_score: float
    impact_level: str
    affected_symbols: list[str]
    summary: str
    confidence: float
    recommended_action: str


class RiskCheckResult(BaseModel):
    """Result of passing a trade through safety layers."""
    passed: bool
    layers_checked: int
    layers_passed: int
    blocked_by: Optional[str] = None
    warnings: list[str] = []
    details: dict = {}


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = "healthy"
    trading_mode: str = "paper"
    version: str = "0.1.0"
    uptime_seconds: float = 0.0
