"""Watchlist API endpoints.

Handles watchlist CRUD operations and reordering.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import yfinance as yf
import logging

from src.core.database import get_db
from src.core.config import settings
from src.core.middleware import get_current_user_id
from src.models import Watchlist
from src.schemas.watchlist import (
    WatchlistAddRequest,
    WatchlistUpdateRequest,
    WatchlistReorderRequest,
    WatchlistItemResponse,
    WatchlistResponse,
)


router = APIRouter()
logger = logging.getLogger(__name__)


def get_stock_price(symbol: str):
    """Get current stock price from yfinance.
    
    Args:
        symbol: Stock ticker symbol
        
    Returns:
        Current stock price (float), or None if unavailable
    """
    try:
        logger.info(f"[PRICE] Fetching price for symbol: {symbol}")
        ticker = yf.Ticker(symbol)
        info = ticker.info
        
        logger.info(f"[PRICE] {symbol} - Info keys available: {list(info.keys())[:10]}...")
        logger.info(f"[PRICE] {symbol} - currentPrice: {info.get('currentPrice')}")
        logger.info(f"[PRICE] {symbol} - regularMarketPrice: {info.get('regularMarketPrice')}")
        logger.info(f"[PRICE] {symbol} - previousClose: {info.get('previousClose')}")
        
        # Try different price fields in order of preference
        price = (
            info.get('currentPrice') or 
            info.get('regularMarketPrice') or 
            info.get('previousClose')
        )
        
        logger.info(f"[PRICE] {symbol} - Final price: {price}")
        
        result = float(price) if price else None
        logger.info(f"[PRICE] {symbol} - Returning: {result}")
        
        return result
    except Exception as e:
        logger.error(f"[PRICE] Error fetching price for {symbol}: {e}", exc_info=True)
        return None


def get_stock_info(symbol: str):
    """Get comprehensive stock information from yfinance.
    
    Args:
        symbol: Stock ticker symbol
        
    Returns:
        Dictionary with price, change, percent, market cap, and company name, or None values if unavailable
    """
    try:
        logger.info(f"[INFO] Fetching info for symbol: {symbol}")
        ticker = yf.Ticker(symbol)
        info = ticker.info
        
        # Get company name
        company_name = (
            info.get('longName') or 
            info.get('shortName') or 
            symbol
        )
        
        # Get current price
        current_price = (
            info.get('currentPrice') or 
            info.get('regularMarketPrice') or 
            info.get('previousClose')
        )
        
        # Get previous close for change calculation
        previous_close = info.get('previousClose') or info.get('regularMarketPreviousClose')
        
        # Calculate change and percent
        price_change = None
        change_percent = None
        if current_price and previous_close:
            price_change = float(current_price) - float(previous_close)
            change_percent = (price_change / float(previous_close)) * 100
        
        # Get market cap
        market_cap = info.get('marketCap')
        
        result = {
            'current_price': float(current_price) if current_price else None,
            'price_change': price_change,
            'change_percent': change_percent,
            'market_cap': market_cap,
            'company_name': company_name
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
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Get user's watchlist ordered by display_order.
    
    Returns all watchlist items sorted by display_order (0-49) with current prices.
    
    Args:
        user_id: User ID from JWT token
        db: Database session
        
    Returns:
        Watchlist with items (including current prices), total count, and max limit
    """
    items = db.query(Watchlist).filter(
        Watchlist.user_id == user_id
    ).order_by(Watchlist.display_order).all()
    
    # Convert to response models and add stock info
    items_with_info = []
    for item in items:
        item_dict = WatchlistItemResponse.model_validate(item).model_dump()
        stock_info = get_stock_info(item.symbol)
        item_dict.update(stock_info)
        items_with_info.append(WatchlistItemResponse(**item_dict))
    
    return WatchlistResponse(
        items=items_with_info,
        total=len(items),
        max_items=settings.MAX_WATCHLIST_ITEMS
    )


