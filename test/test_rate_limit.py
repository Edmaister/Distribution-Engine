from __future__ import annotations

from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient

import apps.api.middleware.rate_limit as rl


class FakeRedis:
    def __init__(self):
        self.values = {}
        self.expiries = {}

    def incr(self, key: str):
        self.values[key] = self.values.get(key, 0) + 1
        return self.values[key]

    def expire(self, key: str, seconds: int):
        self.expiries[key] = seconds


def _client(monkeypatch, fake_redis=None):
    app = FastAPI()
    app.add_middleware(rl.RateLimitMiddleware)

    @app.get("/test")
    def test_endpoint():
        return {"ok": True}

    @app.get("/readyz")
    def readyz():
        return {"status": "ok"}

    monkeypatch.setattr(rl, "get_cache", lambda: fake_redis)

    return TestClient(app)


def test_rate_limit_allows_request_when_under_limit(monkeypatch):
    fake_redis = FakeRedis()
    client = _client(monkeypatch, fake_redis)

    monkeypatch.setattr(rl, "_resolve_tenant_from_key", lambda api_key: "FNB")
    monkeypatch.setattr(rl, "_rate_limit_for_tenant", lambda tenant: 2)

    response = client.get("/test", headers={"x-api-key": "dev-fnb-key-123"})

    assert response.status_code == 200
    assert response.json() == {"ok": True}
    assert response.headers["X-RateLimit-Limit"] == "2"
    assert response.headers["X-RateLimit-Remaining"] == "1"


def test_rate_limit_blocks_when_limit_exceeded(monkeypatch):
    fake_redis = FakeRedis()
    client = _client(monkeypatch, fake_redis)

    monkeypatch.setattr(rl, "_resolve_tenant_from_key", lambda api_key: "FNB")
    monkeypatch.setattr(rl, "_rate_limit_for_tenant", lambda tenant: 1)

    first = client.get("/test", headers={"x-api-key": "dev-fnb-key-123"})
    second = client.get("/test", headers={"x-api-key": "dev-fnb-key-123"})

    assert first.status_code == 200
    assert second.status_code == 429
    payload = second.json()
    assert payload["detail"] == "Rate limit exceeded"
    assert payload["tenant"] == "FNB"
    assert payload["client"].startswith("api-key:")
    assert "dev-fnb-key-123" not in payload["client"]
    assert payload["limitPerMinute"] == 1
    assert second.headers["Retry-After"] == "60"
    assert second.headers["X-RateLimit-Limit"] == "1"
    assert second.headers["X-RateLimit-Remaining"] == "0"


def test_rate_limit_skips_health_ready_and_metrics(monkeypatch):
    fake_redis = FakeRedis()
    client = _client(monkeypatch, fake_redis)

    response = client.get("/readyz")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert fake_redis.values == {}


def test_rate_limit_fails_open_when_redis_unavailable(monkeypatch):
    client = _client(monkeypatch, fake_redis=None)

    response = client.get("/test", headers={"x-api-key": "dev-fnb-key-123"})

    assert response.status_code == 200
    assert response.json() == {"ok": True}


def test_rate_limit_fails_open_when_redis_errors(monkeypatch):
    class BrokenRedis:
        def incr(self, key: str):
            raise RuntimeError("redis unavailable")

    client = _client(monkeypatch, BrokenRedis())

    response = client.get("/test", headers={"x-api-key": "dev-fnb-key-123"})

    assert response.status_code == 200
    assert response.json() == {"ok": True}


def test_resolve_tenant_from_missing_key():
    assert rl._resolve_tenant_from_key(None) == "anonymous"


def test_resolve_admin_tenant(monkeypatch):
    class Settings:
        admin_api_key = "admin-key"
        fnb_partner_api_key = None
        fnb_tenant_user_api_key = None
        fnb_tenant_admin_api_key = None
        pnp_partner_api_key = None
        pnp_tenant_user_api_key = None
        pnp_tenant_admin_api_key = None

    monkeypatch.setattr(rl, "get_settings", lambda: Settings())

    assert rl._resolve_tenant_from_key("admin-key") == "admin"


def test_resolve_fnb_tenant(monkeypatch):
    class Settings:
        admin_api_key = None
        fnb_partner_api_key = "fnb-key"
        fnb_tenant_user_api_key = "fnb-user-key"
        fnb_tenant_admin_api_key = "fnb-admin-key"
        pnp_partner_api_key = None
        pnp_tenant_user_api_key = None
        pnp_tenant_admin_api_key = None

    monkeypatch.setattr(rl, "get_settings", lambda: Settings())

    assert rl._resolve_tenant_from_key("fnb-user-key") == "FNB"


def test_resolve_pnp_tenant(monkeypatch):
    class Settings:
        admin_api_key = None
        fnb_partner_api_key = None
        fnb_tenant_user_api_key = None
        fnb_tenant_admin_api_key = None
        pnp_partner_api_key = "pnp-key"
        pnp_tenant_user_api_key = "pnp-user-key"
        pnp_tenant_admin_api_key = "pnp-admin-key"

    monkeypatch.setattr(rl, "get_settings", lambda: Settings())

    assert rl._resolve_tenant_from_key("pnp-admin-key") == "PNP"


def test_resolve_unknown_key_is_hashed():
    tenant = rl._resolve_tenant_from_key("some-random-key")

    assert tenant.startswith("unknown:")
    assert "some-random-key" not in tenant


def test_rate_limit_keys_include_client_subject(monkeypatch):
    fake_redis = FakeRedis()
    client = _client(monkeypatch, fake_redis)

    monkeypatch.setattr(rl, "_resolve_tenant_from_key", lambda api_key: "FNB")
    monkeypatch.setattr(rl, "_rate_limit_for_tenant", lambda tenant: 1)

    first = client.get("/test", headers={"x-api-key": "client-one"})
    second = client.get("/test", headers={"x-api-key": "client-two"})

    assert first.status_code == 200
    assert second.status_code == 200
    assert len(fake_redis.values) == 2
    assert all(key.startswith("rate-limit:FNB:api-key:") for key in fake_redis.values)


def test_resolve_client_from_bearer_token_is_hashed(monkeypatch):
    request = SimpleNamespace(
        headers={"authorization": "Bearer partner-token-1"},
        client=SimpleNamespace(host="127.0.0.1"),
    )

    subject = rl._resolve_client_from_request(request)

    assert subject.startswith("bearer:")
    assert "partner-token-1" not in subject


def test_admin_rate_limit_is_higher():
    assert rl._rate_limit_for_tenant("admin") == rl.ADMIN_RATE_LIMIT_PER_MINUTE


def test_default_rate_limit_for_tenant():
    assert rl._rate_limit_for_tenant("FNB") == rl.DEFAULT_RATE_LIMIT_PER_MINUTE
