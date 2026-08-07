"""Tests pour le middleware de token API admin (Issue #19)."""

from __future__ import annotations

import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient


def test_auth_optional_when_unset(monkeypatch):
    """Test : sans HIRI_API_TOKEN, le middleware laisse tout passer."""
    monkeypatch.delenv("HIRI_API_TOKEN", raising=False)
    from hiri_bridge.auth import api_token

    assert api_token() == ""


def test_post_protected_when_token_set(monkeypatch):
    """Test : avec HIRI_API_TOKEN, les POST sans Bearer sont rejetes (401)."""
    monkeypatch.setenv("HIRI_API_TOKEN", "secret-test-token")
    import importlib

    import hiri_bridge.api as api_mod

    importlib.reload(api_mod)
    client = TestClient(api_mod.app)

    # GET /health toujours ouvert
    r = client.get("/health")
    assert r.status_code == 200

    # POST sans token -> 401
    r = client.post("/devices/seed")
    assert r.status_code == 401

    # POST avec token correct -> 200
    r = client.post("/devices/seed", headers={"Authorization": "Bearer secret-test-token"})
    assert r.status_code == 200

    # POST avec mauvais token -> 401
    r = client.post("/devices/seed", headers={"Authorization": "Bearer wrong-token"})
    assert r.status_code == 401

    monkeypatch.delenv("HIRI_API_TOKEN", raising=False)
    importlib.reload(api_mod)


def test_api_health_reports_auth_status(monkeypatch):
    """Test : /health indique auth_required quand le token est defini."""
    monkeypatch.setenv("HIRI_API_TOKEN", "test-key")
    import importlib

    import hiri_bridge.api as api_mod

    importlib.reload(api_mod)
    client = TestClient(api_mod.app)
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["auth_required"] is True
    monkeypatch.delenv("HIRI_API_TOKEN", raising=False)
    importlib.reload(api_mod)


def test_get_devices_always_open(monkeypatch):
    """Test : GET /devices reste accessible meme avec token."""
    monkeypatch.setenv("HIRI_API_TOKEN", "key")
    import importlib

    import hiri_bridge.api as api_mod

    importlib.reload(api_mod)
    client = TestClient(api_mod.app)
    r = client.get("/devices")
    assert r.status_code == 200
    monkeypatch.delenv("HIRI_API_TOKEN", raising=False)
    importlib.reload(api_mod)


def test_put_protected(monkeypatch):
    """Test : PUT sans token est protege."""
    monkeypatch.setenv("HIRI_API_TOKEN", "key")
    import importlib

    import hiri_bridge.api as api_mod

    importlib.reload(api_mod)
    client = TestClient(api_mod.app)
    r = client.put("/devices/test.id", json={"name": "test"})
    assert r.status_code == 401
    monkeypatch.delenv("HIRI_API_TOKEN", raising=False)
    importlib.reload(api_mod)
