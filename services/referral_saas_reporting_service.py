from __future__ import annotations

from datetime import datetime
from typing import Any

from services import tenant_safe_analytics_service as analytics
from utils.db import db_connection

REPORT_CAMPAIGN_PERFORMANCE = "campaign_performance"
REPORT_REFERRAL_FUNNEL = "referral_funnel"
REPORT_LINK_CODE_PERFORMANCE = "link_code_performance"
REPORT_PROGRESS_EVENT_HEALTH = "progress_event_health"
REPORT_ATTRIBUTION_QUALITY = "attribution_quality"
REPORT_SAFE_STATUS_DISTRIBUTION = "safe_status_distribution"
REPORT_REWARD_VISIBILITY_SUMMARY = "reward_visibility_summary"

STATUS_AVAILABLE = "AVAILABLE"
STATUS_NOT_IMPLEMENTED = "NOT_IMPLEMENTED"
SOURCE_PROGRESS_EVENT_HEALTH = "referral_progress_event_health"

REPORT_METRIC_NAME_MAPS = {
    REPORT_CAMPAIGN_PERFORMANCE: {
        "opportunities.published_count": "campaigns.ready_count",
        "routes.total_count": "referrals.linked_route_count",
        "routes.accepted_count": "referrals.accepted_route_count",
        "routes.acceptance_rate": "conversion.validation_rate",
        "conversions.linked_count": "attribution.linked_count",
        "conversions.completed_count": "referrals.completed_count",
        "conversions.completion_rate": "conversion.completion_rate",
        "conversions.attribution_rate": "conversion.attribution_rate",
    },
    REPORT_REFERRAL_FUNNEL: {
        "routes.total_count": "funnel.linked_route_count",
        "routes.accepted_count": "funnel.accepted_route_count",
        "routes.acceptance_rate": "funnel.acceptance_rate",
        "conversions.linked_count": "funnel.attributed_referral_count",
        "conversions.completed_count": "funnel.completed_referral_count",
        "conversions.completion_rate": "funnel.completion_rate",
        "conversions.attribution_rate": "funnel.attribution_rate",
    },
}

SENSITIVE_FILTER_PARTS = (
    "ucn",
    "secret",
    "token",
    "password",
    "provider_payload",
    "raw",
    "audit_payload",
    "dlq",
    "settlement",
    "funding",
    "wallet",
)

REFERRAL_SAAS_REPORT_CATALOG: dict[str, dict[str, Any]] = {
    REPORT_CAMPAIGN_PERFORMANCE: {
        "status": STATUS_AVAILABLE,
        "source_report_type": analytics.REPORT_DISTRIBUTION_OVERVIEW,
        "metric_class": analytics.METRIC_OPERATIONAL,
        "allowed_dimensions": {
            "campaign_ref",
            "campaign_code",
            "metric_name",
            "safe_status",
        },
        "default_dimensions": ["campaign_code", "metric_name"],
        "allowed_filters": {"campaign_ref", "campaign_code", "sponsor_code"},
    },
    REPORT_REFERRAL_FUNNEL: {
        "status": STATUS_AVAILABLE,
        "source_report_type": analytics.REPORT_DISTRIBUTION_OVERVIEW,
        "metric_class": analytics.METRIC_OPERATIONAL,
        "allowed_dimensions": {
            "campaign_ref",
            "campaign_code",
            "metric_name",
            "progress_band",
        },
        "default_dimensions": ["campaign_code", "metric_name"],
        "allowed_filters": {"campaign_ref", "campaign_code", "sponsor_code"},
        "source_warnings": [
            {
                "code": "PARTIAL_SOURCE_COVERAGE",
                "message": (
                    "Referral funnel currently uses tenant-safe distribution "
                    "overview metrics; code-issued, validation-state, and "
                    "progress-milestone stage counts need dedicated follow-up "
                    "report sources before they can be promised."
                ),
            }
        ],
    },
    REPORT_LINK_CODE_PERFORMANCE: {
        "status": STATUS_NOT_IMPLEMENTED,
        "metric_class": analytics.METRIC_OPERATIONAL,
    },
    REPORT_PROGRESS_EVENT_HEALTH: {
        "status": STATUS_AVAILABLE,
        "source_report_type": SOURCE_PROGRESS_EVENT_HEALTH,
        "metric_class": analytics.METRIC_OPERATIONAL,
        "allowed_dimensions": {
            "event_family",
            "event_type",
            "failure_category",
            "ingestion_state",
            "metric_name",
            "source_system",
        },
        "default_dimensions": ["event_type", "source_system", "metric_name"],
        "allowed_filters": {"event_type", "failure_category", "source_system", "status"},
        "source_warnings": [
            {
                "code": "PARTIAL_SOURCE_COVERAGE",
                "message": (
                    "Progress event health uses referral_progress_events and "
                    "tenant-scoped referral_event_failures. Deduped/rejected "
                    "event counts are not available until those states are "
                    "persisted in tenant-safe reportable form."
                ),
            },
            {
                "code": "UNSCOPED_FAILURES_EXCLUDED",
                "message": (
                    "Failure rows without a referral_track_id cannot be "
                    "tenant-scoped safely and are excluded from this product "
                    "report."
                ),
            },
        ],
    },
    REPORT_ATTRIBUTION_QUALITY: {
        "status": STATUS_NOT_IMPLEMENTED,
        "metric_class": "DERIVED_STATUS",
    },
    REPORT_SAFE_STATUS_DISTRIBUTION: {
        "status": STATUS_NOT_IMPLEMENTED,
        "metric_class": "DERIVED_STATUS",
    },
    REPORT_REWARD_VISIBILITY_SUMMARY: {
        "status": STATUS_NOT_IMPLEMENTED,
        "metric_class": analytics.METRIC_OPERATIONAL,
    },
}


