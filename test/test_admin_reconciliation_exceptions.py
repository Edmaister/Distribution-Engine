from fastapi.testclient import TestClient

from apps.api.main import app
import apps.api.routers.admin_reconciliation_exceptions as mod


client = TestClient(app)
ADMIN_HEADERS = {"x-api-key": "test-admin-key"}


def test_get_exceptions(monkeypatch):
    async def fake_list_exceptions(**kwargs):
        return [
            {
                "exception_id": "exception-123",
                "status": "OPEN",
            }
        ]

    monkeypatch.setattr(
        mod,
        "list_exceptions",
        fake_list_exceptions,
    )

    response = client.get(
        "/admin/reconciliation/exceptions",
        headers=ADMIN_HEADERS,
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["status"] == "ok"
    assert payload["count"] == 1


def test_get_exception(monkeypatch):
    async def fake_get_exception(**kwargs):
        return {
            "exception_id": "exception-123",
            "status": "OPEN",
        }

    monkeypatch.setattr(
        mod,
        "get_exception",
        fake_get_exception,
    )

    response = client.get(
        "/admin/reconciliation/exceptions/exception-123",
        headers=ADMIN_HEADERS,
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["item"]["exception_id"] == "exception-123"


def test_assign_exception(monkeypatch):
    async def fake_assign_exception(**kwargs):
        return {
            "exception_id": "exception-123",
            "status": "ASSIGNED",
            "assigned_to": "finance.user",
        }

    monkeypatch.setattr(
        mod,
        "assign_exception",
        fake_assign_exception,
    )

    response = client.post(
        "/admin/reconciliation/exceptions/exception-123/assign",
        headers=ADMIN_HEADERS,
        json={
            "assigned_to": "finance.user"
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["item"]["status"] == "ASSIGNED"


def test_resolve_exception(monkeypatch):
    async def fake_resolve_exception(**kwargs):
        return {
            "exception_id": "exception-123",
            "status": "RESOLVED",
        }

    monkeypatch.setattr(
        mod,
        "resolve_exception",
        fake_resolve_exception,
    )

    response = client.post(
        "/admin/reconciliation/exceptions/exception-123/resolve",
        headers=ADMIN_HEADERS,
        json={
            "resolution_notes": "Resolved"
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["item"]["status"] == "RESOLVED"


def test_reopen_exception(monkeypatch):
    async def fake_reopen_exception(**kwargs):
        return {
            "exception_id": "exception-123",
            "status": "REOPENED",
        }

    monkeypatch.setattr(
        mod,
        "reopen_exception",
        fake_reopen_exception,
    )

    response = client.post(
        "/admin/reconciliation/exceptions/exception-123/reopen",
        headers=ADMIN_HEADERS,
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["item"]["status"] == "REOPENED"


def test_get_exception_not_found(monkeypatch):
    async def fake_get_exception(**kwargs):
        return None

    monkeypatch.setattr(
        mod,
        "get_exception",
        fake_get_exception,
    )

    response = client.get(
        "/admin/reconciliation/exceptions/missing",
        headers=ADMIN_HEADERS,
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["status"] == "not_found"
