"""Portfolio and holdings management API endpoints with Cosmos DB.

Provides endpoints for:
- Listing user's portfolios
- Getting portfolio details
- Getting portfolio summary with holdings and P&L calculations
- Adding/updating/deleting holdings
- Enforcing 100-item limit per portfolio
"""

from fastapi import APIRouter, Depends, HTTPException, status
from azure.cosmos import exceptions
from decimal import Decimal
from datetime import datetime
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor
import uuid

from src.core.database import get_db
from src.core.config import settings
from src.core.middleware import get_current_user_id
from src.models.user import UserDocument, PortfolioItem, HoldingItem
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
async def list_portfolios(
    user_id: str = Depends(get_current_user_id),
    container = Depends(get_db),
):
    """List user's portfolios with holdings count.
    
    Each user has exactly 3 portfolios auto-created on registration:
    - 장기투자 (Long-term Investment)
    - 단타 (Short-term Trading)
    - 정찰병 (Scout/Watchlist)
    
    Args:
        user_id: Current user ID from JWT token (document id)
        container: Cosmos DB container
        
    Returns:
        List of 3 portfolios with holdings count
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
        portfolios = user_data.get("portfolios", [])
        
        # Convert to response format with holdings count
        result = []
        for portfolio in portfolios:
            holdings_count = len(portfolio.get("holdings", []))
            portfolio_response = PortfolioResponse(
                id=portfolio["id"],
                user_id=user_id,
                name=portfolio["name"],
                created_at=portfolio["created_at"],
                updated_at=portfolio.get("created_at"),  # Cosmos doesn't track updated_at separately
                holdings_count=holdings_count
            )
            result.append(portfolio_response)
        
        return result
        
    except exceptions.CosmosHttpResponseError as e:
        logger.error(f"Error querying portfolios: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database query failed"
        )


@router.get("/{portfolio_id}", response_model=PortfolioResponse)
async def get_portfolio(
    portfolio_id: str,
    user_id: str = Depends(get_current_user_id),
    container = Depends(get_db),
):
    """Get portfolio details by ID.
    
    Args:
        portfolio_id: Portfolio ID (UUID)
        user_id: Current user ID from JWT token
        container: Cosmos DB container
        
    Returns:
        Portfolio information
        
    Raises:
        HTTPException 404: Portfolio not found or not owned by user
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
        portfolios = user_data.get("portfolios", [])
        
        # Find portfolio by id
        portfolio_found = None
        for portfolio in portfolios:
            if portfolio["id"] == portfolio_id:
                portfolio_found = portfolio
                break
        
        if not portfolio_found:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Portfolio {portfolio_id} not found"
            )
        
        return PortfolioResponse(
            id=portfolio_found["id"],
            user_id=user_id,
            name=portfolio_found["name"],
            created_at=portfolio_found["created_at"],
            updated_at=portfolio_found.get("created_at"),
            holdings_count=len(portfolio_found.get("holdings", []))
        )
        
    except HTTPException:
        raise
    except exceptions.CosmosHttpResponseError as e:
        logger.error(f"Error querying portfolio: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database query failed"
        )


