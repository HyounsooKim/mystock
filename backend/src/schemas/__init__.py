"""Pydantic schemas for request/response validation.

Exports all schema classes for API endpoints.
"""

from .auth import (
    UserRegisterRequest,
    UserLoginRequest,
    TokenResponse,
    UserProfileResponse,
)
from .watchlist import (
    WatchlistItemResponse,
    WatchlistAddRequest,
    WatchlistUpdateRequest,
    WatchlistResponse,
    WatchlistReorderRequest,
)
from .stocks import (
    PeriodEnum,
    MarketEnum,
    MarketStatusEnum,
    StockQuoteResponse,
    CandlestickResponse,
    ChartDataResponse,
)
from .portfolios import (
    PortfolioResponse,
    HoldingResponse,
    AddHoldingRequest,
    UpdateHoldingRequest,
    PortfolioSummaryResponse,
    PortfolioSummary,
)

__all__ = [
    # Auth schemas
    "UserRegisterRequest",
    "UserLoginRequest",
    "TokenResponse",
    "UserProfileResponse",
    # Watchlist schemas
    "WatchlistItemResponse",
    "WatchlistAddRequest",
    "WatchlistUpdateRequest",
    "WatchlistResponse",
    "WatchlistReorderRequest",
    # Stock schemas
    "PeriodEnum",
    "MarketEnum",
    "MarketStatusEnum",
    "StockQuoteResponse",
    "CandlestickResponse",
    "ChartDataResponse",
    # Portfolio schemas
    "PortfolioResponse",
    "HoldingResponse",
    "AddHoldingRequest",
    "UpdateHoldingRequest",
    "PortfolioSummaryResponse",
    "PortfolioSummary",
]
