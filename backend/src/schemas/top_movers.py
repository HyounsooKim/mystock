"""Pydantic schemas for Top Movers (급등락 종목) feature.

Defines request/response models for top gainers, losers, and most actively traded stocks.
"""

from pydantic import BaseModel, Field
from typing import List


class StockMover(BaseModel):
    """Single stock mover item."""
    
    ticker: str = Field(..., description="Stock ticker symbol")
    price: str = Field(..., description="Current price")
    change_amount: str = Field(..., description="Price change amount")
    change_percentage: str = Field(..., description="Price change percentage")
    volume: str = Field(..., description="Trading volume")


class TopMoversResponse(BaseModel):
    """Response model for top movers endpoint."""
    
    top_gainers: List[StockMover] = Field(
        default_factory=list,
        description="Top gaining stocks (up to 20)"
    )
    top_losers: List[StockMover] = Field(
        default_factory=list,
        description="Top losing stocks (up to 20)"
    )
    most_actively_traded: List[StockMover] = Field(
        default_factory=list,
        description="Most actively traded stocks (up to 20)"
    )
    last_updated: str = Field(..., description="Last update timestamp (ISO format)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "top_gainers": [
                    {
                        "ticker": "AAPL",
                        "price": "175.50",
                        "change_amount": "5.25",
                        "change_percentage": "3.09%",
                        "volume": "52000000"
                    }
                ],
                "top_losers": [
                    {
                        "ticker": "TSLA",
                        "price": "245.30",
                        "change_amount": "-8.20",
                        "change_percentage": "-3.23%",
                        "volume": "48000000"
                    }
                ],
                "most_actively_traded": [
                    {
                        "ticker": "NVDA",
                        "price": "495.80",
                        "change_amount": "2.15",
                        "change_percentage": "0.44%",
                        "volume": "95000000"
                    }
                ],
                "last_updated": "2025-10-23T07:00:00Z"
            }
        }
