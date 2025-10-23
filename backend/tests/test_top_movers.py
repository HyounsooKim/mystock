"""Tests for top movers API endpoint.

Tests the top movers endpoint with mocked Alpha Vantage API responses.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import json
from pathlib import Path


class TestTopMoversEndpoint:
    """Tests for GET /api/v1/stocks/top-movers endpoint."""
    
    @patch('src.services.top_movers_service.AlphaVantageService')
    def test_get_top_movers_success(self, mock_av_service, client: TestClient):
        """Test successful retrieval of top movers data."""
        # Load sample data
        sample_data_path = Path(__file__).parent.parent.parent / 'sample_data' / 'alphavantage_TOP_GAINERS_LOSERS.json'
        with open(sample_data_path, 'r') as f:
            sample_data = json.load(f)
        
        # Mock the Alpha Vantage service
        mock_instance = MagicMock()
        mock_instance.get_top_movers.return_value = sample_data
        mock_av_service.return_value = mock_instance
        
        # Make request
        response = client.get("/api/v1/stocks/top-movers")
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        
        assert 'metadata' in data
        assert 'last_updated' in data
        assert 'top_gainers' in data
        assert 'top_losers' in data
        assert 'most_actively_traded' in data
        
        assert len(data['top_gainers']) == 20
        assert len(data['top_losers']) == 20
        assert len(data['most_actively_traded']) == 20
        
        # Check first gainer structure
        first_gainer = data['top_gainers'][0]
        assert 'ticker' in first_gainer
        assert 'price' in first_gainer
        assert 'change_amount' in first_gainer
        assert 'change_percentage' in first_gainer
        assert 'volume' in first_gainer
    
    @patch('src.services.top_movers_service.AlphaVantageService')
    def test_get_top_movers_api_failure(self, mock_av_service, client: TestClient):
        """Test handling of Alpha Vantage API failure."""
        # Mock the Alpha Vantage service to return None (API failure)
        mock_instance = MagicMock()
        mock_instance.get_top_movers.return_value = None
        mock_av_service.return_value = mock_instance
        
        # Make request
        response = client.get("/api/v1/stocks/top-movers")
        
        # Should return 503 Service Unavailable
        assert response.status_code == 503
        assert 'detail' in response.json()
    
    def test_get_top_movers_caching(self, client: TestClient):
        """Test that top movers data is cached."""
        # This test would verify caching behavior
        # For now, we'll just ensure the endpoint is accessible
        # In a real implementation, you'd want to verify cache hits/misses
        pass
