from services.provider_ranking_service import (
    get_best_provider,
    get_worst_provider,
    get_fastest_provider,
    get_most_reliable_provider,
    rank_providers,
)


def test_get_best_provider():
    result = get_best_provider(
        scorecards=[
            {"provider_key": "A", "score": 50},
            {"provider_key": "B", "score": 90},
        ]
    )

    assert result["provider_key"] == "B"


def test_get_worst_provider():
    result = get_worst_provider(
        scorecards=[
            {"provider_key": "A", "score": 10},
            {"provider_key": "B", "score": 90},
        ]
    )

    assert result["provider_key"] == "A"


def test_get_fastest_provider():
    result = get_fastest_provider(
        scorecards=[
            {"provider_key": "A", "avg_latency_ms": 500},
            {"provider_key": "B", "avg_latency_ms": 100},
        ]
    )

    assert result["provider_key"] == "B"


def test_get_most_reliable_provider():
    result = get_most_reliable_provider(
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

    assert result["provider_key"] == "B"


def test_rank_providers():
    rankings = rank_providers(
        scorecards=[
            {
                "provider_key": "A",
                "score": 50,
                "avg_latency_ms": 500,
                "success_rate": 90,
                "failure_rate": 5,
                "retry_rate": 5,
            },
            {
                "provider_key": "B",
                "score": 90,
                "avg_latency_ms": 100,
                "success_rate": 99,
                "failure_rate": 1,
                "retry_rate": 0,
            },
        ]
    )

    assert rankings["best_provider"]["provider_key"] == "B"
    assert rankings["worst_provider"]["provider_key"] == "A"
    assert rankings["fastest_provider"]["provider_key"] == "B"
    assert rankings["most_reliable_provider"]["provider_key"] == "B"


def test_rank_providers_empty():
    rankings = rank_providers(
        scorecards=[]
    )

    assert rankings["ranked"] == []
    assert rankings["best_provider"] is None
    assert rankings["worst_provider"] is None
    assert rankings["fastest_provider"] is None
    assert rankings["most_reliable_provider"] is None