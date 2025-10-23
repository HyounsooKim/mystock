"""Top movers service with caching.

Provides cached access to top gainers, losers, and most active stocks.
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from src.services.alpha_vantage_service import AlphaVantageService


logger = logging.getLogger(__name__)


class TopMoversService:
    """Service for fetching and caching top movers data."""
    
    def __init__(self):
        """Initialize top movers service with Alpha Vantage client."""
        self.alpha_vantage = AlphaVantageService()
        self._cache: Optional[Dict[str, Any]] = None
        self._cache_time: Optional[datetime] = None
        # Cache for 4 hours (data typically updates once per trading day)
        self._cache_ttl = timedelta(hours=4)
    
    def get_top_movers(self, force_refresh: bool = False) -> Optional[Dict[str, Any]]:
        """Get top movers data with caching.
        
        Args:
            force_refresh: If True, bypass cache and fetch fresh data
            
        Returns:
            Dictionary with top movers data or None if fetch fails
        """
        # Check if cache is valid
        if not force_refresh and self._is_cache_valid():
            logger.info("Returning cached top movers data")
            return self._cache
        
        # Fetch fresh data
        logger.info("Fetching fresh top movers data from Alpha Vantage")
        data = self.alpha_vantage.get_top_movers()
        
        if data:
            # Update cache
            self._cache = data
            self._cache_time = datetime.utcnow()
            logger.info(f"Top movers cache updated at {self._cache_time}")
            return data
        else:
            # If fetch fails but we have stale cache, return it with a warning
            if self._cache:
                logger.warning("Returning stale cached data due to API failure")
                return self._cache
            
            logger.error("No top movers data available")
            return None
    
    def _is_cache_valid(self) -> bool:
        """Check if cached data is still valid.
        
        Returns:
            True if cache exists and is not expired
        """
        if self._cache is None or self._cache_time is None:
            return False
        
        age = datetime.utcnow() - self._cache_time
        is_valid = age < self._cache_ttl
        
        if not is_valid:
            logger.info(f"Cache expired (age: {age}, ttl: {self._cache_ttl})")
        
        return is_valid
    
    def clear_cache(self):
        """Clear the cached data."""
        self._cache = None
        self._cache_time = None
        logger.info("Top movers cache cleared")


# Create a singleton instance
top_movers_service = TopMoversService()
