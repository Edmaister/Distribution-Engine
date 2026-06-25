from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from services.distribution.reporting_service import get_marketplace_overview
from services.finance_metrics_service import get_reconciliation_metrics

REPORT_DISTRIBUTION_OVERVIEW = "distribution_overview"
REPORT_RECONCILIATION_SUMMARY = "reconciliation_summary"

METRIC_OPERATIONAL = "OPERATIONAL"
METRIC_LEDGER_BACKED = "LEDGER_BACKED"

FRESHNESS_FRESH = "FRESH"
FRESHNESS_UNAVAILABLE = "UNAVAILABLE"

SENSITIVE_FILTER_PARTS = (
    "ucn",
    "secret",
    "token",
    "password",
    "provider_payload",
    "raw",
    "audit_payload",
)

REPORT_CATALOG: dict[str, dict[str, Any]] = {
    REPORT_DISTRIBUTION_OVERVIEW: {
        "metric_class": METRIC_OPERATIONAL,
        "source_family": "distribution_reporting",
        "allowed_dimensions": {
            "tenant_code",
            "sponsor_code",
            "campaign_code",
            "metric_name",
        },
        "allowed_filters": {"sponsor_code", "campaign_code"},
    },
    REPORT_RECONCILIATION_SUMMARY: {
        "metric_class": METRIC_LEDGER_BACKED,
        "source_family": "finance_reconciliation",
        "allowed_dimensions": {
            "tenant_code",
            "provider_key",
            "metric_name",
            "reconciliation_status",
        },
        "allowed_filters": {"provider_key"},
    },
}


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _iso(value: datetime | None) -> str | None:
    return value.isoformat() if value else None


def _normalise_tenant_code(tenant_code: str) -> str:
    tenant = str(tenant_code or "").strip().upper()
    if not tenant:
        raise ValueError("tenant_code is required")
    return tenant


def _normalise_report_type(report_type: str) -> str:
    report = str(report_type or "").strip().lower()
    if report not in REPORT_CATALOG:
        raise ValueError(f"Unsupported analytics report_type: {report_type}")
    return report


def _normalise_dimensions(report_type: str, dimensions: list[str] | None) -> list[str]:
    requested = [
        str(dimension or "").strip().lower()
        for dimension in (dimensions or ["tenant_code", "metric_name"])
    ]
    requested = [dimension for dimension in requested if dimension]
    if not requested:
        raise ValueError("at least one dimension is required")

    allowed = REPORT_CATALOG[report_type]["allowed_dimensions"]
    rejected = sorted(set(requested) - allowed)
    if rejected:
        raise ValueError("Unsupported analytics dimension(s): " + ", ".join(rejected))
    return requested


def _safe_filters(
    *,
    report_type: str,
    tenant_code: str,
    filters: dict[str, Any] | None,
) -> tuple[dict[str, Any], list[str]]:
    safe: dict[str, Any] = {"tenant_code": tenant_code}
    redactions: list[str] = []
    allowed = REPORT_CATALOG[report_type]["allowed_filters"]

    for key, value in (filters or {}).items():
        name = str(key or "").strip()
        if not name:
            continue
        if any(part in name.lower() for part in SENSITIVE_FILTER_PARTS):
            redactions.append(name)
            continue
        if name not in allowed:
            raise ValueError(f"Unsupported analytics filter: {name}")
        if value is not None and str(value).strip():
            safe[name] = str(value).strip()

    return safe, redactions


def _number(value: Any) -> int | float | str:
    if isinstance(value, Decimal):
        if value == value.to_integral_value():
            return int(value)
        return str(value)
    if isinstance(value, int | float):
        return value
    try:
        decimal = Decimal(str(value or 0))
    except Exception:
        return 0
    if decimal == decimal.to_integral_value():
        return int(decimal)
    return str(decimal)


def _metric(
    *,
    name: str,
    value: Any,
    metric_class: str,
    source: str,
    dimensions: dict[str, Any],
    unit: str = "count",
) -> dict[str, Any]:
    return {
        "name": name,
        "value": _number(value),
        "unit": unit,
        "metric_class": metric_class,
        "source": source,
        "dimensions": dimensions,
    }


