from __future__ import annotations

import pytest
from httpx import AsyncClient

from apps.api.main import app


ADMIN_HEADERS = {"x-api-key": "test-admin-key"}


@pytest.mark.asyncio
async def test_get_provider_rankings(monkeypatch):
    async def fake_list_provider_sla_metrics(*, limit: int = 100):
        return [
            {
                "provider_key": "A",
                "success_count": 10,
                "failure_count": 0,
                "retry_count": 0,
                "total_latency_ms": 1000,
            },
            {
                "provider_key": "B",
                "success_count": 5,
                "failure_count": 5,
                "retry_count": 2,
                "total_latency_ms": 5000,
            },
        ]

    monkeypatch.setattr(
        "apps.api.routers.provider_sla.list_provider_sla_metrics",
        fake_list_provider_sla_metrics,
    )

    async with AsyncClient(
        app=app,
        base_url="http://test",
    ) as client:
        response = await client.get(
            "/admin/providers/rankings",
            headers=ADMIN_HEADERS,
        )

    assert response.status_code == 200

    body = response.json()

    assert body["status"] == "ok"
    assert body["count"] == 2

    assert body["best_provider"] is not None
    assert body["worst_provider"] is not None
    assert body["fastest_provider"] is not None
    assert body["most_reliable_provider"] is not None

    assert body["best_provider"]["provider_key"] == "A"
