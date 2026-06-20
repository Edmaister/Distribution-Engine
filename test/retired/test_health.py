from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

import apps.api.routers.health as mod


def make_client():
    app = FastAPI()
    app.include_router(mod.router)
    return TestClient(app, raise_server_exceptions=False)


def test_healthz_returns_ok():
    client = make_client()

    res = client.get("/healthz")

    assert res.status_code == 200
    assert res.json() == {"status": "ok"}


def test_readyz_success(monkeypatch):
    client = make_client()

    class DummyCursor:
        def execute(self, query):
            assert query == "SELECT 1"

        def fetchone(self):
            return (1,)

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    monkeypatch.setattr(mod, "db_cursor", lambda: DummyCursor())

    res = client.get("/readyz")

    assert res.status_code == 200
    assert res.json() == {"status": "ready"}


def test_readyz_failure(monkeypatch):
    client = make_client()

    def broken_db_cursor():
        raise RuntimeError("db down")

    monkeypatch.setattr(mod, "db_cursor", broken_db_cursor)

    res = client.get("/readyz")

    assert res.status_code == 200
    assert res.json() == {"status": "not_ready"}