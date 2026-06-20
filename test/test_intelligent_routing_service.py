from __future__ import annotations

import pytest

from services.intelligent_routing_service import (
    select_best_provider,
    select_fastest_provider,
    select_most_reliable_provider,
    select_provider,
)


def test_select_best_provider():
    provider = select_best_provider(
        scorecards=[
            {"provider_key": "A", "score": 50},
            {"provider_key": "B", "score": 90},
        ]
    )

    assert provider["provider_key"] == "B"


def test_select_fastest_provider():
    provider = select_fastest_provider(
        scorecards=[
            {"provider_key": "A", "avg_latency_ms": 500},
            {"provider_key": "B", "avg_latency_ms": 100},
        ]
    )

    assert provider["provider_key"] == "B"


def test_select_most_reliable_provider():
    provider = select_most_reliable_provider(
        scorecards=[
            {
                "provider_key": "A",
                "success_rate": 90,
                "failure_rate": 5,
                "retry_rate": 5,
            },
            {
                "provider_key": "B",
                "success_rate": 99,
                "failure_rate": 1,
                "retry_rate": 0,
            },
        ]
    )

    assert provider["provider_key"] == "B"


def test_select_provider_defaults_to_best():
    provider = select_provider(
        scorecards=[
            {"provider_key": "A", "score": 40},
            {"provider_key": "B", "score": 95},
        ]
    )

    assert provider["provider_key"] == "B"


def test_select_provider_fastest_strategy():
    provider = select_provider(
        scorecards=[
            {"provider_key": "A", "avg_latency_ms": 800},
            {"provider_key": "B", "avg_latency_ms": 200},
        ],
        strategy="fastest",
    )

    assert provider["provider_key"] == "B"


def test_select_provider_most_reliable_strategy():
    provider = select_provider(
        scorecards=[
            {
                "provider_key": "A",
                "success_rate": 91,
                "failure_rate": 4,
                "retry_rate": 5,
            },
            {
                "provider_key": "B",
                "success_rate": 98,
                "failure_rate": 1,
                "retry_rate": 1,
            },
        ],
        strategy="most_reliable",
    )

    assert provider["provider_key"] == "B"


def test_select_provider_empty():
    provider = select_provider(
        scorecards=[],
    )

    assert provider is None


def test_select_provider_invalid_strategy():
    with pytest.raises(ValueError) as error:
        select_provider(
            scorecards=[],
            strategy="unknown",
        )

    assert "Unsupported routing strategy" in str(error.value)

def test_select_fastest_provider_empty():
    provider = select_fastest_provider(
        scorecards=[],
    )

    assert provider is None


def test_select_most_reliable_provider_empty():
    provider = select_most_reliable_provider(
        scorecards=[],
    )

    assert provider is None