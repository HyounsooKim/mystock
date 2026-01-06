"""Portfolio and holding schemas for request/response validation.

Defines schemas for portfolio management, holdings CRUD, and summary calculations.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class PortfolioResponse(BaseModel):
    """Response schema for portfolio information.
    
    Attributes:
        id: Portfolio unique identifier (UUID string)
        user_id: Owner user ID (UUID string)
        name: Portfolio name (e.g., "장기투자", "단타", "정찰병")
        created_at: Portfolio creation timestamp
        updated_at: Last update timestamp
        holdings_count: Number of holdings in portfolio (optional)
    """
    
    id: str = Field(..., description="Portfolio ID (UUID)", examples=["cab647a5-3d6c-418d-a4d9-214d064ef2a2"])
    user_id: str = Field(..., description="Owner user ID (UUID)", examples=["4d9cd54d-4569-4833-b495-53d05d787f39"])
    name: str = Field(..., description="Portfolio name", examples=["장기투자"])
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    holdings_count: Optional[int] = Field(None, description="Number of holdings", examples=[5])
    
    class Config:
        from_attributes = True


class HoldingResponse(BaseModel):
    """Response schema for holding information.
    
    Attributes:
        id: Holding unique identifier (UUID string)
        portfolio_id: Parent portfolio ID (UUID string)
        symbol: Stock symbol (e.g., AAPL, 005930.KS)
        company_name: Company name
        quantity: Number of shares held
        avg_price: Average purchase price per share
        cost_basis: Total investment (quantity * avg_price)
        current_price: Current market price (from stock_quotes)
        current_value: Current total value (quantity * current_price)
        profit_loss: Unrealized profit/loss (current_value - cost_basis)
        return_rate: Return percentage ((current_value - cost_basis) / cost_basis * 100)
        notes: Optional user notes
        created_at: Holding creation timestamp
        updated_at: Last update timestamp
    """
    
    id: str = Field(..., description="Holding ID (UUID)", examples=["abc123..."])
    portfolio_id: str = Field(..., description="Portfolio ID (UUID)", examples=["cab647a5..."])
    symbol: str = Field(..., description="Stock symbol", examples=["AAPL"])
    company_name: Optional[str] = Field(None, description="Company name", examples=["Apple Inc."])
    quantity: int = Field(..., description="Number of shares", examples=[10])
    avg_price: Decimal = Field(..., description="Average price per share", examples=[175.50])
    cost_basis: Decimal = Field(..., description="Total investment", examples=[1755.00])
    current_price: Optional[Decimal] = Field(None, description="Current market price", examples=[180.00])
    current_value: Optional[Decimal] = Field(None, description="Current total value", examples=[1800.00])
    profit_loss: Optional[Decimal] = Field(None, description="Unrealized P&L", examples=[45.00])
    return_rate: Optional[Decimal] = Field(None, description="Return percentage", examples=[2.56])
    notes: Optional[str] = Field(None, description="User notes", examples=["Long-term hold"])
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    class Config:
        from_attributes = True


class AddHoldingRequest(BaseModel):
    """Request schema for adding a new holding.
    
    Attributes:
        symbol: Stock symbol (uppercase, alphanumeric + dots)
        quantity: Number of shares (positive integer)
        avg_price: Average purchase price (positive decimal)
        notes: Optional user notes (max 500 characters)
    """
    
    symbol: str = Field(..., description="Stock symbol", examples=["AAPL"])
    quantity: int = Field(..., gt=0, description="Number of shares", examples=[10])
    avg_price: Decimal = Field(..., gt=0, description="Average price per share", examples=[175.50])
    notes: Optional[str] = Field(None, max_length=500, description="User notes", examples=["Bought on dip"])
    
    @field_validator("symbol")
    @classmethod
    def validate_symbol(cls, value: str) -> str:
        """Validate and normalize stock symbol.
        
        Args:
            value: Raw symbol string
            
        Returns:
            Uppercase normalized symbol
            
        Raises:
            ValueError: If symbol format invalid
        """
        symbol = value.strip().upper()
        
        # Check alphanumeric + dots only
        if not all(c.isalnum() or c == '.' for c in symbol):
            raise ValueError("Symbol must contain only letters, numbers, and dots")
        
        # Check length
        if len(symbol) < 1 or len(symbol) > 20:
            raise ValueError("Symbol must be 1-20 characters")
        
        return symbol


class UpdateHoldingRequest(BaseModel):
    """Request schema for updating an existing holding.
    
    Attributes:
        quantity: Number of shares (optional, positive integer)
        avg_price: Average purchase price (optional, positive decimal)
        notes: Optional user notes (max 500 characters)
    """
    
    quantity: Optional[int] = Field(None, gt=0, description="Number of shares", examples=[15])
    avg_price: Optional[Decimal] = Field(None, gt=0, description="Average price per share", examples=[177.00])
    notes: Optional[str] = Field(None, max_length=500, description="User notes", examples=["Added more shares"])


class PortfolioSummary(BaseModel):
    """Aggregated portfolio statistics.
    
    Attributes:
        total_holdings: Number of holdings
        total_cost_basis: Total investment across all holdings
        total_current_value: Total current value across all holdings
        total_profit_loss: Total unrealized P&L
        total_return_rate: Overall return percentage
        usd_cost_basis: Total USD investment
        usd_current_value: Total USD current value
        usd_profit_loss: Total USD P&L
        usd_return_rate: USD return percentage
        krw_cost_basis: Total KRW investment
        krw_current_value: Total KRW current value
        krw_profit_loss: Total KRW P&L
        krw_return_rate: KRW return percentage
    """
    
    total_holdings: int = Field(..., description="Number of holdings", examples=[5])
    total_cost_basis: Decimal = Field(..., description="Total investment", examples=[8750.00])
    total_current_value: Decimal = Field(..., description="Total current value", examples=[9100.00])
    total_profit_loss: Decimal = Field(..., description="Total P&L", examples=[350.00])
    total_return_rate: Decimal = Field(..., description="Overall return %", examples=[4.00])
    
    # USD-specific totals
    usd_cost_basis: Decimal = Field(default=Decimal(0), description="USD investment")
    usd_current_value: Decimal = Field(default=Decimal(0), description="USD current value")
    usd_profit_loss: Decimal = Field(default=Decimal(0), description="USD P&L")
    usd_return_rate: Decimal = Field(default=Decimal(0), description="USD return %")
    
    # KRW-specific totals
    krw_cost_basis: Decimal = Field(default=Decimal(0), description="KRW investment")
    krw_current_value: Decimal = Field(default=Decimal(0), description="KRW current value")
    krw_profit_loss: Decimal = Field(default=Decimal(0), description="KRW P&L")
    krw_return_rate: Decimal = Field(default=Decimal(0), description="KRW return %")
    
    class Config:
        json_schema_extra = {
            "example": {
                "total_holdings": 5,
                "total_cost_basis": 8750.00,
                "total_current_value": 9100.00,
                "total_profit_loss": 350.00,
                "total_return_rate": 4.00,
                "usd_cost_basis": 5000.00,
                "usd_current_value": 5200.00,
                "usd_profit_loss": 200.00,
                "usd_return_rate": 4.00,
                "krw_cost_basis": 3750000,
                "krw_current_value": 3900000,
                "krw_profit_loss": 150000,
                "krw_return_rate": 4.00
            }
        }


class PortfolioSummaryResponse(BaseModel):
    """Response schema for portfolio summary with holdings and calculations.
    
    Attributes:
        portfolio: Portfolio information
        holdings: List of holdings with P&L calculations
        summary: Aggregated portfolio statistics
    """
    
    portfolio: PortfolioResponse
    holdings: list[HoldingResponse]
    summary: PortfolioSummary
    
    class Config:
        from_attributes = True
