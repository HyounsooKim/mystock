"""CandlestickData model for historical OHLCV data.

This module defines the CandlestickData SQLAlchemy model for storing
historical OHLCV (Open, High, Low, Close, Volume) data for chart rendering.
"""

from sqlalchemy import Column, BigInteger, String, DECIMAL, BigInteger as BigInt, DateTime, TIMESTAMP, Enum, func, UniqueConstraint
from src.core.database import Base
import enum


class Period(str, enum.Enum):
    """Enum for candlestick data period/interval."""
    THIRTY_MIN = "30m"  # 30-minute interval
    FIVE_MIN = "5m"     # 5-minute interval, 1-day period
    ONE_HOUR = "1h"     # 1-hour interval, 30-day period
    ONE_DAY = "1d"      # 1-day interval, 3-month period
    ONE_WEEK = "1wk"    # 1-week interval, 2-year period
    ONE_MONTH = "1mo"   # 1-month interval, 6-year period


class CandlestickData(Base):
    """CandlestickData model for MyStock application.
    
    Stores historical OHLCV data for candlestick charts with 5 period options.
    
    Attributes:
        id: Primary key, auto-incrementing integer
        symbol: Stock ticker symbol
        period: Data interval (30m, 1h, 1d, 1wk, 1mo)
        date: Candle timestamp
        open: Opening price
        high: Highest price in period
        low: Lowest price in period
        close: Closing price
        adj_close: Adjusted close (for splits/dividends)
        volume: Trading volume
        created_at: When data was fetched
        
    Period Mappings:
        - 30m interval → 2 day period
        - 1h interval → 1 week period
        - 1d interval → 6 month period
        - 1wk interval → 2 year period
        - 1mo interval → 7 year period
    """
    
    __tablename__ = "candlestick_data"
    __table_args__ = (
        UniqueConstraint("symbol", "period", "date", name="uk_symbol_period_date"),
        {"comment": "Historical OHLCV data for candlestick charts"}
    )
    
    # Primary Key
    id = Column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        comment="Candlestick data ID (primary key)"
    )
    
    # Stock Information
    symbol = Column(
        String(20),
        nullable=False,
        index=True,
        comment="Stock ticker symbol"
    )
    
    period = Column(
        String(10),  # Changed from Enum(Period) to String for MySQL compatibility
        nullable=False,
        index=True,
        comment="Data interval (30m/1h/1d/1wk/1mo)"
    )
    
    date = Column(
        DateTime,
        nullable=False,
        index=True,
        comment="Candle timestamp"
    )
    
    # OHLC Data
    open = Column(
        DECIMAL(15, 4),
        nullable=False,
        comment="Opening price"
    )
    
    high = Column(
        DECIMAL(15, 4),
        nullable=False,
        comment="Highest price in period"
    )
    
    low = Column(
        DECIMAL(15, 4),
        nullable=False,
        comment="Lowest price in period"
    )
    
    close = Column(
        DECIMAL(15, 4),
        nullable=False,
        comment="Closing price"
    )
    
    adj_close = Column(
        DECIMAL(15, 4),
        nullable=True,
        comment="Adjusted close (for splits/dividends)"
    )
    
    # Volume
    volume = Column(
        BigInt,
        nullable=False,
        comment="Trading volume"
    )
    
    # Timestamp
    created_at = Column(
        TIMESTAMP,
        server_default=func.now(),
        nullable=False,
        comment="When data was fetched"
    )
    
    def __repr__(self) -> str:
        """String representation of CandlestickData object."""
        return f"<CandlestickData(symbol='{self.symbol}', period='{self.period.value}', date={self.date}, close={self.close})>"
    
    @classmethod
    def get_period_mapping(cls) -> dict:
        """Get period to yfinance parameter mapping.
        
        Returns:
            Dictionary mapping Period enum to (period, interval) tuples
        """
        return {
            Period.FIVE_MIN: ("1d", "5m"),      # 5분봉 1일
            Period.ONE_HOUR: ("1mo", "1h"),     # 1시간봉 1개월 (30일)
            Period.ONE_DAY: ("3mo", "1d"),      # 1일봉 3개월
            Period.ONE_WEEK: ("2y", "1wk"),     # 1주봉 2년
            Period.ONE_MONTH: ("5y", "1mo"),    # 1월봉 5년 (6년은 지원 안함)
        }
