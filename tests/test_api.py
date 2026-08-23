"""Tests for backend/api.py — the read-only FastAPI JSON API.

Uses FastAPI's TestClient against a temp database. No live market key is set,
so the market source is the simulator.
"""

from fastapi.testclient import TestClient

from backend.api import app

client = TestClient(app)


def test_list_traders(temp_db):
    resp = client.get("/api/traders")
    assert resp.status_code == 200
    traders = resp.json()
    assert len(traders) == 4
    assert all({"name", "lastname", "model_name"} <= set(t) for t in traders)


def test_market_uses_simulator_without_key(temp_db):
    resp = client.get("/api/market")
    assert resp.status_code == 200
    body = resp.json()
    assert body["source"] == "simulator"
    assert body["is_market_open"] is True


def test_get_known_trader(temp_db):
    name = client.get("/api/traders").json()[0]["name"]
    resp = client.get(f"/api/traders/{name}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["name"] == name
    assert body["balance"] == 10000.0
    assert body["holdings"] == []
    assert body["transactions"] == []


def test_unknown_trader_returns_404(temp_db):
    resp = client.get("/api/traders/NotARealTrader")
    assert resp.status_code == 404


def test_trader_logs_shape(temp_db):
    name = client.get("/api/traders").json()[0]["name"]
    resp = client.get(f"/api/traders/{name}/logs?last_n=5")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
