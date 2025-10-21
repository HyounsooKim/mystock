"""Database seed script for MyStock application.

This script creates test data for development and testing:
- Test user account with hashed password
- 3 predefined portfolios for the test user
- Sample watchlist items
- Sample portfolio holdings
- Sample stock quotes
"""

import sys
from pathlib import Path

# Add src directory to Python path
sys.path.append(str(Path(__file__).parent.parent.parent))

from datetime import datetime
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from src.core.database import engine, SessionLocal
from src.models import User, Portfolio, Watchlist, Holding, StockQuote
from src.models.stock_quote import MarketStatus, Market


# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_context.hash(password)


def create_test_user(db: Session) -> User:
    """Create a test user account.
    
    Args:
        db: Database session
        
    Returns:
        Created User object
    """
    print("Creating test user...")
    
    user = User(
        email="test@example.com",
        password_hash=hash_password("password123"),
        is_active=True,
        last_login_at=datetime.now()
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    print(f"  ✓ Created user: {user.email} (ID: {user.id})")
    return user


def create_portfolios(db: Session, user: User) -> list[Portfolio]:
    """Create 3 predefined portfolios for the user.
    
    Args:
        db: Database session
        user: User object
        
    Returns:
        List of created Portfolio objects
    """
    print("Creating portfolios...")
    
    portfolio_names = Portfolio.get_predefined_names()
    portfolios = []
    
    for name in portfolio_names:
        portfolio = Portfolio(
            user_id=user.id,
            name=name
        )
        db.add(portfolio)
        portfolios.append(portfolio)
    
    db.commit()
    
    for portfolio in portfolios:
        db.refresh(portfolio)
        print(f"  ✓ Created portfolio: {portfolio.name} (ID: {portfolio.id})")
    
    return portfolios


def create_watchlist_items(db: Session, user: User) -> list[Watchlist]:
    """Create sample watchlist items for the user.
    
    Args:
        db: Database session
        user: User object
        
    Returns:
        List of created Watchlist objects
    """
    print("Creating watchlist items...")
    
    watchlist_data = [
        {
            "symbol": "AAPL",
            "display_order": 0,
            "notes": "Apple Inc. - 관심있는 미국 기술주"
        },
        {
            "symbol": "MSFT",
            "display_order": 1,
            "notes": "Microsoft Corporation - AI와 클라우드 리더"
        },
        {
            "symbol": "005930.KS",
            "display_order": 2,
            "notes": "삼성전자 - 한국 대표 반도체주"
        }
    ]
    
    watchlist_items = []
    
    for data in watchlist_data:
        item = Watchlist(
            user_id=user.id,
            symbol=data["symbol"],
            display_order=data["display_order"],
            notes=data["notes"]
        )
        db.add(item)
        watchlist_items.append(item)
    
    db.commit()
    
    for item in watchlist_items:
        db.refresh(item)
        print(f"  ✓ Created watchlist item: {item.symbol} (order: {item.display_order})")
    
    return watchlist_items


def create_holdings(db: Session, portfolios: list[Portfolio]) -> list[Holding]:
    """Create sample holdings in the first portfolio.
    
    Args:
        db: Database session
        portfolios: List of Portfolio objects
        
    Returns:
        List of created Holding objects
    """
    print("Creating holdings...")
    
    # Add holdings to "장기투자" portfolio
    long_term_portfolio = portfolios[0]
    
    holdings_data = [
        {
            "symbol": "AAPL",
            "quantity": 10.0,
            "avg_price": 150.25
        },
        {
            "symbol": "005930.KS",
            "quantity": 5.0,
            "avg_price": 70000.00
        }
    ]
    
    holdings = []
    
    for data in holdings_data:
        holding = Holding(
            portfolio_id=long_term_portfolio.id,
            symbol=data["symbol"],
            quantity=data["quantity"],
            avg_price=data["avg_price"]
        )
        db.add(holding)
        holdings.append(holding)
    
    db.commit()
    
    for holding in holdings:
        db.refresh(holding)
        cost_basis = holding.calculate_cost_basis()
        print(f"  ✓ Created holding: {holding.symbol} - {holding.quantity} shares @ ${holding.avg_price} (cost basis: ${cost_basis:.2f})")
    
    return holdings


def create_stock_quotes(db: Session) -> list[StockQuote]:
    """Create sample stock quotes for cached data.
    
    Args:
        db: Database session
        
    Returns:
        List of created StockQuote objects
    """
    print("Creating stock quotes...")
    
    quotes_data = [
        {
            "symbol": "AAPL",
            "current_price": 175.50,
            "daily_change_pct": 1.25,
            "volume": 50000000,
            "market_status": MarketStatus.CLOSED,
            "market": Market.US,
            "cache_data": {
                "regularMarketPrice": 175.50,
                "regularMarketChange": 2.15,
                "regularMarketChangePercent": 1.25,
                "regularMarketVolume": 50000000,
                "marketState": "CLOSED"
            }
        },
        {
            "symbol": "005930.KS",
            "current_price": 75000.00,
            "daily_change_pct": -0.50,
            "volume": 10000000,
            "market_status": MarketStatus.CLOSED,
            "market": Market.KR,
            "cache_data": {
                "regularMarketPrice": 75000.00,
                "regularMarketChange": -375.00,
                "regularMarketChangePercent": -0.50,
                "regularMarketVolume": 10000000,
                "marketState": "CLOSED"
            }
        }
    ]
    
    quotes = []
    
    for data in quotes_data:
        quote = StockQuote(
            symbol=data["symbol"],
            current_price=data["current_price"],
            daily_change_pct=data["daily_change_pct"],
            volume=data["volume"],
            market_status=data["market_status"],
            market=data["market"],
            cache_data=data["cache_data"]
        )
        db.add(quote)
        quotes.append(quote)
    
    db.commit()
    
    for quote in quotes:
        db.refresh(quote)
        change_symbol = "+" if quote.daily_change_pct > 0 else ""
        print(f"  ✓ Created stock quote: {quote.symbol} - ${quote.current_price} ({change_symbol}{quote.daily_change_pct}%)")
    
    return quotes


def seed_database():
    """Seed the database with test data."""
    print("\n" + "="*60)
    print("MyStock Database Seeding")
    print("="*60 + "\n")
    
    db: Session = SessionLocal()
    
    try:
        # Check if data already exists
        existing_user = db.query(User).filter(User.email == "test@example.com").first()
        if existing_user:
            print("⚠ Test data already exists. Skipping seed.")
            return
        
        # Create test data
        user = create_test_user(db)
        portfolios = create_portfolios(db, user)
        watchlist_items = create_watchlist_items(db, user)
        holdings = create_holdings(db, portfolios)
        quotes = create_stock_quotes(db)
        
        print("\n" + "="*60)
        print("✓ Database seeding completed successfully!")
        print("="*60)
        print(f"\nTest credentials:")
        print(f"  Email: test@example.com")
        print(f"  Password: password123")
        print()
        
    except Exception as e:
        print(f"\n✗ Error seeding database: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
