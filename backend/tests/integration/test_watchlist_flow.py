"""Integration tests for watchlist flow.

Tests the complete watchlist management workflow:
- Add stock to watchlist
- View watchlist with current prices
- Update watchlist order (drag & drop)
- Update watchlist notes
- Remove stock from watchlist
- Watchlist limit enforcement (50 items)
"""

import pytest
from fastapi.testclient import TestClient


def test_complete_watchlist_flow(authenticated_client: tuple):
    """Test complete watchlist flow: add → view → update → delete.
    
    This verifies:
    - Adding stocks to watchlist
    - Retrieving watchlist with display order
    - Updating display order (reordering)
    - Adding notes to watchlist items
    - Removing stocks from watchlist
    """
    client, user_data = authenticated_client
    
    # Step 1: Add first stock to watchlist
    watchlist_data = {
        "symbol": "AAPL",
        "notes": "Apple Inc. - Tech giant"
    }
    
    response = client.post("/api/v1/watchlist", json=watchlist_data)
    assert response.status_code == 201
    
    item = response.json()
    assert item["symbol"] == "AAPL"
    assert item["notes"] == watchlist_data["notes"]
    assert item["display_order"] == 0  # First item
    item_id_1 = item["id"]
    
    # Step 2: Add second stock
    response = client.post("/api/v1/watchlist", json={
        "symbol": "NVDA",
        "notes": "NVIDIA - AI chips"
    })
    assert response.status_code == 201
    item_id_2 = response.json()["id"]
    
    # Step 3: Add third stock
    response = client.post("/api/v1/watchlist", json={
        "symbol": "TSLA"
    })
    assert response.status_code == 201
    item_id_3 = response.json()["id"]
    
    # Step 4: Get watchlist (should be ordered by display_order)
    response = client.get("/api/v1/watchlist")
    assert response.status_code == 200
    
    watchlist = response.json()
    assert len(watchlist) == 3
    assert watchlist[0]["symbol"] == "AAPL"
    assert watchlist[1]["symbol"] == "NVDA"
    assert watchlist[2]["symbol"] == "TSLA"
    
    # Step 5: Update display order (drag TSLA to first position)
    reorder_data = {
        "items": [
            {"id": item_id_3, "display_order": 0},
            {"id": item_id_1, "display_order": 1},
            {"id": item_id_2, "display_order": 2}
        ]
    }
    
    response = client.patch("/api/v1/watchlist/reorder", json=reorder_data)
    assert response.status_code == 200
    
    # Verify new order
    response = client.get("/api/v1/watchlist")
    assert response.status_code == 200
    
    watchlist = response.json()
    assert watchlist[0]["symbol"] == "TSLA"
    assert watchlist[1]["symbol"] == "AAPL"
    assert watchlist[2]["symbol"] == "NVDA"
    
    # Step 6: Update notes for AAPL
    response = client.patch(f"/api/v1/watchlist/{item_id_1}", json={
        "notes": "Apple - Updated note"
    })
    assert response.status_code == 200
    
    item = response.json()
    assert item["notes"] == "Apple - Updated note"
    
    # Step 7: Delete NVDA from watchlist
    response = client.delete(f"/api/v1/watchlist/{item_id_2}")
    assert response.status_code == 204
    
    # Verify deletion
    response = client.get("/api/v1/watchlist")
    assert response.status_code == 200
    
    watchlist = response.json()
    assert len(watchlist) == 2
    symbols = [item["symbol"] for item in watchlist]
    assert "NVDA" not in symbols
    assert "AAPL" in symbols
    assert "TSLA" in symbols


def test_watchlist_duplicate_symbol(authenticated_client: tuple):
    """Test that duplicate symbols are rejected."""
    client, _ = authenticated_client
    
    # Add stock
    response = client.post("/api/v1/watchlist", json={"symbol": "MSFT"})
    assert response.status_code == 201
    
    # Try to add same stock again
    response = client.post("/api/v1/watchlist", json={"symbol": "MSFT"})
    assert response.status_code == 409
    assert "already in watchlist" in response.json()["detail"].lower()


def test_watchlist_50_item_limit(authenticated_client: tuple):
    """Test that watchlist enforces 50-item limit."""
    client, _ = authenticated_client
    
    # Add 50 stocks (using symbols like STOCK001, STOCK002, etc.)
    for i in range(50):
        symbol = f"STOCK{i:03d}"
        response = client.post("/api/v1/watchlist", json={"symbol": symbol})
        assert response.status_code == 201
    
    # Try to add 51st stock
    response = client.post("/api/v1/watchlist", json={"symbol": "STOCK051"})
    assert response.status_code == 400
    assert "limit" in response.json()["detail"].lower()


