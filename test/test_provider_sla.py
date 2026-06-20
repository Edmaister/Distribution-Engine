from __future__ import annotations

import pytest
from httpx import AsyncClient

from apps.api.main import app


ADMIN_HEADERS = {"x-api-key": "test-admin-key"}


@pytest.mark.asyncio
async def test_list_provider_sla_metrics(monkeypatch):
    async def fake_list_provider_sla_metrics(*, limit: int = 100):
        return [
            {
                "provider_key": "CASH_PROVIDER",
                "success_count": 10,
                "failure_count": 1,
                "retry_count": 2,
                "total_latency_ms": 1100,
            }
        ]

    monkeypatch.setattr(
        "apps.api.routers.provider_sla.list_provider_sla_metrics",
        fake_list_provider_sla_metrics,
    )

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(
            "/admin/providers/sla",
            headers=ADMIN_HEADERS,
        )

    assert response.status_code == 200

    body = response.json()

    assert body["status"] == "ok"
    assert body["count"] == 1
    assert body["items"][0]["provider_key"] == "CASH_PROVIDER"


@pytest.mark.asyncio
async def test_list_provider_scorecards(monkeypatch):
    async def fake_list_provider_sla_metrics(*, limit: int = 100):
        return [
            {
                "provider_key": "CASH_PROVIDER",
                "success_count": 10,
                "failure_count": 0,
                "retry_count": 1,
                "total_latency_ms": 1000,
            },
            {
                "provider_key": "EBUCKS_PROVIDER",
                "success_count": 5,
                "failure_count": 5,
                "retry_count": 2,
                "total_latency_ms": 3000,
            },
        ]

    monkeypatch.setattr(
        "apps.api.routers.provider_sla.list_provider_sla_metrics",
        fake_list_provider_sla_metrics,
    )

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(
            "/admin/providers/scorecards",
            headers=ADMIN_HEADERS,
        )

    assert response.status_code == 200

    body = response.json()

    assert body["status"] == "ok"
    assert body["count"] == 2
    assert body["items"][0]["provider_key"] == "CASH_PROVIDER"
    assert "score" in body["items"][0]
    assert "success_rate" in body["items"][0]
    assert "avg_latency_ms" in body["items"][0]


@pytest.mark.asyncio
async def test_get_provider_sla(monkeypatch):
    async def fake_get_provider_sla_metrics(*, provider_key: str):
        return {
            "provider_key": provider_key,
            "success_count": 10,
            "failure_count": 1,
            "retry_count": 2,
            "total_latency_ms": 1100,
        }

    monkeypatch.setattr(
        "apps.api.routers.provider_sla.get_provider_sla_metrics",
        fake_get_provider_sla_metrics,
    )

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(
            "/admin/providers/CASH_PROVIDER/sla",
            headers=ADMIN_HEADERS,
        )

    assert response.status_code == 200

    body = response.json()

    assert body["status"] == "ok"
    assert body["item"]["provider_key"] == "CASH_PROVIDER"


@pytest.mark.asyncio
async def test_get_provider_sla_not_found(monkeypatch):
    async def fake_get_provider_sla_metrics(*, provider_key: str):
        return None

    monkeypatch.setattr(
        "apps.api.routers.provider_sla.get_provider_sla_metrics",
        fake_get_provider_sla_metrics,
    )

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(
            "/admin/providers/UNKNOWN/sla",
            headers=ADMIN_HEADERS,
        )

    assert response.status_code == 404

    body = response.json()

    assert body["detail"] == "Provider 'UNKNOWN' not found"


@pytest.mark.asyncio
async def test_get_provider_scorecard(monkeypatch):
    async def fake_get_provider_sla_metrics(*, provider_key: str):
        return {
            "provider_key": provider_key,
            "success_count": 10,
            "failure_count": 0,
            "retry_count": 1,
            "total_latency_ms": 1000,
        }

    monkeypatch.setattr(
        "apps.api.routers.provider_sla.get_provider_sla_metrics",
        fake_get_provider_sla_metrics,
    )

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(
            "/admin/providers/CASH_PROVIDER/scorecard",
            headers=ADMIN_HEADERS,
        )

    assert response.status_code == 200

    body = response.json()

    assert body["status"] == "ok"
    assert body["item"]["provider_key"] == "CASH_PROVIDER"
    assert body["item"]["success_rate"] == 100.0
    assert body["item"]["failure_rate"] == 0.0
    assert body["item"]["retry_rate"] == 10.0
    assert body["item"]["total_attempts"] == 10
    assert "score" in body["item"]


@pytest.mark.asyncio
async def test_get_provider_scorecard_not_found(monkeypatch):
    async def fake_get_provider_sla_metrics(*, provider_key: str):
        return None

    monkeypatch.setattr(
        "apps.api.routers.provider_sla.get_provider_sla_metrics",
        fake_get_provider_sla_metrics,
    )

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(
            "/admin/providers/UNKNOWN/scorecard",
            headers=ADMIN_HEADERS,
        )

    assert response.status_code == 404

    body = response.json()

    assert body["detail"] == "Provider 'UNKNOWN' not found"
