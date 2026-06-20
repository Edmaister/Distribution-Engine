from __future__ import annotations

from typing import Any


VALID_STRATEGIES = {
    "best",
    "fastest",
    "most_reliable",
}


def select_best_provider(
    *,
    scorecards: list[dict[str, Any]],
) -> dict[str, Any] | None:
    if not scorecards:
        return None

    return max(
        scorecards,
        key=lambda item: item.get("score", 0),
    )


def select_fastest_provider(
    *,
    scorecards: list[dict[str, Any]],
) -> dict[str, Any] | None:
    if not scorecards:
        return None

    return min(
        scorecards,
        key=lambda item: item.get("avg_latency_ms", 0),
    )


def select_most_reliable_provider(
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


def select_provider(
    *,
    scorecards: list[dict[str, Any]],
    strategy: str = "best",
) -> dict[str, Any] | None:
    if strategy not in VALID_STRATEGIES:
        raise ValueError(f"Unsupported routing strategy: {strategy}")

    if strategy == "fastest":
        return select_fastest_provider(scorecards=scorecards)

    if strategy == "most_reliable":
        return select_most_reliable_provider(scorecards=scorecards)

    return select_best_provider(scorecards=scorecards)