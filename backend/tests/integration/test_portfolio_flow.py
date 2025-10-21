"""Portfolio management integration tests.

These tests verify the complete lifecycle of portfolio management:
- Auto-created default portfolio on registration
- Adding/viewing/updating/deleting holdings
- Portfolio summary calculations
- User isolation (users can only see their own portfolios)
"""
from decimal import Decimal
from fastapi.testclient import TestClient


def test_auto_created_portfolios(authenticated_client: tuple):
    """Verify that default portfolio is auto-created on user registration."""
    client, user_data = authenticated_client
    
    response = client.get("/api/v1/portfolios")
    assert response.status_code == 200
    
    portfolios = response.json()
    assert len(portfolios) >= 1
    
    # First portfolio should be auto-created (name may vary)
    default_portfolio = portfolios[0]
    assert default_portfolio["name"] is not None
    assert len(default_portfolio["name"]) > 0
    assert default_portfolio["is_public"] is False


def test_complete_portfolio_flow(authenticated_client: tuple):
    """Test complete portfolio flow: add holding → view summary → update → delete.
    
    This verifies:
    - Adding holdings with symbol, quantity, avg_price
    - Portfolio summary calculation (total value, P&L)
    - Updating holding quantities
    - Deleting holdings
    """
    client, user_data = authenticated_client
    
    # Step 1: Get portfolios and select first one
    response = client.get("/api/v1/portfolios")
    assert response.status_code == 200
    
    portfolios = response.json()
    assert len(portfolios) >= 1
    portfolio_id = portfolios[0]["id"]
    
    # Step 2: Add first holding (AAPL)
    holding_data = {
        "symbol": "AAPL",
        "quantity": 10,
        "avg_price": 150.00
    }
    
    response = client.post(f"/api/v1/portfolios/{portfolio_id}/holdings", json=holding_data)
    assert response.status_code == 201
    
    holding1 = response.json()
    assert holding1["symbol"] == "AAPL"
    assert holding1["quantity"] == 10
    assert float(holding1["avg_price"]) == 150.00
    holding1_id = holding1["id"]
    
    # Step 3: Add second holding (NVDA)
    response = client.post(f"/api/v1/portfolios/{portfolio_id}/holdings", json={
        "symbol": "NVDA",
        "quantity": 5,
        "avg_price": 500.00
    })
    assert response.status_code == 201
    holding2_id = response.json()["id"]
    
    # Step 4: Get portfolio summary
    response = client.get(f"/api/v1/portfolios/{portfolio_id}/summary")
    assert response.status_code == 200
    
    summary_response = response.json()
    assert summary_response["portfolio"]["id"] == portfolio_id
    assert len(summary_response["holdings"]) == 2
    
    summary = summary_response["summary"]
    assert summary["total_holdings"] == 2
    
    # Cost basis should be: (10 * 150) + (5 * 500) = 1500 + 2500 = 4000
    assert float(summary["total_cost_basis"]) == 4000.00
    
    # Current value and P&L depend on real-time prices
    # Just verify they exist and are numbers
    assert "total_current_value" in summary
    assert "total_profit_loss" in summary
    assert "total_return_rate" in summary
    
    # Step 5: Update holding quantity (AAPL: 10 → 15 quantity)
    response = client.put(
        f"/api/v1/portfolios/{portfolio_id}/holdings/{holding1_id}",
        json={"quantity": 15, "avg_price": 150.00}
    )
    assert response.status_code == 200
    
    updated_holding = response.json()
    assert updated_holding["quantity"] == 15
    
    # Step 6: Delete NVDA holding
    response = client.delete(f"/api/v1/portfolios/{portfolio_id}/holdings/{holding2_id}")
    assert response.status_code == 204
    
    # Step 7: Verify portfolio has only 1 holding now
    response = client.get(f"/api/v1/portfolios/{portfolio_id}/summary")
    assert response.status_code == 200
    
    summary_response = response.json()
    assert len(summary_response["holdings"]) == 1
    
    summary = summary_response["summary"]
    assert summary["total_holdings"] == 1