def _freshness(
    *,
    status: str,
    generated_at: datetime,
    source_family: str,
    data_window_start: datetime | None,
    data_window_end: datetime | None,
) -> dict[str, Any]:
    source_as_of = generated_at if status == FRESHNESS_FRESH else None
    return {
        "status": status,
        "generated_at": _iso(generated_at),
        "source_as_of": _iso(source_as_of),
        "data_window_start": _iso(data_window_start),
        "data_window_end": _iso(data_window_end),
        "lag_seconds": 0 if source_as_of else None,
        "sources": [
            {
                "source_family": source_family,
                "status": status,
                "source_as_of": _iso(source_as_of),
            }
        ],
    }


def _base_envelope(
    *,
    report_type: str,
    tenant_code: str,
    filters: dict[str, Any],
    dimensions: list[str],
    metric_class: str,
    generated_at: datetime,
    data_window_start: datetime | None,
    data_window_end: datetime | None,
    source_family: str,
    redactions: list[str],
) -> dict[str, Any]:
    return {
        "report_type": report_type,
        "tenant_scope": tenant_code,
        "external_tenant_ref": None,
        "filters": filters,
        "dimensions": dimensions,
        "metric_class": metric_class,
        "metrics": [],
        "data_window_start": _iso(data_window_start),
        "data_window_end": _iso(data_window_end),
        "generated_at": _iso(generated_at),
        "freshness": _freshness(
            status=FRESHNESS_FRESH,
            generated_at=generated_at,
            source_family=source_family,
            data_window_start=data_window_start,
            data_window_end=data_window_end,
        ),
        "source_warnings": [],
        "redactions": redactions,
        "reconciliation_status": (
            "NOT_APPLICABLE" if metric_class == METRIC_OPERATIONAL else "UNAVAILABLE"
        ),
    }


def _unavailable(
    envelope: dict[str, Any],
    *,
    source_family: str,
    generated_at: datetime,
    data_window_start: datetime | None,
    data_window_end: datetime | None,
) -> dict[str, Any]:
    envelope["freshness"] = _freshness(
        status=FRESHNESS_UNAVAILABLE,
        generated_at=generated_at,
        source_family=source_family,
        data_window_start=data_window_start,
        data_window_end=data_window_end,
    )
    envelope["source_warnings"].append(
        {
            "code": "SOURCE_UNAVAILABLE",
            "severity": "WARNING",
            "source": source_family,
            "message": "Analytics source could not be read safely.",
        }
    )
    if envelope["metric_class"] == METRIC_LEDGER_BACKED:
        envelope["reconciliation_status"] = "UNAVAILABLE"
    return envelope


async def get_tenant_safe_analytics_report(
    *,
    tenant_code: str,
    report_type: str,
    dimensions: list[str] | None = None,
    filters: dict[str, Any] | None = None,
    data_window_start: datetime | None = None,
    data_window_end: datetime | None = None,
) -> dict[str, Any]:
    tenant = _normalise_tenant_code(tenant_code)
    report = _normalise_report_type(report_type)
    resolved_dimensions = _normalise_dimensions(report, dimensions)
    safe_filters, redactions = _safe_filters(
        report_type=report,
        tenant_code=tenant,
        filters=filters,
    )

    if data_window_start and data_window_end and data_window_start >= data_window_end:
        raise ValueError("data_window_start must be before data_window_end")

    config = REPORT_CATALOG[report]
    generated_at = _utcnow()
    envelope = _base_envelope(
        report_type=report,
        tenant_code=tenant,
        filters=safe_filters,
        dimensions=resolved_dimensions,
        metric_class=config["metric_class"],
        generated_at=generated_at,
        data_window_start=data_window_start,
        data_window_end=data_window_end,
        source_family=config["source_family"],
        redactions=redactions,
    )

    if report == REPORT_DISTRIBUTION_OVERVIEW:
        return await _distribution_overview(envelope, generated_at)
    return await _reconciliation_summary(envelope, generated_at)


