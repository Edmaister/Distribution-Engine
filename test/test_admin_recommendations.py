from __future__ import annotations

from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import apps.api.routers.admin_recommendations as mod


@pytest.fixture
def app():
    test_app = FastAPI()
    test_app.include_router(mod.router)
    test_app.dependency_overrides[mod.require_admin_key] = lambda: True
    return test_app


@pytest.fixture
def client(app):
    return TestClient(app, raise_server_exceptions=False)


class FakeAsyncConnection:
    def __init__(self, fetchrow_value=None, should_raise=False):
        self.fetchrow_value = fetchrow_value
        self.should_raise = should_raise
        self.calls = []

    async def fetchrow(self, query, *params):
        if self.should_raise:
            raise RuntimeError("db failed")

        self.calls.append((query, params))
        return self.fetchrow_value


class FakeAsyncConnectionContext:
    def __init__(self, conn):
        self.conn = conn

    async def __aenter__(self):
        if self.conn.should_raise:
            raise RuntimeError("db failed")
        return self.conn

    async def __aexit__(self, exc_type, exc, tb):
        return False


def patch_async_db(monkeypatch, conn):
    monkeypatch.setattr(
        mod,
        "get_async_connection",
        lambda: FakeAsyncConnectionContext(conn),
    )


def test_correlation_id_known():
    request = SimpleNamespace(state=SimpleNamespace(correlation_id="abc-123"))
    assert mod._correlation_id(request) == "abc-123"


def test_correlation_id_unknown():
    request = SimpleNamespace(state=SimpleNamespace())
    assert mod._correlation_id(request) == "unknown"


def test_error_response_contains_standard_shape():
    request = SimpleNamespace(state=SimpleNamespace(correlation_id="cid-1"))

    response = mod._error(
        request=request,
        status_code=500,
        error_code="INTERNAL_ERROR",
        message="Something broke",
    )

    assert response.status_code == 500
    assert response.headers["x-request-id"] == "cid-1"


def test_campaign_insights_cache_hit(client, monkeypatch):
    conn = FakeAsyncConnection(
        fetchrow_value={
            "metrics": {"sales": 10},
            "generated_at": "2026-05-04T10:00:00Z",
            "ttl_seconds": 60,
        }
    )
    patch_async_db(monkeypatch, conn)

    res = client.get("/admin/recommendations/campaigns/CAMP001")

    assert res.status_code == 200
    assert res.json() == {
        "campaignCode": "CAMP001",
        "tenantCode": None,
        "metrics": {"sales": 10},
        "cachedAt": "2026-05-04T10:00:00Z",
        "ttlSeconds": 60,
        "source": "cache",
    }

    query, params = conn.calls[0]
    assert "FROM campaign_insights_cache" in query
    assert params == ("CAMP001",)


def test_campaign_insights_cache_hit_ttl_none_becomes_zero(client, monkeypatch):
    conn = FakeAsyncConnection(
        fetchrow_value={
            "metrics": {"sales": 1},
            "generated_at": "cached-date",
            "ttl_seconds": None,
        }
    )
    patch_async_db(monkeypatch, conn)

    res = client.get("/admin/recommendations/campaigns/CAMP002")

    assert res.status_code == 200
    assert res.json()["ttlSeconds"] == 0
    assert res.json()["source"] == "cache"


def test_campaign_insights_cache_miss_uses_live_compute(client, monkeypatch):
    calls = {}

    conn = FakeAsyncConnection(fetchrow_value=None)
    patch_async_db(monkeypatch, conn)

    async def fake_compute_campaign_insights(campaign_code, sticker=None, tenant=None):
        calls["campaign_code"] = campaign_code
        calls["sticker"] = sticker
        calls["tenant"] = tenant
        return {"metrics": {"score": 99}}

    monkeypatch.setattr(
        mod,
        "compute_campaign_insights",
        fake_compute_campaign_insights,
    )

    res = client.get(
        "/admin/recommendations/campaigns/CAMP003",
        params={"sticker": "QR1"},
    )

    assert res.status_code == 200
    assert res.json() == {
        "campaignCode": "CAMP003",
        "tenantCode": None,
        "metrics": {"score": 99},
        "source": "live",
    }

    assert conn.calls[0][1] == ("CAMP003",)
    assert calls["campaign_code"] == "CAMP003"
    assert calls["sticker"] == "QR1"
    assert calls["tenant"] is None


def test_campaign_insights_prefer_cache_false_skips_db(client, monkeypatch):
    def fail_if_called():
        raise AssertionError("get_async_connection should not be called")

    monkeypatch.setattr(mod, "get_async_connection", fail_if_called)

    async def fake_compute_campaign_insights(campaign_code, sticker=None, tenant=None):
        return {"metrics": {"live": True}}

    monkeypatch.setattr(
        mod,
        "compute_campaign_insights",
        fake_compute_campaign_insights,
    )

    res = client.get(
        "/admin/recommendations/campaigns/CAMP004",
        params={"prefer_cache": "false"},
    )

    assert res.status_code == 200
    assert res.json()["source"] == "live"
    assert res.json()["metrics"] == {"live": True}


def test_campaign_insights_validates_tenant(client, monkeypatch):
    calls = {}

    conn = FakeAsyncConnection(fetchrow_value=None)
    patch_async_db(monkeypatch, conn)

    def fake_require_valid_tenant(tenant_code):
        calls["tenant_input"] = tenant_code
        return "FNB"

    async def fake_compute_campaign_insights(campaign_code, sticker=None, tenant=None):
        calls["tenant_output"] = tenant
        return {"metrics": {"ok": True}}

    monkeypatch.setattr(mod, "require_valid_tenant", fake_require_valid_tenant)
    monkeypatch.setattr(
        mod,
        "compute_campaign_insights",
        fake_compute_campaign_insights,
    )

    res = client.get(
        "/admin/recommendations/campaigns/CAMP005",
        params={"tenant_code": " fnb "},
    )

    assert res.status_code == 200
    assert res.json()["tenantCode"] == "FNB"
    assert calls["tenant_input"] == " fnb "
    assert calls["tenant_output"] == "FNB"


def test_campaign_insights_cache_error_returns_500(client, monkeypatch):
    conn = FakeAsyncConnection(should_raise=True)
    patch_async_db(monkeypatch, conn)

    res = client.get(
        "/admin/recommendations/campaigns/CAMP006",
        headers={"X-Request-ID": "cid-cache-error"},
    )

    assert res.status_code == 500
    assert res.json()["detail"]["error_code"] == "INTERNAL_ERROR"
    assert res.json()["detail"]["message"] == "An unexpected error occurred"


def test_campaign_insights_live_compute_error_returns_500(client, monkeypatch):
    conn = FakeAsyncConnection(fetchrow_value=None)
    patch_async_db(monkeypatch, conn)

    async def broken_compute(*args, **kwargs):
        raise RuntimeError("compute failed")

    monkeypatch.setattr(mod, "compute_campaign_insights", broken_compute)

    res = client.get(
        "/admin/recommendations/campaigns/CAMP007",
        headers={"X-Request-ID": "cid-live-error"},
    )

    assert res.status_code == 500
    assert res.json()["detail"]["error_code"] == "INTERNAL_ERROR"
    assert res.json()["detail"]["message"] == "An unexpected error occurred"