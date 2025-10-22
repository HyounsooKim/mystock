"""Alpha Vantage API service for stock data.

Provides functions to fetch stock quotes and candlestick data from Alpha Vantage API.
"""

import requests
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import logging
import os

from src.models.stock_quote import Market, MarketStatus
from src.models.candlestick_data import Period


logger = logging.getLogger(__name__)


class AlphaVantageService:
    """Service for fetching stock data from Alpha Vantage API."""
    
    BASE_URL = "https://www.alphavantage.co/query"
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize Alpha Vantage service.
        
        Args:
            api_key: Alpha Vantage API key. If not provided, reads from env.
        """
        self.api_key = api_key or os.getenv('ALPHA_VANTAGE_API_KEY', 'XONR2H0Y7T34GNF4')
    
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
            # Convert Korean stock symbols to Alpha Vantage format
            av_symbol = self._convert_symbol(symbol)
            
            params = {
                'function': 'GLOBAL_QUOTE',
                'symbol': av_symbol,
                'apikey': self.api_key
            }
            
            response = requests.get(self.BASE_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Check for error or no data
            if 'Error Message' in data:
                logger.error(f"Alpha Vantage error for {symbol}: {data['Error Message']}")
                return None
            
            if 'Note' in data:
                logger.warning(f"Alpha Vantage API limit reached: {data['Note']}")
                return None
            
            global_quote = data.get('Global Quote', {})
            if not global_quote:
                logger.warning(f"No quote data found for symbol: {symbol}")
                return None
            
            # Parse the quote data
            current_price = float(global_quote.get('05. price', 0))
            change_pct = float(global_quote.get('10. change percent', '0').rstrip('%'))
            volume = int(global_quote.get('06. volume', 0))
            previous_close = float(global_quote.get('08. previous close', current_price))
            
            # Determine market (KR or US)
            market = Market.KR if symbol.endswith(('.KS', '.KQ')) else Market.US
            
            # Alpha Vantage doesn't provide real-time market status
            # We'll determine it based on trading hours (simplified)
            market_status = self._determine_market_status(market)
            
            return {
                'symbol': symbol,
                'current_price': current_price,
                'daily_change_pct': round(change_pct, 4),
                'volume': volume,
                'market_status': market_status,
                'market': market,
                'cache_data': {
                    'regularMarketPrice': current_price,
                    'regularMarketChange': float(global_quote.get('09. change', 0)),
                    'regularMarketChangePercent': change_pct,
                    'regularMarketVolume': volume,
                    'previousClose': previous_close,
                    'high': float(global_quote.get('03. high', 0)),
                    'low': float(global_quote.get('04. low', 0)),
                    'open': float(global_quote.get('02. open', 0)),
                    'latestTradingDay': global_quote.get('07. latest trading day'),
                    'shortName': av_symbol,
                    'longName': av_symbol,
                }
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error fetching quote for {symbol}: {str(e)}")
            return None
        except (ValueError, KeyError) as e:
            logger.error(f"Error parsing quote data for {symbol}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching quote for {symbol}: {str(e)}")
            return None
    
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
        """
        try:
            av_symbol = self._convert_symbol(symbol)
            
            # Map Period to Alpha Vantage function and interval
            function, interval = self._get_function_and_interval(period)
            
            params = {
                'function': function,
                'symbol': av_symbol,
                'apikey': self.api_key
            }
            
            # Add interval for intraday data
            if function == 'TIME_SERIES_INTRADAY':
                params['interval'] = interval
                params['outputsize'] = 'full'  # Get more data points
            else:
                params['outputsize'] = 'full'
            
            response = requests.get(self.BASE_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Check for errors
            if 'Error Message' in data:
                logger.error(f"Alpha Vantage error for {symbol}: {data['Error Message']}")
                return None
            
            if 'Note' in data:
                logger.warning(f"Alpha Vantage API limit reached: {data['Note']}")
                return None
            
            # Get the time series data key
            time_series_key = self._get_time_series_key(function, interval)
            time_series = data.get(time_series_key, {})
            
            if not time_series:
                logger.warning(f"No candlestick data found for {symbol}")
                return None
            
            # Convert to our format
            candlesticks = []
            for timestamp_str, ohlcv in sorted(time_series.items(), reverse=True):
                try:
                    # Parse timestamp
                    timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S' if ' ' in timestamp_str else '%Y-%m-%d')
                    
                    candlestick = {
                        'timestamp': timestamp,
                        'open': float(ohlcv['1. open']),
                        'high': float(ohlcv['2. high']),
                        'low': float(ohlcv['3. low']),
                        'close': float(ohlcv['4. close']),
                        'volume': int(ohlcv['5. volume'])
                    }
                    candlesticks.append(candlestick)
                except (ValueError, KeyError) as e:
                    logger.warning(f"Error parsing candlestick data point: {str(e)}")
                    continue
            
            # Limit the number of data points based on period
            max_points = self._get_max_points(period)
            return candlesticks[:max_points]
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error fetching candlestick data for {symbol}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error fetching candlestick data for {symbol}: {str(e)}")
            return None
    
    def search_symbol(self, keywords: str) -> Optional[List[Dict[str, Any]]]:
        """Search for stock symbols using Alpha Vantage.
        
        Args:
            keywords: Search keywords (e.g., 'Apple', 'Samsung')
            
        Returns:
            List of matching symbols with details
        """
        try:
            params = {
                'function': 'SYMBOL_SEARCH',
                'keywords': keywords,
                'apikey': self.api_key
            }
            
            response = requests.get(self.BASE_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if 'Error Message' in data:
                logger.error(f"Alpha Vantage search error: {data['Error Message']}")
                return None
            
            matches = data.get('bestMatches', [])
            results = []
            
            for match in matches:
                results.append({
                    'symbol': match.get('1. symbol'),
                    'name': match.get('2. name'),
                    'type': match.get('3. type'),
                    'region': match.get('4. region'),
                    'marketOpen': match.get('5. marketOpen'),
                    'marketClose': match.get('6. marketClose'),
                    'timezone': match.get('7. timezone'),
                    'currency': match.get('8. currency'),
                    'matchScore': float(match.get('9. matchScore', 0))
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching symbols: {str(e)}")
            return None
    
    def get_news(self, symbol: str, limit: int = 50) -> Optional[List[Dict[str, Any]]]:
        """Fetch news and sentiment data for a stock.
        
        Args:
            symbol: Stock ticker symbol
            limit: Maximum number of news articles to return
            
        Returns:
            List of news articles with sentiment data
        """
        try:
            av_symbol = self._convert_symbol(symbol)
            
            params = {
                'function': 'NEWS_SENTIMENT',
                'tickers': av_symbol,
                'limit': min(limit, 1000),  # API max is 1000
                'apikey': self.api_key
            }
            
            response = requests.get(self.BASE_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if 'Error Message' in data:
                logger.error(f"Alpha Vantage news error: {data['Error Message']}")
                return None
            
            feed = data.get('feed', [])
            news_list = []
            
            for article in feed[:limit]:
                news_list.append({
                    'title': article.get('title'),
                    'url': article.get('url'),
                    'time_published': article.get('time_published'),
                    'authors': article.get('authors', []),
                    'summary': article.get('summary'),
                    'source': article.get('source'),
                    'category_within_source': article.get('category_within_source'),
                    'topics': [topic.get('topic') for topic in article.get('topics', [])],
                    'overall_sentiment_score': float(article.get('overall_sentiment_score', 0)),
                    'overall_sentiment_label': article.get('overall_sentiment_label'),
                })
            
            return news_list
            
        except Exception as e:
            logger.error(f"Error fetching news for {symbol}: {str(e)}")
            return None
    
    def _convert_symbol(self, symbol: str) -> str:
        """Convert stock symbol to Alpha Vantage format.
        
        Alpha Vantage primarily supports US stocks directly.
        Korean stocks need special handling or may not be available.
        
        Args:
            symbol: Original symbol (e.g., 'AAPL', '005930.KS')
            
        Returns:
            Converted symbol for Alpha Vantage
        """
        # Remove Korean exchange suffixes for now
        # Note: Alpha Vantage may not support Korean stocks directly
        if symbol.endswith('.KS') or symbol.endswith('.KQ'):
            logger.warning(f"Korean stock {symbol} may not be supported by Alpha Vantage")
            return symbol.split('.')[0]
        
        return symbol
    
    def _determine_market_status(self, market: Market) -> MarketStatus:
        """Determine if market is open based on current time.
        
        This is a simplified implementation. In production, you'd want
        to check actual market holidays and trading hours.
        
        Args:
            market: Market enum (US or KR)
            
        Returns:
            MarketStatus enum
        """
        now = datetime.now()
        weekday = now.weekday()  # 0=Monday, 6=Sunday
        
        # Weekend check
        if weekday >= 5:  # Saturday or Sunday
            return MarketStatus.CLOSED
        
        # For simplicity, assume closed (Alpha Vantage doesn't provide real-time status)
        return MarketStatus.CLOSED
    
    def _get_function_and_interval(self, period: Period) -> tuple[str, str]:
        """Map Period to Alpha Vantage function and interval.
        
        Args:
            period: Period enum
            
        Returns:
            Tuple of (function_name, interval)
        """
        period_map = {
            Period.THIRTY_MIN: ('TIME_SERIES_INTRADAY', '30min'),
            Period.ONE_HOUR: ('TIME_SERIES_INTRADAY', '60min'),
            Period.ONE_DAY: ('TIME_SERIES_DAILY', None),
            Period.ONE_WEEK: ('TIME_SERIES_WEEKLY', None),
            Period.ONE_MONTH: ('TIME_SERIES_MONTHLY', None),
        }
        
        return period_map.get(period, ('TIME_SERIES_DAILY', None))
    
    def _get_time_series_key(self, function: str, interval: Optional[str]) -> str:
        """Get the time series key from API response.
        
        Args:
            function: Alpha Vantage function name
            interval: Interval for intraday data
            
        Returns:
            Time series key to extract from response
        """
        if function == 'TIME_SERIES_INTRADAY':
            return f'Time Series ({interval})'
        elif function == 'TIME_SERIES_DAILY':
            return 'Time Series (Daily)'
        elif function == 'TIME_SERIES_WEEKLY':
            return 'Weekly Time Series'
        elif function == 'TIME_SERIES_MONTHLY':
            return 'Monthly Time Series'
        else:
            return 'Time Series (Daily)'
    
    def _get_max_points(self, period: Period) -> int:
        """Get maximum number of data points for a period.
        
        Args:
            period: Period enum
            
        Returns:
            Maximum number of candlestick data points
        """
        max_points_map = {
            Period.THIRTY_MIN: 100,
            Period.ONE_HOUR: 100,
            Period.ONE_DAY: 365,
            Period.ONE_WEEK: 104,  # ~2 years
            Period.ONE_MONTH: 60,  # ~5 years
        }
        
        return max_points_map.get(period, 100)


# Create a singleton instance
alpha_vantage_service = AlphaVantageService()
