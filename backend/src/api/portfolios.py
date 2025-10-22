"""Portfolio and holdings management API endpoints.

Provides endpoints for:
- Listing user's portfolios
- Getting portfolio details
- Getting portfolio summary with holdings and P&L calculations
- Adding/updating/deleting holdings
- Enforcing 100-item limit per portfolio
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from decimal import Decimal
from datetime import datetime
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor

from src.core.database import get_db
from src.core.middleware import get_current_user_id
from src.models import Portfolio, Holding, StockQuote
from src.schemas.portfolios import (
    PortfolioResponse,
    HoldingResponse,
    AddHoldingRequest,
    UpdateHoldingRequest,
    PortfolioSummaryResponse,
    PortfolioSummary,
)
from src.api.watchlist import get_stock_price, get_stock_info

router = APIRouter()
logger = logging.getLogger(__name__)

# Thread pool for parallel API calls
executor = ThreadPoolExecutor(max_workers=5)


@router.get("", response_model=list[PortfolioResponse])
def list_portfolios(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """List user's portfolios with holdings count.
    
    Each user has exactly 3 portfolios auto-created on registration:
    - 장기투자 (Long-term Investment)
    - 단타 (Short-term Trading)
    - 정찰병 (Scout/Watchlist)
    
    Args:
        user_id: Current user ID from JWT token
        db: Database session
        
    Returns:
        List of 3 portfolios with holdings count
        
    Example:
        GET /api/v1/portfolios
        Response: [
            {
                "id": 1,
                "user_id": 1,
                "name": "장기투자",
                "created_at": "2024-01-20T10:00:00",
                "updated_at": "2024-01-20T10:00:00",
                "holdings_count": 5
            },
            ...
        ]
    """
    # Query portfolios with holdings count
    portfolios = (
        db.query(
            Portfolio,
            func.count(Holding.id).label("holdings_count")
        )
        .outerjoin(Holding, Holding.portfolio_id == Portfolio.id)
        .filter(Portfolio.user_id == user_id)
        .group_by(Portfolio.id)
        .all()
    )
    
    # Convert to response format
    result = []
    for portfolio, count in portfolios:
        portfolio_dict = {
            "id": portfolio.id,
            "user_id": portfolio.user_id,
            "name": portfolio.name,
            "created_at": portfolio.created_at,
            "updated_at": portfolio.updated_at,
            "holdings_count": count
        }
        result.append(PortfolioResponse(**portfolio_dict))
    
    return result


@router.get("/{portfolio_id}", response_model=PortfolioResponse)
def get_portfolio(
    portfolio_id: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Get portfolio details by ID.
    
    Args:
        portfolio_id: Portfolio ID
        user_id: Current user ID from JWT token
        db: Database session
        
    Returns:
        Portfolio information
        
    Raises:
        HTTPException 404: Portfolio not found or not owned by user
        
    Example:
        GET /api/v1/portfolios/1
        Response: {
            "id": 1,
            "user_id": 1,
            "name": "장기투자",
            "created_at": "2024-01-20T10:00:00",
            "updated_at": "2024-01-20T10:00:00"
        }
    """
    portfolio = (
        db.query(Portfolio)
        .filter(Portfolio.id == portfolio_id, Portfolio.user_id == user_id)
        .first()
    )
    
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Portfolio {portfolio_id} not found"
        )
    
    return portfolio