@router.get("/{portfolio_id}/summary", response_model=PortfolioSummaryResponse)
async def get_portfolio_summary(
    portfolio_id: str,
    user_id: str = Depends(get_current_user_id),
    container = Depends(get_db),
):
    """Get portfolio summary with holdings and P&L calculations.
    
    Fetches current stock prices for all holdings and calculates:
    - Total market value
    - Total invested amount
    - Total profit/loss
    - Total profit/loss percentage
    
    Args:
        portfolio_id: Portfolio ID (UUID)
        user_id: Current user ID from JWT token
        container: Cosmos DB container
        
    Returns:
        Portfolio summary with all holdings and aggregated metrics
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
        portfolios = user_data.get("portfolios", [])
        
        # Find portfolio
        portfolio_found = None
        for portfolio in portfolios:
            if portfolio["id"] == portfolio_id:
                portfolio_found = portfolio
                break
        
        if not portfolio_found:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Portfolio {portfolio_id} not found"
            )
        
        holdings = portfolio_found.get("holdings", [])
        
        if not holdings:
            return PortfolioSummaryResponse(
                portfolio=PortfolioResponse(
                    id=portfolio_found["id"],
                    user_id=user_id,
                    name=portfolio_found["name"],
                    created_at=portfolio_found["created_at"],
                    updated_at=portfolio_found.get("created_at"),
                    holdings_count=0
                ),
                holdings=[],
                summary=PortfolioSummary(
                    total_holdings=0,
                    total_cost_basis=Decimal(0),
                    total_current_value=Decimal(0),
                    total_profit_loss=Decimal(0),
                    total_return_rate=Decimal(0)
                )
            )
        
        # Fetch stock info for all holdings in parallel
        symbols = [holding["symbol"] for holding in holdings]
        loop = asyncio.get_event_loop()
        
        stock_infos = await asyncio.gather(*[
            loop.run_in_executor(executor, get_stock_info, symbol)
            for symbol in symbols
        ])
        
        # Map symbol to stock info
        symbol_to_info = {symbol: info for symbol, info in zip(symbols, stock_infos)}
        
        # Build holdings responses with P&L calculations
        holdings_responses = []
        total_current_value = Decimal(0)
        total_cost_basis = Decimal(0)
        
        for holding in holdings:
            symbol = holding["symbol"]
            quantity = Decimal(str(holding["quantity"]))
            avg_price = Decimal(str(holding["avg_price"]))
            stock_info = symbol_to_info.get(symbol, {})
            current_price = stock_info.get("current_price")
            
            # Calculate cost basis
            cost_basis = quantity * avg_price
            total_cost_basis += cost_basis
            
            # Calculate market value and P&L if current price available
            if current_price:
                current_price_decimal = Decimal(str(current_price))
                market_value = quantity * current_price_decimal
                profit_loss = market_value - cost_basis
                return_rate = (profit_loss / cost_basis * 100) if cost_basis > 0 else Decimal(0)
                total_current_value += market_value
            else:
                market_value = cost_basis
                profit_loss = Decimal(0)
                return_rate = Decimal(0)
                total_current_value += market_value
            
            holding_response = HoldingResponse(
                id=holding.get("id", str(uuid.uuid4())),  # Generate if missing
                portfolio_id=portfolio_id,
                symbol=symbol,
                company_name=stock_info.get("company_name"),
                quantity=int(quantity),
                avg_price=avg_price,
                cost_basis=cost_basis,
                current_price=current_price_decimal if current_price else None,
                current_value=market_value,
                profit_loss=profit_loss,
                return_rate=return_rate,
                notes=holding.get("notes"),
                created_at=holding.get("created_at", datetime.now()),
                updated_at=holding.get("updated_at", datetime.now())
            )
            holdings_responses.append(holding_response)
        
        # Calculate total P&L
        total_profit_loss = total_current_value - total_cost_basis
        total_return_rate = (total_profit_loss / total_cost_basis * 100) if total_cost_basis > 0 else Decimal(0)
        
        return PortfolioSummaryResponse(
            portfolio=PortfolioResponse(
                id=portfolio_found["id"],
                user_id=user_id,
                name=portfolio_found["name"],
                created_at=portfolio_found["created_at"],
                updated_at=portfolio_found.get("created_at"),
                holdings_count=len(holdings)
            ),
            holdings=holdings_responses,
            summary=PortfolioSummary(
                total_holdings=len(holdings),
                total_cost_basis=total_cost_basis,
                total_current_value=total_current_value,
                total_profit_loss=total_profit_loss,
                total_return_rate=total_return_rate
            )
        )
        
    except HTTPException:
        raise
    except exceptions.CosmosHttpResponseError as e:
        logger.error(f"Error querying portfolio summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database query failed"
        )


@router.post("/{portfolio_id}/holdings", response_model=HoldingResponse, status_code=status.HTTP_201_CREATED)
async def add_holding(
    portfolio_id: str,
    request: AddHoldingRequest,
    user_id: str = Depends(get_current_user_id),
    container = Depends(get_db),
):
    """Add a new holding to portfolio.
    
    Args:
        portfolio_id: Portfolio ID (UUID)
        request: Holding data (symbol, quantity, avg_price)
        user_id: Current user ID from JWT token
        container: Cosmos DB container
        
    Returns:
        Created holding
        
    Raises:
        HTTPException 400: If holding limit reached or symbol already exists
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
        portfolios = user_data.get("portfolios", [])
        
        # Find portfolio
        portfolio_index = None
        for idx, portfolio in enumerate(portfolios):
            if portfolio["id"] == portfolio_id:
                portfolio_index = idx
                break
        
        if portfolio_index is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Portfolio {portfolio_id} not found"
            )
        
        portfolio = portfolios[portfolio_index]
        holdings = portfolio.get("holdings", [])
        
        # Check if symbol already exists
        if any(h["symbol"] == request.symbol for h in holdings):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Symbol {request.symbol} already exists in portfolio"
            )
        
        # Check holdings limit
        if len(holdings) >= settings.MAX_HOLDINGS_PER_PORTFOLIO:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Holdings limit reached (max {settings.MAX_HOLDINGS_PER_PORTFOLIO} items)"
            )
        
        # Create new holding
        new_holding = HoldingItem(
            symbol=request.symbol,
            quantity=request.quantity,
            avg_price=request.avg_price,
            purchase_date=datetime.utcnow()
        )
        
        # Add to holdings array
        holding_dict = new_holding.model_dump(mode='json')
        holding_dict["id"] = str(uuid.uuid4())  # Add unique id for holding
        holdings.append(holding_dict)
        
        # Update portfolio
        portfolio["holdings"] = holdings
        portfolios[portfolio_index] = portfolio
        user_data["portfolios"] = portfolios
        
        # Update document
        updated_user = container.replace_item(
            item=user_data["id"],
            body=user_data
        )
        
        logger.info(f"Added holding {request.symbol} to portfolio {portfolio_id}")
        
        # Calculate P&L for response
        stock_info = get_stock_info(request.symbol)
        current_price = stock_info.get("current_price")
        company_name = stock_info.get("company_name")
        quantity = Decimal(str(request.quantity))
        avg_price = Decimal(str(request.avg_price))
        cost_basis = quantity * avg_price
        
        if current_price:
            current_price_decimal = Decimal(str(current_price))
            current_value = quantity * current_price_decimal
            profit_loss = current_value - cost_basis
            return_rate = (profit_loss / cost_basis * 100) if cost_basis > 0 else Decimal(0)
        else:
            current_price_decimal = None
            current_value = cost_basis
            profit_loss = Decimal(0)
            return_rate = Decimal(0)
        
        return HoldingResponse(
            id=holding_dict["id"],
            portfolio_id=portfolio_id,
            symbol=request.symbol,
            company_name=company_name,
            quantity=request.quantity,
            avg_price=avg_price,
            cost_basis=cost_basis,
            current_price=current_price_decimal,
            current_value=current_value,
            profit_loss=profit_loss,
            return_rate=return_rate,
            notes=None,
            created_at=datetime.fromisoformat(holding_dict["purchase_date"]) if isinstance(holding_dict["purchase_date"], str) else holding_dict["purchase_date"],
            updated_at=datetime.fromisoformat(holding_dict["purchase_date"]) if isinstance(holding_dict["purchase_date"], str) else holding_dict["purchase_date"]
        )
        
    except HTTPException:
        raise
    except exceptions.CosmosHttpResponseError as e:
        logger.error(f"Error adding holding: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database operation failed"
        )


