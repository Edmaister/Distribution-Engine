from fastapi.testclient import TestClient

import apps.api.routers.admin_verticals as verticals_router
from apps.api.main import app


client = TestClient(app)
ADMIN_HEADERS = {"x-api-key": "test-admin-key"}


def test_get_admin_vertical_readiness(monkeypatch):
    def fake_get_vertical_readiness():
        return {
            "vertical_count": 2,
            "configured_count": 2,
            "agnostic_ready": True,
            "items": [
                {
                    "vertical_code": "INSURANCE",
                    "status": "CONFIGURED",
                    "journey_code": "INSURANCE_POLICY",
                }
            ],
        }

    monkeypatch.setattr(
        verticals_router,
        "get_vertical_readiness",
        fake_get_vertical_readiness,
    )

    async def fake_get_insurance_journey_proof():
        return {
            "status": "READY",
            "ready": True,
            "steps": [],
        }

    monkeypatch.setattr(
        verticals_router,
        "get_insurance_journey_proof",
        fake_get_insurance_journey_proof,
    )

    response = client.get(
        "/admin/verticals/readiness",
        headers=ADMIN_HEADERS,
    )

    assert response.status_code == 200
    payload = response.json()

    assert payload["status"] == "ok"
    assert payload["readiness"]["agnostic_ready"] is True
    assert payload["readiness"]["items"][0]["vertical_code"] == "INSURANCE"
    assert payload["proof"]["insurance"]["status"] == "READY"


def test_get_admin_vertical_readiness_requires_admin_key():
    response = client.get("/admin/verticals/readiness")

    assert response.status_code == 401


def test_get_admin_insurance_journey_proof(monkeypatch):
    async def fake_get_insurance_journey_proof():
        return {
            "status": "READY",
            "ready": True,
            "campaign_code": "INS-FUNERAL-2026",
            "steps": [
                {
                    "surface": "Producer - Supply",
                    "status": "READY",
                }
            ],
        }

    monkeypatch.setattr(
        verticals_router,
        "get_insurance_journey_proof",
        fake_get_insurance_journey_proof,
    )

    response = client.get(
        "/admin/verticals/proof/insurance",
        headers=ADMIN_HEADERS,
    )

    assert response.status_code == 200
    payload = response.json()

    assert payload["status"] == "ok"
    assert payload["proof"]["status"] == "READY"
    assert payload["proof"]["campaign_code"] == "INS-FUNERAL-2026"
