"""Watchlist model for user's favorite stock symbols.

This module defines the Watchlist SQLAlchemy model for storing user's
watchlist items with custom ordering (max 50 items per user).
"""

from sqlalchemy import Column, BigInteger, String, Integer, Text, TIMESTAMP, ForeignKey, func, UniqueConstraint
from sqlalchemy.orm import relationship
from src.core.database import Base


class Watchlist(Base):
    """Watchlist model for MyStock application.
    
    Users can add up to 50 favorite stock symbols with custom ordering
    and optional notes.
    
    Attributes:
        id: Primary key, auto-incrementing integer
        user_id: Foreign key to users table
        symbol: Stock ticker symbol (e.g., AAPL, 005930.KS)
        display_order: User-defined sort order (0-49)
        notes: Optional user notes for this stock
        created_at: When symbol was added to watchlist
        
    Relationships:
        user: Many-to-one relationship with User model
    """
    
    __tablename__ = "watchlists"
    __table_args__ = (
        UniqueConstraint("user_id", "symbol", name="uk_user_symbol"),
        {"comment": "User watchlists with up to 50 items per user"}
    )
    
    # Primary Key
    id = Column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        comment="Watchlist item ID (primary key)"
    )
    
    # Foreign Key
    user_id = Column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="User ID (foreign key)"
    )
    
    # Watchlist Information
    symbol = Column(
        String(20),
        nullable=False,
        comment="Stock ticker (e.g., AAPL, 005930.KS)"
    )
    
    display_order = Column(
        Integer,
        default=0,
        nullable=False,
        comment="User-defined sort order (0-49)"
    )
    
    notes = Column(
        Text,
        nullable=True,
        comment="Optional user notes for this stock"
    )
    
    # Timestamp
    created_at = Column(
        TIMESTAMP,
        server_default=func.now(),
        nullable=False,
        comment="When symbol was added to watchlist"
    )
    
    # Relationships
    user = relationship(
        "User",
        back_populates="watchlists"
    )
    
    def __repr__(self) -> str:
        """String representation of Watchlist object."""
        return f"<Watchlist(id={self.id}, user_id={self.user_id}, symbol='{self.symbol}', order={self.display_order})>"
