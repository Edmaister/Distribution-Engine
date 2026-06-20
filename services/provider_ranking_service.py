from __future__ import annotations

from typing import Any


def get_best_provider(
    *,
    scorecards: list[dict[str, Any]],
) -> dict[str, Any] | None:
    if not scorecards:
        return None

    return max(
        scorecards,
        key=lambda item: item.get("score", 0),
    )


def get_worst_provider(
    *,
    scorecards: list[dict[str, Any]],
) -> dict[str, Any] | None:
    if not scorecards:
        return None

    return min(
        scorecards,
        key=lambda item: item.get("score", 0),
    )


def get_fastest_provider(
    *,
    scorecards: list[dict[str, Any]],
) -> dict[str, Any] | None:
    if not scorecards:
        return None

    return min(
        scorecards,
        key=lambda item: item.get("avg_latency_ms", 0),
    )


def get_most_reliable_provider(
    *,
    scorecards: list[dict[str, Any]],
) -> dict[str, Any] | None:
    if not scorecards:
        return None

    return max(
        scorecards,
        key=lambda item: (
            item.get("success_rate", 0),
            -item.get("failure_rate", 0),
            -item.get("retry_rate", 0),
        ),
    )


def rank_providers(
    *,
    scorecards: list[dict[str, Any]],
) -> dict[str, Any]:
    ranked = sorted(
        scorecards,
        key=lambda item: item.get("score", 0),
        reverse=True,
    )

    return {
        "ranked": ranked,
        "best_provider": get_best_provider(scorecards=scorecards),
        "worst_provider": get_worst_provider(scorecards=scorecards),
        "fastest_provider": get_fastest_provider(scorecards=scorecards),
        "most_reliable_provider": get_most_reliable_provider(scorecards=scorecards),
    }