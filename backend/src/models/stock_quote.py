"""StockQuote model for cached stock quote data.

This module defines the StockQuote SQLAlchemy model for caching stock quotes
from yfinance API with 5-minute TTL.
"""

from sqlalchemy import Column, BigInteger, String, DECIMAL, BigInteger as BigInt, TIMESTAMP, Enum, JSON, func
from src.core.database import Base
import enum


class MarketStatus(str, enum.Enum):
    """Enum for market status."""
    OPEN = "open"
    CLOSED = "closed"


class Market(str, enum.Enum):
    """Enum for market region."""
    KR = "KR"  # Korean market (KOSPI/KOSDAQ)
    US = "US"  # US market (NYSE/NASDAQ)


class StockQuote(Base):
    """StockQuote model for MyStock application.
    
    Caches stock quote data from yfinance API with 5-minute TTL.
    
    Attributes:
        id: Primary key, auto-incrementing integer
        symbol: Stock ticker symbol (unique)
        current_price: Latest trading price
        daily_change_pct: Daily percentage change
        volume: Trading volume
        market_status: 'open' (장중) or 'closed' (마감)
        market: 'KR' (Korean) or 'US' (American)
        updated_at: Timestamp for TTL calculation
        cache_data: JSON field storing full yfinance response
        
    Cache TTL Logic:
        Quote is valid if updated_at > NOW() - INTERVAL 5 MINUTE
    """
    
    __tablename__ = "stock_quotes"
    __table_args__ = {"comment": "Cached stock quotes with 5-minute TTL"}
    
    # Primary Key
    id = Column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        comment="Stock quote ID (primary key)"
    )
    
    # Stock Information
    symbol = Column(
        String(20),
        unique=True,
        nullable=False,
        index=True,
        comment="Stock ticker symbol (unique)"
    )
    
    current_price = Column(
        DECIMAL(15, 4),
        nullable=True,
        comment="Latest trading price"
    )
    
    daily_change_pct = Column(
        DECIMAL(8, 4),
        nullable=True,
        comment="Daily percentage change"
    )
    
    volume = Column(
        BigInt,
        nullable=True,
        comment="Trading volume"
    )
    
    market_status = Column(
        Enum(MarketStatus),
        default=MarketStatus.CLOSED,
        nullable=False,
        comment="'open' (장중) or 'closed' (마감)"
    )
    
    market = Column(
        Enum(Market),
        nullable=False,
        comment="'KR' (Korean) or 'US' (American)"
    )
    
    # Timestamp
    updated_at = Column(
        TIMESTAMP,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        index=True,
        comment="Timestamp for TTL calculation"
    )
    
    # Cache Data
    cache_data = Column(
        JSON,
        nullable=True,
        comment="Full yfinance response for extensibility"
    )
    
    def __repr__(self) -> str:
        """String representation of StockQuote object."""
        return f"<StockQuote(symbol='{self.symbol}', price={self.current_price}, market={self.market.value})>"
    
    @classmethod
    def detect_market(cls, symbol: str) -> Market:
        """Detect market from symbol suffix.
        
        Args:
            symbol: Stock ticker symbol
            
        Returns:
            Market enum (KR or US)
        """
        if symbol.endswith(".KS") or symbol.endswith(".KQ"):
            return Market.KR
        return Market.US
