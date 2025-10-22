"""Models package for MyStock application.

Exports all Pydantic document models for Cosmos DB.
"""

from src.models.user import UserDocument, WatchlistItem, PortfolioItem, HoldingItem
# Legacy SQLAlchemy models (commented out for Cosmos DB migration)
# from src.models.portfolio import Portfolio
# from src.models.watchlist import Watchlist
# from src.models.holding import Holding
# from src.models.stock_quote import StockQuote
# from src.models.candlestick_data import CandlestickData


__all__ = [
    "UserDocument",
    "WatchlistItem",
    "PortfolioItem",
    "HoldingItem",
]
