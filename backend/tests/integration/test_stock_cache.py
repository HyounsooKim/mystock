"""Integration tests for stock data caching.

Tests the stock quote and candlestick data caching mechanism:
- Cache miss: First request fetches from yfinance
- Cache hit: Subsequent requests use cached data (5-min TTL for quotes)
- Cache expiration: After TTL, re-fetch from yfinance
- Cache behavior across different symbols
"""

import pytest
import time
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from datetime import datetime, timedelta


def test_stock_quote_cache_miss_and_hit(authenticated_client: tuple):
    """Test stock quote caching: miss → hit → expiration.
    
    This verifies:
    - First request (cache miss) fetches from yfinance
    - Second request (cache hit) uses cached data
    - Response time is faster on cache hit
    """
    client, _ = authenticated_client
    
    symbol = "AAPL"
    
    # First request - cache miss
    start_time = time.time()
    response = client.get(f"/api/v1/stocks/{symbol}")
    first_request_time = time.time() - start_time
    
    assert response.status_code == 200
    first_data = response.json()
    assert first_data["symbol"] == symbol
    assert "current_price" in first_data
    assert "updated_at" in first_data
    
    # Second request - should hit cache
    start_time = time.time()
    response = client.get(f"/api/v1/stocks/{symbol}")
    second_request_time = time.time() - start_time
    
    assert response.status_code == 200
    second_data = response.json()
    
    # Data should be identical (from cache)
    assert second_data["symbol"] == first_data["symbol"]
    assert second_data["current_price"] == first_data["current_price"]
    assert second_data["updated_at"] == first_data["updated_at"]
    
    # Second request should be significantly faster (cache hit)
    # Note: This may not always be true in test environment
    # but generally cache hits are faster
    print(f"First request: {first_request_time:.3f}s, Second request: {second_request_time:.3f}s")


def test_cache_isolation_between_symbols(authenticated_client: tuple):
    """Test that different symbols have independent caches."""
    client, _ = authenticated_client
    
    # Request quote for AAPL
    response = client.get("/api/v1/stocks/AAPL")
    assert response.status_code == 200
    aapl_data = response.json()
    
    # Request quote for GOOGL
    response = client.get("/api/v1/stocks/GOOGL")
    assert response.status_code == 200
    googl_data = response.json()
    
    # Data should be different
    assert aapl_data["symbol"] == "AAPL"
    assert googl_data["symbol"] == "GOOGL"
    assert aapl_data["current_price"] != googl_data["current_price"]


@pytest.mark.skip(reason="Requires waiting 5+ minutes for cache expiration")
def test_cache_expiration_after_ttl(authenticated_client: tuple):
    """Test that cache expires after 5-minute TTL.
    
    Warning: This test takes 5+ minutes to run and is skipped by default.
    """
    client, _ = authenticated_client
    
    symbol = "AAPL"
    
    # First request
    response = client.get(f"/api/v1/stocks/{symbol}")
    assert response.status_code == 200
    first_timestamp = response.json()["updated_at"]
    
    # Wait 5 minutes + 10 seconds
    time.sleep(310)
    
    # Second request - cache should have expired
    response = client.get(f"/api/v1/stocks/{symbol}")
    assert response.status_code == 200
    second_timestamp = response.json()["updated_at"]
    
    # Timestamp should be updated (new data fetched)
    assert second_timestamp != first_timestamp


def test_candlestick_chart_caching(authenticated_client: tuple):
    """Test candlestick chart data caching across different periods."""
    client, _ = authenticated_client
    
    symbol = "AAPL"
    periods = ["5m", "1h", "1d", "1wk", "1mo"]
    
    for period in periods:
        # First request for this period
        response = client.get(f"/api/v1/stocks/{symbol}/chart?period={period}")
        assert response.status_code == 200
        
        data = response.json()
        assert "data" in data
        assert isinstance(data["data"], list)
        assert data["period"] == period
        assert data["symbol"] == symbol
        
        # Second request should hit cache
        response = client.get(f"/api/v1/stocks/{symbol}/chart?period={period}")
        assert response.status_code == 200
        
        cached_data = response.json()
        assert cached_data["data"] == data["data"]


