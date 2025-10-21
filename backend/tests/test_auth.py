"""Tests for authentication API endpoints.

Tests user registration, login, profile retrieval, and account deactivation.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.models import User, Portfolio


class TestUserRegistration:
    """Tests for POST /api/v1/auth/register endpoint."""
    
    def test_register_success(self, client: TestClient, db: Session):
        """Test successful user registration."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "SecurePass123"
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        
        # Check user data
        assert data["user"]["email"] == "newuser@example.com"
        assert data["user"]["is_active"] is True
        assert "id" in data["user"]
        assert "created_at" in data["user"]
        
        # Check token
        assert data["token"]["token_type"] == "bearer"
        assert "access_token" in data["token"]
        assert data["token"]["expires_in"] == 86400
        
        # Check portfolios created
        assert len(data["portfolios_created"]) == 3
        assert "장기투자" in data["portfolios_created"]
        assert "단타" in data["portfolios_created"]
        assert "정찰병" in data["portfolios_created"]
        
        # Verify user in database
        user = db.query(User).filter(User.email == "newuser@example.com").first()
        assert user is not None
        assert user.is_active is True
        
        # Verify portfolios in database
        portfolios = db.query(Portfolio).filter(Portfolio.user_id == user.id).all()
        assert len(portfolios) == 3
    
    def test_register_duplicate_email(self, client: TestClient, test_user: User):
        """Test registration with existing email."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",
                "password": "SecurePass123"
            }
        )
        
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()
    
    def test_register_weak_password(self, client: TestClient):
        """Test registration with weak password."""
        # No uppercase
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "weakpass123"
            }
        )
        assert response.status_code == 422
        
        # No lowercase
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "WEAKPASS123"
            }
        )
        assert response.status_code == 422
        
        # No number
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "WeakPassword"
            }
        )
        assert response.status_code == 422
    
    def test_register_invalid_email(self, client: TestClient):
        """Test registration with invalid email format."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "notanemail",
                "password": "SecurePass123"
            }
        )
        
        assert response.status_code == 422


class TestUserLogin:
    """Tests for POST /api/v1/auth/login endpoint."""
    
    def test_login_success(self, client: TestClient, test_user: User):
        """Test successful user login."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@example.com",
                "password": "TestPass123"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check user data
        assert data["user"]["email"] == "test@example.com"
        assert data["user"]["id"] == test_user.id
        assert data["user"]["is_active"] is True
        
        # Check token
        assert data["token"]["token_type"] == "bearer"
        assert "access_token" in data["token"]
        assert data["token"]["expires_in"] == 86400
    
    def test_login_wrong_password(self, client: TestClient, test_user: User):
        """Test login with incorrect password."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@example.com",
                "password": "WrongPass123"
            }
        )
        
        assert response.status_code == 401
        assert "invalid" in response.json()["detail"].lower()
    
    def test_login_nonexistent_user(self, client: TestClient):
        """Test login with non-existent email."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "TestPass123"
            }
        )
        
        assert response.status_code == 401
        assert "invalid" in response.json()["detail"].lower()
    
    def test_login_inactive_account(self, client: TestClient, test_user: User, db: Session):
        """Test login with deactivated account."""
        # Deactivate user
        test_user.is_active = False
        db.commit()
        
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@example.com",
                "password": "TestPass123"
            }
        )
        
        assert response.status_code == 401
        assert "inactive" in response.json()["detail"].lower()


class TestUserProfile:
    """Tests for GET /api/v1/auth/me endpoint."""
    
    def test_get_profile_success(self, client: TestClient, test_user: User, auth_headers: dict):
        """Test successful profile retrieval."""
        response = client.get(
            "/api/v1/auth/me",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["email"] == "test@example.com"
        assert data["id"] == test_user.id
        assert data["is_active"] is True
        assert "created_at" in data
    
    def test_get_profile_no_token(self, client: TestClient):
        """Test profile retrieval without authentication."""
        response = client.get("/api/v1/auth/me")
        
        assert response.status_code == 403  # Forbidden without token
    
    def test_get_profile_invalid_token(self, client: TestClient):
        """Test profile retrieval with invalid token."""
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid_token"}
        )
        
        assert response.status_code == 401


class TestAccountDeactivation:
    """Tests for DELETE /api/v1/auth/me endpoint."""
    
    def test_deactivate_account_success(
        self, 
        client: TestClient, 
        test_user: User, 
        auth_headers: dict,
        db: Session
    ):
        """Test successful account deactivation."""
        response = client.delete(
            "/api/v1/auth/me",
            headers=auth_headers
        )
        
        assert response.status_code == 204
        
        # Verify user is deactivated in database
        db.refresh(test_user)
        assert test_user.is_active is False
    
    def test_deactivate_account_no_token(self, client: TestClient):
        """Test account deactivation without authentication."""
        response = client.delete("/api/v1/auth/me")
        
        assert response.status_code == 403