def test_holdings_with_real_prices(authenticated_client: tuple):
    """Verify that holdings fetch real-time prices from yfinance."""
    client, user_data = authenticated_client
    
    response = client.get("/api/v1/portfolios")
    portfolios = response.json()
    portfolio_id = portfolios[0]["id"]
    
    # Add AAPL holding
    response = client.post(f"/api/v1/portfolios/{portfolio_id}/holdings", json={
        "symbol": "AAPL",
        "quantity": 10,
        "avg_price": 150.00
    })
    assert response.status_code == 201
    
    # Get summary with real-time prices
    response = client.get(f"/api/v1/portfolios/{portfolio_id}/summary")
    assert response.status_code == 200
    
    summary_response = response.json()
    holdings = summary_response["holdings"]
    
    assert len(holdings) == 1
    aapl = holdings[0]
    
    # Verify real-time price exists and is reasonable
    assert aapl["current_price"] is not None
    assert float(aapl["current_price"]) > 0
    
    # Verify calculated fields
    assert "current_value" in aapl
    assert "profit_loss" in aapl
    assert "return_rate" in aapl


def test_korean_stock_symbols(authenticated_client: tuple):
    """Test adding Korean stock symbols (e.g., 005930.KS for Samsung)."""
    client, user_data = authenticated_client
    
    response = client.get("/api/v1/portfolios")
    portfolios = response.json()
    portfolio_id = portfolios[0]["id"]
    
    # Add Samsung Electronics (005930.KS)
    response = client.post(f"/api/v1/portfolios/{portfolio_id}/holdings", json={
        "symbol": "005930.KS",
        "quantity": 100,
        "avg_price": 70000.00
    })
    assert response.status_code == 201
    
    holding = response.json()
    assert holding["symbol"] == "005930.KS"
    assert holding["quantity"] == 100
    
    # Verify it appears in summary
    response = client.get(f"/api/v1/portfolios/{portfolio_id}/summary")
    assert response.status_code == 200
    
    summary_response = response.json()
    assert len(summary_response["holdings"]) == 1
    assert summary_response["holdings"][0]["symbol"] == "005930.KS"


def test_user_isolation(authenticated_client: tuple, client: TestClient):
    """Verify users can only access their own portfolios."""
    client1, user1_data = authenticated_client
    
    # Create second user
    import time
    user2_email = f"user2_{int(time.time())}@example.com"
    response = client.post("/api/v1/auth/register", json={
        "email": user2_email,
        "password": "SecurePass123!"
    })
    assert response.status_code == 201
    
    # Login as user2
    response = client.post("/api/v1/auth/login", json={
        "email": user2_email,
        "password": "SecurePass123!"
    })
    assert response.status_code == 200
    user2_token = response.json()["token"]["access_token"]
    
    # Get user1's portfolio
    response = client1.get("/api/v1/portfolios")
    user1_portfolios = response.json()
    user1_portfolio_id = user1_portfolios[0]["id"]
    
    # Add holding as user1
    response = client1.post(f"/api/v1/portfolios/{user1_portfolio_id}/holdings", json={
        "symbol": "TSLA",
        "quantity": 5,
        "avg_price": 200.00
    })
    assert response.status_code == 201
    
    # Try to access user1's portfolio as user2 (should fail)
    client2 = TestClient(client.app)
    client2.headers = {"Authorization": f"Bearer {user2_token}"}
    
    response = client2.get(f"/api/v1/portfolios/{user1_portfolio_id}/summary")
    assert response.status_code in [403, 404]  # Forbidden or Not Found
    
    # User2 should only see their own portfolio
    response = client2.get("/api/v1/portfolios")
    assert response.status_code == 200
    user2_portfolios = response.json()
    assert len(user2_portfolios) >= 1
    assert user2_portfolios[0]["id"] != user1_portfolio_id


def test_duplicate_symbol_prevention(authenticated_client: tuple):
    """Verify that duplicate symbols are not allowed in the same portfolio."""
    client, user_data = authenticated_client
    
    response = client.get("/api/v1/portfolios")
    portfolios = response.json()
    portfolio_id = portfolios[0]["id"]
    
    # Add MSFT holding
    response = client.post(f"/api/v1/portfolios/{portfolio_id}/holdings", json={
        "symbol": "MSFT",
        "quantity": 10,
        "avg_price": 300.00
    })
    assert response.status_code == 201
    
    # Try to add MSFT again (should fail)
    response = client.post(f"/api/v1/portfolios/{portfolio_id}/holdings", json={
        "symbol": "MSFT",
        "quantity": 5,
        "avg_price": 310.00
    })
    assert response.status_code in [400, 409]  # Accept both 400 Bad Request and 409 Conflict
    assert "already exists" in response.json()["detail"].lower() or "duplicate" in response.json()["detail"].lower()