def list_referral_saas_report_catalog() -> list[dict[str, Any]]:
    return [
        {
            "report_type": report_type,
            "status": config["status"],
            "metric_class": config["metric_class"],
            "source_report_type": config.get("source_report_type"),
        }
        for report_type, config in REFERRAL_SAAS_REPORT_CATALOG.items()
    ]


def _normalise_report_type(report_type: str) -> str:
    report = str(report_type or "").strip().lower()
    if report not in REFERRAL_SAAS_REPORT_CATALOG:
        raise ValueError(f"Unsupported Referral SaaS report_type: {report_type}")
    config = REFERRAL_SAAS_REPORT_CATALOG[report]
    if config["status"] != STATUS_AVAILABLE:
        raise ValueError(f"Referral SaaS report_type not implemented: {report}")
    return report


def _normalise_tenant_code(tenant_code: str) -> str:
    tenant = str(tenant_code or "").strip().upper()
    if not tenant:
        raise ValueError("tenant_code is required")
    return tenant


def _normalise_dimensions(report_type: str, dimensions: list[str] | None) -> list[str]:
    default_dimensions = REFERRAL_SAAS_REPORT_CATALOG[report_type].get(
        "default_dimensions", ["campaign_code", "metric_name"]
    )
    requested = [
        str(dimension or "").strip().lower()
        for dimension in (dimensions or default_dimensions)
    ]
    requested = [dimension for dimension in requested if dimension]
    if not requested:
        raise ValueError("at least one dimension is required")

    allowed = REFERRAL_SAAS_REPORT_CATALOG[report_type]["allowed_dimensions"]
    rejected = sorted(set(requested) - allowed)
    if rejected:
        raise ValueError(
            "Unsupported Referral SaaS report dimension(s): " + ", ".join(rejected)
        )
    return requested


def _safe_filters(
    *,
    report_type: str,
    filters: dict[str, Any] | None,
) -> tuple[dict[str, str], list[str]]:
    allowed = REFERRAL_SAAS_REPORT_CATALOG[report_type]["allowed_filters"]
    safe: dict[str, str] = {}
    redactions: list[str] = []

    for key, value in (filters or {}).items():
        name = str(key or "").strip()
        if not name:
            continue
        if any(part in name.lower() for part in SENSITIVE_FILTER_PARTS):
            redactions.append(name)
            continue
        if name not in allowed:
            raise ValueError(f"Unsupported Referral SaaS report filter: {name}")
        if value is not None and str(value).strip():
            safe[name] = str(value).strip()

    if "campaign_ref" in safe and "campaign_code" not in safe:
        safe["campaign_code"] = safe["campaign_ref"]
    return safe, redactions


