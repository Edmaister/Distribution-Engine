from fastapi.testclient import TestClient

from apps.api.main import app
import apps.api.routers.admin_settlement as settlement_router


client = TestClient(app)
ADMIN_HEADERS = {"x-api-key": "test-admin-key"}


def test_get_settlements(monkeypatch):
    async def fake_list_settlements(**kwargs):
        return [
            {
                "settlement_id": "settlement-123",
                "status": "PENDING",
                "amount": 100.0,
            }
        ]

    monkeypatch.setattr(
        settlement_router,
        "list_settlements",
        fake_list_settlements,
    )

    response = client.get(
        "/admin/settlements",
        headers=ADMIN_HEADERS,
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["status"] == "ok"
    assert payload["count"] == 1
    assert payload["items"][0]["settlement_id"] == "settlement-123"


def test_get_settlement_by_id(monkeypatch):
    async def fake_get_settlement_by_id(**kwargs):
        return {
            "settlement_id": "settlement-123",
            "status": "PENDING",
        }

    monkeypatch.setattr(
        settlement_router,
        "get_settlement_by_id",
        fake_get_settlement_by_id,
    )

    response = client.get(
        "/admin/settlements/settlement-123",
        headers=ADMIN_HEADERS,
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["status"] == "ok"
    assert payload["item"]["settlement_id"] == "settlement-123"


def test_get_settlement_not_found(monkeypatch):
    async def fake_get_settlement_by_id(**kwargs):
        return None

    monkeypatch.setattr(
        settlement_router,
        "get_settlement_by_id",
        fake_get_settlement_by_id,
    )

    response = client.get(
        "/admin/settlements/does-not-exist",
        headers=ADMIN_HEADERS,
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["status"] == "not_found"


def test_get_exposure(monkeypatch):
    async def fake_get_provider_exposure(**kwargs):
        return [
            {
                "provider_key": "CASH_PROVIDER",
                "exposure_amount": 5000,
            }
        ]

    monkeypatch.setattr(
        settlement_router,
        "get_provider_exposure",
        fake_get_provider_exposure,
    )

    response = client.get(
        "/admin/settlements/exposure",
        headers=ADMIN_HEADERS,
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["status"] == "ok"
    assert payload["count"] == 1
    assert payload["items"][0]["provider_key"] == "CASH_PROVIDER"


def test_get_settlements_requires_admin_key():
    response = client.get("/admin/settlements")

    assert response.status_code == 401
