"""Portfolio model for managing user's stock portfolios.

This module defines the Portfolio SQLAlchemy model for storing three
predefined portfolios per user ("장기투자", "단타", "정찰병").
"""

from sqlalchemy import Column, BigInteger, String, TIMESTAMP, ForeignKey, func, UniqueConstraint
from sqlalchemy.orm import relationship
from src.core.database import Base


class Portfolio(Base):
    """Portfolio model for MyStock application.
    
    Each user has exactly 3 portfolios with predefined names:
    - "장기투자" (Long-term Investment)
    - "단타" (Day Trading)
    - "정찰병" (Scout)
    
    Attributes:
        id: Primary key, auto-incrementing integer
        user_id: Foreign key to users table
        name: Portfolio name (must be one of 3 predefined names)
        created_at: Portfolio creation timestamp
        updated_at: Last modification timestamp
        
    Relationships:
        user: Many-to-one relationship with User model
        holdings: One-to-many relationship with Holding model
    """
    
    __tablename__ = "portfolios"
    __table_args__ = (
        UniqueConstraint("user_id", "name", name="uk_user_name"),
        {"comment": "Three predefined portfolios per user"}
    )
    
    # Primary Key
    id = Column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        comment="Portfolio ID (primary key)"
    )
    
    # Foreign Key
    user_id = Column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="User ID (foreign key)"
    )
    
    # Portfolio Information
    name = Column(
        String(50),
        nullable=False,
        comment='Portfolio name (장기투자, 단타, 정찰병)'
    )
    
    # Timestamps
    created_at = Column(
        TIMESTAMP,
        server_default=func.now(),
        nullable=False,
        comment="Portfolio creation timestamp"
    )
    
    updated_at = Column(
        TIMESTAMP,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="Last modification timestamp"
    )
    
    # Relationships
    user = relationship(
        "User",
        back_populates="portfolios"
    )
    
    holdings = relationship(
        "Holding",
        back_populates="portfolio",
        cascade="all, delete-orphan",
        lazy="select"
    )
    
    def __repr__(self) -> str:
        """String representation of Portfolio object."""
        return f"<Portfolio(id={self.id}, user_id={self.user_id}, name='{self.name}')>"
    
    @classmethod
    def get_predefined_names(cls) -> list[str]:
        """Get list of predefined portfolio names.
        
        Returns:
            List of 3 predefined portfolio names
        """
        return ["장기투자", "단타", "정찰병"]