def _analytics_filters(filters: dict[str, str]) -> dict[str, str]:
    return {
        key: value
        for key, value in {
            "sponsor_code": filters.get("sponsor_code"),
            "campaign_code": filters.get("campaign_code"),
        }.items()
        if value
    }


def _progress_health_filters(filters: dict[str, str]) -> dict[str, str]:
    return {
        key: value
        for key, value in {
            "event_type": filters.get("event_type"),
            "failure_category": filters.get("failure_category"),
            "source_system": filters.get("source_system"),
            "status": filters.get("status"),
        }.items()
        if value
    }


def _report_metric(
    *,
    name: str,
    value: Any,
    source: str,
    dimensions: dict[str, Any],
    unit: str = "count",
) -> dict[str, Any]:
    return {
        "name": name,
        "value": int(value or 0),
        "unit": unit,
        "metric_class": analytics.METRIC_OPERATIONAL,
        "source": source,
        "dimensions": {
            key: value for key, value in dimensions.items() if value is not None
        },
    }


def _product_metric(report_type: str, metric: dict[str, Any]) -> dict[str, Any] | None:
    source_name = metric.get("name")
    product_name = REPORT_METRIC_NAME_MAPS.get(report_type, {}).get(source_name)
    if not product_name:
        return None

    dimensions = {
        key: value
        for key, value in {
            "campaign_code": metric.get("dimensions", {}).get("campaign_code"),
            "campaign_ref": metric.get("dimensions", {}).get("campaign_code"),
            "metric_name": product_name,
        }.items()
        if value is not None
    }
    return {
        "name": product_name,
        "value": metric.get("value"),
        "unit": metric.get("unit"),
        "metric_class": analytics.METRIC_OPERATIONAL,
        "source": "referral_saas_report_catalog",
        "source_metric": source_name,
        "dimensions": dimensions,
    }


def _source_warnings(report_type: str, source_report: dict[str, Any]) -> list[Any]:
    configured = REFERRAL_SAAS_REPORT_CATALOG[report_type].get("source_warnings", [])
    return [*source_report["source_warnings"], *configured]


