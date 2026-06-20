from __future__ import annotations

from typing import Any

from services.reconciliation_history_service import (
    list_reconciliation_runs,
)


async def get_reconciliation_metrics(
    *,
    tenant_code: str | None = None,
    provider_key: str | None = None,
) -> dict[str, Any]:

    runs = await list_reconciliation_runs(
        tenant_code=tenant_code,
        provider_key=provider_key,
        limit=1000,
    )

    metrics = {
        "total_runs": len(runs),
        "total_records": 0,
        "matched_count": 0,
        "missing_count": 0,
        "duplicate_count": 0,
        "overpaid_count": 0,
        "underpaid_count": 0,
    }

    for run in runs:
        metrics["total_records"] += run.get("total_records", 0)
        metrics["matched_count"] += run.get("matched_count", 0)
        metrics["missing_count"] += run.get("missing_count", 0)
        metrics["duplicate_count"] += run.get("duplicate_count", 0)
        metrics["overpaid_count"] += run.get("overpaid_count", 0)
        metrics["underpaid_count"] += run.get("underpaid_count", 0)

    if metrics["total_records"] > 0:
        metrics["match_rate"] = round(
            (metrics["matched_count"] / metrics["total_records"]) * 100,
            2,
        )
    else:
        metrics["match_rate"] = 0

    return metrics