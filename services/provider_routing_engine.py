from __future__ import annotations

from typing import Any

from services.intelligent_routing_service import (
    select_provider,
)

from services.provider_scorecard_service import (
    calculate_provider_scorecards,
)

from services.provider_sla_service import (
    list_provider_sla_metrics,
)


async def resolve_provider(
    *,
    strategy: str = "best",
) -> dict[str, Any] | None:
    metrics = await list_provider_sla_metrics()

    if not metrics:
        return None

    scorecards = calculate_provider_scorecards(
        metrics=metrics,
    )

    return select_provider(
        scorecards=scorecards,
        strategy=strategy,
    )


async def resolve_best_provider() -> dict[str, Any] | None:
    return await resolve_provider(
        strategy="best",
    )


async def resolve_fastest_provider() -> dict[str, Any] | None:
    return await resolve_provider(
        strategy="fastest",
    )


async def resolve_most_reliable_provider() -> dict[str, Any] | None:
    return await resolve_provider(
        strategy="most_reliable",
    )