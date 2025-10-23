"""Pydantic schemas for stock data endpoints.

Request/response models for stock quotes and candlestick data.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class PeriodEnum(str, Enum):
    """Chart period options."""
    FIVE_MIN = "5m"
    ONE_HOUR = "1h"
    ONE_DAY = "1d"
    ONE_WEEK = "1wk"
    ONE_MONTH = "1mo"


class MarketEnum(str, Enum):
    """Stock market region."""
    KR = "KR"  # Korea (KOSPI, KOSDAQ)
    US = "US"  # United States (NYSE, NASDAQ)


class MarketStatusEnum(str, Enum):
    """Market trading status."""
    OPEN = "open"
    CLOSED = "closed"


class StockQuoteResponse(BaseModel):
    """Stock quote response schema."""
    
    symbol: str = Field(..., description="Stock ticker symbol")
    current_price: float = Field(..., description="Current stock price")
    daily_change_pct: float = Field(..., description="Daily change percentage")
    volume: Optional[int] = Field(None, description="Trading volume")
    market_status: MarketStatusEnum = Field(..., description="Market open/closed status")
    market: MarketEnum = Field(..., description="Market region (KR/US)")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "symbol": "AAPL",
                "current_price": 175.50,
                "daily_change_pct": 1.25,
                "volume": 50000000,
                "market_status": "CLOSED",
                "market": "US",
                "updated_at": "2024-01-20T15:30:00"
            }
        }


class CandlestickResponse(BaseModel):
    """Single candlestick data point."""
    
    date: datetime = Field(..., description="Candle timestamp")
    open: float = Field(..., description="Opening price")
    high: float = Field(..., description="Highest price")
    low: float = Field(..., description="Lowest price")
    close: float = Field(..., description="Closing price")
    volume: int = Field(..., description="Trading volume")
    
    class Config:
        json_schema_extra = {
            "example": {
                "date": "2024-01-20T10:00:00",
                "open": 175.00,
                "high": 176.50,
                "low": 174.80,
                "close": 175.50,
                "volume": 1000000
            }
        }


class ChartDataResponse(BaseModel):
    """Chart data response with candlesticks."""
    
    symbol: str = Field(..., description="Stock ticker symbol")
    period: PeriodEnum = Field(..., description="Data interval")
    candlesticks: List[CandlestickResponse] = Field(..., description="OHLCV data points")
    total: int = Field(..., description="Total number of candlesticks")
    
    class Config:
        json_schema_extra = {
            "example": {
                "symbol": "AAPL",
                "period": "1d",
                "candlesticks": [
                    {
                        "date": "2024-01-20T10:00:00",
                        "open": 175.00,
                        "high": 176.50,
                        "low": 174.80,
                        "close": 175.50,
                        "volume": 1000000
                    }
                ],
                "total": 120
            }
        }


class NewsItemResponse(BaseModel):
    """Single news article response."""
    
    title: str = Field(..., description="뉴스 제목")
    summary: str = Field(..., description="뉴스 요약")
    publisher: str = Field(..., description="뉴스 출처/출판사")
    link: str = Field(..., description="뉴스 기사 URL")
    thumbnail_url: Optional[str] = Field(None, description="썸네일 이미지 URL")
    published_at: Optional[datetime] = Field(None, description="게시 일시")
    
    class Config:
        json_schema_extra = {
            "example": {
                "title": "Apple announces new product launch",
                "summary": "Apple announced a new product line today...",
                "publisher": "Reuters",
                "link": "https://example.com/article",
                "thumbnail_url": "https://example.com/image.jpg",
                "published_at": "2024-01-20T10:00:00"
            }
        }


class NewsResponse(BaseModel):
    """Stock news response."""
    
    symbol: str = Field(..., description="Stock ticker symbol")
    news: List[NewsItemResponse] = Field(..., description="List of news articles")
    total: int = Field(..., description="Total number of news items")
    
    class Config:
        json_schema_extra = {
            "example": {
                "symbol": "AAPL",
                "news": [
                    {
                        "title": "Apple announces new product launch",
                        "link": "https://example.com/article",
                        "publisher": "Reuters",
                        "published_at": "2024-01-20T10:00:00"
                    }
                ],
                "total": 10
            }
        }


class StockMoverItem(BaseModel):
    """Single stock mover item (gainer/loser/active)."""
    
    ticker: str = Field(..., description="Stock ticker symbol")
    price: str = Field(..., description="Current stock price")
    change_amount: str = Field(..., description="Price change amount")
    change_percentage: str = Field(..., description="Percentage change with % sign")
    volume: str = Field(..., description="Trading volume")
    
    class Config:
        json_schema_extra = {
            "example": {
                "ticker": "BYND",
                "price": "3.62",
                "change_amount": "2.15",
                "change_percentage": "146.2585%",
                "volume": "1812070328"
            }
        }


class TopMoversResponse(BaseModel):
    """Top movers (gainers, losers, most active) response."""
    
    metadata: str = Field(..., description="Response metadata")
    last_updated: str = Field(..., description="Last update timestamp")
    top_gainers: List[StockMoverItem] = Field(..., description="Top gaining stocks")
    top_losers: List[StockMoverItem] = Field(..., description="Top losing stocks")
    most_actively_traded: List[StockMoverItem] = Field(..., description="Most actively traded stocks")
    
    class Config:
        json_schema_extra = {
            "example": {
                "metadata": "Top gainers, losers, and most actively traded US tickers",
                "last_updated": "2025-10-21 16:16:00 US/Eastern",
                "top_gainers": [
                    {
                        "ticker": "BYND",
                        "price": "3.62",
                        "change_amount": "2.15",
                        "change_percentage": "146.2585%",
                        "volume": "1812070328"
                    }
                ],
                "top_losers": [],
                "most_actively_traded": []
            }
        }
