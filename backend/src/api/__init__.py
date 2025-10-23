"""API routes aggregation.

Combines all API routers under /api/v1 prefix.
"""

from fastapi import APIRouter

from . import health, auth, watchlist, stocks, portfolios, top_movers

api_router = APIRouter()

api_router.include_router(health.router, prefix="/health", tags=["Health"])
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(watchlist.router, prefix="/watchlist", tags=["Watchlist"])
api_router.include_router(stocks.router, prefix="/stocks", tags=["Stocks"])
api_router.include_router(portfolios.router, prefix="/portfolios", tags=["Portfolios"])
api_router.include_router(top_movers.router, prefix="/stocks", tags=["Top Movers"])
