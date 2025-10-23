"""Stock data service using Alpha Vantage API.

Provides functions to fetch stock quotes and candlestick data from Alpha Vantage.
"""

import requests
import os
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import logging

from src.schemas.stocks import MarketEnum as Market, MarketStatusEnum as MarketStatus, PeriodEnum as Period
# from src.models.stock_quote import Market, MarketStatus
# from src.models.candlestick_data import Period, CandlestickData


logger = logging.getLogger(__name__)


class StockDataService:
    """Service for fetching stock data from Alpha Vantage API."""
    
    BASE_URL = "https://www.alphavantage.co/query"
    
    def __init__(self):
        """Initialize Alpha Vantage service with API key from environment."""
        self.api_key = os.getenv("ALPHA_VANTAGE_API_KEY")
        if not self.api_key:
            logger.warning("ALPHA_VANTAGE_API_KEY not found in environment variables")
        else:
            logger.info(f"Alpha Vantage API key loaded: {self.api_key[:4]}...{self.api_key[-4:]}")
        
        # Check if delayed data should be used (default: true)
        use_delayed_str = os.getenv("ALPHA_VANTAGE_USE_DELAYED", "true").lower()
        self.use_delayed = use_delayed_str in ("true", "1", "yes")
        
        if self.use_delayed:
            logger.info("Alpha Vantage: Using delayed data (15min delay, higher rate limit)")
        else:
            logger.info("Alpha Vantage: Using realtime data (lower rate limit)")
    
    @staticmethod
    def _convert_symbol(symbol: str) -> str:
        """Convert Korean stock symbols to Alpha Vantage format.
        
        Korean stocks use .KS (KOSPI) or .KQ (KOSDAQ) suffixes.
        Alpha Vantage might not support all Korean stocks.
        """
        # For now, return as-is. Alpha Vantage primarily supports US markets.
        # Korean stocks may need special handling or alternative API
        return symbol
    
    @staticmethod
    def _determine_market_status() -> MarketStatus:
        """Determine if US market is currently open.
        
        Simple heuristic: Check if current time is within market hours (9:30-16:00 ET).
        For production, consider using market calendar API.
        """
        now = datetime.utcnow()
        # Convert to ET (UTC-5 or UTC-4 during DST)
        # This is a simplified check
        hour = now.hour - 5  # Approximate ET time
        
        # Market hours: 9:30 AM - 4:00 PM ET (14:30 - 21:00 UTC during EST)
        if 14 <= hour < 21:
            return MarketStatus.OPEN
        return MarketStatus.CLOSED
    
    def get_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Fetch current stock quote from Alpha Vantage.
        
        Args:
            symbol: Stock ticker symbol (e.g., 'AAPL', 'IBM')
            
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
            converted_symbol = self._convert_symbol(symbol)
            
            params = {
                "function": "GLOBAL_QUOTE",
                "symbol": converted_symbol,
                "apikey": self.api_key
            }
            
            # Add entitlement parameter if using delayed data
            if self.use_delayed:
                params["entitlement"] = "delayed"
            
            response = requests.get(self.BASE_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Check for API errors
            if "Error Message" in data:
                logger.error(f"Alpha Vantage error for {symbol}: {data['Error Message']}")
                return None
            
            if "Note" in data:
                logger.warning(f"Alpha Vantage rate limit for {symbol}: {data['Note']}")
                return None
            
            # Handle both realtime and delayed response keys
            quote = None
            if "Global Quote" in data:
                quote = data["Global Quote"]
            elif "Global Quote - DATA DELAYED BY 15 MINUTES" in data:
                quote = data["Global Quote - DATA DELAYED BY 15 MINUTES"]
            
            if not quote:
                logger.warning(f"No quote data found for symbol: {symbol}")
                return None
            
            # Determine market (KR or US)
            market = Market.KR if symbol.endswith(('.KS', '.KQ')) else Market.US
            
            # Determine market status
            market_status = self._determine_market_status()
            
            # Parse quote data
            current_price = float(quote.get("05. price", 0))
            change_pct = float(quote.get("10. change percent", "0").replace("%", ""))
            volume = int(quote.get("06. volume", 0))
            previous_close = float(quote.get("08. previous close", current_price))
            
            return {
                'symbol': symbol,
                'current_price': current_price,
                'daily_change_pct': round(change_pct, 4),
                'volume': volume,
                'market_status': market_status,
                'market': market,
                'cache_data': {
                    'regularMarketPrice': current_price,
                    'regularMarketChangePercent': change_pct,
                    'regularMarketVolume': volume,
                    'previousClose': previous_close,
                    'open': quote.get("02. open"),
                    'high': quote.get("03. high"),
                    'low': quote.get("04. low"),
                    'latestTradingDay': quote.get("07. latest trading day"),
                }
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error fetching quote for {symbol}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error fetching quote for {symbol}: {str(e)}")
            return None
    
    @staticmethod
    def _get_function_and_interval(period: Period) -> tuple[str, Optional[str]]:
        """Map Period enum to Alpha Vantage function and interval.
        
        Returns:
            Tuple of (function_name, interval) for Alpha Vantage API
        """
        mapping = {
            Period.FIVE_MIN: ("TIME_SERIES_INTRADAY", "5min"),
            Period.ONE_HOUR: ("TIME_SERIES_INTRADAY", "60min"),
            Period.ONE_DAY: ("TIME_SERIES_DAILY", None),
            Period.ONE_WEEK: ("TIME_SERIES_WEEKLY", None),
            Period.ONE_MONTH: ("TIME_SERIES_MONTHLY", None),
        }
        return mapping.get(period, ("TIME_SERIES_DAILY", None))
    
    @staticmethod
    def _get_time_series_key(function: str, interval: Optional[str] = None) -> str:
        """Get the time series key name from API response.
        
        Args:
            function: Alpha Vantage function name
            interval: Interval for intraday data
            
        Returns:
            Key name for accessing time series data in response
        """
        if function == "TIME_SERIES_INTRADAY":
            return f"Time Series ({interval})"
        elif function == "TIME_SERIES_DAILY":
            return "Time Series (Daily)"
        elif function == "TIME_SERIES_WEEKLY":
            return "Weekly Time Series"
        elif function == "TIME_SERIES_MONTHLY":
            return "Monthly Time Series"
        return "Time Series (Daily)"
    
    @staticmethod
    def _get_max_points(period: Period) -> int:
        """Get maximum number of data points to return based on period."""
        limits = {
            Period.FIVE_MIN: 100,
            Period.ONE_HOUR: 100,
            Period.ONE_DAY: 100,
            Period.ONE_WEEK: 52,
            Period.ONE_MONTH: 24,
        }
        return limits.get(period, 100)
    
    def get_candlestick_data(
        self, 
        symbol: str, 
        period: Period
    ) -> Optional[List[Dict[str, Any]]]:
        """Fetch candlestick (OHLCV) data from Alpha Vantage.
        
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
            converted_symbol = self._convert_symbol(symbol)
            function, interval = self._get_function_and_interval(period)
            
            params = {
                "function": function,
                "symbol": converted_symbol,
                "apikey": self.api_key
            }
            
            # Add interval for intraday data
            if interval:
                params["interval"] = interval
            
            # For intraday, request full outputsize
            if function == "TIME_SERIES_INTRADAY":
                params["outputsize"] = "full"
            
            # Add entitlement parameter if using delayed data
            if self.use_delayed:
                params["entitlement"] = "delayed"
            
            logger.info(f"Requesting candlestick data for {symbol} with params: {params}")
            
            response = requests.get(self.BASE_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Check for API errors
            if "Error Message" in data:
                logger.error(f"Alpha Vantage error for {symbol}: {data['Error Message']}")
                return None
            
            if "Note" in data:
                logger.warning(f"Alpha Vantage rate limit for {symbol}: {data['Note']}")
                return None
            
            # Get time series data
            time_series_key = self._get_time_series_key(function, interval)
            
            if time_series_key not in data:
                logger.warning(f"No candlestick data found for {symbol} with period {period.value}")
                return None
            
            time_series = data[time_series_key]
            
            # Convert to list of dictionaries
            candlesticks = []
            max_points = self._get_max_points(period)
            
            for date_str, values in list(time_series.items())[:max_points]:
                try:
                    # Parse date string (format: "2024-01-20" or "2024-01-20 10:00:00")
                    if " " in date_str:
                        date_obj = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
                    else:
                        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                    
                    candlesticks.append({
                        'date': date_obj,
                        'open': float(values.get('1. open', 0)),
                        'high': float(values.get('2. high', 0)),
                        'low': float(values.get('3. low', 0)),
                        'close': float(values.get('4. close', 0)),
                        'adj_close': float(values.get('4. close', 0)),  # Alpha Vantage adjusted close same as close
                        'volume': int(values.get('5. volume', 0))
                    })
                except (ValueError, KeyError) as e:
                    logger.warning(f"Failed to parse candlestick data for {date_str}: {e}")
                    continue
            
            # Sort by date ascending (oldest first)
            candlesticks.sort(key=lambda x: x['date'])
            
            logger.info(f"Fetched {len(candlesticks)} candlesticks for {symbol} ({period.value})")
            return candlesticks
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error fetching candlestick data for {symbol}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error fetching candlestick data for {symbol}: {str(e)}")
            return None
    
    def validate_symbol(self, symbol: str) -> bool:
        """Validate if a symbol exists in Alpha Vantage.
        
        Args:
            symbol: Stock ticker symbol
            
        Returns:
            True if symbol exists, False otherwise
        """
        try:
            # Use SYMBOL_SEARCH to validate
            params = {
                "function": "SYMBOL_SEARCH",
                "keywords": symbol,
                "apikey": self.api_key
            }
            
            # Add entitlement parameter if using delayed data
            if self.use_delayed:
                params["entitlement"] = "delayed"
            
            response = requests.get(self.BASE_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if "bestMatches" in data and data["bestMatches"]:
                # Check if exact symbol match exists
                for match in data["bestMatches"]:
                    if match.get("1. symbol", "").upper() == symbol.upper():
                        return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error validating symbol {symbol}: {str(e)}")
            return False
    
    def search_symbol(self, keywords: str) -> List[Dict[str, Any]]:
        """Search for stock symbols matching keywords.
        
        Args:
            keywords: Search keywords (company name or symbol)
            
        Returns:
            List of matching symbols with company info
        """
        try:
            params = {
                "function": "SYMBOL_SEARCH",
                "keywords": keywords,
                "apikey": self.api_key
            }
            
            # Add entitlement parameter if using delayed data
            if self.use_delayed:
                params["entitlement"] = "delayed"
            
            response = requests.get(self.BASE_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if "bestMatches" not in data:
                return []
            
            results = []
            for match in data["bestMatches"]:
                results.append({
                    'symbol': match.get("1. symbol", ""),
                    'name': match.get("2. name", ""),
                    'type': match.get("3. type", ""),
                    'region': match.get("4. region", ""),
                    'currency': match.get("8. currency", ""),
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching symbols for '{keywords}': {str(e)}")
            return []
    
    def get_news(self, symbol: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Fetch recent news articles for a stock from Alpha Vantage.
        
        Args:
            symbol: Stock ticker symbol (e.g., 'AAPL', 'IBM')
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
            
            converted_symbol = self._convert_symbol(symbol)
            
            params = {
                "function": "NEWS_SENTIMENT",
                "tickers": converted_symbol,
                "limit": min(limit, 50),  # Alpha Vantage max is 50
                "apikey": self.api_key
            }
            
            # Add entitlement parameter if using delayed data
            if self.use_delayed:
                params["entitlement"] = "delayed"
            
            response = requests.get(self.BASE_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Check for API errors
            if "Error Message" in data:
                logger.error(f"Alpha Vantage error for {symbol}: {data['Error Message']}")
                return []
            
            if "Note" in data:
                logger.warning(f"Alpha Vantage rate limit for {symbol}: {data['Note']}")
                return []
            
            if "feed" not in data or not data["feed"]:
                logger.warning(f"No news found for symbol: {symbol}")
                return []
            
            logger.info(f"Retrieved {len(data['feed'])} news items from Alpha Vantage for {symbol}")
            
            # Convert news data to structured format
            news_items = []
            for idx, item in enumerate(data["feed"]):
                try:
                    title = item.get('title', '')
                    summary = item.get('summary', '')
                    source = item.get('source', 'Unknown')
                    url = item.get('url', '#')
                    banner_image = item.get('banner_image')
                    time_published = item.get('time_published', '')
                    
                    # Skip if title is missing
                    if not title:
                        logger.warning(f"Skipping news item {idx}: missing title")
                        continue
                    
                    # Parse timestamp: Alpha Vantage format "20250120T011450"
                    published_at = None
                    if time_published:
                        try:
                            published_at = datetime.strptime(time_published, "%Y%m%dT%H%M%S")
                        except (ValueError, TypeError) as e:
                            logger.warning(f"Failed to parse timestamp '{time_published}': {e}")
                            published_at = datetime.now()
                    else:
                        published_at = datetime.now()
                    
                    # Extract sentiment for the specific ticker
                    sentiment_score = None
                    sentiment_label = None
                    if 'ticker_sentiment' in item:
                        for sentiment in item['ticker_sentiment']:
                            if sentiment.get('ticker', '').upper() == symbol.upper():
                                sentiment_score = sentiment.get('ticker_sentiment_score')
                                sentiment_label = sentiment.get('ticker_sentiment_label')
                                break
                    
                    news_item = {
                        'title': title,
                        'summary': summary if summary else '',
                        'publisher': source,
                        'link': url,
                        'thumbnail_url': banner_image,
                        'published_at': published_at,
                        'sentiment_score': sentiment_score,
                        'sentiment_label': sentiment_label,
                    }
                    news_items.append(news_item)
                    
                except Exception as item_error:
                    logger.error(f"Failed to process news item {idx} for {symbol}: {item_error}")
                    continue
            
            # Sort by published_at in descending order (newest first)
            news_items.sort(key=lambda x: x['published_at'], reverse=True)
            
            # Limit the results
            news_items = news_items[:limit]
            
            logger.info(f"Successfully processed {len(news_items)} news articles for {symbol}")
            return news_items
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error fetching news for {symbol}: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Error fetching news for {symbol}: {str(e)}")
            return []
    
    def get_company_overview(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Fetch company overview including market cap from Alpha Vantage.
        
        Args:
            symbol: Stock ticker symbol (e.g., 'AAPL', 'IBM')
            
        Returns:
            Dictionary with company information including market cap, or None if fetch fails
        """
        try:
            logger.info(f"Fetching company overview for symbol: {symbol}")
            
            converted_symbol = self._convert_symbol(symbol)
            
            params = {
                "function": "OVERVIEW",
                "symbol": converted_symbol,
                "apikey": self.api_key
            }
            
            # Add entitlement parameter if using delayed data
            if self.use_delayed:
                params["entitlement"] = "delayed"
            
            response = requests.get(self.BASE_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Check for API errors
            if "Error Message" in data:
                logger.error(f"Alpha Vantage error for {symbol}: {data['Error Message']}")
                return None
            
            if "Note" in data:
                logger.warning(f"Alpha Vantage rate limit for {symbol}: {data['Note']}")
                return None
            
            if not data or "Symbol" not in data:
                logger.warning(f"No company overview data found for symbol: {symbol}")
                return None
            
            # Extract relevant information
            market_cap_str = data.get("MarketCapitalization", "0")
            try:
                market_cap = int(market_cap_str) if market_cap_str and market_cap_str != "None" else None
            except (ValueError, TypeError):
                market_cap = None
            
            return {
                'symbol': data.get("Symbol"),
                'name': data.get("Name"),
                'description': data.get("Description"),
                'sector': data.get("Sector"),
                'industry': data.get("Industry"),
                'market_cap': market_cap,
                'pe_ratio': data.get("PERatio"),
                'dividend_yield': data.get("DividendYield"),
                'eps': data.get("EPS"),
                '52_week_high': data.get("52WeekHigh"),
                '52_week_low': data.get("52WeekLow"),
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error fetching company overview for {symbol}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error fetching company overview for {symbol}: {str(e)}")
            return None
    
    def get_top_movers(self) -> Optional[Dict[str, Any]]:
        """Fetch top gainers, losers, and most actively traded stocks from Alpha Vantage.
        
        Returns:
            Dictionary with top_gainers, top_losers, and most_actively_traded lists,
            or None if fetch fails
            
        Example:
            {
                'metadata': 'Top gainers, losers, and most actively traded US tickers',
                'last_updated': '2025-10-21 16:16:00 US/Eastern',
                'top_gainers': [...],
                'top_losers': [...],
                'most_actively_traded': [...]
            }
        """
        try:
            logger.info("Fetching top movers from Alpha Vantage")
            
            params = {
                "function": "TOP_GAINERS_LOSERS",
                "apikey": self.api_key
            }
            
            # Add entitlement parameter if using delayed data
            if self.use_delayed:
                params["entitlement"] = "delayed"
            
            response = requests.get(self.BASE_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Check for API errors
            if "Error Message" in data:
                logger.error(f"Alpha Vantage error: {data['Error Message']}")
                return None
            
            if "Note" in data:
                logger.warning(f"Alpha Vantage rate limit: {data['Note']}")
                return None
            
            # Validate required fields exist
            if "top_gainers" not in data or "top_losers" not in data or "most_actively_traded" not in data:
                logger.warning("Missing required fields in top movers response")
                return None
            
            logger.info(f"Successfully fetched top movers: {len(data['top_gainers'])} gainers, "
                       f"{len(data['top_losers'])} losers, {len(data['most_actively_traded'])} active")
            
            return {
                'metadata': data.get('metadata', 'Top gainers, losers, and most actively traded US tickers'),
                'last_updated': data.get('last_updated', ''),
                'top_gainers': data.get('top_gainers', []),
                'top_losers': data.get('top_losers', []),
                'most_actively_traded': data.get('most_actively_traded', [])
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error fetching top movers: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error fetching top movers: {str(e)}")
            return None
