"""Configuration management for MyStock application.

Loads environment variables and provides typed configuration settings.
"""

from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import List, Union, Optional
import secrets
from pathlib import Path
from dotenv import load_dotenv


# Get the backend directory (parent of src)
BACKEND_DIR = Path(__file__).parent.parent.parent
ENV_FILE = BACKEND_DIR / ".env"

# Load .env file before anything else
load_dotenv(ENV_FILE)


class Settings(BaseSettings):
    """Application settings loaded from environment variables.
    
    All settings can be overridden via .env file in backend directory.
    """
    
    # Application Settings
    APP_NAME: str = "MyStock API"
    APP_VERSION: str = "1.0.0"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    DEBUG: bool = False
    
    # Database Settings - Cosmos DB
    COSMOS_ENDPOINT: str
    COSMOS_KEY: str
    COSMOS_DATABASE_NAME: str = "mystockdb"
    COSMOS_CONTAINER_NAME: str = "users"
    
    # Legacy MySQL settings (commented out for Cosmos DB migration)
    # DATABASE_URL: Optional[str] = None
    # DATABASE_POOL_SIZE: int = 10
    # DATABASE_MAX_OVERFLOW: int = 20
    # DATABASE_POOL_RECYCLE: int = 3600
    
    # Security Settings
    # Use JWT_SECRET env var if available, otherwise SECRET_KEY, otherwise generate random
    SECRET_KEY: Optional[str] = None
    JWT_SECRET: Optional[str] = None
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_HOURS: int = 24
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Prioritize JWT_SECRET over SECRET_KEY
        if self.JWT_SECRET:
            self.SECRET_KEY = self.JWT_SECRET
        elif not self.SECRET_KEY:
            self.SECRET_KEY = secrets.token_urlsafe(32)
    
    # CORS Settings
    CORS_ORIGINS: Union[List[str], str] = "http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000,http://127.0.0.1:5173"
    CORS_CREDENTIALS: bool = True
    CORS_METHODS: List[str] = ["GET", "POST", "PUT", "DELETE", "PATCH"]
    CORS_HEADERS: List[str] = ["*"]
    
    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS_ORIGINS from comma-separated string or list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    # Stock API Settings
    STOCK_CACHE_TTL_SECONDS: int = 300  # 5 minutes
    STOCK_API_TIMEOUT_SECONDS: int = 10
    STOCK_API_MAX_RETRIES: int = 3
    
    # Alpha Vantage API Settings
    ALPHA_VANTAGE_API_KEY: Optional[str] = None
    ALPHA_VANTAGE_USE_DELAYED: bool = True  # Default to delayed mode (15min delay, higher rate limit)
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    
    # Pagination
    MAX_PAGE_SIZE: int = 100
    DEFAULT_PAGE_SIZE: int = 20
    
    # Business Logic Constraints
    MAX_WATCHLIST_ITEMS: int = 50
    MAX_HOLDINGS_PER_PORTFOLIO: int = 100
    PORTFOLIO_NAMES: List[str] = ["장기투자", "단타", "정찰병"]
    
    class Config:
        """Pydantic configuration."""
        env_file = str(ENV_FILE)
        env_file_encoding = "utf-8"
        case_sensitive = True


# Global settings instance
settings = Settings()