async def _distribution_overview(
    envelope: dict[str, Any],
    generated_at: datetime,
) -> dict[str, Any]:
    filters = envelope["filters"]
    tenant_code = filters["tenant_code"]
    try:
        overview = await get_marketplace_overview(
            tenant_code=tenant_code,
            sponsor_code=filters.get("sponsor_code"),
            campaign_code=filters.get("campaign_code"),
        )
    except Exception:
        return _unavailable(
            envelope,
            source_family="distribution_reporting",
            generated_at=generated_at,
            data_window_start=None,
            data_window_end=None,
        )

    base_dimensions = {
        "tenant_code": tenant_code,
        "sponsor_code": filters.get("sponsor_code"),
        "campaign_code": filters.get("campaign_code"),
    }
    metrics = [
        (
            "distributors.total_count",
            overview.get("distributors", {}).get("total_count"),
        ),
        (
            "distributors.active_count",
            overview.get("distributors", {}).get("active_count"),
        ),
        (
            "opportunities.total_count",
            overview.get("opportunities", {}).get("total_count"),
        ),
        (
            "opportunities.published_count",
            overview.get("opportunities", {}).get("published_count"),
        ),
        ("routes.total_count", overview.get("routes", {}).get("total_count")),
        ("routes.accepted_count", overview.get("routes", {}).get("accepted_count")),
        (
            "routes.acceptance_rate",
            overview.get("routes", {}).get("acceptance_rate"),
            "ratio",
        ),
        (
            "conversions.linked_count",
            overview.get("conversions", {}).get("linked_count"),
        ),
        (
            "conversions.completed_count",
            overview.get("conversions", {}).get("completed_count"),
        ),
        (
            "conversions.completion_rate",
            overview.get("conversions", {}).get("completion_rate"),
            "ratio",
        ),
        (
            "conversions.attribution_rate",
            overview.get("conversions", {}).get("attribution_rate"),
            "ratio",
        ),
        ("wallets.wallet_count", overview.get("wallets", {}).get("wallet_count")),
        (
            "governance.open_dispute_count",
            overview.get("governance", {}).get("open_dispute_count"),
        ),
    ]
    envelope["metrics"] = [
        _metric(
            name=item[0],
            value=item[1],
            metric_class=METRIC_OPERATIONAL,
            source="distribution_reporting",
            dimensions={**base_dimensions, "metric_name": item[0]},
            unit=item[2] if len(item) > 2 else "count",
        )
        for item in metrics
    ]
    return envelope


async def _reconciliation_summary(
    envelope: dict[str, Any],
    generated_at: datetime,
) -> dict[str, Any]:
    filters = envelope["filters"]
    tenant_code = filters["tenant_code"]
    try:
        summary = await get_reconciliation_metrics(
            tenant_code=tenant_code,
            provider_key=filters.get("provider_key"),
        )
    except Exception:
        return _unavailable(
            envelope,
            source_family="finance_reconciliation",
            generated_at=generated_at,
            data_window_start=None,
            data_window_end=None,
        )

    total_records = int(summary.get("total_records") or 0)
    matched_count = int(summary.get("matched_count") or 0)
    reconciliation_status = "NOT_APPLICABLE"
    if total_records:
        reconciliation_status = (
            "MATCHED" if matched_count == total_records else "PARTIAL"
        )

    base_dimensions = {
        "tenant_code": tenant_code,
        "provider_key": filters.get("provider_key"),
        "reconciliation_status": reconciliation_status,
    }
    metric_names = [
        "total_runs",
        "total_records",
        "matched_count",
        "missing_count",
        "duplicate_count",
        "overpaid_count",
        "underpaid_count",
        "match_rate",
    ]
    envelope["metrics"] = [
        _metric(
            name=f"reconciliation.{name}",
            value=summary.get(name),
            metric_class=METRIC_LEDGER_BACKED,
            source="finance_reconciliation",
            dimensions={**base_dimensions, "metric_name": f"reconciliation.{name}"},
            unit="percent" if name == "match_rate" else "count",
        )
        for name in metric_names
    ]
    envelope["reconciliation_status"] = reconciliation_status
    return envelope
