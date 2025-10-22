"""FastAPI application entry point for MyStock.

Initializes FastAPI app with CORS middleware, routes, and lifecycle events.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from src.core.config import settings
from src.core.database import initialize_cosmos_db, close_cosmos_client
from src.api import api_router


# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events.
    
    Handles startup and shutdown tasks.
    """
    # Startup
    logger.info("Starting MyStock API...")
    logger.info(f"Cosmos DB endpoint: {settings.COSMOS_ENDPOINT}")
    logger.info(f"Cosmos DB database: {settings.COSMOS_DATABASE_NAME}")
    logger.info(f"Cosmos DB container: {settings.COSMOS_CONTAINER_NAME}")
    logger.info(f"Debug mode: {settings.DEBUG}")
    logger.info(f"CORS origins: {settings.CORS_ORIGINS}")
    
    # Initialize Cosmos DB
    try:
        initialize_cosmos_db()
        logger.info("Cosmos DB initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Cosmos DB: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down MyStock API...")
    close_cosmos_client()
    logger.info("Cosmos DB connection closed")


# Initialize FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Stock portfolio management API with watchlist and holdings tracking",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)


# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_CREDENTIALS,
    allow_methods=settings.CORS_METHODS,
    allow_headers=settings.CORS_HEADERS,
)


# Include API routes under /api/v1 prefix
app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": "/api/v1/health"
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=settings.DEBUG,
        log_level="debug" if settings.DEBUG else "info"
    )
