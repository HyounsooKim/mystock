"""Tests for stock data API endpoints.

Tests stock quote and chart data endpoints with caching.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from src.models import StockQuote, CandlestickData
from src.models.stock_quote import MarketStatus, Market
from src.models.candlestick_data import Period


class TestGetStockQuote:
    """Tests for GET /api/v1/stocks/{symbol} endpoint."""
    
    @patch('src.services.stock_data_service.yf.Ticker')
    def test_get_quote_cache_miss(self, mock_ticker, client: TestClient, db: Session):
        """Test getting quote with cache miss (fetch from yfinance)."""
        # Mock yfinance response
        mock_info = {
            'regularMarketPrice': 175.50,
            'previousClose': 173.50,
            'regularMarketVolume': 50000000,
            'marketState': 'CLOSED',
            'currency': 'USD',
            'shortName': 'Apple Inc.'
        }
        mock_ticker.return_value.info = mock_info
        
        response = client.get("/api/v1/stocks/AAPL")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["symbol"] == "AAPL"
        assert data["current_price"] == 175.50
        assert abs(data["daily_change_pct"] - 1.1527) < 0.01  # (175.50 - 173.50) / 173.50 * 100
        assert data["volume"] == 50000000
        assert data["market_status"] == "CLOSED"
        assert data["market"] == "US"
        
        # Verify cached in database
        cached = db.query(StockQuote).filter(StockQuote.symbol == "AAPL").first()
        assert cached is not None
        assert cached.current_price == 175.50
    
    def test_get_quote_cache_hit(self, client: TestClient, db: Session):
        """Test getting quote with cache hit (no yfinance call)."""
        # Create cached quote (fresh, less than 5 minutes old)
        cached_quote = StockQuote(
            symbol="AAPL",
            current_price=175.50,
            daily_change_pct=1.15,
            volume=50000000,
            market_status=MarketStatus.CLOSED,
            market=Market.US,
            updated_at=datetime.utcnow(),
            cache_data={}
        )
        db.add(cached_quote)
        db.commit()
        
        response = client.get("/api/v1/stocks/AAPL")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["symbol"] == "AAPL"
        assert data["current_price"] == 175.50
        assert data["daily_change_pct"] == 1.15
    
    def test_get_quote_stale_cache(self, client: TestClient, db: Session):
        """Test getting quote with stale cache (>5 minutes old)."""
        # Create stale cached quote (6 minutes old)
        stale_time = datetime.utcnow() - timedelta(minutes=6)
        cached_quote = StockQuote(
            symbol="MSFT",
            current_price=300.00,
            daily_change_pct=0.5,
            volume=10000000,
            market_status=MarketStatus.CLOSED,
            market=Market.US,
            updated_at=stale_time,
            cache_data={}
        )
        db.add(cached_quote)
        db.commit()
        
        # Mock yfinance for fresh data
        with patch('src.services.stock_data_service.yf.Ticker') as mock_ticker:
            mock_info = {
                'regularMarketPrice': 305.00,
                'previousClose': 300.00,
                'regularMarketVolume': 12000000,
                'marketState': 'REGULAR',
                'currency': 'USD',
                'shortName': 'Microsoft'
            }
            mock_ticker.return_value.info = mock_info
            
            response = client.get("/api/v1/stocks/MSFT")
            
            assert response.status_code == 200
            data = response.json()
            
            # Should have fresh data
            assert data["current_price"] == 305.00
            assert data["market_status"] == "OPEN"  # REGULAR -> OPEN
    
    @patch('src.services.stock_data_service.yf.Ticker')
    def test_get_quote_korean_stock(self, mock_ticker, client: TestClient, db: Session):
        """Test getting quote for Korean stock (market detection)."""
        mock_info = {
            'regularMarketPrice': 75000.00,
            'previousClose': 74500.00,
            'regularMarketVolume': 10000000,
            'marketState': 'CLOSED',
            'currency': 'KRW',
            'shortName': 'Samsung Electronics'
        }
        mock_ticker.return_value.info = mock_info
        
        response = client.get("/api/v1/stocks/005930.KS")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["symbol"] == "005930.KS"
        assert data["market"] == "KR"  # Korean market detected
    
    @patch('src.services.stock_data_service.yf.Ticker')
    def test_get_quote_invalid_symbol(self, mock_ticker, client: TestClient):
        """Test getting quote for invalid symbol."""
        mock_ticker.return_value.info = {}  # Empty info = invalid
        
        response = client.get("/api/v1/stocks/INVALID")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestGetChartData:
    """Tests for GET /api/v1/stocks/{symbol}/chart endpoint."""
    
    @patch('src.services.stock_data_service.yf.Ticker')
    def test_get_chart_data_cache_miss(self, mock_ticker, client: TestClient, db: Session):
        """Test getting chart data with cache miss."""
        # Mock yfinance history response
        import pandas as pd
        mock_history = pd.DataFrame({
            'Open': [175.00, 176.00],
            'High': [176.50, 177.00],
            'Low': [174.80, 175.50],
            'Close': [175.50, 176.50],
            'Volume': [1000000, 1100000]
        }, index=[
            pd.Timestamp('2024-01-20 10:00:00'),
            pd.Timestamp('2024-01-20 11:00:00')
        ])
        mock_ticker.return_value.history.return_value = mock_history
        
        response = client.get("/api/v1/stocks/AAPL/chart?period=1d")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["symbol"] == "AAPL"
        assert data["period"] == "1d"
        assert data["total"] == 2
        assert len(data["candlesticks"]) == 2
        
        # Check first candlestick
        candle = data["candlesticks"][0]
        assert candle["open"] == 175.00
        assert candle["high"] == 176.50
        assert candle["low"] == 174.80
        assert candle["close"] == 175.50
        assert candle["volume"] == 1000000
    
    def test_get_chart_data_cache_hit(self, client: TestClient, db: Session):
        """Test getting chart data with cache hit."""
        # Create cached candlestick data
        candles = [
            CandlestickData(
                symbol="AAPL",
                period=Period.ONE_DAY,
                date=datetime(2024, 1, 20, 10, 0),
                open=175.00,
                high=176.50,
                low=174.80,
                close=175.50,
                adj_close=175.50,
                volume=1000000,
                created_at=datetime.utcnow()
            ),
            CandlestickData(
                symbol="AAPL",
                period=Period.ONE_DAY,
                date=datetime(2024, 1, 20, 11, 0),
                open=176.00,
                high=177.00,
                low=175.50,
                close=176.50,
                adj_close=176.50,
                volume=1100000,
                created_at=datetime.utcnow()
            )
        ]
        
        for candle in candles:
            db.add(candle)
        db.commit()
        
        response = client.get("/api/v1/stocks/AAPL/chart?period=1d")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total"] == 2
        assert data["candlesticks"][0]["open"] == 175.00
    
    def test_get_chart_data_all_periods(self, client: TestClient, db: Session):
        """Test all period options."""
        periods = ["30m", "1h", "1d", "1wk", "1mo"]
        
        for period_str in periods:
            # Mock yfinance
            with patch('src.services.stock_data_service.yf.Ticker') as mock_ticker:
                import pandas as pd
                mock_history = pd.DataFrame({
                    'Open': [175.00],
                    'High': [176.50],
                    'Low': [174.80],
                    'Close': [175.50],
                    'Volume': [1000000]
                }, index=[pd.Timestamp('2024-01-20 10:00:00')])
                mock_ticker.return_value.history.return_value = mock_history
                
                response = client.get(f"/api/v1/stocks/AAPL/chart?period={period_str}")
                
                assert response.status_code == 200
                data = response.json()
                assert data["period"] == period_str
    
    @patch('src.services.stock_data_service.yf.Ticker')
    def test_get_chart_data_invalid_symbol(self, mock_ticker, client: TestClient):
        """Test getting chart data for invalid symbol."""
        import pandas as pd
        mock_ticker.return_value.history.return_value = pd.DataFrame()  # Empty = no data
        
        response = client.get("/api/v1/stocks/INVALID/chart?period=1d")
        
        assert response.status_code == 404
        assert "not available" in response.json()["detail"].lower()
    
    def test_get_chart_data_missing_period(self, client: TestClient):
        """Test getting chart data without period parameter."""
        response = client.get("/api/v1/stocks/AAPL/chart")
        
        assert response.status_code == 422  # Validation error


class TestGetTopMovers:
    """Tests for GET /api/v1/stocks/market/top-movers endpoint."""
    
    @patch('src.services.stock_data_service.StockDataService.get_top_movers')
    def test_get_top_movers_success(self, mock_get_top_movers, client: TestClient):
        """Test getting top movers successfully."""
        # Mock Alpha Vantage response
        mock_get_top_movers.return_value = {
            'metadata': 'Top gainers, losers, and most actively traded US tickers',
            'last_updated': '2025-10-21 16:16:00 US/Eastern',
            'top_gainers': [
                {
                    'ticker': 'BYND',
                    'price': '3.62',
                    'change_amount': '2.15',
                    'change_percentage': '146.2585%',
                    'volume': '1812070328'
                },
                {
                    'ticker': 'TEST',
                    'price': '10.50',
                    'change_amount': '5.00',
                    'change_percentage': '90.9091%',
                    'volume': '500000000'
                }
            ],
            'top_losers': [
                {
                    'ticker': 'RGTU',
                    'price': '72.89',
                    'change_amount': '-185.11',
                    'change_percentage': '-71.7174%',
                    'volume': '50000000'
                }
            ],
            'most_actively_traded': [
                {
                    'ticker': 'AAPL',
                    'price': '175.50',
                    'change_amount': '2.00',
                    'change_percentage': '1.1527%',
                    'volume': '80000000'
                }
            ]
        }
        
        response = client.get("/api/v1/stocks/market/top-movers")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data['metadata'] == 'Top gainers, losers, and most actively traded US tickers'
        assert data['last_updated'] == '2025-10-21 16:16:00 US/Eastern'
        assert len(data['top_gainers']) == 2
        assert len(data['top_losers']) == 1
        assert len(data['most_actively_traded']) == 1
        
        # Verify first gainer
        assert data['top_gainers'][0]['ticker'] == 'BYND'
        assert data['top_gainers'][0]['price'] == '3.62'
        assert data['top_gainers'][0]['change_percentage'] == '146.2585%'
    
    @patch('src.services.stock_data_service.StockDataService.get_top_movers')
    def test_get_top_movers_service_unavailable(self, mock_get_top_movers, client: TestClient):
        """Test top movers when service returns None."""
        mock_get_top_movers.return_value = None
        
        response = client.get("/api/v1/stocks/market/top-movers")
        
        assert response.status_code == 503
        assert "unavailable" in response.json()["detail"].lower()
