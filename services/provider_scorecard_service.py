from __future__ import annotations

from typing import Any


def _safe_rate(
    *,
    numerator: int,
    denominator: int,
) -> float:
    if denominator <= 0:
        return 0.0

    return round((numerator / denominator) * 100, 2)


def calculate_provider_scorecard(
    *,
    metrics: dict[str, Any],
) -> dict[str, Any]:
    provider_key = metrics["provider_key"]

    success_count = int(metrics.get("success_count", 0))
    failure_count = int(metrics.get("failure_count", 0))
    retry_count = int(metrics.get("retry_count", 0))
    total_latency_ms = int(metrics.get("total_latency_ms", 0))

    total_attempts = success_count + failure_count

    success_rate = _safe_rate(
        numerator=success_count,
        denominator=total_attempts,
    )

    failure_rate = _safe_rate(
        numerator=failure_count,
        denominator=total_attempts,
    )

    retry_rate = _safe_rate(
        numerator=retry_count,
        denominator=total_attempts,
    )

    avg_latency_ms = (
        round(total_latency_ms / total_attempts, 2)
        if total_attempts > 0
        else 0.0
    )

    score = round(
        success_rate
        - failure_rate
        - retry_rate
        - min(avg_latency_ms / 1000, 10),
        2,
    )

    return {
        "provider_key": provider_key,
        "score": max(score, 0),
        "success_rate": success_rate,
        "failure_rate": failure_rate,
        "retry_rate": retry_rate,
        "avg_latency_ms": avg_latency_ms,
        "success_count": success_count,
        "failure_count": failure_count,
        "retry_count": retry_count,
        "total_attempts": total_attempts,
    }


def calculate_provider_scorecards(
    *,
    metrics: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    scorecards = [
        calculate_provider_scorecard(metrics=item)
        for item in metrics
    ]

    return sorted(
        scorecards,
        key=lambda item: item["score"],
        reverse=True,
    )