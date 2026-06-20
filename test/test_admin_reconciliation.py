from fastapi.testclient import TestClient

from apps.api.main import app
import apps.api.routers.admin_reconciliation as mod

client = TestClient(app)
ADMIN_HEADERS = {"x-api-key": "test-admin-key"}


def test_get_runs(monkeypatch):
    async def fake_list_reconciliation_runs(**kwargs):
        return [
            {
                "run_id": "run-123",
                "provider_key": "CASH_PROVIDER",
            }
        ]

    monkeypatch.setattr(
        mod,
        "list_reconciliation_runs",
        fake_list_reconciliation_runs,
    )

    response = client.get(
        "/admin/reconciliation/runs",
        headers=ADMIN_HEADERS,
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["status"] == "ok"
    assert payload["count"] == 1


def test_get_run(monkeypatch):
    async def fake_get_reconciliation_run(**kwargs):
        return {
            "run_id": "run-123",
        }

    monkeypatch.setattr(
        mod,
        "get_reconciliation_run",
        fake_get_reconciliation_run,
    )

    response = client.get(
        "/admin/reconciliation/runs/run-123",
        headers=ADMIN_HEADERS,
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["item"]["run_id"] == "run-123"


def test_get_run_results(monkeypatch):
    async def fake_get_reconciliation_results(**kwargs):
        return [
            {
                "result_id": "result-123",
                "status": "MATCHED",
            }
        ]

    monkeypatch.setattr(
        mod,
        "get_reconciliation_results",
        fake_get_reconciliation_results,
    )

    response = client.get(
        "/admin/reconciliation/runs/run-123/results",
        headers=ADMIN_HEADERS,
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["count"] == 1
