"""Tests for portfolio and holdings API endpoints.

Tests portfolio listing, holdings CRUD, P&L calculations, and 100-item limit.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime
from decimal import Decimal

from src.models import User, Portfolio, Holding, StockQuote
from src.models.stock_quote import MarketStatus, Market


class TestListPortfolios:
    """Tests for GET /api/v1/portfolios endpoint."""
    
    def test_list_portfolios(self, client: TestClient, db: Session, auth_headers: dict):
        """Test listing user's 3 portfolios with holdings count."""
        # Auth fixture already creates user with 3 portfolios
        response = client.get("/api/v1/portfolios", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) == 3
        assert {p["name"] for p in data} == {"장기투자", "단타", "정찰병"}
        
        # Check holdings_count
        for portfolio in data:
            assert "holdings_count" in portfolio
            assert portfolio["holdings_count"] == 0  # No holdings yet
    
    def test_list_portfolios_with_holdings(self, client: TestClient, db: Session, auth_headers: dict):
        """Test listing portfolios with holdings count."""
        # Get first portfolio
        response = client.get("/api/v1/portfolios", headers=auth_headers)
        portfolio_id = response.json()[0]["id"]
        
        # Add 2 holdings
        client.post(
            f"/api/v1/portfolios/{portfolio_id}/holdings",
            json={"symbol": "AAPL", "quantity": 10, "avg_price": 175.50},
            headers=auth_headers
        )
        client.post(
            f"/api/v1/portfolios/{portfolio_id}/holdings",
            json={"symbol": "MSFT", "quantity": 5, "avg_price": 300.00},
            headers=auth_headers
        )
        
        # List portfolios
        response = client.get("/api/v1/portfolios", headers=auth_headers)
        data = response.json()
        
        # First portfolio should have 2 holdings
        first_portfolio = next(p for p in data if p["id"] == portfolio_id)
        assert first_portfolio["holdings_count"] == 2
    
    def test_list_portfolios_unauthorized(self, client: TestClient):
        """Test listing portfolios without authentication."""
        response = client.get("/api/v1/portfolios")
        
        assert response.status_code == 401


