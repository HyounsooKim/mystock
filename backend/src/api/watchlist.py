"""Watchlist API endpoints.

Handles watchlist CRUD operations and reordering with Cosmos DB.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from azure.cosmos import exceptions
from typing import List
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

from src.core.database import get_db
from src.core.config import settings
from src.core.middleware import get_current_user_id
from src.models.user import UserDocument, WatchlistItem
from src.schemas.watchlist import (
    WatchlistAddRequest,
    WatchlistUpdateRequest,
    WatchlistReorderRequest,
    WatchlistItemResponse,
    WatchlistResponse,
)
from src.services.stock_data_service import StockDataService


router = APIRouter()
logger = logging.getLogger(__name__)

# Create stock data service instance
stock_service = StockDataService()

# Thread pool for parallel API calls
executor = ThreadPoolExecutor(max_workers=5)


def get_stock_price(symbol: str):
    """Get current stock price from Alpha Vantage.
    
    Args:
        symbol: Stock ticker symbol
        
    Returns:
        Current stock price (float), or None if unavailable
    """
    try:
        logger.info(f"[PRICE] Fetching price for symbol: {symbol}")
        quote_data = stock_service.get_quote(symbol)
        
        if not quote_data:
            logger.warning(f"[PRICE] No data returned for {symbol}")
            return None
        
        price = quote_data.get('current_price')
        logger.info(f"[PRICE] {symbol} - Returning: {price}")
        
        return price
    except Exception as e:
        logger.error(f"[PRICE] Error fetching price for {symbol}: {e}", exc_info=True)
        return None


def get_stock_info(symbol: str):
    """Get comprehensive stock information from Alpha Vantage.
    
    Args:
        symbol: Stock ticker symbol
        
    Returns:
        Dictionary with price, change, percent, and company name (market cap excluded to reduce API calls)
    """
    try:
        logger.info(f"[INFO] Fetching info for symbol: {symbol}")
        quote_data = stock_service.get_quote(symbol)
        
        if not quote_data:
            logger.warning(f"[INFO] No data returned for {symbol}")
            return {
                'current_price': None,
                'price_change': None,
                'change_percent': None,
                'market_cap': None,
                'company_name': symbol
            }
        
        current_price = quote_data.get('current_price')
        change_percent = quote_data.get('daily_change_pct')
        
        # Calculate price change from percentage and current price
        price_change = None
        if current_price and change_percent:
            # change_pct is already in percentage form
            previous_close = current_price / (1 + change_percent / 100)
            price_change = current_price - previous_close
        
        result = {
            'current_price': current_price,
            'price_change': price_change,
            'change_percent': change_percent,
            'market_cap': None,  # TODO: Cache in DB to reduce API calls
            'company_name': symbol  # Using symbol for now, can be enhanced with DB cache
        }
        
        logger.info(f"[INFO] {symbol} - Result: {result}")
        return result
        
    except Exception as e:
        logger.error(f"[INFO] Error fetching info for {symbol}: {e}", exc_info=True)
        return {
            'current_price': None,
            'price_change': None,
            'change_percent': None,
            'market_cap': None,
            'company_name': symbol
        }


@router.get("", response_model=WatchlistResponse)
async def get_watchlist(
    user_id: str = Depends(get_current_user_id),
    container = Depends(get_db)
):
    """Get user's watchlist ordered by display_order.
    
    Returns all watchlist items sorted by display_order (0-49) with current prices.
    Fetches stock info in parallel to reduce latency.
    
    Args:
        user_id: User ID from JWT token (document id)
        container: Cosmos DB container
        
    Returns:
        Watchlist with items (including current prices), total count, and max limit
    """
    # Get user document
    query = "SELECT * FROM c WHERE c.id = @user_id"
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
        items = user_data.get("watchlists", [])
        
        if not items:
            return WatchlistResponse(
                items=[],
                total=0,
                max_items=settings.MAX_WATCHLIST_ITEMS
            )
        
        # Sort by display_order
        items.sort(key=lambda x: x.get("display_order", 0))
        
        # Fetch stock info in parallel using thread pool
        loop = asyncio.get_event_loop()
        
        async def fetch_stock_info_async(item):
            """Fetch stock info asynchronously in thread pool."""
            stock_info = await loop.run_in_executor(executor, get_stock_info, item["symbol"])
            item_response = {
                "symbol": item["symbol"],
                "display_order": item["display_order"],
                "notes": item.get("notes"),
                "added_at": item["added_at"]
            }
            item_response.update(stock_info)
            return WatchlistItemResponse(**item_response)
        
        # Fetch all stock info concurrently
        items_with_info = await asyncio.gather(*[
            fetch_stock_info_async(item) for item in items
        ])
        
        return WatchlistResponse(
            items=items_with_info,
            total=len(items),
            max_items=settings.MAX_WATCHLIST_ITEMS
        )
        
    except exceptions.CosmosHttpResponseError as e:
        logger.error(f"Error querying watchlist: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database query failed"
        )


@router.post("", response_model=WatchlistItemResponse, status_code=status.HTTP_201_CREATED)
async def add_to_watchlist(
    request: WatchlistAddRequest,
    user_id: str = Depends(get_current_user_id),
    container = Depends(get_db)
):
    """Add a stock to user's watchlist.
    
    Adds stock at the end of the watchlist (highest display_order + 1).
    Enforces maximum of 50 items per user.
    
    Args:
        request: Stock symbol and optional notes
        user_id: User ID from JWT token (document id)
        container: Cosmos DB container
        
    Returns:
        Created watchlist item
        
    Raises:
        HTTPException 400: If symbol already in watchlist or limit reached
    """
    # Get user document
    query = "SELECT * FROM c WHERE c.id = @user_id"
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
        watchlists = user_data.get("watchlists", [])
        
        # Check if symbol already exists
        if any(item["symbol"] == request.symbol for item in watchlists):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Symbol {request.symbol} already in watchlist"
            )
        
        # Check watchlist size limit
        if len(watchlists) >= settings.MAX_WATCHLIST_ITEMS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Watchlist limit reached (max {settings.MAX_WATCHLIST_ITEMS} items)"
            )
        
        # Get next display_order (append to end)
        next_order = max([item["display_order"] for item in watchlists], default=-1) + 1
        
        # Create watchlist item
        new_item = WatchlistItem(
            symbol=request.symbol,
            display_order=next_order,
            notes=request.notes,
            added_at=datetime.utcnow()
        )
        
        # Add to watchlists array (convert datetime to ISO string)
        watchlists.append(new_item.model_dump(mode='json'))
        user_data["watchlists"] = watchlists
        
        # Update document
        updated_user = container.replace_item(
            item=user_data["id"],
            body=user_data
        )
        
        logger.info(f"Added {request.symbol} to watchlist for user {user_id}")
        
        # Prepare response with stock info
        item_response = {
            "symbol": new_item.symbol,
            "display_order": new_item.display_order,
            "notes": new_item.notes,
            "added_at": new_item.added_at
        }
        stock_info = get_stock_info(new_item.symbol)
        item_response.update(stock_info)
        
        return WatchlistItemResponse(**item_response)
        
    except HTTPException:
        raise
    except exceptions.CosmosHttpResponseError as e:
        logger.error(f"Error adding to watchlist: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database operation failed"
        )


@router.put("/reorder", response_model=WatchlistResponse)
async def reorder_watchlist(
    request: WatchlistReorderRequest,
    user_id: str = Depends(get_current_user_id),
    container = Depends(get_db)
):
    """Reorder watchlist items.
    
    Updates display_order for all items based on provided symbol order.
    All symbols in request must exist in user's watchlist.
    
    Args:
        request: Ordered list of symbols
        user_id: User ID from JWT token (document id)
        container: Cosmos DB container
        
    Returns:
        Updated watchlist with new order
        
    Raises:
        HTTPException 400: If symbols don't match user's watchlist
    """
    # Get user document
    query = "SELECT * FROM c WHERE c.id = @user_id"
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
        watchlists = user_data.get("watchlists", [])
        
        # Create symbol to item mapping
        item_map = {item["symbol"]: item for item in watchlists}
        
        # Validate all symbols exist
        for symbol in request.symbol_order:
            if symbol not in item_map:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Symbol {symbol} not found in watchlist"
                )
        
        # Check if all existing symbols are included
        if len(request.symbol_order) != len(watchlists):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Must include all {len(watchlists)} symbols in reorder request"
            )
        
        # Update display orders
        for index, symbol in enumerate(request.symbol_order):
            item_map[symbol]["display_order"] = index
        
        # Update document
        user_data["watchlists"] = list(item_map.values())
        updated_user = container.replace_item(
            item=user_data["id"],
            body=user_data
        )
        
        logger.info(f"Reordered watchlist for user {user_id}")
        
        # Return updated watchlist with stock info (sorted by display_order)
        updated_watchlists = sorted(updated_user.get("watchlists", []), key=lambda x: x["display_order"])
        
        items_with_info = []
        for item in updated_watchlists:
            item_response = {
                "symbol": item["symbol"],
                "display_order": item["display_order"],
                "notes": item.get("notes"),
                "added_at": item["added_at"]
            }
            stock_info = get_stock_info(item["symbol"])
            item_response.update(stock_info)
            items_with_info.append(WatchlistItemResponse(**item_response))
        
        return WatchlistResponse(
            items=items_with_info,
            total=len(updated_watchlists),
            max_items=settings.MAX_WATCHLIST_ITEMS
        )
        
    except HTTPException:
        raise
    except exceptions.CosmosHttpResponseError as e:
        logger.error(f"Error reordering watchlist: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database operation failed"
        )


@router.put("/{symbol}", response_model=WatchlistItemResponse)
async def update_watchlist_item(
    symbol: str,
    request: WatchlistUpdateRequest,
    user_id: str = Depends(get_current_user_id),
    container = Depends(get_db)
):
    """Update notes for a watchlist item.
    
    Args:
        symbol: Stock ticker symbol
        request: Updated notes
        user_id: User ID from JWT token (document id)
        container: Cosmos DB container
        
    Returns:
        Updated watchlist item
        
    Raises:
        HTTPException 404: If symbol not found in watchlist
    """
    symbol = symbol.upper()
    
    # Get user document
    query = "SELECT * FROM c WHERE c.id = @user_id"
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
        watchlists = user_data.get("watchlists", [])
        
        # Find item by symbol
        item_found = None
        for item in watchlists:
            if item["symbol"] == symbol:
                item["notes"] = request.notes
                item_found = item
                break
        
        if not item_found:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Symbol {symbol} not found in watchlist"
            )
        
        # Update document
        user_data["watchlists"] = watchlists
        updated_user = container.replace_item(
            item=user_data["id"],
            body=user_data
        )
        
        logger.info(f"Updated notes for {symbol} in user {user_id} watchlist")
        
        return WatchlistItemResponse(
            symbol=item_found["symbol"],
            display_order=item_found["display_order"],
            notes=item_found.get("notes"),
            added_at=item_found["added_at"],
            current_price=None,
            price_change=None,
            change_percent=None,
            market_cap=None,
            company_name=symbol
        )
        
    except HTTPException:
        raise
    except exceptions.CosmosHttpResponseError as e:
        logger.error(f"Error updating watchlist item: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database operation failed"
        )


@router.delete("/{symbol}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_from_watchlist(
    symbol: str,
    user_id: str = Depends(get_current_user_id),
    container = Depends(get_db)
):
    """Remove a stock from user's watchlist.
    
    Deletes the item and reorders remaining items to fill the gap.
    
    Args:
        symbol: Stock ticker symbol
        user_id: User ID from JWT token (document id)
        container: Cosmos DB container
        
    Raises:
        HTTPException 404: If symbol not found in watchlist
    """
    symbol = symbol.upper()
    
    # Get user document
    query = "SELECT * FROM c WHERE c.id = @user_id"
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
        watchlists = user_data.get("watchlists", [])
        
        # Find and remove item by symbol
        deleted_order = None
        updated_watchlists = []
        
        for item in watchlists:
            if item["symbol"] == symbol:
                deleted_order = item["display_order"]
            else:
                updated_watchlists.append(item)
        
        if deleted_order is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Symbol {symbol} not found in watchlist"
            )
        
        # Reorder remaining items (decrement orders after deleted item)
        for item in updated_watchlists:
            if item["display_order"] > deleted_order:
                item["display_order"] -= 1
        
        # Update document
        user_data["watchlists"] = updated_watchlists
        container.replace_item(
            item=user_data["id"],
            body=user_data
        )
        
        logger.info(f"Removed {symbol} from user {user_id} watchlist")
        return None
        
    except HTTPException:
        raise
    except exceptions.CosmosHttpResponseError as e:
        logger.error(f"Error removing from watchlist: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database operation failed"
        )