async def _progress_event_health_report(
    *,
    tenant_code: str,
    dimensions: list[str],
    filters: dict[str, str],
    redactions: list[str],
    data_window_start: datetime | None,
    data_window_end: datetime | None,
) -> dict[str, Any]:
    generated_at = analytics._utcnow()
    safe_filters = {
        "tenant_code": tenant_code,
        **_progress_health_filters(filters),
    }
    source_warnings = REFERRAL_SAAS_REPORT_CATALOG[REPORT_PROGRESS_EVENT_HEALTH].get(
        "source_warnings", []
    )

    try:
        async with db_connection() as conn:
            recorded_rows = await conn.fetch(
                """
                SELECT
                    e.event_type,
                    e.source_system,
                    COUNT(*)::int AS recorded_count
                FROM referral_progress_events e
                JOIN referral_instances ri
                  ON ri.referral_track_id = e.referral_track_id
                WHERE ri.tenant_code = $1
                  AND ($2::text IS NULL OR e.event_type = $2)
                  AND ($3::text IS NULL OR e.source_system = $3)
                  AND ($4::timestamptz IS NULL OR e.occurred_at >= $4)
                  AND ($5::timestamptz IS NULL OR e.occurred_at < $5)
                GROUP BY e.event_type, e.source_system
                ORDER BY e.event_type, e.source_system
                """,
                tenant_code,
                safe_filters.get("event_type"),
                safe_filters.get("source_system"),
                data_window_start,
                data_window_end,
            )
            failure_rows = await conn.fetch(
                """
                SELECT
                    f.event_type,
                    f.source_system,
                    f.failure_category,
                    f.status,
                    COUNT(*)::int AS failed_count,
                    COALESCE(SUM(f.retry_count), 0)::int AS retry_attempt_count
                FROM referral_event_failures f
                JOIN referral_instances ri
                  ON ri.referral_track_id = f.referral_track_id
                WHERE ri.tenant_code = $1
                  AND ($2::text IS NULL OR f.event_type = $2)
                  AND ($3::text IS NULL OR f.source_system = $3)
                  AND ($4::text IS NULL OR f.failure_category = $4)
                  AND ($5::text IS NULL OR f.status = $5)
                  AND ($6::timestamptz IS NULL OR f.first_failed_at >= $6)
                  AND ($7::timestamptz IS NULL OR f.first_failed_at < $7)
                GROUP BY f.event_type, f.source_system, f.failure_category, f.status
                ORDER BY f.event_type, f.source_system, f.failure_category, f.status
                """,
                tenant_code,
                safe_filters.get("event_type"),
                safe_filters.get("source_system"),
                safe_filters.get("failure_category"),
                safe_filters.get("status"),
                data_window_start,
                data_window_end,
            )
    except Exception:
        source_report = {
            "report_type": SOURCE_PROGRESS_EVENT_HEALTH,
            "tenant_scope": tenant_code,
            "external_tenant_ref": None,
            "filters": safe_filters,
            "dimensions": dimensions,
            "metric_class": analytics.METRIC_OPERATIONAL,
            "metrics": [],
            "data_window_start": analytics._iso(data_window_start),
            "data_window_end": analytics._iso(data_window_end),
            "generated_at": analytics._iso(generated_at),
            "freshness": analytics._freshness(
                status=analytics.FRESHNESS_UNAVAILABLE,
                generated_at=generated_at,
                source_family=SOURCE_PROGRESS_EVENT_HEALTH,
                data_window_start=data_window_start,
                data_window_end=data_window_end,
            ),
            "source_warnings": [
                {
                    "code": "SOURCE_UNAVAILABLE",
                    "severity": "WARNING",
                    "source": SOURCE_PROGRESS_EVENT_HEALTH,
                    "message": "Progress event health source could not be read safely.",
                },
                *source_warnings,
            ],
            "redactions": redactions,
            "reconciliation_status": "NOT_APPLICABLE",
        }
        return source_report

    metrics: list[dict[str, Any]] = []
    for row in recorded_rows:
        row_data = dict(row)
        event_type = row_data.get("event_type")
        source_system = row_data.get("source_system")
        metrics.append(
            _report_metric(
                name="progress.events_recorded_count",
                value=row_data.get("recorded_count"),
                source=SOURCE_PROGRESS_EVENT_HEALTH,
                dimensions={
                    "event_family": "progress",
                    "event_type": event_type,
                    "source_system": source_system,
                    "ingestion_state": "RECORDED",
                    "metric_name": "progress.events_recorded_count",
                },
            )
        )

    for row in failure_rows:
        row_data = dict(row)
        event_type = row_data.get("event_type")
        source_system = row_data.get("source_system")
        failure_category = row_data.get("failure_category")
        status = row_data.get("status")
        base_dimensions = {
            "event_family": "progress",
            "event_type": event_type,
            "source_system": source_system,
            "failure_category": failure_category,
            "ingestion_state": status,
        }
        metrics.extend(
            [
                _report_metric(
                    name="progress.events_failed_count",
                    value=row_data.get("failed_count"),
                    source=SOURCE_PROGRESS_EVENT_HEALTH,
                    dimensions={
                        **base_dimensions,
                        "metric_name": "progress.events_failed_count",
                    },
                ),
                _report_metric(
                    name="progress.retry_attempt_count",
                    value=row_data.get("retry_attempt_count"),
                    source=SOURCE_PROGRESS_EVENT_HEALTH,
                    dimensions={
                        **base_dimensions,
                        "metric_name": "progress.retry_attempt_count",
                    },
                ),
            ]
        )
        if status == "OPEN":
            metrics.append(
                _report_metric(
                    name="progress.events_open_failure_count",
                    value=row_data.get("failed_count"),
                    source=SOURCE_PROGRESS_EVENT_HEALTH,
                    dimensions={
                        **base_dimensions,
                        "metric_name": "progress.events_open_failure_count",
                    },
                )
            )
        if status == "RESOLVED":
            metrics.append(
                _report_metric(
                    name="progress.events_resolved_failure_count",
                    value=row_data.get("failed_count"),
                    source=SOURCE_PROGRESS_EVENT_HEALTH,
                    dimensions={
                        **base_dimensions,
                        "metric_name": "progress.events_resolved_failure_count",
                    },
                )
            )

    return {
        "report_type": SOURCE_PROGRESS_EVENT_HEALTH,
        "tenant_scope": tenant_code,
        "external_tenant_ref": None,
        "filters": safe_filters,
        "dimensions": dimensions,
        "metric_class": analytics.METRIC_OPERATIONAL,
        "metrics": metrics,
        "data_window_start": analytics._iso(data_window_start),
        "data_window_end": analytics._iso(data_window_end),
        "generated_at": analytics._iso(generated_at),
        "freshness": analytics._freshness(
            status=analytics.FRESHNESS_FRESH,
            generated_at=generated_at,
            source_family=SOURCE_PROGRESS_EVENT_HEALTH,
            data_window_start=data_window_start,
            data_window_end=data_window_end,
        ),
        "source_warnings": source_warnings,
        "redactions": redactions,
        "reconciliation_status": "NOT_APPLICABLE",
    }


