from __future__ import annotations

import pytest

from services.provider_routing_engine import (
    resolve_best_provider,
    resolve_fastest_provider,
    resolve_most_reliable_provider,
    resolve_provider,
)


@pytest.mark.asyncio
async def test_resolve_provider_best(monkeypatch):
    async def fake_metrics(*, limit: int = 100):
        return [
            {
                "provider_key": "A",
                "success_count": 5,
                "failure_count": 5,
                "retry_count": 0,
                "total_latency_ms": 5000,
            },
            {
                "provider_key": "B",
                "success_count": 10,
                "failure_count": 0,
                "retry_count": 0,
                "total_latency_ms": 1000,
            },
        ]

    monkeypatch.setattr(
        "services.provider_routing_engine.list_provider_sla_metrics",
        fake_metrics,
    )

    provider = await resolve_provider()

    assert provider is not None
    assert provider["provider_key"] == "B"


@pytest.mark.asyncio
async def test_resolve_provider_fastest(monkeypatch):
    async def fake_metrics(*, limit: int = 100):
        return [
            {
                "provider_key": "A",
                "success_count": 10,
                "failure_count": 0,
                "retry_count": 0,
                "total_latency_ms": 6000,
            },
            {
                "provider_key": "B",
                "success_count": 10,
                "failure_count": 0,
                "retry_count": 0,
                "total_latency_ms": 1000,
            },
        ]

    monkeypatch.setattr(
        "services.provider_routing_engine.list_provider_sla_metrics",
        fake_metrics,
    )

    provider = await resolve_provider(
        strategy="fastest",
    )

    assert provider["provider_key"] == "B"


@pytest.mark.asyncio
async def test_resolve_provider_reliable(monkeypatch):
    async def fake_metrics(*, limit: int = 100):
        return [
            {
                "provider_key": "A",
                "success_count": 90,
                "failure_count": 10,
                "retry_count": 5,
                "total_latency_ms": 1000,
            },
            {
                "provider_key": "B",
                "success_count": 99,
                "failure_count": 1,
                "retry_count": 0,
                "total_latency_ms": 3000,
            },
        ]

    monkeypatch.setattr(
        "services.provider_routing_engine.list_provider_sla_metrics",
        fake_metrics,
    )

    provider = await resolve_provider(
        strategy="most_reliable",
    )

    assert provider["provider_key"] == "B"


@pytest.mark.asyncio
async def test_resolve_provider_empty(monkeypatch):
    async def fake_metrics(*, limit: int = 100):
        return []

    monkeypatch.setattr(
        "services.provider_routing_engine.list_provider_sla_metrics",
        fake_metrics,
    )

    provider = await resolve_provider()

    assert provider is None


@pytest.mark.asyncio
async def test_resolve_best_provider(monkeypatch):
    async def fake_metrics(*, limit: int = 100):
        return [
            {
                "provider_key": "BEST",
                "success_count": 100,
                "failure_count": 0,
                "retry_count": 0,
                "total_latency_ms": 1000,
            }
        ]

    monkeypatch.setattr(
        "services.provider_routing_engine.list_provider_sla_metrics",
        fake_metrics,
    )

    provider = await resolve_best_provider()

    assert provider["provider_key"] == "BEST"


@pytest.mark.asyncio
async def test_resolve_fastest_provider(monkeypatch):
    async def fake_metrics(*, limit: int = 100):
        return [
            {
                "provider_key": "FAST",
                "success_count": 100,
                "failure_count": 0,
                "retry_count": 0,
                "total_latency_ms": 100,
            }
        ]

    monkeypatch.setattr(
        "services.provider_routing_engine.list_provider_sla_metrics",
        fake_metrics,
    )

    provider = await resolve_fastest_provider()

    assert provider["provider_key"] == "FAST"


@pytest.mark.asyncio
async def test_resolve_most_reliable_provider(monkeypatch):
    async def fake_metrics(*, limit: int = 100):
        return [
            {
                "provider_key": "RELIABLE",
                "success_count": 100,
                "failure_count": 0,
                "retry_count": 0,
                "total_latency_ms": 5000,
            }
        ]

    monkeypatch.setattr(
        "services.provider_routing_engine.list_provider_sla_metrics",
        fake_metrics,
    )

    provider = await resolve_most_reliable_provider()

    assert provider["provider_key"] == "RELIABLE"