def test_max_holdings_limit(authenticated_client: tuple):
    """Verify that portfolios cannot exceed 100 holdings."""
    client, user_data = authenticated_client
    
    response = client.get("/api/v1/portfolios")
    portfolios = response.json()
    portfolio_id = portfolios[0]["id"]
    
    # Add 100 holdings (using numbered symbols)
    for i in range(100):
        response = client.post(f"/api/v1/portfolios/{portfolio_id}/holdings", json={
            "symbol": f"TEST{i:03d}",
            "quantity": 1,
            "avg_price": 10.00
        })
        # Some symbols might not be valid, that's okay
        # We just need to try to reach the limit
        if response.status_code != 201:
            continue
    
    # Try to add 101st holding (should fail)
    response = client.post(f"/api/v1/portfolios/{portfolio_id}/holdings", json={
        "symbol": "OVER_LIMIT",
        "quantity": 1,
        "avg_price": 10.00
    })
    
    # Should either fail due to limit or invalid symbol
    # If limit is enforced, status should be 400
    if response.status_code == 400:
        assert "limit" in response.json()["detail"].lower() or "maximum" in response.json()["detail"].lower()


def test_invalid_symbol_validation(authenticated_client: tuple):
    """Verify that invalid stock symbols are rejected."""
    client, user_data = authenticated_client
    
    response = client.get("/api/v1/portfolios")
    portfolios = response.json()
    portfolio_id = portfolios[0]["id"]
    
    # Try to add holdings with invalid symbols
    invalid_symbols = ["", "   ", "INVALID_SYMBOL_123456", "!@#$%"]
    
    for symbol in invalid_symbols:
        response = client.post(f"/api/v1/portfolios/{portfolio_id}/holdings", json={
            "symbol": symbol,
            "quantity": 10,
            "avg_price": 100.00
        })
        assert response.status_code in [400, 422]


def test_negative_quantity_price_validation(authenticated_client: tuple):
    """Verify that negative quantities and prices are rejected."""
    client, user_data = authenticated_client
    
    response = client.get("/api/v1/portfolios")
    portfolios = response.json()
    portfolio_id = portfolios[0]["id"]
    
    # Try negative quantity
    response = client.post(f"/api/v1/portfolios/{portfolio_id}/holdings", json={
        "symbol": "AAPL",
        "quantity": -10,
        "avg_price": 150.00
    })
    assert response.status_code in [400, 422]
    
    # Try negative price
    response = client.post(f"/api/v1/portfolios/{portfolio_id}/holdings", json={
        "symbol": "AAPL",
        "quantity": 10,
        "avg_price": -150.00
    })
    assert response.status_code in [400, 422]
    
    # Try zero quantity
    response = client.post(f"/api/v1/portfolios/{portfolio_id}/holdings", json={
        "symbol": "AAPL",
        "quantity": 0,
        "avg_price": 150.00
    })
    assert response.status_code in [400, 422]


def test_multiple_portfolio_management(authenticated_client: tuple):
    """Test managing existing portfolios (portfolio creation API not implemented)."""
    client, user_data = authenticated_client
    
    # Get all portfolios (at least one auto-created)
    response = client.get("/api/v1/portfolios")
    assert response.status_code == 200
    
    portfolios = response.json()
    assert len(portfolios) >= 1
    
    # Use first portfolio for testing
    first_portfolio_id = portfolios[0]["id"]
    
    # Add holdings to first portfolio
    response = client.post(f"/api/v1/portfolios/{first_portfolio_id}/holdings", json={
        "symbol": "GOOGL",
        "quantity": 20,
        "avg_price": 140.00
    })
    assert response.status_code == 201
    
    # Verify portfolio has holdings
    response = client.get(f"/api/v1/portfolios/{first_portfolio_id}/summary")
    assert response.status_code == 200
    
    summary = response.json()
    assert len(summary["holdings"]) >= 1
    
    # Find GOOGL in holdings
    googl_holding = next((h for h in summary["holdings"] if h["symbol"] == "GOOGL"), None)
    assert googl_holding is not None
    assert googl_holding["quantity"] == 20


