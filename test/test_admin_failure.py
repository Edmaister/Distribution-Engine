from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import apps.api.routers.admin_failure as mod


@pytest.fixture
def app():
    test_app = FastAPI()
    test_app.include_router(mod.router)
    return test_app


@pytest.fixture
def client(app):
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture(autouse=True)
def bypass_admin_auth(app):
    def allow_admin():
        return True

    app.dependency_overrides[mod.require_admin_key] = allow_admin
    yield
    app.dependency_overrides.clear()


def test_get_failures_defaults(client, monkeypatch):
    calls = {}

    async def fake_list_failures(status, failure_category, limit):
        calls["status"] = status
        calls["failure_category"] = failure_category
        calls["limit"] = limit
        return [{"id": 1}, {"id": 2}]

    monkeypatch.setattr(mod, "list_failures", fake_list_failures)

    res = client.get("/admin/failures")

    assert res.status_code == 200
    assert res.json() == {
        "count": 2,
        "items": [{"id": 1}, {"id": 2}],
    }
    assert calls == {
        "status": "OPEN",
        "failure_category": None,
        "limit": 100,
    }


def test_get_failures_normalizes_query_values(client, monkeypatch):
    calls = {}

    async def fake_list_failures(status, failure_category, limit):
        calls["status"] = status
        calls["failure_category"] = failure_category
        calls["limit"] = limit
        return []

    monkeypatch.setattr(mod, "list_failures", fake_list_failures)

    res = client.get(
        "/admin/failures",
        params={
            "status": " resolved ",
            "failureCategory": " technical ",
            "limit": 25,
        },
    )

    assert res.status_code == 200
    assert res.json() == {"count": 0, "items": []}
    assert calls == {
        "status": "RESOLVED",
        "failure_category": "TECHNICAL",
        "limit": 25,
    }


def test_get_failures_blank_status_and_category_become_none(client, monkeypatch):
    calls = {}

    async def fake_list_failures(status, failure_category, limit):
        calls["status"] = status
        calls["failure_category"] = failure_category
        calls["limit"] = limit
        return []

    monkeypatch.setattr(mod, "list_failures", fake_list_failures)

    res = client.get(
        "/admin/failures",
        params={
            "status": "   ",
            "failureCategory": "   ",
        },
    )

    assert res.status_code == 200
    assert calls["status"] is None
    assert calls["failure_category"] is None
    assert calls["limit"] == 100


def test_get_failures_limit_too_low_returns_422(client):
    res = client.get("/admin/failures?limit=0")
    assert res.status_code == 422


def test_get_failures_limit_too_high_returns_422(client):
    res = client.get("/admin/failures?limit=501")
    assert res.status_code == 422


def test_resolve_failure_success(client, monkeypatch):
    calls = {}

    async def fake_resolve_failure(failure_id, resolution_note):
        calls["failure_id"] = failure_id
        calls["resolution_note"] = resolution_note
        return True

    monkeypatch.setattr(mod, "resolve_failure", fake_resolve_failure)

    res = client.post(
        "/admin/failures/123/resolve",
        json={"resolutionNote": "Fixed manually"},
    )

    assert res.status_code == 200
    assert res.json() == {
        "status": "ok",
        "failureId": 123,
        "resolved": True,
    }
    assert calls == {
        "failure_id": 123,
        "resolution_note": "Fixed manually",
    }


def test_resolve_failure_allows_null_note(client, monkeypatch):
    calls = {}

    async def fake_resolve_failure(failure_id, resolution_note):
        calls["failure_id"] = failure_id
        calls["resolution_note"] = resolution_note
        return True

    monkeypatch.setattr(mod, "resolve_failure", fake_resolve_failure)

    res = client.post("/admin/failures/10/resolve", json={})

    assert res.status_code == 200
    assert calls == {
        "failure_id": 10,
        "resolution_note": None,
    }


def test_resolve_failure_not_found_returns_404(client, monkeypatch):
    async def fake_resolve_failure(failure_id, resolution_note):
        return False

    monkeypatch.setattr(mod, "resolve_failure", fake_resolve_failure)

    res = client.post(
        "/admin/failures/999/resolve",
        json={"resolutionNote": "Already done"},
    )

    assert res.status_code == 404
    assert res.json()["detail"] == "Failure not found or already resolved"


def test_resolve_failure_note_too_long_returns_422(client):
    res = client.post(
        "/admin/failures/1/resolve",
        json={"resolutionNote": "x" * 1001},
    )

    assert res.status_code == 422


def test_reprocess_failure_success(client, monkeypatch):
    async def fake_reprocess_failure(failure_id):
        return {
            "status": "ok",
            "failureId": failure_id,
            "reprocessed": True,
        }

    monkeypatch.setattr(mod, "reprocess_failure", fake_reprocess_failure)

    res = client.post("/admin/failures/77/reprocess")

    assert res.status_code == 200
    assert res.json() == {
        "status": "ok",
        "failureId": 77,
        "reprocessed": True,
    }


def test_reprocess_failure_value_error_returns_400(client, monkeypatch):
    async def fake_reprocess_failure(failure_id):
        raise ValueError("bad state")

    monkeypatch.setattr(mod, "reprocess_failure", fake_reprocess_failure)

    res = client.post("/admin/failures/77/reprocess")

    assert res.status_code == 400
    assert res.json()["detail"] == "Invalid request"


def test_get_failures_summary(client, monkeypatch):
    async def fake_get_failure_summary():
        return {
            "open": 2,
            "resolved": 3,
        }

    monkeypatch.setattr(
        mod,
        "get_failure_summary",
        fake_get_failure_summary,
    )

    res = client.get("/admin/failures/summary")

    assert res.status_code == 200
    assert res.json() == {
        "open": 2,
        "resolved": 3,
    }
