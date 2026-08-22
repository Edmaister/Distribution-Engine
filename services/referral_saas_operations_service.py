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
    "SERVER_OWNED_SERVICE_TARGET_EVIDENCE",
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
                "withinServiceTargetPercent": "Completed support-case clocks within target during the rolling 30-day reporting window.",
                "productionIncidents": "Visible open CRITICAL support cases.",
            },
            "guardrails": OPERATIONS_GUARDRAILS,
            "redactions": OPERATIONS_REDACTIONS,
        }


@dataclass(frozen=True)
class CustomerPortfolioPage:
    customers: list[dict[str, Any]]
    next_cursor: str | None
    filters: dict[str, Any]
    summary: dict[str, int]

    def to_safe_dict(self) -> dict[str, Any]:
        return {
            "customers": self.customers,
            "nextCursor": self.next_cursor,
            "filters": self.filters,
            "summary": self.summary,
            "guardrails": OPERATIONS_GUARDRAILS + ["ACCOUNT_REGISTRY_SOURCE"],
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


async def read_referral_saas_customer_portfolio(
    *,
    jurisdictions: Iterable[str] | None,
    search: str | None = None,
    account_status: str | None = None,
    attention: str | None = None,
    sort: str = "ATTENTION",
    limit: int = 25,
    cursor: str | None = None,
) -> CustomerPortfolioPage:
    safe_jurisdictions = _normalise_jurisdictions(jurisdictions)
    safe_search = str(search).strip() if search else None
    safe_status = str(account_status).strip().upper() if account_status else None
    if safe_status not in {None, "PENDING_ONBOARDING", "ACTIVE", "SUSPENDED"}:
        raise ReferralSaasOperationsReadError("Account-status filter is invalid.")
    safe_attention = str(attention).strip().upper() if attention else None
    if safe_attention not in {None, "NEEDS_ATTENTION", "NO_OPEN_WORK"}:
        raise ReferralSaasOperationsReadError("Attention filter is invalid.")
    safe_sort = str(sort or "ATTENTION").strip().upper()
    order_by = {
        "ATTENTION": "open_case_count DESC, priority_rank ASC, account_name ASC, account_id ASC",
        "NAME_ASC": "account_name ASC, account_id ASC",
        "UPDATED_DESC": "updated_at DESC, account_id DESC",
    }.get(safe_sort)
    if order_by is None:
        raise ReferralSaasOperationsReadError("Sort option is invalid.")
    safe_limit = _safe_limit(limit)
    offset = _safe_cursor(cursor)

    async with db_connection() as conn:
        rows = await conn.fetch(
            f"""
            WITH customer_portfolio AS (
                SELECT
                    account.account_id,
                    account.account_code,
                    account.account_name,
                    account.account_type,
                    account.status AS account_status,
                    account.onboarding_status,
                    COALESCE(account.operating_jurisdiction_code, 'ZA') AS jurisdiction,
                    account.primary_external_tenant_ref AS customer_reference,
                    MAX(external_ref.external_ref) FILTER (
                        WHERE external_ref.ref_type = 'organisation_ref'
                    ) AS organisation_reference,
                    account.updated_at,
                    COUNT(DISTINCT support_case.support_case_id) FILTER (
                        WHERE support_case.status IN ('OPEN', 'INVESTIGATING', 'WAITING')
                    ) AS open_case_count,
                    COUNT(DISTINCT support_case.support_case_id) FILTER (
                        WHERE support_case.status IN ('OPEN', 'INVESTIGATING', 'WAITING')
                          AND support_case.priority = 'CRITICAL'
                    ) AS critical_case_count,
                    MIN(CASE support_case.priority
                        WHEN 'CRITICAL' THEN 0 WHEN 'HIGH' THEN 1
                        WHEN 'MEDIUM' THEN 2 WHEN 'LOW' THEN 3 ELSE 4 END
                    ) FILTER (WHERE support_case.status IN ('OPEN', 'INVESTIGATING', 'WAITING')) AS priority_rank,
                    ARRAY_AGG(DISTINCT support_case.category) FILTER (
                        WHERE support_case.status IN ('OPEN', 'INVESTIGATING', 'WAITING')
                    ) AS attention_categories
                FROM platform_accounts account
                LEFT JOIN platform_external_tenant_refs external_ref
                    ON external_ref.account_id = account.account_id
                   AND external_ref.status = 'ACTIVE'
                LEFT JOIN referral_saas_support_cases support_case
                    ON support_case.account_id = account.account_id
                   AND support_case.archived_at IS NULL
                WHERE account.status IN ('PENDING_ONBOARDING', 'ACTIVE', 'SUSPENDED')
                  AND account.archived_at IS NULL
                  AND ($1::text[] IS NULL OR account.operating_jurisdiction_code = ANY($1::text[]))
                  AND ($2::text IS NULL OR account.account_name ILIKE '%' || $2 || '%'
                       OR account.account_code ILIKE '%' || $2 || '%'
                       OR account.account_id::text = $2
                       OR account.primary_external_tenant_ref ILIKE '%' || $2 || '%'
                       OR external_ref.external_ref ILIKE '%' || $2 || '%')
                  AND ($3::text IS NULL OR account.status = $3)
                GROUP BY account.account_id
            )
            SELECT * FROM customer_portfolio
            WHERE ($4::text IS NULL
                OR ($4 = 'NEEDS_ATTENTION' AND open_case_count > 0)
                OR ($4 = 'NO_OPEN_WORK' AND open_case_count = 0))
            ORDER BY {order_by}
            LIMIT $5 OFFSET $6
            """,
            safe_jurisdictions,
            safe_search,
            safe_status,
            safe_attention,
            safe_limit + 1,
            offset,
        )

    visible = rows[:safe_limit]
    customers: list[dict[str, Any]] = []
    for raw in visible:
        row = dict(raw)
        open_cases = int(row.get("open_case_count") or 0)
        critical_cases = int(row.get("critical_case_count") or 0)
        categories = sorted(str(value) for value in (row.get("attention_categories") or []) if value)
        reasons: list[str] = []
        if critical_cases:
            reasons.append(f"{critical_cases} critical operational case{'s' if critical_cases != 1 else ''}")
        if open_cases:
            reasons.append(f"{open_cases} open operational case{'s' if open_cases != 1 else ''}")
        if categories:
            reasons.append("Areas: " + ", ".join(value.replace("_", " ").lower() for value in categories[:3]))
        priority_rank = row.get("priority_rank")
        highest_priority = {0: "CRITICAL", 1: "HIGH", 2: "MEDIUM", 3: "LOW"}.get(priority_rank)
        account_ref = str(row["account_id"])
        customers.append({
            "accountRef": account_ref,
            "accountCode": str(row["account_code"]),
            "accountName": str(row["account_name"]),
            "accountType": str(row["account_type"]),
            "accountStatus": str(row["account_status"]),
            "onboardingStatus": str(row["onboarding_status"]),
            "jurisdiction": str(row["jurisdiction"]),
            "customerReference": str(row["customer_reference"]) if row.get("customer_reference") else None,
            "organisationReference": str(row["organisation_reference"]) if row.get("organisation_reference") else None,
            "updatedAt": row["updated_at"].isoformat() if row.get("updated_at") else None,
            "attention": {
                "needsAttention": open_cases > 0,
                "openCaseCount": open_cases,
                "criticalCaseCount": critical_cases,
                "highestPriority": highest_priority,
                "reasons": reasons,
            },
            "destination": f"{OPERATIONS_DESTINATION_PREFIX}/{account_ref}",
        })

    return CustomerPortfolioPage(
        customers=customers,
        next_cursor=str(offset + safe_limit) if len(rows) > safe_limit else None,
        filters={
            "jurisdictions": safe_jurisdictions,
            "search": safe_search,
            "accountStatus": safe_status,
            "attention": safe_attention,
            "sort": safe_sort,
            "limit": safe_limit,
        },
        summary={
            "visibleCustomers": len(customers),
            "needingAttention": sum(1 for customer in customers if customer["attention"]["needsAttention"]),
            "criticalAttention": sum(1 for customer in customers if customer["attention"]["criticalCaseCount"] > 0),
        },
    )


async def read_referral_saas_operations(
    *,
    jurisdictions: Iterable[str] | None,
    priority: str | None = None,
    customer: str | None = None,
    category: str | None = None,
    status: str | None = None,
    owner: str | None = None,
    work_type: str | None = None,
    service_target: str | None = None,
    sort: str = "PRIORITY",
    limit: int = 25,
    cursor: str | None = None,
) -> OperationsPage:
    safe_jurisdictions = _normalise_jurisdictions(jurisdictions)
    safe_priority = str(priority).strip().upper() if priority else None
    if safe_priority not in {None, "LOW", "MEDIUM", "HIGH", "CRITICAL"}:
        raise ReferralSaasOperationsReadError("Priority filter is invalid.")
    safe_customer = str(customer).strip() if customer else None
    safe_category = str(category).strip().upper() if category else None
    safe_status = str(status).strip().upper() if status else None
    if safe_status not in {None, "OPEN", "INVESTIGATING", "WAITING"}:
        raise ReferralSaasOperationsReadError("Status filter is invalid.")
    safe_owner = str(owner).strip() if owner else None
    safe_work_type = str(work_type).strip().upper() if work_type else None
    if safe_work_type not in {None, "SUPPORT_CASE"}:
        raise ReferralSaasOperationsReadError("Work type filter is invalid.")
    safe_service_target = str(service_target).strip().upper() if service_target else None
    if safe_service_target not in {
        None, "AVAILABLE", "UNAVAILABLE", "ON_TRACK", "APPROACHING_TARGET",
        "OVERDUE", "PAUSED",
    }:
        raise ReferralSaasOperationsReadError("Service-target filter is invalid.")
    safe_sort = str(sort or "PRIORITY").strip().upper()
    order_by = {
        "PRIORITY": "CASE support_case.priority WHEN 'CRITICAL' THEN 0 WHEN 'HIGH' THEN 1 WHEN 'MEDIUM' THEN 2 ELSE 3 END, support_case.updated_at, support_case.support_case_id",
        "UPDATED_ASC": "support_case.updated_at ASC, support_case.support_case_id ASC",
        "UPDATED_DESC": "support_case.updated_at DESC, support_case.support_case_id DESC",
        "DUE_ASC": "clock.due_at ASC NULLS LAST, support_case.updated_at ASC, support_case.support_case_id ASC",
    }.get(safe_sort)
    if order_by is None:
        raise ReferralSaasOperationsReadError("Sort option is invalid.")
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
                ) AS production_incidents,
                COUNT(*) FILTER (
                    WHERE clock.completed_at >= NOW() - INTERVAL '30 days'
                      AND clock.completion_outcome IN ('WITHIN_TARGET', 'LATE')
                ) AS service_target_eligible,
                COUNT(*) FILTER (
                    WHERE clock.completed_at >= NOW() - INTERVAL '30 days'
                      AND clock.completion_outcome = 'WITHIN_TARGET'
                ) AS service_target_within,
                COUNT(*) FILTER (
                    WHERE support_case.updated_at >= NOW() - INTERVAL '30 days'
                      AND NOT (
                        clock.completed_at >= NOW() - INTERVAL '30 days'
                        AND clock.completion_outcome IN ('WITHIN_TARGET', 'LATE')
                      )
                ) AS service_target_excluded,
                COUNT(*) FILTER (
                    WHERE support_case.updated_at >= NOW() - INTERVAL '30 days'
                ) AS service_target_window_cases,
                COUNT(*) FILTER (
                    WHERE support_case.updated_at >= NOW() - INTERVAL '30 days'
                      AND clock.service_target_clock_id IS NOT NULL
                ) AS service_target_covered_cases,
                NOW() - INTERVAL '30 days' AS service_target_window_start,
                NOW() AS service_target_window_end
            FROM referral_saas_support_cases support_case
            JOIN platform_accounts account ON account.account_id = support_case.account_id
            LEFT JOIN referral_saas_operational_service_target_clocks clock
              ON clock.support_case_id = support_case.support_case_id
            WHERE support_case.archived_at IS NULL
              AND ($1::text[] IS NULL OR account.operating_jurisdiction_code = ANY($1::text[]))
              AND ($2::text IS NULL OR support_case.priority = $2)
              AND ($3::text IS NULL OR account.account_name ILIKE '%' || $3 || '%'
                   OR account.account_code ILIKE '%' || $3 || '%'
                   OR account.account_id::text = $3)
              AND ($4::text IS NULL OR support_case.category = $4)
              AND ($5::text IS NULL OR support_case.status = $5)
              AND ($6::text IS NULL OR ($6 = 'UNASSIGNED' AND support_case.assignee_ref IS NULL)
                   OR support_case.assignee_ref = $6)
              AND ($7::text IS NULL
                OR ($7 = 'AVAILABLE' AND clock.service_target_clock_id IS NOT NULL)
                OR ($7 = 'UNAVAILABLE' AND clock.service_target_clock_id IS NULL)
                OR ($7 = 'PAUSED' AND clock.clock_status = 'PAUSED')
                OR ($7 = 'OVERDUE' AND clock.clock_status = 'RUNNING' AND clock.due_at <= NOW())
                OR ($7 = 'APPROACHING_TARGET' AND clock.clock_status = 'RUNNING'
                    AND clock.warning_at <= NOW() AND clock.due_at > NOW())
                OR ($7 = 'ON_TRACK' AND clock.clock_status = 'RUNNING' AND clock.warning_at > NOW()))
            """,
            safe_jurisdictions,
            safe_priority,
            safe_customer,
            safe_category,
            safe_status,
            safe_owner,
            safe_service_target,
        )
        rows = await conn.fetch(
            f"""
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
                support_case.updated_at,
                clock.clock_status AS service_target_clock_status,
                clock.warning_at AS service_target_warning_at,
                clock.due_at AS service_target_due_at,
                CASE
                    WHEN clock.service_target_clock_id IS NULL THEN 'UNAVAILABLE'
                    WHEN clock.clock_status = 'PAUSED' THEN 'PAUSED'
                    WHEN clock.clock_status = 'RUNNING' AND clock.due_at <= NOW() THEN 'OVERDUE'
                    WHEN clock.clock_status = 'RUNNING' AND clock.warning_at <= NOW() THEN 'APPROACHING_TARGET'
                    WHEN clock.clock_status = 'RUNNING' THEN 'ON_TRACK'
                    ELSE 'UNAVAILABLE'
                END AS service_target_state
            FROM referral_saas_support_cases support_case
            JOIN platform_accounts account ON account.account_id = support_case.account_id
            LEFT JOIN referral_saas_operational_service_target_clocks clock
              ON clock.support_case_id = support_case.support_case_id
            WHERE support_case.archived_at IS NULL
              AND support_case.status IN ('OPEN', 'INVESTIGATING', 'WAITING')
              AND ($1::text[] IS NULL OR account.operating_jurisdiction_code = ANY($1::text[]))
              AND ($2::text IS NULL OR support_case.priority = $2)
              AND ($3::text IS NULL OR account.account_name ILIKE '%' || $3 || '%'
                   OR account.account_code ILIKE '%' || $3 || '%'
                   OR account.account_id::text = $3)
              AND ($4::text IS NULL OR support_case.category = $4)
              AND ($5::text IS NULL OR support_case.status = $5)
              AND ($6::text IS NULL OR ($6 = 'UNASSIGNED' AND support_case.assignee_ref IS NULL)
                   OR support_case.assignee_ref = $6)
              AND ($7::text IS NULL
                OR ($7 = 'AVAILABLE' AND clock.service_target_clock_id IS NOT NULL)
                OR ($7 = 'UNAVAILABLE' AND clock.service_target_clock_id IS NULL)
                OR ($7 = 'PAUSED' AND clock.clock_status = 'PAUSED')
                OR ($7 = 'OVERDUE' AND clock.clock_status = 'RUNNING' AND clock.due_at <= NOW())
                OR ($7 = 'APPROACHING_TARGET' AND clock.clock_status = 'RUNNING'
                    AND clock.warning_at <= NOW() AND clock.due_at > NOW())
                OR ($7 = 'ON_TRACK' AND clock.clock_status = 'RUNNING' AND clock.warning_at > NOW()))
            ORDER BY {order_by}
            LIMIT $8 OFFSET $9
            """,
            safe_jurisdictions,
            safe_priority,
            safe_customer,
            safe_category,
            safe_status,
            safe_owner,
            safe_service_target,
            safe_limit + 1,
            offset,
        )

    visible = rows[:safe_limit]
    work_items = []
    for raw in visible:
        row = dict(raw)
        account_id = str(row["account_id"])
        case_ref = str(row["support_case_id"])
        warning_at = row.get("service_target_warning_at")
        due_at = row.get("service_target_due_at")
        service_target_status = str(row.get("service_target_state") or "UNAVAILABLE")
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
                "serviceTarget": {
                    "status": service_target_status,
                    "dueAt": due_at.isoformat() if due_at else None,
                    "warningAt": warning_at.isoformat() if warning_at else None,
                },
                "destination": f"{OPERATIONS_DESTINATION_PREFIX}/{account_id}/support?case={case_ref}",
            }
        )

    metrics = dict(metrics_row or {})
    eligible = int(metrics.get("service_target_eligible") or 0)
    within = int(metrics.get("service_target_within") or 0)
    window_cases = int(metrics.get("service_target_window_cases") or 0)
    covered_cases = int(metrics.get("service_target_covered_cases") or 0)
    within_percent = round((within / eligible) * 100) if eligible else None
    return OperationsPage(
        metrics={
            "awaitingYourAction": int(metrics.get("awaiting_action") or 0),
            "customersNeedingAttention": int(metrics.get("customers_needing_attention") or 0),
            "withinServiceTargetPercent": within_percent,
            "serviceTargetStatus": "AVAILABLE" if eligible else "UNAVAILABLE",
            "serviceTargetEvidence": {
                "reportingWindow": {
                    "startAt": metrics["service_target_window_start"].isoformat() if metrics.get("service_target_window_start") else None,
                    "endAt": metrics["service_target_window_end"].isoformat() if metrics.get("service_target_window_end") else None,
                    "basis": "ROLLING_30_DAYS_COMPLETED_AT",
                },
                "eligibleCount": eligible,
                "withinTargetCount": within,
                "excludedCount": int(metrics.get("service_target_excluded") or 0),
                "policyCoverage": {
                    "coveredCount": covered_cases,
                    "visibleWindowCount": window_cases,
                    "percent": round((covered_cases / window_cases) * 100) if window_cases else None,
                },
            },
            "productionIncidents": int(metrics.get("production_incidents") or 0),
        },
        work_items=work_items,
        next_cursor=str(offset + safe_limit) if len(rows) > safe_limit else None,
        filters={
            "jurisdictions": safe_jurisdictions,
            "priority": safe_priority,
            "customer": safe_customer,
            "category": safe_category,
            "status": safe_status,
            "owner": safe_owner,
            "workType": safe_work_type,
            "serviceTarget": safe_service_target,
            "sort": safe_sort,
            "limit": safe_limit,
        },
    )