@router.get("/{portfolio_id}/summary", response_model=PortfolioSummaryResponse)
async def get_portfolio_summary(
    portfolio_id: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Get portfolio summary with holdings and P&L calculations.
    
    Joins holdings with stock_quotes to get current prices and calculates:
    - cost_basis = quantity * avg_price
    - current_value = quantity * current_price
    - profit_loss = current_value - cost_basis
    - return_rate = (profit_loss / cost_basis) * 100
    
    Fetches stock prices in parallel to reduce latency.
    
    Args:
        portfolio_id: Portfolio ID
        user_id: Current user ID from JWT token
        db: Database session
        
    Returns:
        Portfolio summary with holdings and aggregated statistics
        
    Raises:
        HTTPException 404: Portfolio not found or not owned by user
    """
    # Verify portfolio ownership
    portfolio = (
        db.query(Portfolio)
        .filter(Portfolio.id == portfolio_id, Portfolio.user_id == user_id)
        .first()
    )
    
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Portfolio {portfolio_id} not found"
        )
    
    # Get all holdings for this portfolio
    holdings = (
        db.query(Holding)
        .filter(Holding.portfolio_id == portfolio_id)
        .all()
    )
    
    if not holdings:
        return PortfolioSummaryResponse(
            portfolio=PortfolioResponse.model_validate(portfolio),
            holdings=[],
            summary=PortfolioSummary(
                total_holdings=0,
                total_cost_basis=Decimal(0),
                total_current_value=Decimal(0),
                total_profit_loss=Decimal(0),
                total_return_rate=Decimal(0),
                usd_cost_basis=Decimal(0),
                usd_current_value=Decimal(0),
                usd_profit_loss=Decimal(0),
                usd_return_rate=Decimal(0),
                krw_cost_basis=Decimal(0),
                krw_current_value=Decimal(0),
                krw_profit_loss=Decimal(0),
                krw_return_rate=Decimal(0),
            )
        )
    
    # Fetch all stock info in parallel
    loop = asyncio.get_event_loop()
    symbols = [holding.symbol for holding in holdings]
    
    stock_infos = await asyncio.gather(*[
        loop.run_in_executor(executor, get_stock_info, symbol)
        for symbol in symbols
    ])
    
    # Create a mapping of symbol to stock info
    symbol_to_info = dict(zip(symbols, stock_infos))
    
    # Calculate P&L for each holding using fetched prices
    holdings_response = []
    total_cost_basis = Decimal(0)
    total_current_value = Decimal(0)
    
    # Separate USD and KRW totals
    usd_cost_basis = Decimal(0)
    usd_current_value = Decimal(0)
    krw_cost_basis = Decimal(0)
    krw_current_value = Decimal(0)
    
    for holding in holdings:
        cost_basis = Decimal(holding.quantity) * holding.avg_price
        total_cost_basis += cost_basis
        
        # Check if US stock (no dot in symbol)
        is_us_stock = '.' not in holding.symbol
        
        # Get stock info from pre-fetched data
        stock_info = symbol_to_info.get(holding.symbol, {})
        current_price = stock_info.get('current_price')
        company_name = stock_info.get('company_name', holding.symbol)
        
        if current_price:
            current_value = Decimal(holding.quantity) * Decimal(current_price)
            total_current_value += current_value
            profit_loss = current_value - cost_basis
            return_rate = (profit_loss / cost_basis * 100) if cost_basis > 0 else Decimal(0)
            
            # Add to USD or KRW totals
            if is_us_stock:
                usd_cost_basis += cost_basis
                usd_current_value += current_value
            else:
                krw_cost_basis += cost_basis
                krw_current_value += current_value
        else:
            current_value = None
            profit_loss = None
            return_rate = None
        
        holding_dict = {
            "id": holding.id,
            "portfolio_id": holding.portfolio_id,
            "symbol": holding.symbol,
            "company_name": company_name,
            "quantity": holding.quantity,
            "avg_price": holding.avg_price,
            "cost_basis": cost_basis,
            "current_price": current_price,
            "current_value": current_value,
            "profit_loss": profit_loss,
            "return_rate": return_rate,
            "notes": None,  # Notes field not in model yet
            "created_at": holding.created_at,
            "updated_at": holding.updated_at,
        }
        holdings_response.append(HoldingResponse(**holding_dict))
    
    # Calculate overall summary
    total_profit_loss = total_current_value - total_cost_basis
    total_return_rate = (
        (total_profit_loss / total_cost_basis * 100) if total_cost_basis > 0 else Decimal(0)
    )
    
    # Calculate USD summary
    usd_profit_loss = usd_current_value - usd_cost_basis
    usd_return_rate = (
        (usd_profit_loss / usd_cost_basis * 100) if usd_cost_basis > 0 else Decimal(0)
    )
    
    # Calculate KRW summary
    krw_profit_loss = krw_current_value - krw_cost_basis
    krw_return_rate = (
        (krw_profit_loss / krw_cost_basis * 100) if krw_cost_basis > 0 else Decimal(0)
    )
    
    summary = PortfolioSummary(
        total_holdings=len(holdings_response),
        total_cost_basis=total_cost_basis,
        total_current_value=total_current_value,
        total_profit_loss=total_profit_loss,
        total_return_rate=total_return_rate,
        usd_cost_basis=usd_cost_basis,
        usd_current_value=usd_current_value,
        usd_profit_loss=usd_profit_loss,
        usd_return_rate=usd_return_rate,
        krw_cost_basis=krw_cost_basis,
        krw_current_value=krw_current_value,
        krw_profit_loss=krw_profit_loss,
        krw_return_rate=krw_return_rate,
    )
    
    return PortfolioSummaryResponse(
        portfolio=portfolio,
        holdings=holdings_response,
        summary=summary,
    )


@router.post("/{portfolio_id}/holdings", response_model=HoldingResponse, status_code=status.HTTP_201_CREATED)
def add_holding(
    portfolio_id: int,
    request: AddHoldingRequest,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Add a new holding to portfolio.
    
    Enforces:
    - 100 holdings per portfolio limit
    - No duplicate symbols in same portfolio
    - Portfolio ownership verification
    
    Args:
        portfolio_id: Portfolio ID
        request: Holding data (symbol, quantity, avg_price, notes)
        user_id: Current user ID from JWT token
        db: Database session
        
    Returns:
        Created holding with calculated cost_basis
        
    Raises:
        HTTPException 404: Portfolio not found or not owned by user
        HTTPException 409: Holding limit reached (100) or duplicate symbol
        
    Example:
        POST /api/v1/portfolios/1/holdings
        Body: {
            "symbol": "AAPL",
            "quantity": 10,
            "avg_price": 175.50,
            "notes": "Long-term hold"
        }
        Response: {
            "id": 1,
            "portfolio_id": 1,
            "symbol": "AAPL",
            "quantity": 10,
            "avg_price": 175.50,
            "cost_basis": 1755.00,
            ...
        }
    """
    # Verify portfolio ownership
    portfolio = (
        db.query(Portfolio)
        .filter(Portfolio.id == portfolio_id, Portfolio.user_id == user_id)
        .first()
    )
    
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Portfolio {portfolio_id} not found"
        )
    
    # Check 100-item limit
    holdings_count = db.query(func.count(Holding.id)).filter(Holding.portfolio_id == portfolio_id).scalar()
    
    if holdings_count >= 100:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Portfolio has reached the maximum of 100 holdings"
        )
    
    # Check duplicate symbol
    existing = (
        db.query(Holding)
        .filter(Holding.portfolio_id == portfolio_id, Holding.symbol == request.symbol)
        .first()
    )
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Symbol {request.symbol} already exists in this portfolio"
        )
    
    # Create holding
    holding = Holding(
        portfolio_id=portfolio_id,
        symbol=request.symbol,
        quantity=request.quantity,
        avg_price=request.avg_price,
    )
    
    db.add(holding)
    db.commit()
    db.refresh(holding)
    
    # Calculate cost_basis for response
    cost_basis = Decimal(holding.quantity) * holding.avg_price
    
    holding_dict = {
        "id": holding.id,
        "portfolio_id": holding.portfolio_id,
        "symbol": holding.symbol,
        "quantity": holding.quantity,
        "avg_price": holding.avg_price,
        "cost_basis": cost_basis,
        "current_price": None,
        "current_value": None,
        "profit_loss": None,
        "return_rate": None,
        "notes": request.notes,  # Include notes from request even if not stored
        "created_at": holding.created_at,
        "updated_at": holding.updated_at,
    }
    
    return HoldingResponse(**holding_dict)


