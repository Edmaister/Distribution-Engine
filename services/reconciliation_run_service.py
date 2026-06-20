from __future__ import annotations

from typing import Any

from services.fulfilment.settlement.reconciliation import (
    reconcile_settlements,
)
from services.provider_statement_import_service import (
    import_provider_statement,
)
from services.reconciliation_history_service import (
    create_reconciliation_results,
    create_reconciliation_run,
)


async def run_reconciliation(
    *,
    provider_key: str,
    platform_records: list[dict[str, Any]],
    provider_records: list[dict[str, Any]],
    tenant_code: str | None = None,
) -> dict[str, Any]:

    imported_statement = import_provider_statement(
        provider_key=provider_key,
        records=provider_records,
    )

    reconciliation_results = reconcile_settlements(
        platform_records=platform_records,
        provider_records=imported_statement["records"],
    )

    summary = {
        "matched": 0,
        "missing": 0,
        "duplicate": 0,
        "overpaid": 0,
        "underpaid": 0,
    }

    for result in reconciliation_results:
        status = result["status"].lower()

        if status in summary:
            summary[status] += 1

    run_record = await create_reconciliation_run(
        tenant_code=tenant_code,
        provider_key=provider_key,
        total_records=len(reconciliation_results),
        matched_count=summary["matched"],
        missing_count=summary["missing"],
        duplicate_count=summary["duplicate"],
        overpaid_count=summary["overpaid"],
        underpaid_count=summary["underpaid"],
    )

    run_id = str(run_record["run_id"])

    await create_reconciliation_results(
        run_id=run_id,
        results=reconciliation_results,
    )

    return {
        "run_id": run_id,
        "provider_key": provider_key,
        "statement_import": imported_statement,
        "summary": summary,
        "results": reconciliation_results,
    }