def test_watchlist_invalid_symbol(authenticated_client: tuple):
    """Test that invalid symbols are handled gracefully."""
    client, _ = authenticated_client
    
    # Try to add empty symbol
    response = client.post("/api/v1/watchlist", json={"symbol": ""})
    assert response.status_code == 422  # Validation error


def test_watchlist_with_stock_quotes(authenticated_client: tuple):
    """Test retrieving watchlist with real-time stock quotes.
    
    Note: This test may make actual API calls to yfinance.
    Consider mocking in CI/CD environment.
    """
    client, _ = authenticated_client
    
    # Add real stock symbols
    symbols = ["AAPL", "GOOGL", "MSFT"]
    for symbol in symbols:
        response = client.post("/api/v1/watchlist", json={"symbol": symbol})
        assert response.status_code == 201
    
    # Get watchlist with quotes
    response = client.get("/api/v1/watchlist?include_quotes=true")
    assert response.status_code == 200
    
    watchlist = response.json()
    assert len(watchlist) == 3
    
    # Verify each item has stock quote data (if available)
    for item in watchlist:
        assert "symbol" in item
        # Quote data may be null if market is closed or API fails
        if item.get("current_price"):
            assert isinstance(item["current_price"], (int, float))


def test_delete_nonexistent_watchlist_item(authenticated_client: tuple):
    """Test deleting non-existent watchlist item returns 404."""
    client, _ = authenticated_client
    
    response = client.delete("/api/v1/watchlist/99999")
    assert response.status_code == 404


def test_update_nonexistent_watchlist_item(authenticated_client: tuple):
    """Test updating non-existent watchlist item returns 404."""
    client, _ = authenticated_client
    
    response = client.patch("/api/v1/watchlist/99999", json={
        "notes": "This should fail"
    })
    assert response.status_code == 404


def test_watchlist_isolation_between_users(client: TestClient):
    """Test that users can only see their own watchlist items."""
    # Create first user
    user1_data = {
        "email": "user1@example.com",
        "password": "Password123",
        "full_name": "User One"
    }
    response = client.post("/api/v1/auth/register", json=user1_data)
    assert response.status_code == 200
    
    # Login as user1
    response = client.post("/api/v1/auth/login", json={
        "email": user1_data["email"],
        "password": user1_data["password"]
    })
    token1 = response.json()["access_token"]
    
    # User1 adds stock
    headers1 = {"Authorization": f"Bearer {token1}"}
    response = client.post("/api/v1/watchlist", 
                          json={"symbol": "AAPL"},
                          headers=headers1)
    assert response.status_code == 201
    
    # Create second user
    user2_data = {
        "email": "user2@example.com",
        "password": "Password123",
        "full_name": "User Two"
    }
    response = client.post("/api/v1/auth/register", json=user2_data)
    assert response.status_code == 200
    
    # Login as user2
    response = client.post("/api/v1/auth/login", json={
        "email": user2_data["email"],
        "password": user2_data["password"]
    })
    token2 = response.json()["access_token"]
    
    # User2 should have empty watchlist
    headers2 = {"Authorization": f"Bearer {token2}"}
    response = client.get("/api/v1/watchlist", headers=headers2)
    assert response.status_code == 200
    
    watchlist = response.json()
    assert len(watchlist) == 0  # User2 should not see User1's stocks


def test_korean_stock_symbols(authenticated_client: tuple):
    """Test adding Korean stock symbols with .KS and .KQ suffixes."""
    client, _ = authenticated_client
    
    # Add KOSPI stock (Samsung Electronics)
    response = client.post("/api/v1/watchlist", json={
        "symbol": "005930.KS",
        "notes": "삼성전자"
    })
    assert response.status_code == 201
    
    # Add KOSDAQ stock
    response = client.post("/api/v1/watchlist", json={
        "symbol": "035720.KQ",
        "notes": "카카오"
    })
    assert response.status_code == 201
    
    # Verify both are in watchlist
    response = client.get("/api/v1/watchlist")
    assert response.status_code == 200
    
    watchlist = response.json()
    symbols = [item["symbol"] for item in watchlist]
    assert "005930.KS" in symbols
    assert "035720.KQ" in symbols
