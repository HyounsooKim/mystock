"""Stock data API endpoints.

Handles stock quote retrieval and candlestick chart data with caching.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional

from src.core.database import get_db
from src.core.config import settings
from src.models import StockQuote, CandlestickData
from src.models.stock_quote import MarketStatus, Market
from src.models.candlestick_data import Period
from src.schemas.stocks import (
    PeriodEnum,
    StockQuoteResponse,
    CandlestickResponse,
    ChartDataResponse,
    NewsResponse,
    NewsItemResponse,
)
from src.services.stock_data_service import StockDataService


router = APIRouter()


@router.get("/{symbol}", response_model=StockQuoteResponse)
async def get_stock_quote(
    symbol: str,
    db: Session = Depends(get_db)
):
    """Get stock quote with 5-minute cache.
    
    Fetches current stock price, daily change, volume, and market status.
    Uses cached data if less than 5 minutes old, otherwise fetches fresh data from yfinance.
    
    Args:
        symbol: Stock ticker symbol (e.g., 'AAPL', '005930.KS')
        db: Database session
        
    Returns:
        Stock quote data
        
    Raises:
        HTTPException 404: If symbol not found or invalid
    """
    symbol = symbol.upper()
    
    # Check cache (5-minute TTL)
    cache_ttl = timedelta(seconds=settings.STOCK_CACHE_TTL_SECONDS)
    cached_quote = db.query(StockQuote).filter(
        StockQuote.symbol == symbol,
        StockQuote.updated_at >= datetime.utcnow() - cache_ttl
    ).first()
    
    if cached_quote:
        return StockQuoteResponse(
            symbol=str(cached_quote.symbol),  # type: ignore
            current_price=float(cached_quote.current_price),  # type: ignore
            daily_change_pct=float(cached_quote.daily_change_pct),  # type: ignore
            volume=int(cached_quote.volume) if cached_quote.volume else None,  # type: ignore
            market_status=str(cached_quote.market_status),  # type: ignore
            market=str(cached_quote.market),  # type: ignore
            updated_at=cached_quote.updated_at  # type: ignore
        )
    
    # Cache miss - fetch from yfinance
    quote_data = StockDataService.get_quote(symbol)
    
    if not quote_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Stock symbol '{symbol}' not found or data unavailable"
        )
    
    # Update or create cache entry
    existing = db.query(StockQuote).filter(StockQuote.symbol == symbol).first()
    
    if existing:
        existing.current_price = quote_data['current_price']  # type: ignore
        existing.daily_change_pct = quote_data['daily_change_pct']  # type: ignore
        existing.volume = quote_data['volume']  # type: ignore
        existing.market_status = quote_data['market_status']  # type: ignore
        existing.market = quote_data['market']  # type: ignore
        existing.updated_at = datetime.utcnow()  # type: ignore
        existing.cache_data = quote_data['cache_data']  # type: ignore
        db.commit()
        db.refresh(existing)
        cached_quote = existing
    else:
        cached_quote = StockQuote(
            symbol=symbol,
            current_price=quote_data['current_price'],
            daily_change_pct=quote_data['daily_change_pct'],
            volume=quote_data['volume'],
            market_status=quote_data['market_status'],
            market=quote_data['market'],
            cache_data=quote_data['cache_data']
        )
        db.add(cached_quote)
        db.commit()
        db.refresh(cached_quote)
    
    return StockQuoteResponse(
        symbol=str(cached_quote.symbol),  # type: ignore
        current_price=float(cached_quote.current_price),  # type: ignore
        daily_change_pct=float(cached_quote.daily_change_pct),  # type: ignore
        volume=int(cached_quote.volume) if cached_quote.volume else None,  # type: ignore
        market_status=str(cached_quote.market_status),  # type: ignore
        market=str(cached_quote.market),  # type: ignore
        updated_at=cached_quote.updated_at  # type: ignore
    )


@router.get("/{symbol}/chart", response_model=ChartDataResponse)
async def get_chart_data(
    symbol: str,
    period: PeriodEnum = Query(..., description="Chart period (5m/1h/1d/1wk/1mo)")
):
    """Get candlestick chart data for a stock.
    
    Fetches OHLCV (Open, High, Low, Close, Volume) data directly from yfinance.
    No database caching is used - always fetches fresh data.
    
    Args:
        symbol: Stock ticker symbol
        period: Chart period/interval
        
    Returns:
        Chart data with candlesticks
        
    Raises:
        HTTPException 404: If symbol not found or no data available
    """
    symbol = symbol.upper()
    
    # Convert PeriodEnum to Period model enum
    period_map = {
        PeriodEnum.FIVE_MIN: Period.FIVE_MIN,
        PeriodEnum.ONE_HOUR: Period.ONE_HOUR,
        PeriodEnum.ONE_DAY: Period.ONE_DAY,
        PeriodEnum.ONE_WEEK: Period.ONE_WEEK,
        PeriodEnum.ONE_MONTH: Period.ONE_MONTH,
    }
    db_period = period_map[period]
    
    # Fetch directly from yfinance (no caching)
    candle_data = StockDataService.get_candlestick_data(symbol, db_period)
    
    if not candle_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chart data not available for symbol '{symbol}' with period '{period.value}'"
        )
    
    # Convert to response format (no database storage)
    candlesticks = [
        CandlestickResponse(
            date=candle['date'],
            open=candle['open'],
            high=candle['high'],
            low=candle['low'],
            close=candle['close'],
            volume=candle['volume']
        )
        for candle in candle_data
    ]
    
    return ChartDataResponse(
        symbol=symbol,
        period=period,
        candlesticks=candlesticks,
        total=len(candlesticks)
    )


@router.get("/{symbol}/news", response_model=NewsResponse)
async def get_stock_news(
    symbol: str,
    limit: int = Query(default=10, ge=1, le=100, description="Number of news articles to fetch")
):
    """Get news articles for a stock symbol.
    
    Fetches recent news articles directly from yfinance API.
    No database caching is used for news data.
    
    Args:
        symbol: Stock ticker symbol (e.g., 'AAPL', 'NVDA')
        limit: Number of articles to return (default: 10, max: 100)
        
    Returns:
        List of news articles with title, summary, publisher, link, thumbnail, and publication date
        Sorted by publication date in descending order (newest first)
    """
    symbol = symbol.upper()
    
    # Fetch news directly from yfinance via StockDataService (no DB involved)
    news_data = StockDataService.get_news(symbol, limit=limit)
    
    # news_data is always a list (empty list if no news)
    if news_data is None or len(news_data) == 0:
        # Return empty response instead of 404
        return NewsResponse(
            symbol=symbol,
            news=[],
            total=0
        )
    
    # Convert to response format
    news_items = [
        NewsItemResponse(
            title=item['title'],
            summary=item['summary'],
            publisher=item['publisher'],
            link=item['link'],
            thumbnail_url=item['thumbnail_url'],
            published_at=item['published_at']
        )
        for item in news_data
    ]
    
    return NewsResponse(
        symbol=symbol,
        news=news_items,
        total=len(news_items)
    )
