"""Top Movers API endpoints.

Provides endpoints for fetching top gainers, losers, and most actively traded stocks
using Alpha Vantage API.
"""

from fastapi import APIRouter, HTTPException
import logging

from src.services.alpha_vantage_service import alpha_vantage_service
from src.schemas.top_movers import TopMoversResponse, StockMover

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/top-movers",
    response_model=TopMoversResponse,
    summary="Get Top Movers",
    description="Fetch top gaining stocks, top losing stocks, and most actively traded stocks"
)
async def get_top_movers() -> TopMoversResponse:
    """Get top movers (gainers, losers, most active).
    
    Returns data from Alpha Vantage TOP_GAINERS_LOSERS endpoint.
    Data is cached for 15 minutes to reduce API calls.
    
    Returns:
        TopMoversResponse with three lists of stocks
        
    Raises:
        HTTPException: 503 if Alpha Vantage API is unavailable
        HTTPException: 500 for other errors
    """
    try:
        data = alpha_vantage_service.get_top_movers()
        
        if data is None:
            logger.error("Failed to fetch top movers from Alpha Vantage")
            raise HTTPException(
                status_code=503,
                detail="Unable to fetch top movers data. Please try again later."
            )
        
        # Convert to Pydantic models
        response = TopMoversResponse(
            top_gainers=[StockMover(**item) for item in data['top_gainers']],
            top_losers=[StockMover(**item) for item in data['top_losers']],
            most_actively_traded=[StockMover(**item) for item in data['most_actively_traded']],
            last_updated=data['last_updated']
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_top_movers endpoint: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error while fetching top movers"
        )
