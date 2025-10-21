"""Integration tests for authentication flow.

Tests the complete authentication workflow:
- User registration
- User login with JWT token generation
- Token validation
- Protected endpoint access
"""

import pytest
from fastapi.testclient import TestClient


def test_complete_auth_flow(client: TestClient):
    """Test complete authentication flow: register → login → access protected endpoint.
    
    This verifies:
    - User registration with validation
    - 3 portfolios auto-created on registration
    - Login with valid credentials
    - JWT token generation
    - Protected endpoint access with token
    """
    # Step 1: Register new user
    register_data = {
        "email": "authflow@example.com",
        "password": "SecurePass123",
        "full_name": "Auth Flow User"
    }
    
    response = client.post("/api/v1/auth/register", json=register_data)
    assert response.status_code == 201  # REST API: 201 for resource creation
    
    response_data = response.json()
    assert "user" in response_data
    assert "token" in response_data
    assert "portfolios_created" in response_data
    
    user_data = response_data["user"]
    assert user_data["email"] == register_data["email"]
    assert "password" not in user_data  # Password should never be returned
    assert "id" in user_data
    user_id = user_data["id"]
    
        # Verify 3 portfolios were auto-created
    assert len(response_data["portfolios_created"]) == 3
    assert "장기투자" in response_data["portfolios_created"]
    assert "단타" in response_data["portfolios_created"]
    assert "정찰병" in response_data["portfolios_created"]
    
    # Step 3: Login with valid credentials
    
    # Step 3: Login with valid credentials
    login_data = {
        "email": register_data["email"],
        "password": register_data["password"]
    }
    
    response = client.post("/api/v1/auth/login", json=login_data)
    assert response.status_code == 200
    
    login_response = response.json()
    assert "user" in login_response
    assert "token" in login_response
    
    token_data = login_response["token"]
    assert "access_token" in token_data
    assert "token_type" in token_data
    assert token_data["token_type"] == "bearer"
    
    access_token = token_data["access_token"]
    
    # Step 4: Access protected endpoint with token
    headers = {"Authorization": f"Bearer {access_token}"}
    response = client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 200
    
    me_data = response.json()
    assert me_data["id"] == user_id
    assert me_data["email"] == register_data["email"]


def test_duplicate_email_registration(client: TestClient):
    """Test that duplicate email registration is rejected."""
    register_data = {
        "email": "duplicate@example.com",
        "password": "Password123",
        "full_name": "First User"
    }
    
    # First registration succeeds
    response = client.post("/api/v1/auth/register", json=register_data)
    assert response.status_code == 201  # REST API: 201 for resource creation
    
    # Second registration with same email fails
    response = client.post("/api/v1/auth/register", json=register_data)
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"].lower()


def test_invalid_password_format(client: TestClient):
    """Test that weak passwords are rejected."""
    # Password too short
    response = client.post("/api/v1/auth/register", json={
        "email": "weak@example.com",
        "password": "123",
        "full_name": "Weak User"
    })
    assert response.status_code == 422  # Validation error


def test_invalid_email_format(client: TestClient):
    """Test that invalid email formats are rejected."""
    response = client.post("/api/v1/auth/register", json={
        "email": "not-an-email",
        "password": "ValidPass123",
        "full_name": "Invalid Email User"
    })
    assert response.status_code == 422  # Validation error


def test_login_with_wrong_password(client: TestClient):
    """Test that login with wrong password fails."""
    # Register user
    register_data = {
        "email": "wrongpass@example.com",
        "password": "CorrectPass123",
        "full_name": "Test User"
    }
    response = client.post("/api/v1/auth/register", json=register_data)
    assert response.status_code == 201  # REST API: 201 for resource creation
    
    # Try login with wrong password
    login_data = {
        "email": register_data["email"],
        "password": "WrongPass123"
    }
    response = client.post("/api/v1/auth/login", json=login_data)
    assert response.status_code == 401
    detail = response.json()["detail"].lower()
    assert "invalid" in detail or "incorrect" in detail  # Accept both wordings


def test_login_with_nonexistent_email(client: TestClient):
    """Test that login with non-existent email fails."""
    login_data = {
        "email": "nonexistent@example.com",
        "password": "AnyPassword123"
    }
    response = client.post("/api/v1/auth/login", json=login_data)
    assert response.status_code == 401
    detail = response.json()["detail"].lower()
    assert "invalid" in detail or "incorrect" in detail  # Accept both wordings


def test_protected_endpoint_without_token(client: TestClient):
    """Test that protected endpoints require authentication."""
    response = client.get("/api/v1/auth/me")
    assert response.status_code in [401, 403]  # Accept both Unauthorized and Forbidden
    assert "not authenticated" in response.json()["detail"].lower() or "forbidden" in response.json()["detail"].lower()


def test_protected_endpoint_with_invalid_token(client: TestClient):
    """Test that invalid tokens are rejected."""
    headers = {"Authorization": "Bearer invalid.token.here"}
    response = client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 401


def test_token_refresh_flow(client: TestClient, authenticated_client: tuple):
    """Test token refresh mechanism (if implemented)."""
    auth_client, user_data = authenticated_client
    
    # Verify current token works
    response = auth_client.get("/api/v1/auth/me")
    assert response.status_code == 200
    
    # If refresh endpoint exists, test it
    # This is a placeholder for future implementation
    # response = auth_client.post("/api/v1/auth/refresh")
    # assert response.status_code == 200
    # assert "access_token" in response.json()


def test_logout_flow(client: TestClient, authenticated_client: tuple):
    """Test logout functionality (if implemented)."""
    auth_client, user_data = authenticated_client
    
    # Verify authenticated
    response = auth_client.get("/api/v1/auth/me")
    assert response.status_code == 200
    
    # If logout endpoint exists, test it
    # This is a placeholder for future implementation
    # response = auth_client.post("/api/v1/auth/logout")
    # assert response.status_code == 200
    
    # Verify token is invalidated (if session-based)
    # response = auth_client.get("/api/v1/auth/me")
    # assert response.status_code == 401
