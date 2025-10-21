"""User model for authentication and account management.

This module defines the User SQLAlchemy model for storing user account
information with email/password authentication.
"""

from sqlalchemy import Column, BigInteger, String, TIMESTAMP, Boolean, func
from sqlalchemy.orm import relationship
from src.core.database import Base


class User(Base):
    """User account model for MyStock application.
    
    Attributes:
        id: Primary key, auto-incrementing integer
        email: Unique email address for authentication
        password_hash: bcrypt hashed password (never store plaintext)
        created_at: Account creation timestamp
        last_login_at: Last successful login timestamp
        is_active: Soft delete flag (False when account deleted)
        
    Relationships:
        watchlists: One-to-many relationship with Watchlist model
        portfolios: One-to-many relationship with Portfolio model
    """
    
    __tablename__ = "users"
    __table_args__ = {"comment": "User accounts with email/password authentication"}
    
    # Primary Key
    id = Column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        comment="User ID (primary key)"
    )
    
    # Authentication Fields
    email = Column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
        comment="User email address (unique)"
    )
    
    password_hash = Column(
        String(255),
        nullable=False,
        comment="bcrypt hash with cost factor 12"
    )
    
    # Timestamps
    created_at = Column(
        TIMESTAMP,
        server_default=func.now(),
        nullable=False,
        comment="Account creation timestamp"
    )
    
    last_login_at = Column(
        TIMESTAMP,
        nullable=True,
        comment="Last successful login timestamp"
    )
    
    # Status
    is_active = Column(
        Boolean,
        server_default="1",
        nullable=False,
        index=True,
        comment="Soft delete flag (False when account deleted)"
    )
    
    # Relationships
    watchlists = relationship(
        "Watchlist",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="select"
    )
    
    portfolios = relationship(
        "Portfolio",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="select"
    )
    
    def __repr__(self) -> str:
        """String representation of User object."""
        return f"<User(id={self.id}, email='{self.email}', active={self.is_active})>"
