"""Pydantic schemas for watchlist endpoints.

Request/response models for watchlist management.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime


class WatchlistAddRequest(BaseModel):
    """Add stock to watchlist request schema."""
    
    symbol: str = Field(..., min_length=1, max_length=20, description="Stock ticker symbol")
    notes: Optional[str] = Field(None, max_length=500, description="User notes about the stock")
    
    @validator('symbol')
    def validate_symbol_format(cls, v):
        """Validate symbol is uppercase and alphanumeric with dots."""
        v = v.upper().strip()
        if not v.replace('.', '').isalnum():
            raise ValueError('Symbol must contain only letters, numbers, and dots')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "symbol": "AAPL",
                "notes": "Apple Inc. - 관심있는 미국 기술주"
            }
        }


class WatchlistUpdateRequest(BaseModel):
    """Update watchlist item request schema."""
    
    notes: Optional[str] = Field(None, max_length=500, description="User notes about the stock")
    
    class Config:
        json_schema_extra = {
            "example": {
                "notes": "Updated notes about this stock"
            }
        }


class WatchlistReorderRequest(BaseModel):
    """Reorder watchlist items request schema."""
    
    symbol_order: List[str] = Field(
        ..., 
        min_length=1, 
        max_length=50,
        description="Ordered list of symbols (max 50 items)"
    )
    
    @validator('symbol_order')
    def validate_unique_symbols(cls, v):
        """Validate all symbols are unique."""
        if len(v) != len(set(v)):
            raise ValueError('Symbol list must not contain duplicates')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "symbol_order": ["AAPL", "MSFT", "005930.KS", "GOOGL"]
            }
        }


class WatchlistItemResponse(BaseModel):
    """Watchlist item response schema."""
    
    id: int = Field(..., description="Watchlist item ID")
    user_id: int = Field(..., description="User ID")
    symbol: str = Field(..., description="Stock ticker symbol")
    display_order: int = Field(..., description="Display order (0-49)")
    notes: Optional[str] = Field(None, description="User notes")
    created_at: datetime = Field(..., description="When stock was added")
    current_price: Optional[float] = Field(None, description="Current stock price")
    price_change: Optional[float] = Field(None, description="Price change from previous close")
    change_percent: Optional[float] = Field(None, description="Percent change from previous close")
    market_cap: Optional[int] = Field(None, description="Market capitalization")
    company_name: Optional[str] = Field(None, description="Company name")
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "user_id": 1,
                "symbol": "AAPL",
                "display_order": 0,
                "notes": "Apple Inc. - 관심있는 미국 기술주",
                "created_at": "2024-01-20T10:00:00",
                "current_price": 175.50,
                "price_change": 2.50,
                "change_percent": 1.45,
                "market_cap": 2800000000000,
                "company_name": "Apple Inc."
            }
        }


class WatchlistResponse(BaseModel):
    """Full watchlist response schema."""
    
    items: List[WatchlistItemResponse] = Field(..., description="Watchlist items")
    total: int = Field(..., description="Total number of items")
    max_items: int = Field(default=50, description="Maximum allowed items")
    
    class Config:
        json_schema_extra = {
            "example": {
                "items": [
                    {
                        "id": 1,
                        "user_id": 1,
                        "symbol": "AAPL",
                        "display_order": 0,
                        "notes": "Apple Inc.",
                        "created_at": "2024-01-20T10:00:00"
                    },
                    {
                        "id": 2,
                        "user_id": 1,
                        "symbol": "MSFT",
                        "display_order": 1,
                        "notes": "Microsoft Corporation",
                        "created_at": "2024-01-20T10:01:00"
                    }
                ],
                "total": 2,
                "max_items": 50
            }
        }