@router.put("/{portfolio_id}/holdings/{holding_id}", response_model=HoldingResponse)
async def update_holding(
    portfolio_id: str,
    holding_id: str,
    request: UpdateHoldingRequest,
    user_id: str = Depends(get_current_user_id),
    container = Depends(get_db),
):
    """Update existing holding quantity and/or average price.
    
    Args:
        portfolio_id: Portfolio ID (UUID)
        holding_id: Holding ID (UUID)
        request: Updated holding data
        user_id: Current user ID from JWT token
        container: Cosmos DB container
        
    Returns:
        Updated holding
        
    Raises:
        HTTPException 404: If portfolio or holding not found
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
        portfolios = user_data.get("portfolios", [])
        
        # Find portfolio
        portfolio_index = None
        for idx, portfolio in enumerate(portfolios):
            if portfolio["id"] == portfolio_id:
                portfolio_index = idx
                break
        
        if portfolio_index is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Portfolio {portfolio_id} not found"
            )
        
        portfolio = portfolios[portfolio_index]
        holdings = portfolio.get("holdings", [])
        
        # Find holding
        holding_index = None
        for idx, holding in enumerate(holdings):
            if holding.get("id") == holding_id:
                holding_index = idx
                break
        
        if holding_index is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Holding {holding_id} not found"
            )
        
        # Update holding
        holding = holdings[holding_index]
        holding["quantity"] = request.quantity
        holding["avg_price"] = request.avg_price
        holdings[holding_index] = holding
        
        # Update portfolio
        portfolio["holdings"] = holdings
        portfolios[portfolio_index] = portfolio
        user_data["portfolios"] = portfolios
        
        # Update document
        updated_user = container.replace_item(
            item=user_data["id"],
            body=user_data
        )
        
        logger.info(f"Updated holding {holding_id} in portfolio {portfolio_id}")
        
        # Calculate P&L for response
        stock_info = get_stock_info(holding["symbol"])
        current_price = stock_info.get("current_price")
        company_name = stock_info.get("company_name")
        quantity = Decimal(str(request.quantity))
        avg_price = Decimal(str(request.avg_price))
        cost_basis = quantity * avg_price
        
        if current_price:
            current_price_decimal = Decimal(str(current_price))
            current_value = quantity * current_price_decimal
            profit_loss = current_value - cost_basis
            return_rate = (profit_loss / cost_basis * 100) if cost_basis > 0 else Decimal(0)
        else:
            current_price_decimal = None
            current_value = cost_basis
            profit_loss = Decimal(0)
            return_rate = Decimal(0)
        
        return HoldingResponse(
            id=holding_id,
            portfolio_id=portfolio_id,
            symbol=holding["symbol"],
            company_name=company_name,
            quantity=request.quantity,
            avg_price=avg_price,
            cost_basis=cost_basis,
            current_price=current_price_decimal,
            current_value=current_value,
            profit_loss=profit_loss,
            return_rate=return_rate,
            notes=holding.get("notes"),
            created_at=datetime.fromisoformat(holding["purchase_date"]) if isinstance(holding["purchase_date"], str) else holding["purchase_date"],
            updated_at=datetime.now()
        )
        
    except HTTPException:
        raise
    except exceptions.CosmosHttpResponseError as e:
        logger.error(f"Error updating holding: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database operation failed"
        )


@router.delete("/{portfolio_id}/holdings/{holding_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_holding(
    portfolio_id: str,
    holding_id: str,
    user_id: str = Depends(get_current_user_id),
    container = Depends(get_db),
):
    """Delete holding from portfolio.
    
    Args:
        portfolio_id: Portfolio ID (UUID)
        holding_id: Holding ID (UUID)
        user_id: Current user ID from JWT token
        container: Cosmos DB container
        
    Raises:
        HTTPException 404: If portfolio or holding not found
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
        portfolios = user_data.get("portfolios", [])
        
        # Find portfolio
        portfolio_index = None
        for idx, portfolio in enumerate(portfolios):
            if portfolio["id"] == portfolio_id:
                portfolio_index = idx
                break
        
        if portfolio_index is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Portfolio {portfolio_id} not found"
            )
        
        portfolio = portfolios[portfolio_index]
        holdings = portfolio.get("holdings", [])
        
        # Find and remove holding
        holding_found = False
        updated_holdings = []
        for holding in holdings:
            if holding.get("id") == holding_id:
                holding_found = True
            else:
                updated_holdings.append(holding)
        
        if not holding_found:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Holding {holding_id} not found"
            )
        
        # Update portfolio
        portfolio["holdings"] = updated_holdings
        portfolios[portfolio_index] = portfolio
        user_data["portfolios"] = portfolios
        
        # Update document
        container.replace_item(
            item=user_data["id"],
            body=user_data
        )
        
        logger.info(f"Deleted holding {holding_id} from portfolio {portfolio_id}")
        return None
        
    except HTTPException:
        raise
    except exceptions.CosmosHttpResponseError as e:
        logger.error(f"Error deleting holding: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database operation failed"
        )
