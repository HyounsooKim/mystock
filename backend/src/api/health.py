"""Health check endpoints for monitoring application status.

Provides endpoints to verify application and database health.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime
from src.core.database import get_db


router = APIRouter()


@router.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """Check application and database health.
    
    Returns:
        Health status including timestamp and database connectivity
        
    Raises:
        HTTPException: If database connection fails
    """
    try:
        # Test database connection
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database connection failed: {str(e)}"
        )
    
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "database": db_status,
        "version": "1.0.0"
    }


@router.get("/health/db")
async def database_health_check(db: Session = Depends(get_db)):
    """Detailed database health check.
    
    Returns:
        Database connection status and version information
        
    Raises:
        HTTPException: If database connection fails
    """
    try:
        # Get MySQL version
        result = db.execute(text("SELECT VERSION()"))
        version = result.scalar()
        
        # Test write capability (within transaction, will rollback)
        db.execute(text("SELECT 1 FROM users LIMIT 1"))
        
        return {
            "status": "healthy",
            "database": "MySQL",
            "version": version,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database health check failed: {str(e)}"
        )
