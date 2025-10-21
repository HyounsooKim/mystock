"""Pytest configuration and fixtures for MyStock backend tests.

Provides shared fixtures for database setup, test client, and authentication.
"""

import pytest
from typing import Generator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from src.main import app
from src.core.database import Base, get_db
from src.core.security import create_access_token
from src.models import User, Portfolio
from src.core.security import hash_password


# Use in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db() -> Generator[Session, None, None]:
    """Create a test database session.
    
    Yields:
        Database session for testing
    """
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        # Drop tables after test
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db: Session) -> Generator[TestClient, None, None]:
    """Create a test client with database dependency override.
    
    Args:
        db: Test database session
        
    Yields:
        FastAPI test client
    """
    def override_get_db():
        try:
            yield db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db: Session) -> User:
    """Create a test user in the database.
    
    Args:
        db: Database session
        
    Returns:
        Created test user
    """
    user = User(
        email="test@example.com",
        password_hash=hash_password("TestPass123"),
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def test_user_with_portfolios(db: Session, test_user: User) -> User:
    """Create a test user with 3 predefined portfolios.
    
    Args:
        db: Database session
        test_user: Test user
        
    Returns:
        Test user with portfolios
    """
    portfolio_names = Portfolio.get_predefined_names()
    
    for name in portfolio_names:
        portfolio = Portfolio(
            user_id=test_user.id,
            name=name
        )
        db.add(portfolio)
    
    db.commit()
    return test_user


@pytest.fixture
def auth_token(test_user: User) -> str:
    """Generate JWT token for test user.
    
    Args:
        test_user: Test user
        
    Returns:
        JWT access token
    """
    return create_access_token(data={"sub": str(test_user.id)})


@pytest.fixture
def auth_headers(auth_token: str) -> dict:
    """Generate authentication headers with JWT token.
    
    Args:
        auth_token: JWT access token
        
    Returns:
        Dictionary with Authorization header
    """
    return {"Authorization": f"Bearer {auth_token}"}
