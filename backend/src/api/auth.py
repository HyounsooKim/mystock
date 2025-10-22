"""Authentication API endpoints.

Handles user registration, login, and profile management with Cosmos DB.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from azure.cosmos import exceptions
from datetime import datetime, timedelta
import logging

from src.core.database import get_db
from src.core.security import hash_password, verify_password, create_access_token
from src.core.config import settings
from src.core.middleware import get_current_user_id
from src.models.user import UserDocument, PortfolioItem
from src.schemas.auth import (
    UserRegisterRequest,
    UserLoginRequest,
    TokenResponse,
    UserProfileResponse,
    UserRegisterResponse,
    UserLoginResponse,
)


router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/register", response_model=UserRegisterResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    request: UserRegisterRequest,
    container = Depends(get_db)
):
    """Register a new user account.
    
    Creates a new user document with hashed password and automatically creates
    3 predefined portfolios (장기투자, 단타, 정찰병) embedded in the user document.
    
    Args:
        request: User registration data (email, password)
        container: Cosmos DB container
        
    Returns:
        User profile, JWT token, and list of created portfolios
        
    Raises:
        HTTPException 400: If email already exists
        HTTPException 500: If user creation fails
    """
    # Check if email already exists
    query = "SELECT * FROM c WHERE c.email = @email"
    parameters = [{"name": "@email", "value": request.email}]
    
    try:
        existing_users = list(container.query_items(
            query=query,
            parameters=parameters,
            enable_cross_partition_query=True
        ))
        
        if existing_users:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
    except exceptions.CosmosHttpResponseError as e:
        logger.error(f"Error checking existing user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database query failed"
        )
    
    try:
        # Create user document with 3 predefined portfolios
        portfolio_names = settings.PORTFOLIO_NAMES  # ["장기투자", "단타", "정찰병"]
        portfolios = [
            PortfolioItem(name=name)
            for name in portfolio_names
        ]
        
        user_doc = UserDocument(
            email=request.email,
            password_hash=hash_password(request.password),
            is_active=True,
            last_login_at=datetime.utcnow(),
            portfolios=portfolios
        )
        
        # Insert document into Cosmos DB
        created_item = container.create_item(body=user_doc.to_cosmos_dict())
        logger.info(f"User registered: {request.email}")
        
        # Generate JWT token (use document id)
        access_token = create_access_token(
            data={"sub": created_item["id"]},
            expires_delta=timedelta(hours=settings.ACCESS_TOKEN_EXPIRE_HOURS)
        )
        
        token_response = TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_HOURS * 3600
        )
        
        # Convert to response model
        user_response = UserProfileResponse(
            id=created_item["id"],
            email=created_item["email"],
            created_at=created_item["created_at"],
            last_login_at=created_item.get("last_login_at"),
            is_active=created_item["is_active"]
        )
        
        return UserRegisterResponse(
            user=user_response,
            token=token_response,
            portfolios_created=portfolio_names
        )
        
    except exceptions.CosmosHttpResponseError as e:
        logger.error(f"Error creating user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user: {str(e)}"
        )


@router.post("/login", response_model=UserLoginResponse)
async def login_user(
    request: UserLoginRequest,
    container = Depends(get_db)
):
    """Authenticate user and return JWT token.
    
    Verifies email and password, updates last login timestamp,
    and generates a new JWT token.
    
    Args:
        request: User login credentials (email, password)
        container: Cosmos DB container
        
    Returns:
        User profile and JWT token
        
    Raises:
        HTTPException 401: If credentials are invalid or account is inactive
    """
    # Find user by email
    query = "SELECT * FROM c WHERE c.email = @email"
    parameters = [{"name": "@email", "value": request.email}]
    
    try:
        users = list(container.query_items(
            query=query,
            parameters=parameters,
            enable_cross_partition_query=True
        ))
        
        if not users:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        user_data = users[0]
        
    except exceptions.CosmosHttpResponseError as e:
        logger.error(f"Error querying user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database query failed"
        )
    
    # Verify password
    if not verify_password(request.password, user_data["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Check if account is active
    if not user_data.get("is_active", False):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is inactive"
        )
    
    # Update last login timestamp
    user_data["last_login_at"] = datetime.utcnow().isoformat()
    
    try:
        updated_user = container.replace_item(
            item=user_data["id"],
            body=user_data
        )
        logger.info(f"User logged in: {request.email}")
        
    except exceptions.CosmosHttpResponseError as e:
        logger.error(f"Error updating user: {e}")
        # Non-critical error, continue with login
        updated_user = user_data
    
    # Generate JWT token
    access_token = create_access_token(
        data={"sub": updated_user["id"]},
        expires_delta=timedelta(hours=settings.ACCESS_TOKEN_EXPIRE_HOURS)
    )
    
    token_response = TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_HOURS * 3600
    )
    
    user_response = UserProfileResponse(
        id=updated_user["id"],
        email=updated_user["email"],
        created_at=updated_user["created_at"],
        last_login_at=updated_user.get("last_login_at"),
        is_active=updated_user["is_active"]
    )
    
    return UserLoginResponse(
        user=user_response,
        token=token_response
    )


@router.get("/me", response_model=UserProfileResponse)
async def get_current_user_profile(
    user_id: str = Depends(get_current_user_id),
    container = Depends(get_db)
):
    """Get current authenticated user's profile.
    
    Requires valid JWT token in Authorization header.
    
    Args:
        user_id: User ID from JWT token (document id)
        container: Cosmos DB container
        
    Returns:
        User profile information
        
    Raises:
        HTTPException 404: If user not found
    """
    # Query user by document id
    query = "SELECT * FROM c WHERE c.id = @user_id AND c.is_active = true"
    parameters = [{"name": "@user_id", "value": user_id}]
    
    try:
        users = list(container.query_items(
            query=query,
            parameters=parameters,
            enable_cross_partition_query=True
        ))
        
        if not users:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        user_data = users[0]
        
        return UserProfileResponse(
            id=user_data["id"],
            email=user_data["email"],
            created_at=user_data["created_at"],
            last_login_at=user_data.get("last_login_at"),
            is_active=user_data["is_active"]
        )
        
    except exceptions.CosmosHttpResponseError as e:
        logger.error(f"Error querying user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database query failed"
        )


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_account(
    user_id: str = Depends(get_current_user_id),
    container = Depends(get_db)
):
    """Deactivate current user's account (soft delete).
    
    Sets is_active to False instead of deleting the document.
    Requires valid JWT token in Authorization header.
    
    Args:
        user_id: User ID from JWT token
        container: Cosmos DB container
        
    Raises:
        HTTPException 404: If user not found
    """
    # Query user by document id
    query = "SELECT * FROM c WHERE c.id = @user_id AND c.is_active = true"
    parameters = [{"name": "@user_id", "value": user_id}]
    
    try:
        users = list(container.query_items(
            query=query,
            parameters=parameters,
            enable_cross_partition_query=True
        ))
        
        if not users:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        user_data = users[0]
        user_data["is_active"] = False
        
        container.replace_item(
            item=user_data["id"],
            body=user_data
        )
        
        logger.info(f"User deactivated: {user_data['email']}")
        return None
        
    except exceptions.CosmosHttpResponseError as e:
        logger.error(f"Error deactivating user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database operation failed"
        )
