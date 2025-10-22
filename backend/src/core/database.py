"""Database connection and session management for MyStock application.

This module provides Azure Cosmos DB client and container access
for all database operations.
"""

from azure.cosmos import CosmosClient, PartitionKey, exceptions
from typing import Optional
import logging
from .config import settings

logger = logging.getLogger(__name__)

# Legacy SQLAlchemy Base (kept for backward compatibility with old migrations)
# This is a dummy placeholder and should not be used for new code
Base = None

# Global Cosmos client instance
_cosmos_client: Optional[CosmosClient] = None
_database = None
_container = None


def get_cosmos_client() -> CosmosClient:
    """Get or create Cosmos DB client singleton.
    
    Returns:
        CosmosClient: Azure Cosmos DB client instance
    """
    global _cosmos_client
    
    if _cosmos_client is None:
        logger.info(f"Creating Cosmos DB client for endpoint: {settings.COSMOS_ENDPOINT}")
        
        # For local emulator (localhost), disable SSL verification
        connection_verify = True
        if "localhost" in settings.COSMOS_ENDPOINT or "127.0.0.1" in settings.COSMOS_ENDPOINT:
            logger.warning("Detected localhost endpoint - disabling SSL verification for emulator")
            connection_verify = False
        
        _cosmos_client = CosmosClient(
            url=settings.COSMOS_ENDPOINT,
            credential=settings.COSMOS_KEY,
            connection_verify=connection_verify
        )
    
    return _cosmos_client


def get_database():
    """Get or create Cosmos DB database instance.
    
    Returns:
        DatabaseProxy: Cosmos DB database instance
    """
    global _database
    
    if _database is None:
        client = get_cosmos_client()
        _database = client.get_database_client(settings.COSMOS_DATABASE_NAME)
        logger.info(f"Connected to database: {settings.COSMOS_DATABASE_NAME}")
    
    return _database


def get_container():
    """Get or create Cosmos DB container instance.
    
    Returns:
        ContainerProxy: Cosmos DB container instance for users
    """
    global _container
    
    if _container is None:
        database = get_database()
        _container = database.get_container_client(settings.COSMOS_CONTAINER_NAME)
        logger.info(f"Connected to container: {settings.COSMOS_CONTAINER_NAME}")
    
    return _container


def initialize_cosmos_db():
    """Initialize Cosmos DB database and container if they don't exist.
    
    This function creates the database and container with proper partition key
    and indexing policy. Should be called during application startup.
    """
    client = get_cosmos_client()
    
    # Create database if it doesn't exist
    try:
        database = client.create_database_if_not_exists(id=settings.COSMOS_DATABASE_NAME)
        logger.info(f"Database ready: {settings.COSMOS_DATABASE_NAME}")
    except exceptions.CosmosHttpResponseError as e:
        logger.error(f"Error creating database: {e}")
        raise
    
    # Create container if it doesn't exist
    # Partition key: /email (each user is a separate partition)
    try:
        container = database.create_container_if_not_exists(
            id=settings.COSMOS_CONTAINER_NAME,
            partition_key=PartitionKey(path="/email"),
            offer_throughput=400  # 400 RU/s (minimum for production)
        )
        logger.info(f"Container ready: {settings.COSMOS_CONTAINER_NAME} with partition key /email")
    except exceptions.CosmosHttpResponseError as e:
        logger.error(f"Error creating container: {e}")
        raise
    
    return container


def close_cosmos_client():
    """Close Cosmos DB client connection.
    
    Should be called during application shutdown.
    """
    global _cosmos_client, _database, _container
    
    if _cosmos_client is not None:
        # CosmosClient doesn't have close() method
        # Just clear the references
        _cosmos_client = None
        _database = None
        _container = None
        logger.info("Cosmos DB client closed")


# Dependency function for FastAPI (replaces get_db)
def get_db():
    """Dependency function to get Cosmos DB container.
    
    Yields:
        ContainerProxy: Cosmos DB container instance
        
    Example:
        @app.get("/users")
        def get_users(container = Depends(get_db)):
            query = "SELECT * FROM c WHERE c.type = 'user'"
            return list(container.query_items(query, enable_cross_partition_query=True))
    """
    try:
        container = get_container()
        yield container
    except Exception as e:
        logger.error(f"Error getting container: {e}")
        raise
