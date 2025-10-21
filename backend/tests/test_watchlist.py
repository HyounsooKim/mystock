"""Tests for watchlist API endpoints.

Tests watchlist CRUD operations and reordering functionality.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.models import Watchlist
from src.core.config import settings


class TestGetWatchlist:
    """Tests for GET /api/v1/watchlist endpoint."""
    
    def test_get_empty_watchlist(self, client: TestClient, auth_headers: dict):
        """Test getting empty watchlist."""
        response = client.get("/api/v1/watchlist", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["items"] == []
        assert data["total"] == 0
        assert data["max_items"] == 50
    
    def test_get_watchlist_with_items(
        self, 
        client: TestClient, 
        test_user, 
        auth_headers: dict,
        db: Session
    ):
        """Test getting watchlist with items."""
        # Add test items
        items_data = [
            {"symbol": "AAPL", "display_order": 0, "notes": "Apple Inc."},
            {"symbol": "MSFT", "display_order": 1, "notes": "Microsoft"},
            {"symbol": "005930.KS", "display_order": 2, "notes": "삼성전자"}
        ]
        
        for item_data in items_data:
            item = Watchlist(user_id=test_user.id, **item_data)
            db.add(item)
        db.commit()
        
        response = client.get("/api/v1/watchlist", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total"] == 3
        assert len(data["items"]) == 3
        assert data["items"][0]["symbol"] == "AAPL"
        assert data["items"][1]["symbol"] == "MSFT"
        assert data["items"][2]["symbol"] == "005930.KS"
    
    def test_get_watchlist_no_auth(self, client: TestClient):
        """Test getting watchlist without authentication."""
        response = client.get("/api/v1/watchlist")
        
        assert response.status_code == 403


class TestAddToWatchlist:
    """Tests for POST /api/v1/watchlist endpoint."""
    
    def test_add_to_watchlist_success(
        self, 
        client: TestClient, 
        auth_headers: dict,
        db: Session
    ):
        """Test successfully adding stock to watchlist."""
        response = client.post(
            "/api/v1/watchlist",
            headers=auth_headers,
            json={
                "symbol": "AAPL",
                "notes": "Apple Inc. - 관심있는 미국 기술주"
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        
        assert data["symbol"] == "AAPL"
        assert data["display_order"] == 0
        assert data["notes"] == "Apple Inc. - 관심있는 미국 기술주"
        assert "id" in data
        assert "created_at" in data
    
    def test_add_to_watchlist_lowercase_symbol(
        self, 
        client: TestClient, 
        auth_headers: dict
    ):
        """Test adding with lowercase symbol (should convert to uppercase)."""
        response = client.post(
            "/api/v1/watchlist",
            headers=auth_headers,
            json={"symbol": "aapl"}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["symbol"] == "AAPL"
    
    def test_add_duplicate_symbol(
        self, 
        client: TestClient, 
        test_user,
        auth_headers: dict,
        db: Session
    ):
        """Test adding duplicate symbol."""
        # Add first item
        item = Watchlist(user_id=test_user.id, symbol="AAPL", display_order=0)
        db.add(item)
        db.commit()
        
        # Try to add duplicate
        response = client.post(
            "/api/v1/watchlist",
            headers=auth_headers,
            json={"symbol": "AAPL"}
        )
        
        assert response.status_code == 400
        assert "already in watchlist" in response.json()["detail"].lower()
    
    def test_add_beyond_limit(
        self, 
        client: TestClient, 
        test_user,
        auth_headers: dict,
        db: Session
    ):
        """Test adding beyond 50 item limit."""
        # Add 50 items
        for i in range(settings.MAX_WATCHLIST_ITEMS):
            item = Watchlist(
                user_id=test_user.id, 
                symbol=f"SYM{i:03d}", 
                display_order=i
            )
            db.add(item)
        db.commit()
        
        # Try to add 51st item
        response = client.post(
            "/api/v1/watchlist",
            headers=auth_headers,
            json={"symbol": "OVERFLOW"}
        )
        
        assert response.status_code == 400
        assert "limit reached" in response.json()["detail"].lower()
    
    def test_add_invalid_symbol(self, client: TestClient, auth_headers: dict):
        """Test adding invalid symbol format."""
        response = client.post(
            "/api/v1/watchlist",
            headers=auth_headers,
            json={"symbol": "INVALID@SYMBOL"}
        )
        
        assert response.status_code == 422


class TestUpdateWatchlistItem:
    """Tests for PUT /api/v1/watchlist/{symbol} endpoint."""
    
    def test_update_notes_success(
        self, 
        client: TestClient, 
        test_user,
        auth_headers: dict,
        db: Session
    ):
        """Test successfully updating watchlist item notes."""
        # Add item
        item = Watchlist(
            user_id=test_user.id, 
            symbol="AAPL", 
            display_order=0,
            notes="Old notes"
        )
        db.add(item)
        db.commit()
        
        # Update notes
        response = client.put(
            "/api/v1/watchlist/AAPL",
            headers=auth_headers,
            json={"notes": "Updated notes"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["notes"] == "Updated notes"
        assert data["symbol"] == "AAPL"
    
    def test_update_nonexistent_item(
        self, 
        client: TestClient, 
        auth_headers: dict
    ):
        """Test updating non-existent watchlist item."""
        response = client.put(
            "/api/v1/watchlist/NONEXISTENT",
            headers=auth_headers,
            json={"notes": "Notes"}
        )
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestRemoveFromWatchlist:
    """Tests for DELETE /api/v1/watchlist/{symbol} endpoint."""
    
    def test_remove_success(
        self, 
        client: TestClient, 
        test_user,
        auth_headers: dict,
        db: Session
    ):
        """Test successfully removing stock from watchlist."""
        # Add items
        items_data = [
            {"symbol": "AAPL", "display_order": 0},
            {"symbol": "MSFT", "display_order": 1},
            {"symbol": "GOOGL", "display_order": 2}
        ]
        
        for item_data in items_data:
            item = Watchlist(user_id=test_user.id, **item_data)
            db.add(item)
        db.commit()
        
        # Remove middle item
        response = client.delete(
            "/api/v1/watchlist/MSFT",
            headers=auth_headers
        )
        
        assert response.status_code == 204
        
        # Verify removal and reordering
        remaining = db.query(Watchlist).filter(
            Watchlist.user_id == test_user.id
        ).order_by(Watchlist.display_order).all()
        
        assert len(remaining) == 2
        assert remaining[0].symbol == "AAPL"
        assert remaining[0].display_order == 0
        assert remaining[1].symbol == "GOOGL"
        assert remaining[1].display_order == 1  # Reordered from 2 to 1
    
    def test_remove_nonexistent_item(
        self, 
        client: TestClient, 
        auth_headers: dict
    ):
        """Test removing non-existent watchlist item."""
        response = client.delete(
            "/api/v1/watchlist/NONEXISTENT",
            headers=auth_headers
        )
        
        assert response.status_code == 404


class TestReorderWatchlist:
    """Tests for PUT /api/v1/watchlist/reorder endpoint."""
    
    def test_reorder_success(
        self, 
        client: TestClient, 
        test_user,
        auth_headers: dict,
        db: Session
    ):
        """Test successfully reordering watchlist."""
        # Add items
        items_data = [
            {"symbol": "AAPL", "display_order": 0},
            {"symbol": "MSFT", "display_order": 1},
            {"symbol": "GOOGL", "display_order": 2}
        ]
        
        for item_data in items_data:
            item = Watchlist(user_id=test_user.id, **item_data)
            db.add(item)
        db.commit()
        
        # Reorder: GOOGL, AAPL, MSFT
        response = client.put(
            "/api/v1/watchlist/reorder",
            headers=auth_headers,
            json={"symbol_order": ["GOOGL", "AAPL", "MSFT"]}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total"] == 3
        assert data["items"][0]["symbol"] == "GOOGL"
        assert data["items"][0]["display_order"] == 0
        assert data["items"][1]["symbol"] == "AAPL"
        assert data["items"][1]["display_order"] == 1
        assert data["items"][2]["symbol"] == "MSFT"
        assert data["items"][2]["display_order"] == 2
    
    def test_reorder_missing_symbol(
        self, 
        client: TestClient, 
        test_user,
        auth_headers: dict,
        db: Session
    ):
        """Test reordering with missing symbols."""
        # Add items
        items_data = [
            {"symbol": "AAPL", "display_order": 0},
            {"symbol": "MSFT", "display_order": 1}
        ]
        
        for item_data in items_data:
            item = Watchlist(user_id=test_user.id, **item_data)
            db.add(item)
        db.commit()
        
        # Try to reorder with only one symbol (missing MSFT)
        response = client.put(
            "/api/v1/watchlist/reorder",
            headers=auth_headers,
            json={"symbol_order": ["AAPL"]}
        )
        
        assert response.status_code == 400
        assert "must include all" in response.json()["detail"].lower()
    
    def test_reorder_invalid_symbol(
        self, 
        client: TestClient, 
        test_user,
        auth_headers: dict,
        db: Session
    ):
        """Test reordering with non-existent symbol."""
        # Add item
        item = Watchlist(user_id=test_user.id, symbol="AAPL", display_order=0)
        db.add(item)
        db.commit()
        
        # Try to reorder with non-existent symbol
        response = client.put(
            "/api/v1/watchlist/reorder",
            headers=auth_headers,
            json={"symbol_order": ["NONEXISTENT"]}
        )
        
        assert response.status_code == 400
        assert "not found" in response.json()["detail"].lower()
    
    def test_reorder_duplicate_symbols(
        self, 
        client: TestClient, 
        auth_headers: dict
    ):
        """Test reordering with duplicate symbols."""
        response = client.put(
            "/api/v1/watchlist/reorder",
            headers=auth_headers,
            json={"symbol_order": ["AAPL", "AAPL"]}
        )
        
        assert response.status_code == 422  # Validation error
