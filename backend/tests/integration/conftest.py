"""Pytest configuration for integration tests.

Provides fixtures for integration testing with real MySQL database.
Uses Docker MySQL for accurate production-like testing.
"""

import pytest
from typing import Generator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session

from src.main import app
from src.core.database import Base, get_db
from src.core.security import create_access_token
from src.models import User, Portfolio
from src.core.security import hash_password


# Use real MySQL for integration tests (Docker)
# Separate test database to avoid polluting development data
TEST_DATABASE_URL = "mysql+pymysql://mystockuser:mystockpass123@localhost:3306/mystockdb_test"

# Create test database engine
engine = create_engine(
    TEST_DATABASE_URL,
    pool_pre_ping=True,  # Verify connections before using
    pool_recycle=3600,   # Recycle connections after 1 hour
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Create test database tables before all tests and drop after all tests.
    
    This runs once per test session.
    Note: mystockdb_test database should already exist with proper permissions.
    """
    # Create all tables in test database
    Base.metadata.create_all(bind=engine)
    
    yield
    
    # Drop all tables after all tests (keeps database, just cleans tables)
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db() -> Generator[Session, None, None]:
    """Create a clean database session for each test.
    
    Clears all data before each test to ensure isolation.
    
    Yields:
        Database session for testing
    """
    # Create session
    db = TestingSessionLocal()
    
    # Clean all tables before test
    for table in reversed(Base.metadata.sorted_tables):
        db.execute(text(f"DELETE FROM {table.name}"))
    db.commit()
    
    try:
        yield db
    finally:
        db.rollback()  # Rollback any uncommitted changes
        db.close()


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
def test_user_data() -> dict:
    """Test user registration data.
    
    Returns:
        User registration data dictionary
    """
    return {
        "email": "integration@example.com",
        "password": "IntegrationTest123",
        "full_name": "Integration Test User"
    }


@pytest.fixture
def authenticated_client(client: TestClient, test_user_data: dict) -> tuple[TestClient, dict]:
    """Create an authenticated test client with a registered user.
    
    Args:
        client: Test client
        test_user_data: User registration data
        
    Returns:
        Tuple of (authenticated client, user data with token)
    """
    # Register user
    response = client.post("/api/v1/auth/register", json=test_user_data)
    assert response.status_code == 201  # REST API: 201 for resource creation
    
    # Login to get token
    login_data = {
        "email": test_user_data["email"],
        "password": test_user_data["password"]
    }
    response = client.post("/api/v1/auth/login", json=login_data)
    assert response.status_code == 200
    
    login_response = response.json()
    assert "token" in login_response
    token_data = login_response["token"]
    access_token = token_data["access_token"]
    
    # Set authorization header
    client.headers = {"Authorization": f"Bearer {access_token}"}
    
    return client, {**test_user_data, "access_token": access_token}
