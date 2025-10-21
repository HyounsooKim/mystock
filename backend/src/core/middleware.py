"""Middleware for request processing and authentication.

Provides authentication middleware for protected routes.
"""

from fastapi import Request, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from src.core.security import get_user_id_from_token


# HTTP Bearer token security scheme
security = HTTPBearer()


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> int:
    """Extract and validate user ID from JWT token.
    
    Args:
        credentials: HTTP Authorization credentials
        
    Returns:
        User ID from token
        
    Raises:
        HTTPException: If token is invalid or missing
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials
    user_id = get_user_id_from_token(token)
    
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user_id


async def get_optional_user_id(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))
) -> Optional[int]:
    """Extract user ID from JWT token if present (for optional auth).
    
    Args:
        credentials: HTTP Authorization credentials (optional)
        
    Returns:
        User ID from token if present and valid, None otherwise
    """
    if credentials is None:
        return None
    
    token = credentials.credentials
    return get_user_id_from_token(token)
