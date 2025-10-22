"""User document model for Cosmos DB.

This module defines the UserDocument Pydantic model for storing user account
information with embedded watchlists and portfolios in a single document.
"""

from pydantic import BaseModel, Field, EmailStr, ConfigDict
from typing import List, Optional
from datetime import datetime
import uuid


class WatchlistItem(BaseModel):
    """Embedded watchlist item within User document.
    
    Attributes:
        symbol: Stock ticker symbol (e.g., "AAPL", "TSLA")
        display_order: Order position in watchlist (0-49)
        notes: Optional user notes about the stock
        added_at: Timestamp when stock was added to watchlist
    """
    
    symbol: str = Field(..., description="Stock ticker symbol")
    display_order: int = Field(..., ge=0, lt=50, description="Order position (0-49)")
    notes: Optional[str] = Field(None, max_length=500, description="User notes")
    added_at: datetime = Field(default_factory=datetime.utcnow, description="Added timestamp")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "symbol": "AAPL",
                "display_order": 0,
                "notes": "Apple Inc. - Long term investment",
                "added_at": "2024-01-20T10:30:00Z"
            }
        }
    )


class HoldingItem(BaseModel):
    """Embedded holding item within Portfolio.
    
    Attributes:
        symbol: Stock ticker symbol
        quantity: Number of shares held (positive decimal)
        avg_price: Average purchase price per share
        purchase_date: Date when position was opened
    """
    
    symbol: str = Field(..., description="Stock ticker symbol")
    quantity: float = Field(..., gt=0, description="Number of shares")
    avg_price: float = Field(..., gt=0, description="Average purchase price")
    purchase_date: datetime = Field(default_factory=datetime.utcnow, description="Purchase timestamp")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "symbol": "TSLA",
                "quantity": 10.5,
                "avg_price": 245.30,
                "purchase_date": "2024-01-15T14:20:00Z"
            }
        }
    )


class PortfolioItem(BaseModel):
    """Embedded portfolio within User document.
    
    Attributes:
        id: Unique portfolio identifier (UUID)
        name: Portfolio name (장기투자, 단타, 정찰병)
        holdings: List of stock holdings in this portfolio
        created_at: Portfolio creation timestamp
    """
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Portfolio UUID")
    name: str = Field(..., description="Portfolio name (장기투자, 단타, 정찰병)")
    holdings: List[HoldingItem] = Field(default_factory=list, description="List of holdings")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Created timestamp")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "장기투자",
                "holdings": [
                    {"symbol": "AAPL", "quantity": 50, "avg_price": 150.25, "purchase_date": "2024-01-10T10:00:00Z"}
                ],
                "created_at": "2024-01-01T00:00:00Z"
            }
        }
    )


class UserDocument(BaseModel):
    """User document model for Cosmos DB NoSQL storage.
    
    This model represents a complete user with embedded watchlists and portfolios.
    Each user is stored as a single document with partition key = email.
    
    Attributes:
        id: Document ID (user UUID or email for simplicity)
        email: Unique email address (also used as partition key)
        password_hash: bcrypt hashed password
        created_at: Account creation timestamp
        last_login_at: Last successful login timestamp
        is_active: Soft delete flag
        watchlists: Embedded list of watchlist items (max 50)
        portfolios: Embedded list of portfolios (장기투자, 단타, 정찰병)
    """
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id", description="Document ID")
    email: EmailStr = Field(..., description="User email (partition key)")
    password_hash: str = Field(..., description="bcrypt hash")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Account creation")
    last_login_at: Optional[datetime] = Field(None, description="Last login")
    is_active: bool = Field(True, description="Account active status")
    watchlists: List[WatchlistItem] = Field(default_factory=list, max_length=50, description="Watchlist items")
    portfolios: List[PortfolioItem] = Field(default_factory=list, max_length=3, description="Portfolios")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "_id": "user-123e4567-e89b-12d3-a456-426614174000",
                "email": "user@example.com",
                "password_hash": "$2b$12$...",
                "created_at": "2024-01-01T00:00:00Z",
                "last_login_at": "2024-01-20T10:30:00Z",
                "is_active": True,
                "watchlists": [
                    {"symbol": "AAPL", "display_order": 0, "notes": "Apple", "added_at": "2024-01-10T10:00:00Z"}
                ],
                "portfolios": [
                    {
                        "id": "portfolio-001",
                        "name": "장기투자",
                        "holdings": [{"symbol": "AAPL", "quantity": 50, "avg_price": 150.25, "purchase_date": "2024-01-10T10:00:00Z"}],
                        "created_at": "2024-01-01T00:00:00Z"
                    }
                ]
            }
        },
        populate_by_name=True  # Allow using alias "_id" and field name "id"
    )
    
    def to_cosmos_dict(self) -> dict:
        """Convert to Cosmos DB document format.
        
        Returns:
            dict: Document ready for Cosmos DB insertion with 'id' field
        """
        data = self.model_dump(by_alias=True, exclude_none=False, mode='json')
        # Ensure 'id' field exists (Cosmos DB requirement)
        if '_id' in data:
            data['id'] = data.pop('_id')
        return data
    
    @classmethod
    def from_cosmos_dict(cls, data: dict) -> "UserDocument":
        """Create UserDocument from Cosmos DB document.
        
        Args:
            data: Cosmos DB document dictionary
            
        Returns:
            UserDocument: Parsed user document
        """
        # Convert 'id' to '_id' for Pydantic
        if 'id' in data and '_id' not in data:
            data['_id'] = data['id']
        return cls(**data)