class TestGetPortfolio:
    """Tests for GET /api/v1/portfolios/{portfolio_id} endpoint."""
    
    def test_get_portfolio(self, client: TestClient, db: Session, auth_headers: dict):
        """Test getting portfolio by ID."""
        # Get first portfolio ID
        response = client.get("/api/v1/portfolios", headers=auth_headers)
        portfolio_id = response.json()[0]["id"]
        
        # Get portfolio details
        response = client.get(f"/api/v1/portfolios/{portfolio_id}", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == portfolio_id
        assert data["name"] in ["장기투자", "단타", "정찰병"]
    
    def test_get_portfolio_not_found(self, client: TestClient, auth_headers: dict):
        """Test getting non-existent portfolio."""
        response = client.get("/api/v1/portfolios/99999", headers=auth_headers)
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestGetPortfolioSummary:
    """Tests for GET /api/v1/portfolios/{portfolio_id}/summary endpoint."""
    
    def test_get_empty_portfolio_summary(self, client: TestClient, db: Session, auth_headers: dict):
        """Test getting summary for portfolio with no holdings."""
        # Get first portfolio ID
        response = client.get("/api/v1/portfolios", headers=auth_headers)
        portfolio_id = response.json()[0]["id"]
        
        # Get summary
        response = client.get(f"/api/v1/portfolios/{portfolio_id}/summary", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "portfolio" in data
        assert "holdings" in data
        assert "summary" in data
        
        assert len(data["holdings"]) == 0
        assert data["summary"]["total_holdings"] == 0
        assert data["summary"]["total_cost_basis"] == 0
        assert data["summary"]["total_current_value"] == 0
    
    def test_get_portfolio_summary_with_holdings(self, client: TestClient, db: Session, auth_headers: dict):
        """Test getting summary with holdings and P&L calculations."""
        # Get first portfolio ID
        response = client.get("/api/v1/portfolios", headers=auth_headers)
        portfolio_id = response.json()[0]["id"]
        
        # Add holdings
        client.post(
            f"/api/v1/portfolios/{portfolio_id}/holdings",
            json={"symbol": "AAPL", "quantity": 10, "avg_price": 175.50},
            headers=auth_headers
        )
        client.post(
            f"/api/v1/portfolios/{portfolio_id}/holdings",
            json={"symbol": "MSFT", "quantity": 5, "avg_price": 300.00},
            headers=auth_headers
        )
        
        # Create stock quotes for current prices
        user_id = 1  # From auth fixture
        portfolios = db.query(Portfolio).filter(Portfolio.user_id == user_id).all()
        portfolio = next(p for p in portfolios if p.id == portfolio_id)
        
        # Add stock quotes
        aapl_quote = StockQuote(
            symbol="AAPL",
            current_price=Decimal("180.00"),
            daily_change_pct=Decimal("2.56"),
            volume=50000000,
            market_status=MarketStatus.CLOSED,
            market=Market.US,
            cache_data={}
        )
        msft_quote = StockQuote(
            symbol="MSFT",
            current_price=Decimal("310.00"),
            daily_change_pct=Decimal("3.33"),
            volume=30000000,
            market_status=MarketStatus.CLOSED,
            market=Market.US,
            cache_data={}
        )
        db.add(aapl_quote)
        db.add(msft_quote)
        db.commit()
        
        # Get summary
        response = client.get(f"/api/v1/portfolios/{portfolio_id}/summary", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # Check holdings
        assert len(data["holdings"]) == 2
        
        aapl_holding = next(h for h in data["holdings"] if h["symbol"] == "AAPL")
        assert aapl_holding["quantity"] == 10
        assert Decimal(str(aapl_holding["avg_price"])) == Decimal("175.50")
        assert Decimal(str(aapl_holding["cost_basis"])) == Decimal("1755.00")  # 10 * 175.50
        assert Decimal(str(aapl_holding["current_price"])) == Decimal("180.00")
        assert Decimal(str(aapl_holding["current_value"])) == Decimal("1800.00")  # 10 * 180.00
        assert Decimal(str(aapl_holding["profit_loss"])) == Decimal("45.00")  # 1800 - 1755
        
        msft_holding = next(h for h in data["holdings"] if h["symbol"] == "MSFT")
        assert msft_holding["quantity"] == 5
        assert Decimal(str(msft_holding["cost_basis"])) == Decimal("1500.00")  # 5 * 300
        assert Decimal(str(msft_holding["current_value"])) == Decimal("1550.00")  # 5 * 310
        assert Decimal(str(msft_holding["profit_loss"])) == Decimal("50.00")  # 1550 - 1500
        
        # Check summary
        summary = data["summary"]
        assert summary["total_holdings"] == 2
        assert Decimal(str(summary["total_cost_basis"])) == Decimal("3255.00")  # 1755 + 1500
        assert Decimal(str(summary["total_current_value"])) == Decimal("3350.00")  # 1800 + 1550
        assert Decimal(str(summary["total_profit_loss"])) == Decimal("95.00")  # 45 + 50


class TestAddHolding:
    """Tests for POST /api/v1/portfolios/{portfolio_id}/holdings endpoint."""
    
    def test_add_holding(self, client: TestClient, db: Session, auth_headers: dict):
        """Test adding a new holding."""
        # Get first portfolio ID
        response = client.get("/api/v1/portfolios", headers=auth_headers)
        portfolio_id = response.json()[0]["id"]
        
        # Add holding
        response = client.post(
            f"/api/v1/portfolios/{portfolio_id}/holdings",
            json={
                "symbol": "AAPL",
                "quantity": 10,
                "avg_price": 175.50,
                "notes": "Long-term hold"
            },
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        
        assert data["symbol"] == "AAPL"
        assert data["quantity"] == 10
        assert Decimal(str(data["avg_price"])) == Decimal("175.50")
        assert Decimal(str(data["cost_basis"])) == Decimal("1755.00")
        assert data["notes"] == "Long-term hold"
    
    def test_add_holding_duplicate_symbol(self, client: TestClient, db: Session, auth_headers: dict):
        """Test adding duplicate symbol to same portfolio."""
        # Get first portfolio ID
        response = client.get("/api/v1/portfolios", headers=auth_headers)
        portfolio_id = response.json()[0]["id"]
        
        # Add holding
        client.post(
            f"/api/v1/portfolios/{portfolio_id}/holdings",
            json={"symbol": "AAPL", "quantity": 10, "avg_price": 175.50},
            headers=auth_headers
        )
        
        # Try to add again
        response = client.post(
            f"/api/v1/portfolios/{portfolio_id}/holdings",
            json={"symbol": "AAPL", "quantity": 5, "avg_price": 180.00},
            headers=auth_headers
        )
        
        assert response.status_code == 409
        assert "already exists" in response.json()["detail"].lower()
    
    def test_add_holding_100_item_limit(self, client: TestClient, db: Session, auth_headers: dict):
        """Test 100-item limit per portfolio."""
        # Get first portfolio ID
        response = client.get("/api/v1/portfolios", headers=auth_headers)
        portfolio_id = response.json()[0]["id"]
        
        # Get portfolio from DB
        user_id = 1  # From auth fixture
        portfolio = db.query(Portfolio).filter(
            Portfolio.id == portfolio_id,
            Portfolio.user_id == user_id
        ).first()
        
        # Add 100 holdings directly to DB
        for i in range(100):
            holding = Holding(
                portfolio_id=portfolio.id,
                symbol=f"SYM{i:03d}",
                quantity=1,
                avg_price=Decimal("100.00")
            )
            db.add(holding)
        db.commit()
        
        # Try to add 101st holding
        response = client.post(
            f"/api/v1/portfolios/{portfolio_id}/holdings",
            json={"symbol": "AAPL", "quantity": 10, "avg_price": 175.50},
            headers=auth_headers
        )
        
        assert response.status_code == 409
        assert "maximum of 100" in response.json()["detail"].lower()
    
    def test_add_holding_invalid_symbol(self, client: TestClient, auth_headers: dict):
        """Test adding holding with invalid symbol."""
        # Get first portfolio ID
        response = client.get("/api/v1/portfolios", headers=auth_headers)
        portfolio_id = response.json()[0]["id"]
        
        # Try to add with invalid symbol
        response = client.post(
            f"/api/v1/portfolios/{portfolio_id}/holdings",
            json={"symbol": "AAPL@#$", "quantity": 10, "avg_price": 175.50},
            headers=auth_headers
        )
        
        assert response.status_code == 422  # Validation error


class TestUpdateHolding:
    """Tests for PUT /api/v1/portfolios/{portfolio_id}/holdings/{holding_id} endpoint."""
    
    def test_update_holding(self, client: TestClient, db: Session, auth_headers: dict):
        """Test updating holding quantity and avg_price."""
        # Get first portfolio ID
        response = client.get("/api/v1/portfolios", headers=auth_headers)
        portfolio_id = response.json()[0]["id"]
        
        # Add holding
        response = client.post(
            f"/api/v1/portfolios/{portfolio_id}/holdings",
            json={"symbol": "AAPL", "quantity": 10, "avg_price": 175.50},
            headers=auth_headers
        )
        holding_id = response.json()["id"]
        
        # Update holding
        response = client.put(
            f"/api/v1/portfolios/{portfolio_id}/holdings/{holding_id}",
            json={"quantity": 15, "avg_price": 177.00},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["quantity"] == 15
        assert Decimal(str(data["avg_price"])) == Decimal("177.00")
        assert Decimal(str(data["cost_basis"])) == Decimal("2655.00")  # 15 * 177
    
    def test_update_holding_not_found(self, client: TestClient, auth_headers: dict):
        """Test updating non-existent holding."""
        # Get first portfolio ID
        response = client.get("/api/v1/portfolios", headers=auth_headers)
        portfolio_id = response.json()[0]["id"]
        
        response = client.put(
            f"/api/v1/portfolios/{portfolio_id}/holdings/99999",
            json={"quantity": 15},
            headers=auth_headers
        )
        
        assert response.status_code == 404


class TestDeleteHolding:
    """Tests for DELETE /api/v1/portfolios/{portfolio_id}/holdings/{holding_id} endpoint."""
    
    def test_delete_holding(self, client: TestClient, db: Session, auth_headers: dict):
        """Test deleting a holding."""
        # Get first portfolio ID
        response = client.get("/api/v1/portfolios", headers=auth_headers)
        portfolio_id = response.json()[0]["id"]
        
        # Add holding
        response = client.post(
            f"/api/v1/portfolios/{portfolio_id}/holdings",
            json={"symbol": "AAPL", "quantity": 10, "avg_price": 175.50},
            headers=auth_headers
        )
        holding_id = response.json()["id"]
        
        # Delete holding
        response = client.delete(
            f"/api/v1/portfolios/{portfolio_id}/holdings/{holding_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 204
        
        # Verify deleted
        response = client.get(f"/api/v1/portfolios/{portfolio_id}/summary", headers=auth_headers)
        data = response.json()
        assert len(data["holdings"]) == 0
    
    def test_delete_holding_not_found(self, client: TestClient, auth_headers: dict):
        """Test deleting non-existent holding."""
        # Get first portfolio ID
        response = client.get("/api/v1/portfolios", headers=auth_headers)
        portfolio_id = response.json()[0]["id"]
        
        response = client.delete(
            f"/api/v1/portfolios/{portfolio_id}/holdings/99999",
            headers=auth_headers
        )
        
        assert response.status_code == 404