@router.put("/{portfolio_id}/holdings/{holding_id}", response_model=HoldingResponse)
def update_holding(
    portfolio_id: int,
    holding_id: int,
    request: UpdateHoldingRequest,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Update an existing holding.
    
    Allows updating quantity, avg_price, and notes.
    At least one field must be provided.
    
    Args:
        portfolio_id: Portfolio ID
        holding_id: Holding ID
        request: Updated holding data (quantity, avg_price, notes)
        user_id: Current user ID from JWT token
        db: Database session
        
    Returns:
        Updated holding with recalculated cost_basis
        
    Raises:
        HTTPException 404: Portfolio or holding not found, or not owned by user
        HTTPException 400: No fields to update
        
    Example:
        PUT /api/v1/portfolios/1/holdings/1
        Body: {
            "quantity": 15,
            "avg_price": 177.00
        }
        Response: {
            "id": 1,
            "symbol": "AAPL",
            "quantity": 15,
            "avg_price": 177.00,
            "cost_basis": 2655.00,
            ...
        }
    """
    # Verify portfolio ownership
    portfolio = (
        db.query(Portfolio)
        .filter(Portfolio.id == portfolio_id, Portfolio.user_id == user_id)
        .first()
    )
    
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Portfolio {portfolio_id} not found"
        )
    
    # Get holding
    holding = (
        db.query(Holding)
        .filter(Holding.id == holding_id, Holding.portfolio_id == portfolio_id)
        .first()
    )
    
    if not holding:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Holding {holding_id} not found in portfolio {portfolio_id}"
        )
    
    # Update fields
    updated = False
    
    if request.quantity is not None:
        holding.quantity = request.quantity
        updated = True
    
    if request.avg_price is not None:
        holding.avg_price = request.avg_price
        updated = True
    
    # Skip notes update since model doesn't have notes field yet
    # if request.notes is not None:
    #     holding.notes = request.notes
    #     updated = True
    
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one field must be provided to update"
        )
    
    holding.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(holding)
    
    # Calculate cost_basis for response
    cost_basis = Decimal(holding.quantity) * holding.avg_price
    
    holding_dict = {
        "id": holding.id,
        "portfolio_id": holding.portfolio_id,
        "symbol": holding.symbol,
        "quantity": holding.quantity,
        "avg_price": holding.avg_price,
        "cost_basis": cost_basis,
        "current_price": None,
        "current_value": None,
        "profit_loss": None,
        "return_rate": None,
        "notes": request.notes,  # Return notes from request since model doesn't store it
        "created_at": holding.created_at,
        "updated_at": holding.updated_at,
    }
    
    return HoldingResponse(**holding_dict)


@router.delete("/{portfolio_id}/holdings/{holding_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_holding(
    portfolio_id: int,
    holding_id: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Delete a holding from portfolio.
    
    Args:
        portfolio_id: Portfolio ID
        holding_id: Holding ID
        user_id: Current user ID from JWT token
        db: Database session
        
    Raises:
        HTTPException 404: Portfolio or holding not found, or not owned by user
        
    Example:
        DELETE /api/v1/portfolios/1/holdings/1
        Response: 204 No Content
    """
    # Verify portfolio ownership
    portfolio = (
        db.query(Portfolio)
        .filter(Portfolio.id == portfolio_id, Portfolio.user_id == user_id)
        .first()
    )
    
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Portfolio {portfolio_id} not found"
        )
    
    # Get holding
    holding = (
        db.query(Holding)
        .filter(Holding.id == holding_id, Holding.portfolio_id == portfolio_id)
        .first()
    )
    
    if not holding:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Holding {holding_id} not found in portfolio {portfolio_id}"
        )
    
    db.delete(holding)
    db.commit()
