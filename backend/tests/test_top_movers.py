"""Unit tests for Top Movers feature.

Tests Alpha Vantage service integration and API endpoints.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import time

from src.services.alpha_vantage_service import AlphaVantageService
from src.schemas.top_movers import StockMover, TopMoversResponse


class TestAlphaVantageServiceTopMovers:
    """Tests for AlphaVantageService.get_top_movers() method."""
    
    @pytest.fixture
    def service(self):
        """Create service instance with test API key."""
        return AlphaVantageService(api_key='test-api-key')
    
    @pytest.fixture
    def mock_api_response(self):
        """Mock successful API response."""
        return {
            'metadata': 'Top gainers, losers, and most actively traded US tickers',
            'last_updated': '2025-10-23 07:00:00 US/Eastern',
            'top_gainers': [
                {
                    'ticker': 'AAPL',
                    'price': '175.50',
                    'change_amount': '5.25',
                    'change_percentage': '3.09%',
                    'volume': '52000000'
                },
                {
                    'ticker': 'MSFT',
                    'price': '380.20',
                    'change_amount': '10.50',
                    'change_percentage': '2.84%',
                    'volume': '35000000'
                }
            ],
            'top_losers': [
                {
                    'ticker': 'TSLA',
                    'price': '245.30',
                    'change_amount': '-8.20',
                    'change_percentage': '-3.23%',
                    'volume': '48000000'
                }
            ],
            'most_actively_traded': [
                {
                    'ticker': 'NVDA',
                    'price': '495.80',
                    'change_amount': '2.15',
                    'change_percentage': '0.44%',
                    'volume': '95000000'
                }
            ]
        }
    
    @patch('src.services.alpha_vantage_service.requests.get')
    def test_get_top_movers_success(self, mock_get, service, mock_api_response):
        """Test successful top movers fetch."""
        mock_response = Mock()
        mock_response.json.return_value = mock_api_response
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        result = service.get_top_movers()
        
        assert result is not None
        assert 'top_gainers' in result
        assert 'top_losers' in result
        assert 'most_actively_traded' in result
        assert 'last_updated' in result
        assert len(result['top_gainers']) == 2
        assert len(result['top_losers']) == 1
        assert len(result['most_actively_traded']) == 1
        assert result['top_gainers'][0]['ticker'] == 'AAPL'
        
        # Verify API was called correctly
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        assert call_args[1]['params']['function'] == 'TOP_GAINERS_LOSERS'
        assert call_args[1]['timeout'] == 10
    
    @patch('src.services.alpha_vantage_service.requests.get')
    def test_get_top_movers_caching(self, mock_get, service, mock_api_response):
        """Test that results are cached and reused."""
        mock_response = Mock()
        mock_response.json.return_value = mock_api_response
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        # First call - should hit API
        result1 = service.get_top_movers()
        assert result1 is not None
        assert mock_get.call_count == 1
        
        # Second call - should use cache
        result2 = service.get_top_movers()
        assert result2 is not None
        assert mock_get.call_count == 1  # Still 1, not 2
        assert result1 == result2
    
    @patch('src.services.alpha_vantage_service.requests.get')
    def test_get_top_movers_cache_expiration(self, mock_get, service, mock_api_response):
        """Test that cache expires after TTL."""
        service._cache_ttl = 1  # Set TTL to 1 second for testing
        
        mock_response = Mock()
        mock_response.json.return_value = mock_api_response
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        # First call
        result1 = service.get_top_movers()
        assert result1 is not None
        assert mock_get.call_count == 1
        
        # Wait for cache to expire
        time.sleep(1.5)
        
        # Second call - should hit API again
        result2 = service.get_top_movers()
        assert result2 is not None
        assert mock_get.call_count == 2
    
    @patch('src.services.alpha_vantage_service.requests.get')
    def test_get_top_movers_api_error(self, mock_get, service):
        """Test handling of API error response."""
        mock_response = Mock()
        mock_response.json.return_value = {
            'Error Message': 'Invalid API key'
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        result = service.get_top_movers()
        
        assert result is None
    
    @patch('src.services.alpha_vantage_service.requests.get')
    def test_get_top_movers_rate_limit(self, mock_get, service, mock_api_response):
        """Test handling of rate limit with cached data fallback."""
        # First, populate the cache
        mock_response = Mock()
        mock_response.json.return_value = mock_api_response
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        result1 = service.get_top_movers()
        assert result1 is not None
        
        # Clear cache time to force re-fetch
        service._top_movers_cache_time = None
        
        # Now simulate rate limit
        mock_response.json.return_value = {
            'Note': 'Thank you for using Alpha Vantage! Our standard API call frequency is 5 calls per minute.'
        }
        
        result2 = service.get_top_movers()
        assert result2 is not None  # Should return cached data
        assert result2 == result1
    
    @patch('src.services.alpha_vantage_service.requests.get')
    def test_get_top_movers_network_timeout(self, mock_get, service, mock_api_response):
        """Test handling of network timeout."""
        import requests
        mock_get.side_effect = requests.exceptions.Timeout()
        
        result = service.get_top_movers()
        
        # Should return None (or cached data if available)
        assert result is None or isinstance(result, dict)
    
    @patch('src.services.alpha_vantage_service.requests.get')
    def test_get_top_movers_network_error(self, mock_get, service):
        """Test handling of network error."""
        import requests
        mock_get.side_effect = requests.exceptions.RequestException('Network error')
        
        result = service.get_top_movers()
        
        assert result is None
    
    @patch('src.services.alpha_vantage_service.requests.get')
    def test_get_top_movers_invalid_response(self, mock_get, service):
        """Test handling of invalid response structure."""
        mock_response = Mock()
        mock_response.json.return_value = {
            'invalid': 'structure'
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        result = service.get_top_movers()
        
        assert result is None
    
    @patch('src.services.alpha_vantage_service.requests.get')
    def test_get_top_movers_limits_to_20_items(self, mock_get, service):
        """Test that results are limited to 20 items per list."""
        # Create response with more than 20 items
        many_items = [
            {
                'ticker': f'STOCK{i}',
                'price': '100.00',
                'change_amount': '1.00',
                'change_percentage': '1.00%',
                'volume': '1000000'
            }
            for i in range(30)
        ]
        
        mock_response = Mock()
        mock_response.json.return_value = {
            'last_updated': '2025-10-23',
            'top_gainers': many_items,
            'top_losers': many_items,
            'most_actively_traded': many_items
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        result = service.get_top_movers()
        
        assert result is not None
        assert len(result['top_gainers']) == 20
        assert len(result['top_losers']) == 20
        assert len(result['most_actively_traded']) == 20


class TestTopMoversAPI:
    """Tests for /api/v1/stocks/top-movers endpoint."""
    
    @pytest.fixture
    def mock_top_movers_data(self):
        """Mock top movers data."""
        return {
            'top_gainers': [
                {
                    'ticker': 'AAPL',
                    'price': '175.50',
                    'change_amount': '5.25',
                    'change_percentage': '3.09%',
                    'volume': '52000000'
                }
            ],
            'top_losers': [
                {
                    'ticker': 'TSLA',
                    'price': '245.30',
                    'change_amount': '-8.20',
                    'change_percentage': '-3.23%',
                    'volume': '48000000'
                }
            ],
            'most_actively_traded': [
                {
                    'ticker': 'NVDA',
                    'price': '495.80',
                    'change_amount': '2.15',
                    'change_percentage': '0.44%',
                    'volume': '95000000'
                }
            ],
            'last_updated': '2025-10-23T07:00:00Z'
        }
    
    @pytest.mark.asyncio
    @patch('src.api.top_movers.alpha_vantage_service.get_top_movers')
    async def test_get_top_movers_success(self, mock_get_top_movers, client, mock_top_movers_data):
        """Test successful top movers API call."""
        mock_get_top_movers.return_value = mock_top_movers_data
        
        response = client.get('/api/v1/stocks/top-movers')
        
        assert response.status_code == 200
        data = response.json()
        assert 'top_gainers' in data
        assert 'top_losers' in data
        assert 'most_actively_traded' in data
        assert 'last_updated' in data
        assert len(data['top_gainers']) == 1
        assert data['top_gainers'][0]['ticker'] == 'AAPL'
    
    @pytest.mark.asyncio
    @patch('src.api.top_movers.alpha_vantage_service.get_top_movers')
    async def test_get_top_movers_service_unavailable(self, mock_get_top_movers, client):
        """Test API error when service returns None."""
        mock_get_top_movers.return_value = None
        
        response = client.get('/api/v1/stocks/top-movers')
        
        assert response.status_code == 503
        assert 'detail' in response.json()
    
    @pytest.mark.asyncio
    @patch('src.api.top_movers.alpha_vantage_service.get_top_movers')
    async def test_get_top_movers_internal_error(self, mock_get_top_movers, client):
        """Test handling of unexpected errors."""
        mock_get_top_movers.side_effect = Exception('Unexpected error')
        
        response = client.get('/api/v1/stocks/top-movers')
        
        assert response.status_code == 500
        assert 'detail' in response.json()


def test_stock_mover_schema():
    """Test StockMover Pydantic model."""
    data = {
        'ticker': 'AAPL',
        'price': '175.50',
        'change_amount': '5.25',
        'change_percentage': '3.09%',
        'volume': '52000000'
    }
    
    mover = StockMover(**data)
    
    assert mover.ticker == 'AAPL'
    assert mover.price == '175.50'
    assert mover.change_amount == '5.25'
    assert mover.change_percentage == '3.09%'
    assert mover.volume == '52000000'


def test_top_movers_response_schema():
    """Test TopMoversResponse Pydantic model."""
    data = {
        'top_gainers': [
            {
                'ticker': 'AAPL',
                'price': '175.50',
                'change_amount': '5.25',
                'change_percentage': '3.09%',
                'volume': '52000000'
            }
        ],
        'top_losers': [],
        'most_actively_traded': [],
        'last_updated': '2025-10-23T07:00:00Z'
    }
    
    response = TopMoversResponse(**data)
    
    assert len(response.top_gainers) == 1
    assert len(response.top_losers) == 0
    assert len(response.most_actively_traded) == 0
    assert response.last_updated == '2025-10-23T07:00:00Z'
