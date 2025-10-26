"""Top Movers Service - Cosmos DB based

This service fetches top movers data from Cosmos DB instead of directly
calling Alpha Vantage API. The data is updated hourly by Azure Functions.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from azure.cosmos import exceptions

from src.core.database import get_top_movers_container

logger = logging.getLogger(__name__)


class TopMoversService:
    """Service for fetching top movers data from Cosmos DB."""
    
    def get_top_movers(self) -> Optional[Dict[str, Any]]:
        """Get the latest top movers data from Cosmos DB.
        
        Returns:
            Dictionary containing top gainers, losers, and most active stocks.
            Returns None if no data is available.
            
        Example:
            {
                'metadata': 'Top gainers, losers, and most actively traded stocks',
                'last_updated': '2025-10-25T01:00:00Z',
                'top_gainers': [...],
                'top_losers': [...],
                'most_actively_traded': [...]
            }
        """
        try:
            container = get_top_movers_container()
            
            # Query to get the latest document
            # Sort by timestamp descending and take the first one
            query = """
                SELECT TOP 1 *
                FROM c
                ORDER BY c.timestamp DESC
            """
            
            items = list(container.query_items(
                query=query,
                enable_cross_partition_query=True
            ))
            
            if not items:
                logger.warning("No top movers data found in Cosmos DB")
                return None
            
            latest = items[0]
            
            # Extract data
            result = {
                'metadata': 'Top gainers, losers, and most actively traded US stocks',
                'last_updated': latest.get('timestamp', ''),
                'top_gainers': latest.get('data', {}).get('top_gainers', []),
                'top_losers': latest.get('data', {}).get('top_losers', []),
                'most_actively_traded': latest.get('data', {}).get('most_actively_traded', [])
            }
            
            logger.info(f"Retrieved top movers data from {latest.get('timestamp')}")
            return result
            
        except exceptions.CosmosHttpResponseError as e:
            logger.error(f"Cosmos DB error fetching top movers: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error fetching top movers from Cosmos DB: {str(e)}")
            return None
    
    def get_top_movers_by_date(self, date: str) -> Optional[Dict[str, Any]]:
        """Get top movers data for a specific date.
        
        Args:
            date: Date string in format 'YYYY-MM-DD'
            
        Returns:
            Dictionary containing top movers data for the specified date.
            Returns None if no data is available for that date.
        """
        try:
            container = get_top_movers_container()
            
            # Query by date partition
            query = """
                SELECT *
                FROM c
                WHERE c.date = @date
                ORDER BY c.timestamp DESC
            """
            
            parameters = [{"name": "@date", "value": date}]
            
            items = list(container.query_items(
                query=query,
                parameters=parameters,
                partition_key=date
            ))
            
            if not items:
                logger.warning(f"No top movers data found for date: {date}")
                return None
            
            # Get the latest entry for that date
            latest = items[0]
            
            result = {
                'metadata': f'Top movers for {date}',
                'last_updated': latest.get('timestamp', ''),
                'date': date,
                'top_gainers': latest.get('data', {}).get('top_gainers', []),
                'top_losers': latest.get('data', {}).get('top_losers', []),
                'most_actively_traded': latest.get('data', {}).get('most_actively_traded', [])
            }
            
            logger.info(f"Retrieved top movers data for date {date}")
            return result
            
        except exceptions.CosmosHttpResponseError as e:
            logger.error(f"Cosmos DB error fetching top movers for date {date}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error fetching top movers for date {date}: {str(e)}")
            return None


# Create singleton instance
top_movers_service = TopMoversService()
