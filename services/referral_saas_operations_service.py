from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from utils.db import db_connection

OPERATIONS_DESTINATION_PREFIX = "/admin/referral-saas/account-maintenance"
OPERATIONS_GUARDRAILS = [
    "READ_ONLY_OPERATIONAL_EVIDENCE",
    "JURISDICTION_FILTERED",
    "DESTINATION_ALLOW_LISTED",
    "NO_SYNTHETIC_SERVICE_TARGET",
    "NO_PRODUCT_STATE_MUTATION",
]
OPERATIONS_REDACTIONS = ["tenant_code", "internal_tenant_identifier", "raw_secret"]


class ReferralSaasOperationsReadError(Exception):
    safe_code = "OPERATIONS_READ_FAILED"


@dataclass(frozen=True)
class OperationsPage:
    metrics: dict[str, Any]
    work_items: list[dict[str, Any]]
    next_cursor: str | None
    filters: dict[str, Any]

    def to_safe_dict(self) -> dict[str, Any]:
        return {
            "metrics": self.metrics,
            "workItems": self.work_items,
            "nextCursor": self.next_cursor,
            "filters": self.filters,
            "metricDefinitions": {
                "awaitingYourAction": "Open, investigating, or waiting persisted support cases.",
                "customersNeedingAttention": "Distinct visible customers with an open operational case.",
                "withinServiceTargetPercent": "Unavailable until a persisted service-target contract exists.",
                "productionIncidents": "Visible open CRITICAL support cases.",
            },
            "guardrails": OPERATIONS_GUARDRAILS,
            "redactions": OPERATIONS_REDACTIONS,
        }


def _safe_limit(value: int) -> int:
    return max(1, min(int(value or 25), 100))


def _safe_cursor(value: str | None) -> int:
    if value in (None, ""):
        return 0
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise ReferralSaasOperationsReadError("Cursor must be a non-negative integer.") from exc
    if parsed < 0:
        raise ReferralSaasOperationsReadError("Cursor must be a non-negative integer.")
    return parsed


def _normalise_jurisdictions(values: Iterable[str] | None) -> list[str] | None:
    if values is None:
        return None
    result = sorted({str(value).strip().upper() for value in values if str(value).strip()})
    return result or []


async def read_referral_saas_operations(
    *,
    jurisdictions: Iterable[str] | None,
    priority: str | None = None,
    limit: int = 25,
    cursor: str | None = None,
) -> OperationsPage:
    safe_jurisdictions = _normalise_jurisdictions(jurisdictions)
    safe_priority = str(priority).strip().upper() if priority else None
    if safe_priority not in {None, "LOW", "MEDIUM", "HIGH", "CRITICAL"}:
        raise ReferralSaasOperationsReadError("Priority filter is invalid.")
    safe_limit = _safe_limit(limit)
    offset = _safe_cursor(cursor)

    async with db_connection() as conn:
        metrics_row = await conn.fetchrow(
            """
            SELECT
                COUNT(*) FILTER (WHERE support_case.status IN ('OPEN', 'INVESTIGATING', 'WAITING')) AS awaiting_action,
                COUNT(DISTINCT support_case.account_id) FILTER (
                    WHERE support_case.status IN ('OPEN', 'INVESTIGATING', 'WAITING')
                ) AS customers_needing_attention,
                COUNT(*) FILTER (
                    WHERE support_case.status IN ('OPEN', 'INVESTIGATING', 'WAITING')
                      AND support_case.priority = 'CRITICAL'
                ) AS production_incidents
            FROM referral_saas_support_cases support_case
            JOIN platform_accounts account ON account.account_id = support_case.account_id
            WHERE support_case.archived_at IS NULL
              AND ($1::text[] IS NULL OR account.operating_jurisdiction_code = ANY($1::text[]))
              AND ($2::text IS NULL OR support_case.priority = $2)
            """,
            safe_jurisdictions,
            safe_priority,
        )
        rows = await conn.fetch(
            """
            SELECT
                support_case.support_case_id,
                support_case.account_id,
                account.account_code,
                account.account_name,
                COALESCE(account.operating_jurisdiction_code, 'ZA') AS jurisdiction,
                support_case.title,
                support_case.category,
                support_case.priority,
                support_case.status,
                support_case.assignee_ref,
                support_case.updated_at
            FROM referral_saas_support_cases support_case
            JOIN platform_accounts account ON account.account_id = support_case.account_id
            WHERE support_case.archived_at IS NULL
              AND support_case.status IN ('OPEN', 'INVESTIGATING', 'WAITING')
              AND ($1::text[] IS NULL OR account.operating_jurisdiction_code = ANY($1::text[]))
              AND ($2::text IS NULL OR support_case.priority = $2)
            ORDER BY
                CASE support_case.priority WHEN 'CRITICAL' THEN 0 WHEN 'HIGH' THEN 1 WHEN 'MEDIUM' THEN 2 ELSE 3 END,
                support_case.updated_at,
                support_case.support_case_id
            LIMIT $3 OFFSET $4
            """,
            safe_jurisdictions,
            safe_priority,
            safe_limit + 1,
            offset,
        )

    visible = rows[:safe_limit]
    work_items = []
    for raw in visible:
        row = dict(raw)
        account_id = str(row["account_id"])
        case_ref = str(row["support_case_id"])
        work_items.append(
            {
                "workItemRef": case_ref,
                "workItemType": "SUPPORT_CASE",
                "title": str(row["title"]),
                "customer": {
                    "accountRef": account_id,
                    "accountCode": str(row["account_code"]),
                    "label": str(row["account_name"] or row["account_code"]),
                },
                "jurisdiction": str(row["jurisdiction"]),
                "priority": str(row["priority"]),
                "status": str(row["status"]),
                "category": str(row["category"]),
                "ownerRef": str(row["assignee_ref"]) if row.get("assignee_ref") else None,
                "updatedAt": row["updated_at"].isoformat() if row.get("updated_at") else None,
                "serviceTarget": {"status": "UNAVAILABLE", "dueAt": None},
                "destination": f"{OPERATIONS_DESTINATION_PREFIX}/{account_id}/support?case={case_ref}",
            }
        )

    metrics = dict(metrics_row or {})
    return OperationsPage(
        metrics={
            "awaitingYourAction": int(metrics.get("awaiting_action") or 0),
            "customersNeedingAttention": int(metrics.get("customers_needing_attention") or 0),
            "withinServiceTargetPercent": None,
            "serviceTargetStatus": "UNAVAILABLE",
            "productionIncidents": int(metrics.get("production_incidents") or 0),
        },
        work_items=work_items,
        next_cursor=str(offset + safe_limit) if len(rows) > safe_limit else None,
        filters={"jurisdictions": safe_jurisdictions, "priority": safe_priority, "limit": safe_limit},
    )
