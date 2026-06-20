from services.provider_scorecard_service import (
    calculate_provider_scorecard,
    calculate_provider_scorecards,
)


def test_calculate_provider_scorecard():
    result = calculate_provider_scorecard(
        metrics={
            "provider_key": "CASH_PROVIDER",
            "success_count": 95,
            "failure_count": 5,
            "retry_count": 2,
            "total_latency_ms": 10000,
        }
    )

    assert result["provider_key"] == "CASH_PROVIDER"
    assert result["success_rate"] == 95.0
    assert result["failure_rate"] == 5.0
    assert result["retry_rate"] == 2.0
    assert result["avg_latency_ms"] == 100.0
    assert result["total_attempts"] == 100
    assert result["score"] > 0


def test_calculate_provider_scorecard_handles_zero_attempts():
    result = calculate_provider_scorecard(
        metrics={
            "provider_key": "EMPTY_PROVIDER",
            "success_count": 0,
            "failure_count": 0,
            "retry_count": 0,
            "total_latency_ms": 0,
        }
    )

    assert result["provider_key"] == "EMPTY_PROVIDER"
    assert result["success_rate"] == 0.0
    assert result["failure_rate"] == 0.0
    assert result["retry_rate"] == 0.0
    assert result["avg_latency_ms"] == 0.0
    assert result["score"] == 0


def test_calculate_provider_scorecards_sorts_by_score():
    result = calculate_provider_scorecards(
        metrics=[
            {
                "provider_key": "BAD_PROVIDER",
                "success_count": 50,
                "failure_count": 50,
                "retry_count": 10,
                "total_latency_ms": 100000,
            },
            {
                "provider_key": "GOOD_PROVIDER",
                "success_count": 99,
                "failure_count": 1,
                "retry_count": 0,
                "total_latency_ms": 1000,
            },
        ]
    )

    assert result[0]["provider_key"] == "GOOD_PROVIDER"
    assert result[1]["provider_key"] == "BAD_PROVIDER"