async def get_referral_saas_report(
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
    safe_filters, redactions = _safe_filters(report_type=report, filters=filters)
    config = REFERRAL_SAAS_REPORT_CATALOG[report]

    if report == REPORT_PROGRESS_EVENT_HEALTH:
        source_report = await _progress_event_health_report(
            tenant_code=tenant,
            dimensions=resolved_dimensions,
            filters=safe_filters,
            redactions=redactions,
            data_window_start=data_window_start,
            data_window_end=data_window_end,
        )
        return {
            "report_type": report,
            "source_report_type": source_report["report_type"],
            "tenant_scope": source_report["tenant_scope"],
            "external_tenant_ref": source_report.get("external_tenant_ref"),
            "filters": source_report["filters"],
            "dimensions": resolved_dimensions,
            "metric_class": config["metric_class"],
            "metrics": source_report["metrics"],
            "data_window_start": source_report["data_window_start"],
            "data_window_end": source_report["data_window_end"],
            "generated_at": source_report["generated_at"],
            "freshness": source_report["freshness"],
            "source_warnings": source_report["source_warnings"],
            "redactions": source_report["redactions"],
            "reconciliation_status": source_report["reconciliation_status"],
            "catalog_status": config["status"],
            "export_status": STATUS_NOT_IMPLEMENTED,
        }

    source_report = await analytics.get_tenant_safe_analytics_report(
        tenant_code=tenant,
        report_type=config["source_report_type"],
        dimensions=["tenant_code", "campaign_code", "metric_name"],
        filters=_analytics_filters(safe_filters),
        data_window_start=data_window_start,
        data_window_end=data_window_end,
    )

    metrics = [
        metric
        for metric in (
            _product_metric(report, metric) for metric in source_report["metrics"]
        )
        if metric is not None
    ]
    product_filters = {
        key: value
        for key, value in safe_filters.items()
        if key in {"campaign_ref", "campaign_code", "sponsor_code"}
    }

    return {
        "report_type": report,
        "source_report_type": source_report["report_type"],
        "tenant_scope": source_report["tenant_scope"],
        "external_tenant_ref": source_report.get("external_tenant_ref"),
        "filters": product_filters,
        "dimensions": resolved_dimensions,
        "metric_class": config["metric_class"],
        "metrics": metrics,
        "data_window_start": source_report["data_window_start"],
        "data_window_end": source_report["data_window_end"],
        "generated_at": source_report["generated_at"],
        "freshness": source_report["freshness"],
        "source_warnings": _source_warnings(report, source_report),
        "redactions": sorted(set([*redactions, *source_report["redactions"]])),
        "reconciliation_status": "NOT_APPLICABLE",
        "catalog_status": config["status"],
        "export_status": STATUS_NOT_IMPLEMENTED,
    }
