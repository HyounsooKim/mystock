"""Stock data service using yfinance API.

Provides functions to fetch stock quotes and candlestick data from yfinance.
"""

import yfinance as yf
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import logging

from src.models.stock_quote import Market, MarketStatus
from src.models.candlestick_data import Period, CandlestickData


logger = logging.getLogger(__name__)


class StockDataService:
    """Service for fetching stock data from yfinance."""
    
    @staticmethod
    def get_quote(symbol: str) -> Optional[Dict[str, Any]]:
        """Fetch current stock quote from yfinance.
        
        Args:
            symbol: Stock ticker symbol (e.g., 'AAPL', '005930.KS')
            
        Returns:
            Dictionary with quote data or None if fetch fails
            
        Example:
            {
                'symbol': 'AAPL',
                'current_price': 175.50,
                'daily_change_pct': 1.25,
                'volume': 50000000,
                'market_status': 'CLOSED',
                'market': 'US',
                'cache_data': {...}
            }
        """
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            if not info or 'regularMarketPrice' not in info:
                logger.warning(f"No data found for symbol: {symbol}")
                return None
            
            # Determine market (KR or US)
            market = Market.KR if symbol.endswith(('.KS', '.KQ')) else Market.US
            
            # Determine market status
            market_state = info.get('marketState', 'CLOSED').upper()
            market_status = MarketStatus.OPEN if market_state == 'REGULAR' else MarketStatus.CLOSED
            
            # Calculate daily change percentage
            regular_price = info.get('regularMarketPrice', 0)
            previous_close = info.get('previousClose', regular_price)
            daily_change = regular_price - previous_close
            daily_change_pct = (daily_change / previous_close * 100) if previous_close else 0
            
            return {
                'symbol': symbol,
                'current_price': regular_price,
                'daily_change_pct': round(daily_change_pct, 4),
                'volume': info.get('regularMarketVolume', 0),
                'market_status': market_status,
                'market': market,
                'cache_data': {
                    'regularMarketPrice': regular_price,
                    'regularMarketChange': daily_change,
                    'regularMarketChangePercent': daily_change_pct,
                    'regularMarketVolume': info.get('regularMarketVolume', 0),
                    'marketState': market_state,
                    'previousClose': previous_close,
                    'marketCap': info.get('marketCap'),
                    'currency': info.get('currency'),
                    'shortName': info.get('shortName'),
                    'longName': info.get('longName'),
                }
            }
            
        except Exception as e:
            logger.error(f"Error fetching quote for {symbol}: {str(e)}")
            return None
    
    @staticmethod
    def get_candlestick_data(
        symbol: str, 
        period: Period
    ) -> Optional[List[Dict[str, Any]]]:
        """Fetch candlestick (OHLCV) data from yfinance.
        
        Args:
            symbol: Stock ticker symbol
            period: Period enum (30m, 1h, 1d, 1wk, 1mo)
            
        Returns:
            List of candlestick data dictionaries or None if fetch fails
            
        Example:
            [
                {
                    'date': datetime(2024, 1, 20, 10, 0),
                    'open': 175.00,
                    'high': 176.50,
                    'low': 174.80,
                    'close': 175.50,
                    'adj_close': 175.50,
                    'volume': 1000000
                },
                ...
            ]
        """
        try:
            # Get period mapping
            period_map = CandlestickData.get_period_mapping()
            if period not in period_map:
                logger.error(f"Invalid period: {period}")
                return None
            
            yf_period, yf_interval = period_map[period]
            
            # Fetch data
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=yf_period, interval=yf_interval)
            
            if hist.empty:
                logger.warning(f"No candlestick data found for {symbol} with period {period.value}")
                return None
            
            # Convert DataFrame to list of dictionaries
            candlesticks = []
            for index, row in hist.iterrows():
                candlesticks.append({
                    'date': index.to_pydatetime() if hasattr(index, 'to_pydatetime') else index,  # type: ignore
                    'open': float(row['Open']),
                    'high': float(row['High']),
                    'low': float(row['Low']),
                    'close': float(row['Close']),
                    'adj_close': float(row['Close']),  # yfinance returns adjusted close
                    'volume': int(row['Volume'])
                })
            
            logger.info(f"Fetched {len(candlesticks)} candlesticks for {symbol} ({period.value})")
            return candlesticks
            
        except Exception as e:
            logger.error(f"Error fetching candlestick data for {symbol}: {str(e)}")
            return None
    
    @staticmethod
    def validate_symbol(symbol: str) -> bool:
        """Validate if a symbol exists in yfinance.
        
        Args:
            symbol: Stock ticker symbol
            
        Returns:
            True if symbol exists, False otherwise
        """
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # Check if we got valid data
            return bool(info and 'regularMarketPrice' in info)
            
        except Exception as e:
            logger.error(f"Error validating symbol {symbol}: {str(e)}")
            return False
    
    @staticmethod
    def get_news(symbol: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Fetch recent news articles for a stock from yfinance.
        
        Uses yfinance API directly without any database caching.
        
        Args:
            symbol: Stock ticker symbol (e.g., 'AAPL', 'NVDA')
            limit: Maximum number of news articles to return (default 10)
            
        Returns:
            List of news article dictionaries sorted by publish date (newest first)
            
        Example:
            [
                {
                    'title': 'Apple announces new product launch',
                    'summary': 'Apple today announced...',
                    'publisher': 'Reuters',
                    'link': 'https://example.com/article',
                    'thumbnail_url': 'https://example.com/image.jpg',
                    'published_at': datetime(2024, 1, 20, 10, 0)
                },
                ...
            ]
        """
        try:
            logger.info(f"Fetching {limit} news articles for symbol: {symbol}")
            
            # Create ticker object
            ticker = yf.Ticker(symbol)
            
            # Fetch news using .news property (yfinance 0.2.x)
            news_data = ticker.news
            
            if not news_data or len(news_data) == 0:
                logger.warning(f"No news found for symbol: {symbol}")
                return []
            
            logger.info(f"Retrieved {len(news_data)} news items from yfinance for {symbol}")
            
            # Convert news data to structured format
            news_items = []
            for idx, item in enumerate(news_data):  # Process all available items
                try:
                    # yfinance news structure: data is nested in 'content' object
                    content = item.get('content', {})
                    provider = content.get('provider', {})
                    canonical_url = content.get('canonicalUrl', {})
                    thumbnail = content.get('thumbnail', {})
                    
                    # Extract fields from the nested structure
                    title = content.get('title', '')
                    summary = content.get('summary', '')
                    publisher = provider.get('displayName', '')
                    link = canonical_url.get('url', '')
                    
                    # Get thumbnail URL
                    thumbnail_url = None
                    if thumbnail and 'originalUrl' in thumbnail:
                        thumbnail_url = thumbnail.get('originalUrl')
                    
                    # Get publication date from content.pubDate or displayTime (ISO format string)
                    pub_date_str = content.get('pubDate') or content.get('displayTime', '')
                    
                    # Skip if title is missing
                    if not title:
                        logger.warning(f"Skipping news item {idx}: missing title")
                        continue
                    
                    # Handle timestamp conversion
                    published_at = None
                    if pub_date_str:
                        try:
                            # Parse ISO 8601 format: '2025-10-20T01:14:50Z'
                            published_at = datetime.fromisoformat(pub_date_str.replace('Z', '+00:00'))
                        except (ValueError, TypeError) as e:
                            logger.warning(f"Failed to parse timestamp '{pub_date_str}' for news item {idx}: {e}")
                    
                    news_item = {
                        'title': title,
                        'summary': summary if summary else '',
                        'publisher': publisher if publisher else 'Unknown',
                        'link': link if link else '#',
                        'thumbnail_url': thumbnail_url,
                        'published_at': published_at if published_at else datetime.now()
                    }
                    news_items.append(news_item)
                    
                except Exception as item_error:
                    logger.error(f"Failed to process news item {idx} for {symbol}: {item_error}", exc_info=True)
                    continue
            
            # Sort by published_at in descending order (newest first)
            news_items.sort(key=lambda x: x['published_at'], reverse=True)
            
            # Limit the results
            news_items = news_items[:limit]
            
            logger.info(f"Successfully processed {len(news_items)} news articles for {symbol}")
            return news_items
            
        except Exception as e:
            logger.error(f"Error fetching news for {symbol}: {str(e)}", exc_info=True)
            return []
