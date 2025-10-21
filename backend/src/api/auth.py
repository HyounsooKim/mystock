"""Authentication API endpoints.

Handles user registration, login, and profile management.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from src.core.database import get_db
from src.core.security import hash_password, verify_password, create_access_token
from src.core.config import settings
from src.core.middleware import get_current_user_id
from src.models import User, Portfolio
from src.schemas.auth import (
    UserRegisterRequest,
    UserLoginRequest,
    TokenResponse,
    UserProfileResponse,
    UserRegisterResponse,
    UserLoginResponse,
)


router = APIRouter()


@router.post("/register", response_model=UserRegisterResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    request: UserRegisterRequest,
    db: Session = Depends(get_db)
):
    """Register a new user account.
    
    Creates a new user with hashed password and automatically creates
    3 predefined portfolios (장기투자, 단타, 정찰병).
    
    Args:
        request: User registration data (email, password)
        db: Database session
        
    Returns:
        User profile, JWT token, and list of created portfolios
        
    Raises:
        HTTPException 400: If email already exists
        HTTPException 500: If portfolio creation fails
    """
    # Check if email already exists
    existing_user = db.query(User).filter(User.email == request.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    try:
        # Create user
        user = User(
            email=request.email,
            password_hash=hash_password(request.password),
            is_active=True,
            last_login_at=datetime.utcnow()
        )
        db.add(user)
        db.flush()  # Get user.id without committing
        
        # Auto-create 3 predefined portfolios
        portfolio_names = Portfolio.get_predefined_names()
        portfolios = []
        
        for name in portfolio_names:
            portfolio = Portfolio(
                user_id=user.id,
                name=name
            )
            db.add(portfolio)
            portfolios.append(name)
        
        db.commit()
        db.refresh(user)
        
        # Generate JWT token
        access_token = create_access_token(
            data={"sub": str(user.id)},
            expires_delta=timedelta(hours=settings.ACCESS_TOKEN_EXPIRE_HOURS)
        )
        
        token_response = TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_HOURS * 3600
        )
        
        return UserRegisterResponse(
            user=UserProfileResponse.model_validate(user),
            token=token_response,
            portfolios_created=portfolios
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user: {str(e)}"
        )


@router.post("/login", response_model=UserLoginResponse)
async def login_user(
    request: UserLoginRequest,
    db: Session = Depends(get_db)
):
    """Authenticate user and return JWT token.
    
    Verifies email and password, updates last login timestamp,
    and generates a new JWT token.
    
    Args:
        request: User login credentials (email, password)
        db: Database session
        
    Returns:
        User profile and JWT token
        
    Raises:
        HTTPException 401: If credentials are invalid or account is inactive
    """
    # Find user by email
    user = db.query(User).filter(User.email == request.email).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Verify password
    if not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Check if account is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is inactive"
        )
    
    # Update last login timestamp
    user.last_login_at = datetime.utcnow()
    db.commit()
    db.refresh(user)
    
    # Generate JWT token
    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=timedelta(hours=settings.ACCESS_TOKEN_EXPIRE_HOURS)
    )
    
    token_response = TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_HOURS * 3600
    )
    
    return UserLoginResponse(
        user=UserProfileResponse.model_validate(user),
        token=token_response
    )


@router.get("/me", response_model=UserProfileResponse)
async def get_current_user_profile(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Get current authenticated user's profile.
    
    Requires valid JWT token in Authorization header.
    
    Args:
        user_id: User ID from JWT token
        db: Database session
        
    Returns:
        User profile information
        
    Raises:
        HTTPException 404: If user not found
    """
    user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserProfileResponse.model_validate(user)


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_account(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Deactivate current user's account (soft delete).
    
    Sets is_active to False instead of deleting the record.
    Requires valid JWT token in Authorization header.
    
    Args:
        user_id: User ID from JWT token
        db: Database session
        
    Raises:
        HTTPException 404: If user not found
    """
    user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user.is_active = False
    db.commit()
    
    return None
