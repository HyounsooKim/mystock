"""Stock data API endpoints.

Handles stock quote retrieval and candlestick chart data without caching (Cosmos DB migration).
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from datetime import datetime, timedelta
from typing import Optional

from src.core.database import get_db
from src.core.config import settings
# Legacy SQLAlchemy models (commented out for Cosmos DB migration)
# from src.models import StockQuote, CandlestickData
# from src.models.stock_quote import MarketStatus, Market
# from src.models.candlestick_data import Period
from src.schemas.stocks import (
    PeriodEnum,
    StockQuoteResponse,
    CandlestickResponse,
    ChartDataResponse,
    NewsResponse,
    NewsItemResponse,
    TopMoversResponse,
    TopMoverItem,
)
from src.services.stock_data_service import StockDataService


router = APIRouter()

# Create a singleton instance of StockDataService
stock_service = StockDataService()


@router.get("/{symbol}", response_model=StockQuoteResponse)
async def get_stock_quote(symbol: str):
    """Get stock quote directly from Alpha Vantage API (no caching).
    
    Fetches current stock price, daily change, volume, and market status.
    
    Args:
        symbol: Stock ticker symbol (e.g., 'AAPL', 'TSLA')
        
    Returns:
        Stock quote data
        
    Raises:
        HTTPException 404: If symbol not found or invalid
    """
    symbol = symbol.upper()
    
    # Fetch from Alpha Vantage
    quote_data = stock_service.get_quote(symbol)
    
    if not quote_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Stock symbol '{symbol}' not found or data unavailable"
        )
    
    return StockQuoteResponse(
        symbol=symbol,
        current_price=quote_data.get('current_price'),
        daily_change_pct=quote_data.get('daily_change_pct'),
        volume=quote_data.get('volume'),
        market_status=quote_data.get('market_status', 'unknown'),
        market=quote_data.get('market', 'US'),
        updated_at=datetime.utcnow()
    )


@router.get("/{symbol}/chart", response_model=ChartDataResponse)
async def get_chart_data(
    symbol: str,
    period: PeriodEnum = Query(..., description="Chart period (5m/1h/1d/1wk/1mo)")
):
    """Get candlestick chart data for a stock.
    
    Fetches OHLCV (Open, High, Low, Close, Volume) data directly from Alpha Vantage.
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
    
    # Fetch directly from Alpha Vantage (no caching)
    # Pass the Period enum directly, not the value
    candle_data = stock_service.get_candlestick_data(symbol, period)
    
    if not candle_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chart data not available for symbol '{symbol}' with period '{period.value}'"
        )
    
    # Convert to response format
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
    
    Fetches recent news articles directly from Alpha Vantage API.
    No database caching is used for news data.
    
    Args:
        symbol: Stock ticker symbol (e.g., 'AAPL', 'IBM')
        limit: Number of articles to return (default: 10, max: 100)
        
    Returns:
        List of news articles with title, summary, publisher, link, thumbnail, and publication date
        Sorted by publication date in descending order (newest first)
    """
    symbol = symbol.upper()
    
    # Fetch news directly from Alpha Vantage via StockDataService (no DB involved)
    news_data = stock_service.get_news(symbol, limit=limit)
    
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


@router.get("/market/top-movers", response_model=TopMoversResponse)
async def get_top_movers():
    """Get top gainers, losers, and most actively traded stocks.
    
    Fetches the top 20 gaining, losing, and most actively traded US stocks
    from Alpha Vantage API. This data is updated periodically by Alpha Vantage.
    
    Returns:
        Top movers data with gainers, losers, and most actively traded lists
        
    Raises:
        HTTPException 503: If data is unavailable from Alpha Vantage
    """
    # Fetch top movers directly from Alpha Vantage
    movers_data = stock_service.get_top_movers()
    
    if not movers_data:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Top movers data is currently unavailable. Please try again later."
        )
    
    # Convert to response format
    top_gainers = [
        TopMoverItem(
            ticker=item['ticker'],
            price=item['price'],
            change_amount=item['change_amount'],
            change_percentage=item['change_percentage'],
            volume=item['volume']
        )
        for item in movers_data.get('top_gainers', [])
    ]
    
    top_losers = [
        TopMoverItem(
            ticker=item['ticker'],
            price=item['price'],
            change_amount=item['change_amount'],
            change_percentage=item['change_percentage'],
            volume=item['volume']
        )
        for item in movers_data.get('top_losers', [])
    ]
    
    most_actively_traded = [
        TopMoverItem(
            ticker=item['ticker'],
            price=item['price'],
            change_amount=item['change_amount'],
            change_percentage=item['change_percentage'],
            volume=item['volume']
        )
        for item in movers_data.get('most_actively_traded', [])
    ]
    
    return TopMoversResponse(
        metadata=movers_data.get('metadata', 'Top gainers, losers, and most actively traded US tickers'),
        last_updated=movers_data.get('last_updated', ''),
        top_gainers=top_gainers,
        top_losers=top_losers,
        most_actively_traded=most_actively_traded
    )