@router.post("", response_model=WatchlistItemResponse, status_code=status.HTTP_201_CREATED)
async def add_to_watchlist(
    request: WatchlistAddRequest,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Add a stock to user's watchlist.
    
    Adds stock at the end of the watchlist (highest display_order + 1).
    Enforces maximum of 50 items per user.
    
    Args:
        request: Stock symbol and optional notes
        user_id: User ID from JWT token
        db: Database session
        
    Returns:
        Created watchlist item
        
    Raises:
        HTTPException 400: If symbol already in watchlist or limit reached
    """
    # Check if symbol already exists
    existing = db.query(Watchlist).filter(
        Watchlist.user_id == user_id,
        Watchlist.symbol == request.symbol
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Symbol {request.symbol} already in watchlist"
        )
    
    # Check watchlist size limit
    current_count = db.query(Watchlist).filter(
        Watchlist.user_id == user_id
    ).count()
    
    if current_count >= settings.MAX_WATCHLIST_ITEMS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Watchlist limit reached (max {settings.MAX_WATCHLIST_ITEMS} items)"
        )
    
    # Get next display_order (append to end)
    max_order = db.query(Watchlist.display_order).filter(
        Watchlist.user_id == user_id
    ).order_by(Watchlist.display_order.desc()).first()
    
    next_order = (max_order[0] + 1) if max_order else 0
    
    # Create watchlist item
    item = Watchlist(
        user_id=user_id,
        symbol=request.symbol,
        display_order=next_order,
        notes=request.notes
    )
    
    db.add(item)
    db.commit()
    db.refresh(item)
    
    # Add stock info to response
    item_dict = WatchlistItemResponse.model_validate(item).model_dump()
    stock_info = get_stock_info(item.symbol)
    item_dict.update(stock_info)
    
    return WatchlistItemResponse(**item_dict)


@router.put("/reorder", response_model=WatchlistResponse)
async def reorder_watchlist(
    request: WatchlistReorderRequest,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Reorder watchlist items.
    
    Updates display_order for all items based on provided symbol order.
    All symbols in request must exist in user's watchlist.
    
    Args:
        request: Ordered list of symbols
        user_id: User ID from JWT token
        db: Database session
        
    Returns:
        Updated watchlist with new order
        
    Raises:
        HTTPException 400: If symbols don't match user's watchlist
    """
    # Get all user's watchlist items
    items = db.query(Watchlist).filter(
        Watchlist.user_id == user_id
    ).all()
    
    # Create symbol to item mapping
    item_map = {item.symbol: item for item in items}
    
    # Validate all symbols exist
    for symbol in request.symbol_order:
        if symbol not in item_map:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Symbol {symbol} not found in watchlist"
            )
    
    # Check if all existing symbols are included
    if len(request.symbol_order) != len(items):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Must include all {len(items)} symbols in reorder request"
        )
    
    # Update display orders
    for index, symbol in enumerate(request.symbol_order):
        item_map[symbol].display_order = index
    
    db.commit()
    
    # Return updated watchlist with stock info
    updated_items = db.query(Watchlist).filter(
        Watchlist.user_id == user_id
    ).order_by(Watchlist.display_order).all()
    
    # Add stock info to items
    items_with_info = []
    for item in updated_items:
        item_dict = WatchlistItemResponse.model_validate(item).model_dump()
        stock_info = get_stock_info(item.symbol)
        item_dict.update(stock_info)
        items_with_info.append(WatchlistItemResponse(**item_dict))
    
    return WatchlistResponse(
        items=items_with_info,
        total=len(updated_items),
        max_items=settings.MAX_WATCHLIST_ITEMS
    )


@router.put("/{symbol}", response_model=WatchlistItemResponse)
async def update_watchlist_item(
    symbol: str,
    request: WatchlistUpdateRequest,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Update notes for a watchlist item.
    
    Args:
        symbol: Stock ticker symbol
        request: Updated notes
        user_id: User ID from JWT token
        db: Database session
        
    Returns:
        Updated watchlist item
        
    Raises:
        HTTPException 404: If symbol not found in watchlist
    """
    symbol = symbol.upper()
    
    item = db.query(Watchlist).filter(
        Watchlist.user_id == user_id,
        Watchlist.symbol == symbol
    ).first()
    
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Symbol {symbol} not found in watchlist"
        )
    
    item.notes = request.notes
    db.commit()
    db.refresh(item)
    
    return WatchlistItemResponse.model_validate(item)


@router.delete("/{symbol}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_from_watchlist(
    symbol: str,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Remove a stock from user's watchlist.
    
    Deletes the item and reorders remaining items to fill the gap.
    
    Args:
        symbol: Stock ticker symbol
        user_id: User ID from JWT token
        db: Database session
        
    Raises:
        HTTPException 404: If symbol not found in watchlist
    """
    symbol = symbol.upper()
    
    item = db.query(Watchlist).filter(
        Watchlist.user_id == user_id,
        Watchlist.symbol == symbol
    ).first()
    
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Symbol {symbol} not found in watchlist"
        )
    
    deleted_order = item.display_order
    
    # Delete the item
    db.delete(item)
    
    # Reorder remaining items (decrement orders after deleted item)
    remaining_items = db.query(Watchlist).filter(
        Watchlist.user_id == user_id,
        Watchlist.display_order > deleted_order
    ).all()
    
    for remaining in remaining_items:
        remaining.display_order -= 1
    
    db.commit()
    
    return None

