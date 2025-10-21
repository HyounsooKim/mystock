"""Holding model for portfolio stock holdings.

This module defines the Holding SQLAlchemy model for storing stock holdings
(symbol, quantity, average price) within portfolios (max 100 per portfolio).
"""

from sqlalchemy import Column, BigInteger, String, DECIMAL, TIMESTAMP, ForeignKey, func, UniqueConstraint, CheckConstraint
from sqlalchemy.orm import relationship
from src.core.database import Base


class Holding(Base):
    """Holding model for MyStock application.
    
    Stores stock holdings within portfolios with quantity and average price.
    Maximum 100 holdings per portfolio.
    
    Attributes:
        id: Primary key, auto-incrementing integer
        portfolio_id: Foreign key to portfolios table
        symbol: Stock ticker symbol
        quantity: Number of shares (supports fractional shares)
        avg_price: Average purchase price per share
        created_at: When holding was added
        updated_at: Last modification timestamp
        
    Relationships:
        portfolio: Many-to-one relationship with Portfolio model
    """
    
    __tablename__ = "holdings"
    __table_args__ = (
        UniqueConstraint("portfolio_id", "symbol", name="uk_portfolio_symbol"),
        CheckConstraint("quantity > 0", name="check_positive_quantity"),
        CheckConstraint("avg_price > 0", name="check_positive_price"),
        {"comment": "Stock holdings within portfolios (max 100 per portfolio)"}
    )
    
    # Primary Key
    id = Column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        comment="Holding ID (primary key)"
    )
    
    # Foreign Key
    portfolio_id = Column(
        BigInteger,
        ForeignKey("portfolios.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Portfolio ID (foreign key)"
    )
    
    # Holding Information
    symbol = Column(
        String(20),
        nullable=False,
        comment="Stock ticker symbol"
    )
    
    quantity = Column(
        DECIMAL(15, 4),
        nullable=False,
        comment="Number of shares (supports fractional shares)"
    )
    
    avg_price = Column(
        DECIMAL(15, 4),
        nullable=False,
        comment="Average purchase price per share"
    )
    
    # Timestamps
    created_at = Column(
        TIMESTAMP,
        server_default=func.now(),
        nullable=False,
        comment="When holding was added"
    )
    
    updated_at = Column(
        TIMESTAMP,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="Last modification timestamp"
    )
    
    # Relationships
    portfolio = relationship(
        "Portfolio",
        back_populates="holdings"
    )
    
    def __repr__(self) -> str:
        """String representation of Holding object."""
        return f"<Holding(id={self.id}, portfolio_id={self.portfolio_id}, symbol='{self.symbol}', quantity={self.quantity})>"
    
    def calculate_cost_basis(self) -> float:
        """Calculate cost basis (quantity * avg_price).
        
        Returns:
            Cost basis as float
        """
        return float(self.quantity) * float(self.avg_price)
    
    def calculate_current_value(self, current_price: float) -> float:
        """Calculate current value (quantity * current_price).
        
        Args:
            current_price: Current stock price
            
        Returns:
            Current value as float
        """
        return float(self.quantity) * current_price
    
    def calculate_profit_loss(self, current_price: float) -> float:
        """Calculate profit/loss (current_value - cost_basis).
        
        Args:
            current_price: Current stock price
            
        Returns:
            Profit/loss as float
        """
        return self.calculate_current_value(current_price) - self.calculate_cost_basis()
    
    def calculate_return_rate(self, current_price: float) -> float:
        """Calculate return rate percentage ((profit_loss / cost_basis) * 100).
        
        Args:
            current_price: Current stock price
            
        Returns:
            Return rate as percentage
        """
        cost_basis = self.calculate_cost_basis()
        if cost_basis == 0:
            return 0.0
        return (self.calculate_profit_loss(current_price) / cost_basis) * 100
