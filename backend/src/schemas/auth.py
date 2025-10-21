"""Pydantic schemas for authentication endpoints.

Request/response models for user registration, login, and profile.
"""

from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
from datetime import datetime
import re


class UserRegisterRequest(BaseModel):
    """User registration request schema."""
    
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, max_length=100, description="Password (8-100 characters)")
    
    @validator('password')
    def validate_password_strength(cls, v):
        """Validate password contains uppercase, lowercase, and number."""
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one number')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "SecurePass123"
            }
        }


class UserLoginRequest(BaseModel):
    """User login request schema."""
    
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password")
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "SecurePass123"
            }
        }


class TokenResponse(BaseModel):
    """JWT token response schema."""
    
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")
    
    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 86400
            }
        }


class UserProfileResponse(BaseModel):
    """User profile response schema."""
    
    id: int = Field(..., description="User ID")
    email: str = Field(..., description="User email address")
    created_at: datetime = Field(..., description="Account creation timestamp")
    last_login_at: Optional[datetime] = Field(None, description="Last login timestamp")
    is_active: bool = Field(..., description="Account active status")
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "email": "user@example.com",
                "created_at": "2024-01-20T10:00:00",
                "last_login_at": "2024-01-21T15:30:00",
                "is_active": True
            }
        }


class UserRegisterResponse(BaseModel):
    """User registration response schema."""
    
    user: UserProfileResponse
    token: TokenResponse
    portfolios_created: list[str] = Field(..., description="List of auto-created portfolio names")
    
    class Config:
        json_schema_extra = {
            "example": {
                "user": {
                    "id": 1,
                    "email": "user@example.com",
                    "created_at": "2024-01-20T10:00:00",
                    "last_login_at": "2024-01-20T10:00:00",
                    "is_active": True
                },
                "token": {
                    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "token_type": "bearer",
                    "expires_in": 86400
                },
                "portfolios_created": ["장기투자", "단타", "정찰병"]
            }
        }


class UserLoginResponse(BaseModel):
    """User login response schema."""
    
    user: UserProfileResponse
    token: TokenResponse
    
    class Config:
        json_schema_extra = {
            "example": {
                "user": {
                    "id": 1,
                    "email": "user@example.com",
                    "created_at": "2024-01-20T10:00:00",
                    "last_login_at": "2024-01-21T15:30:00",
                    "is_active": True
                },
                "token": {
                    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "token_type": "bearer",
                    "expires_in": 86400
                }
            }
        }