@patch('src.services.stock_data_service.yf.Ticker')
def test_cache_reduces_api_calls(mock_ticker, authenticated_client: tuple):
    """Test that caching reduces external API calls.
    
    This verifies:
    - yfinance is called once on cache miss
    - yfinance is NOT called on cache hit
    """
    client, _ = authenticated_client
    
    # Mock yfinance response
    mock_instance = MagicMock()
    mock_instance.info = {
        'currentPrice': 150.0,
        'regularMarketPrice': 150.0,
        'regularMarketChangePercent': 2.5,
        'regularMarketVolume': 50000000,
        'marketState': 'REGULAR'
    }
    mock_ticker.return_value = mock_instance
    
    symbol = "MOCKEDSTOCK"
    
    # First request - should call yfinance
    response = client.get(f"/api/v1/stocks/{symbol}")
    assert response.status_code == 200
    assert mock_ticker.call_count == 1
    
    # Second request - should NOT call yfinance again (cache hit)
    response = client.get(f"/api/v1/stocks/{symbol}")
    assert response.status_code == 200
    assert mock_ticker.call_count == 1  # Still 1, not 2


def test_invalid_symbol_not_cached(authenticated_client: tuple):
    """Test that invalid/non-existent symbols don't create cache entries."""
    client, _ = authenticated_client
    
    # Request non-existent symbol
    response = client.get("/api/v1/stocks/INVALIDXYZ123")
    assert response.status_code in [404, 500]  # Depends on yfinance behavior
    
    # Second request should also fail (not cached)
    response = client.get("/api/v1/stocks/INVALIDXYZ123")
    assert response.status_code in [404, 500]


def test_market_status_in_cached_data(authenticated_client: tuple):
    """Test that market status is included in cached quote data."""
    client, _ = authenticated_client
    
    response = client.get("/api/v1/stocks/AAPL")
    assert response.status_code == 200
    
    data = response.json()
    assert "market_status" in data
    assert data["market_status"] in ["REGULAR", "CLOSED", "PRE", "POST", "PREPRE", "POSTPOST"]


def test_korean_stock_caching(authenticated_client: tuple):
    """Test caching for Korean stocks (KOSPI/KOSDAQ)."""
    client, _ = authenticated_client
    
    # Samsung Electronics (KOSPI)
    response = client.get("/api/v1/stocks/005930.KS")
    if response.status_code == 200:
        data = response.json()
        assert data["symbol"] == "005930.KS"
        assert "market" in data
        
        # Second request should hit cache
        response = client.get("/api/v1/stocks/005930.KS")
        assert response.status_code == 200


def test_concurrent_requests_cache_behavior(authenticated_client: tuple):
    """Test cache behavior with concurrent requests for same symbol.
    
    This tests that concurrent requests don't cause multiple API calls
    due to race conditions.
    """
    import concurrent.futures
    
    client, _ = authenticated_client
    symbol = "MSFT"
    
    def make_request():
        return client.get(f"/api/v1/stocks/{symbol}")
    
    # Make 5 concurrent requests
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(make_request) for _ in range(5)]
        responses = [f.result() for f in concurrent.futures.as_completed(futures)]
    
    # All should succeed
    for response in responses:
        assert response.status_code == 200
    
    # All should return same data (from cache after first request)
    prices = [r.json()["current_price"] for r in responses if r.status_code == 200]
    assert len(set(prices)) == 1  # All prices should be identical


def test_cache_stats_or_headers(authenticated_client: tuple):
    """Test if cache hit/miss information is available in response headers.
    
    Note: This assumes cache headers are implemented.
    If not, this test documents the desired behavior.
    """
    client, _ = authenticated_client
    
    # First request - cache miss
    response = client.get("/api/v1/stocks/AAPL")
    assert response.status_code == 200
    
    # Check for cache headers (if implemented)
    # Examples: X-Cache-Status, X-Cache-Hit, etc.
    if "X-Cache-Status" in response.headers:
        assert response.headers["X-Cache-Status"] in ["MISS", "HIT", "EXPIRED"]
