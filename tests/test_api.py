import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

import mongomock

from api import app

client = TestClient(app)


# ---------------------------------------------------------------------------
# /health
# ---------------------------------------------------------------------------

def test_health_returns_ok():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


# ---------------------------------------------------------------------------
# /metrics
# ---------------------------------------------------------------------------

def test_metrics_returns_prometheus_text():
    resp = client.get("/metrics")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/plain")
    assert "groceror_orders_events_total" in resp.text


# ---------------------------------------------------------------------------
# /analytics/summary
# ---------------------------------------------------------------------------

def _make_mock_db():
    """Return a DB-like mock backed by mongomock."""
    mock_client = mongomock.MongoClient()
    mock_mongo_db = mock_client["orders"]
    mock_db = MagicMock()
    mock_db.get_collection.side_effect = lambda name: mock_mongo_db[name]
    mock_db.close = MagicMock()
    return mock_db


def test_summary_returns_200():
    mock_db = _make_mock_db()
    with patch("api.DB", return_value=mock_db):
        resp = client.get("/analytics/summary")
    assert resp.status_code == 200
    data = resp.json()
    assert "total_revenue" in data
    assert "order_count" in data


def test_summary_with_data():
    mock_db = _make_mock_db()
    # Insert a document so counts are non-zero
    col = mock_db.get_collection("client_orders")
    col.insert_one({"order_id": "abc", "total_price": 15.0, "items": ["apple"]})

    with patch("api.DB", return_value=mock_db):
        resp = client.get("/analytics/summary")
    assert resp.status_code == 200
    data = resp.json()
    assert data["order_count"] == 1
    assert data["total_revenue"] == 15.0


# ---------------------------------------------------------------------------
# /analytics/most-ordered-items
# ---------------------------------------------------------------------------

def test_most_ordered_items_returns_200():
    mock_db = _make_mock_db()
    with patch("api.DB", return_value=mock_db):
        resp = client.get("/analytics/most-ordered-items")
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert isinstance(data["items"], list)


def test_most_ordered_items_with_data():
    mock_db = _make_mock_db()
    col = mock_db.get_collection("client_orders")
    col.insert_many([
        {"order_id": "1", "items": ["apple", "banana"], "total_price": 5.0},
        {"order_id": "2", "items": ["apple"], "total_price": 2.0},
    ])

    with patch("api.DB", return_value=mock_db):
        resp = client.get("/analytics/most-ordered-items?limit=5")
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert len(items) > 0
    # apple appears twice so should be first
    assert items[0]["item"] == "apple"
    assert items[0]["order_count"] == 2
