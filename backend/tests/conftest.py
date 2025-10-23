"""Pytest configuration and fixtures for MyStock backend tests.

Note: Tests currently need to be updated for Cosmos DB.
The existing SQLAlchemy-based tests will not work with Cosmos DB.
"""

import pytest
from typing import Generator
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from src.main import app
from src.core.security import create_access_token


@pytest.fixture(scope="function", autouse=True)
def mock_cosmos_db():
    """Mock Cosmos DB initialization for all tests."""
    with patch('src.core.database.initialize_cosmos_db') as mock_init:
        with patch('src.core.database.close_cosmos_client') as mock_close:
            mock_init.return_value = None
            mock_close.return_value = None
            yield


@pytest.fixture(scope="function")
def client() -> Generator[TestClient, None, None]:
    """Create a test client.
    
    Yields:
        FastAPI test client
    """
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def auth_token() -> str:
    """Create a test authentication token.
    
    Returns:
        JWT token for test user
    """
    return create_access_token({"sub": "test@example.com"})


@pytest.fixture
def auth_headers(auth_token: str) -> dict:
    """Create authentication headers.
    
    Args:
        auth_token: JWT token
        
    Returns:
        Headers dictionary with authorization
    """
    return {"Authorization": f"Bearer {auth_token}"}


# Note: Additional fixtures for Cosmos DB testing need to be implemented
# This may include:
# - Cosmos DB emulator setup
# - Test data creation/cleanup
# - Mock Cosmos DB client for unit tests
