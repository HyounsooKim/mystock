"""Health check endpoints for monitoring application status.

Provides endpoints to verify application and database health.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from datetime import datetime
from src.core.database import get_db


router = APIRouter()


@router.get("")  # "/" 대신 "" 사용
async def health_check(container = Depends(get_db)):
    """Check application and database health.
    
    Returns:
        Health status including timestamp and database connectivity
        
    Raises: 
        HTTPException: If database connection fails
    """
    try:
        # Test Cosmos DB connection with a simple query
        query = "SELECT VALUE COUNT(1) FROM c"
        result = list(container.query_items(
            query=query,
            enable_cross_partition_query=True
        ))
        db_status = "connected"
        user_count = result[0] if result else 0
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database connection failed: {str(e)}"
        )
    
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "database": db_status,
        "database_type": "Azure Cosmos DB NoSQL",
        "user_count": user_count,
        "version": "2.0.0"
    }


@router.get("/db")  # "/health/db" 대신 "/db"
async def database_health_check(container = Depends(get_db)):
    """Detailed database health check.
    
    Returns:
        Database connection status and version information
        
    Raises:
        HTTPException: If database connection fails
    """
    try:
        # Test Cosmos DB connection
        query = "SELECT VALUE COUNT(1) FROM c"
        result = list(container.query_items(
            query=query,
            enable_cross_partition_query=True
        ))
        
        return {
            "status": "healthy",
            "database": "connected",
            "database_type": "Azure Cosmos DB NoSQL",
            "user_count": result[0] if result else 0,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database health check failed: {str(e)}"
        )