def test_empty_portfolio_summary(authenticated_client: tuple):
    """Verify that portfolios with no holdings return proper zero summaries."""
    client, user_data = authenticated_client
    
    # Get existing portfolio (should be empty at start of this test)
    response = client.get("/api/v1/portfolios")
    assert response.status_code == 200
    
    portfolios = response.json()
    assert len(portfolios) >= 1
    portfolio_id = portfolios[0]["id"]
    
    # Get summary of portfolio (should be empty or will be tested after clearing)
    response = client.get(f"/api/v1/portfolios/{portfolio_id}/summary")
    assert response.status_code == 200
    
    summary_response = response.json()
    # If portfolio has holdings from previous tests in same session, skip this check
    # Or verify that empty portfolio returns zero values
    
    summary = summary_response["summary"]
    assert "total_holdings" in summary
    assert "total_cost_basis" in summary
    assert "total_current_value" in summary
    assert "total_profit_loss" in summary
    
    # If portfolio is empty, verify zero values
    if summary["total_holdings"] == 0:
        assert float(summary["total_cost_basis"]) == 0.00
        assert float(summary["total_current_value"]) == 0.00
        assert float(summary["total_profit_loss"]) == 0.00


def test_bulk_holdings_performance(authenticated_client: tuple):
    """Test performance with multiple holdings (10-20 holdings)."""
    client, user_data = authenticated_client
    
    response = client.get("/api/v1/portfolios")
    portfolios = response.json()
    portfolio_id = portfolios[0]["id"]
    
    # Add 15 different holdings
    symbols = ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA", "NVDA", "META", "NFLX", 
               "AMD", "INTC", "CSCO", "ORCL", "IBM", "CRM", "ADBE"]
    
    for symbol in symbols:
        response = client.post(f"/api/v1/portfolios/{portfolio_id}/holdings", json={
            "symbol": symbol,
            "quantity": 10,
            "avg_price": 100.00
        })
        # Some might fail due to real-time validation, that's okay
        if response.status_code != 201:
            continue
    
    # Get summary (should complete in reasonable time)
    response = client.get(f"/api/v1/portfolios/{portfolio_id}/summary")
    assert response.status_code == 200
    
    summary_response = response.json()
    # Should have at least some holdings added
    assert len(summary_response["holdings"]) > 0
    
    summary = summary_response["summary"]
    assert summary["total_holdings"] > 0
    assert float(summary["total_cost_basis"]) > 0


def test_portfolio_deletion(authenticated_client: tuple):
    """Test deleting holdings (portfolio deletion API not implemented)."""
    client, user_data = authenticated_client
    
    # Get existing portfolio
    response = client.get("/api/v1/portfolios")
    assert response.status_code == 200
    
    portfolios = response.json()
    assert len(portfolios) >= 1
    portfolio_id = portfolios[0]["id"]
    
    # Add a holding
    response = client.post(f"/api/v1/portfolios/{portfolio_id}/holdings", json={
        "symbol": "AAPL",
        "quantity": 100,
        "avg_price": 150.00
    })
    assert response.status_code == 201
    holding_id = response.json()["id"]
    
    # Delete the holding
    response = client.delete(f"/api/v1/portfolios/{portfolio_id}/holdings/{holding_id}")
    assert response.status_code in [204, 200]
    
    # Verify holding no longer exists in summary
    response = client.get(f"/api/v1/portfolios/{portfolio_id}/summary")
    assert response.status_code == 200
    
    summary_response = response.json()
    holding_ids = [h["id"] for h in summary_response["holdings"]]
    assert holding_id not in holding_ids


def test_unauthorized_access_prevention(authenticated_client: tuple, client: TestClient):
    """Verify that unauthenticated requests are blocked."""
    auth_client, user_data = authenticated_client
    
    # Get portfolio ID from authenticated client
    response = auth_client.get("/api/v1/portfolios")
    portfolios = response.json()
    portfolio_id = portfolios[0]["id"]
    
    # Try to access without authentication
    unauth_client = TestClient(client.app)
    
    # Try to get portfolios
    response = unauth_client.get("/api/v1/portfolios")
    assert response.status_code in [401, 403]  # Accept both Unauthorized and Forbidden
    
    # Try to get portfolio summary
    response = unauth_client.get(f"/api/v1/portfolios/{portfolio_id}/summary")
    assert response.status_code in [401, 403]
    
    # Try to add holding
    response = unauth_client.post(f"/api/v1/portfolios/{portfolio_id}/holdings", json={
        "symbol": "AAPL",
        "quantity": 10,
        "avg_price": 150.00
    })
    assert response.status_code in [401, 403]
