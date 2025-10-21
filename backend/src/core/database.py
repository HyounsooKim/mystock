"""Database connection and session management for MyStock application.

This module provides SQLAlchemy engine, session factory, and Base class
for all database models.
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from typing import Generator
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL", "mysql+pymysql://mystockuser:mystockpass123@localhost:3306/mystockdb")

# Create SQLAlchemy engine with connection pooling
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # Verify connections before using
    pool_size=10,  # Number of connections to keep open
    max_overflow=20,  # Additional connections when pool is exhausted
    pool_recycle=3600,  # Recycle connections after 1 hour
    echo=os.getenv("DEBUG", "false").lower() == "true",  # Log SQL queries in debug mode
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for all models
Base = declarative_base()


def get_db() -> Generator:
    """Dependency function to get database session.
    
    Yields:
        Session: SQLAlchemy database session
        
    Example:
        @app.get("/users")
        def get_users(db: Session = Depends(get_db)):
            return db.query(User).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
