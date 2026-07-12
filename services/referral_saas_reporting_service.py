from __future__ import annotations

import csv
import io
import json
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
STATUS_PREVIEW_READY = "PREVIEW_READY"
STATUS_VALIDATED_NOT_CREATED = "VALIDATED_NOT_CREATED"
EXPORT_FORMAT_CSV = "csv"
EXPORT_FORMAT_JSON = "json"
EXPORT_REDACTION_PROFILE_TENANT_SAFE = "tenant_safe"
DEFAULT_EXPORT_ROW_LIMIT = 10000
MAX_EXPORT_ROW_LIMIT = 50000
SOURCE_PROGRESS_EVENT_HEALTH = "referral_progress_event_health"
SOURCE_ATTRIBUTION_QUALITY = "referral_attribution_quality"
SOURCE_SAFE_STATUS_DISTRIBUTION = "referral_safe_status_distribution"
SOURCE_LINK_CODE_PERFORMANCE = "referral_link_code_performance"
SOURCE_REWARD_VISIBILITY_SUMMARY = "referral_reward_visibility_summary"

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
    "beneficiary_ref",
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
                    "overview metrics; validation-state and "
                    "progress-milestone stage counts need dedicated follow-up "
                    "report sources before they can be promised."
                ),
            }
        ],
    },
    REPORT_LINK_CODE_PERFORMANCE: {
        "status": STATUS_AVAILABLE,
        "source_report_type": SOURCE_LINK_CODE_PERFORMANCE,
        "metric_class": analytics.METRIC_OPERATIONAL,
        "allowed_dimensions": {
            "campaign_ref",
            "campaign_code",
            "issued_period",
            "link_code_status",
            "metric_name",
            "resolved_period",
            "source_type",
        },
        "default_dimensions": ["source_type", "link_code_status", "metric_name"],
        "allowed_filters": {"campaign_ref", "campaign_code", "link_code_status", "source_type"},
        "source_warnings": [
            {
                "code": "PARTIAL_SOURCE_COVERAGE",
                "message": (
                    "Link/code performance uses durable referral code, campaign "
                    "code, campaign-referral link, and route-referral link "
                    "sources. Composite-code compatibility evidence is not "
                    "durable enough for aggregate reporting yet."
                ),
            }
        ],
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
        "status": STATUS_AVAILABLE,
        "source_report_type": SOURCE_ATTRIBUTION_QUALITY,
        "metric_class": "DERIVED_STATUS",
        "allowed_dimensions": {
            "attribution_source",
            "campaign_ref",
            "campaign_code",
            "metric_name",
            "source_confidence",
            "trace_status",
            "warning_code",
        },
        "default_dimensions": ["trace_status", "source_confidence", "metric_name"],
        "allowed_filters": {
            "campaign_ref",
            "campaign_code",
            "source_confidence",
            "trace_status",
        },
        "source_warnings": [
            {
                "code": "DERIVED_TRACE_STATUS",
                "message": (
                    "Attribution quality uses current referral, campaign-link, "
                    "and route-link evidence to derive aggregate trace status; "
                    "it does not expose raw outcome trace payloads."
                ),
            }
        ],
    },
    REPORT_SAFE_STATUS_DISTRIBUTION: {
        "status": STATUS_AVAILABLE,
        "source_report_type": SOURCE_SAFE_STATUS_DISTRIBUTION,
        "metric_class": "DERIVED_STATUS",
        "allowed_dimensions": {
            "action_category",
            "metric_name",
            "product_status",
            "safe_status",
            "source_family",
            "viewer_role",
        },
        "default_dimensions": ["viewer_role", "product_status", "metric_name"],
        "allowed_filters": {
            "action_category",
            "product_status",
            "safe_status",
            "viewer_role",
        },
        "source_warnings": [
            {
                "code": "DERIVED_SAFE_STATUS",
                "message": (
                    "Safe-status distribution is derived from tenant-scoped "
                    "referral outcome evidence using the Referral SaaS safe "
                    "status projection vocabulary; it does not expose raw "
                    "viewer, UCN, reward, audit, provider, or money evidence."
                ),
            }
        ],
    },
    REPORT_REWARD_VISIBILITY_SUMMARY: {
        "status": STATUS_AVAILABLE,
        "source_report_type": SOURCE_REWARD_VISIBILITY_SUMMARY,
        "metric_class": analytics.METRIC_OPERATIONAL,
        "allowed_dimensions": {
            "beneficiary_type",
            "metric_name",
            "product",
            "reward_source",
            "reward_status",
            "reward_type",
            "source_family",
            "sub_product",
            "visibility_period",
        },
        "default_dimensions": ["reward_status", "beneficiary_type", "metric_name"],
        "allowed_filters": {
            "beneficiary_type",
            "product",
            "reward_source",
            "reward_status",
            "reward_type",
            "sub_product",
        },
        "source_warnings": [
            {
                "code": "COUNT_ONLY_REWARD_VISIBILITY",
                "message": (
                    "Reward visibility summary reports counts only. Reward "
                    "amount totals, fulfilment, funding, settlement, wallet, "
                    "commission, invoice, and payout evidence remain outside "
                    "this Referral SaaS report."
                ),
            },
            {
                "code": "PENDING_MISSION_BONUS_DERIVED",
                "message": (
                    "Pending mission bonus counts are derived from incomplete "
                    "mission progress with active bonus definitions; no money "
                    "totals are exposed."
                ),
            },
        ],
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


def _normalise_export_format(export_format: str | None) -> str:
    value = str(export_format or EXPORT_FORMAT_JSON).strip().lower()
    if value not in {EXPORT_FORMAT_JSON, EXPORT_FORMAT_CSV}:
        raise ValueError(f"Unsupported Referral SaaS export format: {export_format}")
    return value


def _normalise_redaction_profile(redaction_profile: str | None) -> str:
    value = str(
        redaction_profile or EXPORT_REDACTION_PROFILE_TENANT_SAFE
    ).strip().lower()
    if value != EXPORT_REDACTION_PROFILE_TENANT_SAFE:
        raise ValueError(
            f"Unsupported Referral SaaS export redaction_profile: {redaction_profile}"
        )
    return value


def _normalise_export_row_limit(row_limit: int | None) -> int:
    if row_limit is None:
        return DEFAULT_EXPORT_ROW_LIMIT
    try:
        value = int(row_limit)
    except (TypeError, ValueError) as exc:
        raise ValueError("Referral SaaS export row_limit must be an integer") from exc
    if value < 1 or value > MAX_EXPORT_ROW_LIMIT:
        raise ValueError(
            "Referral SaaS export row_limit must be between "
            f"1 and {MAX_EXPORT_ROW_LIMIT}"
        )
    return value


def _validate_data_window(
    *,
    data_window_start: datetime | None,
    data_window_end: datetime | None,
) -> None:
    if (
        data_window_start is not None
        and data_window_end is not None
        and data_window_end <= data_window_start
    ):
        raise ValueError("data_window_end must be after data_window_start")


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


def validate_referral_saas_report_export_request(
    *,
    tenant_code: str,
    report_type: str,
    export_format: str | None = None,
    redaction_profile: str | None = None,
    dimensions: list[str] | None = None,
    filters: dict[str, Any] | None = None,
    row_limit: int | None = None,
    data_window_start: datetime | None = None,
    data_window_end: datetime | None = None,
) -> dict[str, Any]:
    tenant = _normalise_tenant_code(tenant_code)
    report = _normalise_report_type(report_type)
    resolved_dimensions = _normalise_dimensions(report, dimensions)
    safe_filters, redactions = _safe_filters(report_type=report, filters=filters)
    resolved_format = _normalise_export_format(export_format)
    resolved_redaction_profile = _normalise_redaction_profile(redaction_profile)
    resolved_row_limit = _normalise_export_row_limit(row_limit)
    _validate_data_window(
        data_window_start=data_window_start,
        data_window_end=data_window_end,
    )
    config = REFERRAL_SAAS_REPORT_CATALOG[report]

    return {
        "tenant_scope": tenant,
        "report_type": report,
        "source_report_type": config["source_report_type"],
        "metric_class": config["metric_class"],
        "dimensions": resolved_dimensions,
        "filters": safe_filters,
        "redactions": sorted(set(redactions)),
        "export_format": resolved_format,
        "redaction_profile": resolved_redaction_profile,
        "row_limit": resolved_row_limit,
        "data_window_start": data_window_start,
        "data_window_end": data_window_end,
        "catalog_status": config["status"],
        "export_status": STATUS_VALIDATED_NOT_CREATED,
        "creation_status": STATUS_NOT_IMPLEMENTED,
        "storage_status": STATUS_NOT_IMPLEMENTED,
        "delivery_status": STATUS_NOT_IMPLEMENTED,
        "audit_status": STATUS_NOT_IMPLEMENTED,
        "guardrail": (
            "Export request validated only. No export file, storage record, "
            "delivery job, scheduled export, audit row, invoice, billing event, "
            "or reward/funding/fulfilment/settlement mutation was created."
        ),
    }


def _export_rows(report: dict[str, Any], row_limit: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for metric in report.get("metrics", [])[:row_limit]:
        rows.append(
            {
                "metric_name": metric.get("name"),
                "value": metric.get("value"),
                "unit": metric.get("unit"),
                "metric_class": metric.get("metric_class"),
                "source": metric.get("source"),
                "dimensions": metric.get("dimensions") or {},
            }
        )
    return rows


def _csv_payload(rows: list[dict[str, Any]]) -> str:
    buffer = io.StringIO()
    writer = csv.DictWriter(
        buffer,
        fieldnames=[
            "metric_name",
            "value",
            "unit",
            "metric_class",
            "source",
            "dimensions",
        ],
        lineterminator="\n",
    )
    writer.writeheader()
    for row in rows:
        writer.writerow(
            {
                **row,
                "dimensions": json.dumps(row["dimensions"], sort_keys=True),
            }
        )
    return buffer.getvalue()


async def build_referral_saas_report_export_preview(
    *,
    tenant_code: str,
    report_type: str,
    export_format: str | None = None,
    redaction_profile: str | None = None,
    dimensions: list[str] | None = None,
    filters: dict[str, Any] | None = None,
    row_limit: int | None = None,
    data_window_start: datetime | None = None,
    data_window_end: datetime | None = None,
) -> dict[str, Any]:
    export_request = validate_referral_saas_report_export_request(
        tenant_code=tenant_code,
        report_type=report_type,
        export_format=export_format,
        redaction_profile=redaction_profile,
        dimensions=dimensions,
        filters=filters,
        row_limit=row_limit,
        data_window_start=data_window_start,
        data_window_end=data_window_end,
    )
    report = await get_referral_saas_report(
        tenant_code=export_request["tenant_scope"],
        report_type=export_request["report_type"],
        dimensions=export_request["dimensions"],
        filters=export_request["filters"],
        data_window_start=data_window_start,
        data_window_end=data_window_end,
    )
    rows = _export_rows(report, export_request["row_limit"])
    metadata = {
        "tenant_scope": report["tenant_scope"],
        "report_type": report["report_type"],
        "source_report_type": report["source_report_type"],
        "metric_class": report["metric_class"],
        "dimensions": report["dimensions"],
        "filters": report["filters"],
        "data_window_start": report["data_window_start"],
        "data_window_end": report["data_window_end"],
        "generated_at": report["generated_at"],
        "freshness": report["freshness"],
        "source_warnings": report["source_warnings"],
        "redactions": sorted(
            set([*export_request["redactions"], *report.get("redactions", [])])
        ),
        "reconciliation_status": report["reconciliation_status"],
        "row_limit": export_request["row_limit"],
        "row_count": len(rows),
    }

    if export_request["export_format"] == EXPORT_FORMAT_CSV:
        payload: Any = _csv_payload(rows)
        content_type = "text/csv"
        file_extension = "csv"
    else:
        payload = {
            "metadata": metadata,
            "rows": rows,
        }
        content_type = "application/json"
        file_extension = "json"

    return {
        "export_request": export_request,
        "report": report,
        "preview": {
            "status": STATUS_PREVIEW_READY,
            "export_format": export_request["export_format"],
            "content_type": content_type,
            "file_extension": file_extension,
            "metadata": metadata,
            "payload": payload,
        },
        "creation_status": STATUS_NOT_IMPLEMENTED,
        "storage_status": STATUS_NOT_IMPLEMENTED,
        "delivery_status": STATUS_NOT_IMPLEMENTED,
        "audit_status": STATUS_NOT_IMPLEMENTED,
        "guardrail": (
            "Inline export preview only. No export file, storage record, "
            "delivery job, scheduled export, audit row, retention record, "
            "download URL, invoice, billing event, or reward/funding/"
            "fulfilment/settlement mutation was created."
        ),
    }


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


def _link_code_performance_filters(filters: dict[str, str]) -> dict[str, str]:
    if "campaign_ref" in filters and "campaign_code" not in filters:
        filters = {**filters, "campaign_code": filters["campaign_ref"]}
    return {
        key: value
        for key, value in {
            "campaign_ref": filters.get("campaign_ref"),
            "campaign_code": filters.get("campaign_code"),
            "link_code_status": filters.get("link_code_status"),
            "source_type": filters.get("source_type"),
        }.items()
        if value
    }


def _attribution_quality_filters(filters: dict[str, str]) -> dict[str, str]:
    if "campaign_ref" in filters and "campaign_code" not in filters:
        filters = {**filters, "campaign_code": filters["campaign_ref"]}
    return {
        key: value
        for key, value in {
            "campaign_ref": filters.get("campaign_ref"),
            "campaign_code": filters.get("campaign_code"),
            "source_confidence": filters.get("source_confidence"),
            "trace_status": filters.get("trace_status"),
        }.items()
        if value
    }


def _safe_status_distribution_filters(filters: dict[str, str]) -> dict[str, str]:
    return {
        key: value
        for key, value in {
            "action_category": filters.get("action_category"),
            "product_status": filters.get("product_status"),
            "safe_status": filters.get("safe_status"),
            "viewer_role": filters.get("viewer_role"),
        }.items()
        if value
    }


def _reward_visibility_filters(filters: dict[str, str]) -> dict[str, str]:
    return {
        key: value
        for key, value in {
            "beneficiary_type": filters.get("beneficiary_type"),
            "product": filters.get("product"),
            "reward_source": filters.get("reward_source"),
            "reward_status": filters.get("reward_status"),
            "reward_type": filters.get("reward_type"),
            "sub_product": filters.get("sub_product"),
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
    metric_class: str = analytics.METRIC_OPERATIONAL,
) -> dict[str, Any]:
    return {
        "name": name,
        "value": int(value or 0),
        "unit": unit,
        "metric_class": metric_class,
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


async def _link_code_performance_report(
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
        **_link_code_performance_filters(filters),
    }
    source_warnings = REFERRAL_SAAS_REPORT_CATALOG[REPORT_LINK_CODE_PERFORMANCE].get(
        "source_warnings", []
    )

    try:
        async with db_connection() as conn:
            link_rows = await conn.fetch(
                """
                WITH link_sources AS (
                    SELECT
                        'REFERRAL_CODE' AS source_type,
                        'ISSUED' AS link_code_status,
                        NULL::text AS campaign_code,
                        date_trunc('day', rc.created_at)::date::text AS issued_period,
                        NULL::text AS resolved_period,
                        rc.created_at AS source_created_at
                    FROM referrer_codes rc
                    WHERE rc.tenant_code = $1

                    UNION ALL

                    SELECT
                        'CAMPAIGN_CODE' AS source_type,
                        CASE
                            WHEN mc.is_active IS NOT TRUE THEN 'INVALID'
                            WHEN mc.ends_at IS NOT NULL AND mc.ends_at < NOW()
                                THEN 'EXPIRED'
                            WHEN mc.max_uses IS NOT NULL
                             AND mc.uses_count >= mc.max_uses THEN 'INVALID'
                            ELSE 'ISSUED'
                        END AS link_code_status,
                        mc.campaign_code,
                        date_trunc('day', mc.created_at)::date::text AS issued_period,
                        NULL::text AS resolved_period,
                        mc.created_at AS source_created_at
                    FROM marketing_campaigns mc
                    WHERE mc.tenant_code = $1

                    UNION ALL

                    SELECT
                        'CAMPAIGN_REFERRAL_LINK' AS source_type,
                        'LINKED' AS link_code_status,
                        ca.campaign_code,
                        date_trunc('day', crl.created_at)::date::text AS issued_period,
                        date_trunc('day', crl.created_at)::date::text AS resolved_period,
                        crl.created_at AS source_created_at
                    FROM campaign_referral_links crl
                    JOIN campaign_attributions ca
                      ON ca.campaign_track_id = crl.campaign_track_id
                    WHERE ca.tenant_code = $1

                    UNION ALL

                    SELECT
                        'ROUTE_REFERRAL_LINK' AS source_type,
                        CASE
                            WHEN drl.link_status = 'VOIDED' THEN 'VOIDED'
                            ELSE 'ACTIVE'
                        END AS link_code_status,
                        o.campaign_code,
                        date_trunc('day', drl.created_at)::date::text AS issued_period,
                        CASE
                            WHEN drl.link_status = 'VOIDED'
                                THEN date_trunc('day', drl.updated_at)::date::text
                            ELSE NULL::text
                        END AS resolved_period,
                        drl.created_at AS source_created_at
                    FROM distribution_route_referral_links drl
                    LEFT JOIN distribution_opportunities o
                      ON o.opportunity_id = drl.opportunity_id
                     AND o.tenant_code = drl.tenant_code
                    WHERE drl.tenant_code = $1
                )
                SELECT
                    source_type,
                    link_code_status,
                    campaign_code,
                    issued_period,
                    resolved_period,
                    COUNT(*)::int AS link_code_count
                FROM link_sources
                WHERE ($2::text IS NULL OR campaign_code = $2)
                  AND ($3::text IS NULL OR source_type = $3)
                  AND ($4::text IS NULL OR link_code_status = $4)
                  AND ($5::timestamptz IS NULL OR source_created_at >= $5)
                  AND ($6::timestamptz IS NULL OR source_created_at < $6)
                GROUP BY
                    source_type,
                    link_code_status,
                    campaign_code,
                    issued_period,
                    resolved_period
                ORDER BY source_type, link_code_status, campaign_code
                """,
                tenant_code,
                safe_filters.get("campaign_code"),
                safe_filters.get("source_type"),
                safe_filters.get("link_code_status"),
                data_window_start,
                data_window_end,
            )
    except Exception:
        return {
            "report_type": SOURCE_LINK_CODE_PERFORMANCE,
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
                source_family=SOURCE_LINK_CODE_PERFORMANCE,
                data_window_start=data_window_start,
                data_window_end=data_window_end,
            ),
            "source_warnings": [
                {
                    "code": "SOURCE_UNAVAILABLE",
                    "severity": "WARNING",
                    "source": SOURCE_LINK_CODE_PERFORMANCE,
                    "message": "Link/code performance source could not be read safely.",
                },
                *source_warnings,
            ],
            "redactions": redactions,
            "reconciliation_status": "NOT_APPLICABLE",
        }

    metric_name_by_status = {
        "ACTIVE": "link_codes.active_count",
        "EXPIRED": "link_codes.expired_count",
        "INVALID": "link_codes.invalid_count",
        "ISSUED": "link_codes.issued_count",
        "LINKED": "link_codes.linked_count",
        "VOIDED": "link_codes.voided_count",
    }
    metrics: list[dict[str, Any]] = []
    for row in link_rows:
        row_data = dict(row)
        link_code_status = row_data.get("link_code_status")
        metric_name = metric_name_by_status.get(
            link_code_status, "link_codes.unknown_count"
        )
        campaign_code = row_data.get("campaign_code")
        metrics.append(
            _report_metric(
                name=metric_name,
                value=row_data.get("link_code_count"),
                source=SOURCE_LINK_CODE_PERFORMANCE,
                dimensions={
                    "campaign_code": campaign_code,
                    "campaign_ref": campaign_code,
                    "issued_period": row_data.get("issued_period"),
                    "link_code_status": link_code_status,
                    "metric_name": metric_name,
                    "resolved_period": row_data.get("resolved_period"),
                    "source_type": row_data.get("source_type"),
                },
            )
        )

    return {
        "report_type": SOURCE_LINK_CODE_PERFORMANCE,
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
            source_family=SOURCE_LINK_CODE_PERFORMANCE,
            data_window_start=data_window_start,
            data_window_end=data_window_end,
        ),
        "source_warnings": source_warnings,
        "redactions": redactions,
        "reconciliation_status": "NOT_APPLICABLE",
    }


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
        return {
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


async def _attribution_quality_report(
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
        **_attribution_quality_filters(filters),
    }
    source_warnings = REFERRAL_SAAS_REPORT_CATALOG[REPORT_ATTRIBUTION_QUALITY].get(
        "source_warnings", []
    )

    try:
        async with db_connection() as conn:
            quality_rows = await conn.fetch(
                """
                WITH base AS (
                    SELECT
                        ri.referral_track_id,
                        ri.status AS referral_status,
                        COALESCE(ri.is_complete, false) AS is_complete,
                        COALESCE(ca.campaign_code, o.campaign_code) AS campaign_code,
                        crl.campaign_track_id,
                        ca.status AS campaign_track_status,
                        drl.route_id,
                        drl.link_status AS route_link_status,
                        CASE
                            WHEN crl.campaign_track_id IS NOT NULL
                             AND drl.route_id IS NOT NULL
                                THEN 'INCONSISTENT'
                            WHEN crl.campaign_track_id IS NOT NULL
                              OR drl.route_id IS NOT NULL
                                THEN CASE
                                    WHEN COALESCE(ri.is_complete, false)
                                      OR ri.status = 'COMPLETED'
                                        THEN 'COMPLETE'
                                    ELSE 'PARTIAL'
                                END
                            WHEN COALESCE(ri.is_complete, false)
                              OR ri.status = 'COMPLETED'
                                THEN 'MISSING_EVIDENCE'
                            ELSE 'UNATTRIBUTED'
                        END AS trace_status,
                        CASE
                            WHEN crl.campaign_track_id IS NOT NULL
                             AND drl.route_id IS NOT NULL
                                THEN 'CONFLICT'
                            WHEN crl.campaign_track_id IS NOT NULL
                              OR drl.route_id IS NOT NULL
                                THEN CASE
                                    WHEN COALESCE(ri.is_complete, false)
                                      OR ri.status = 'COMPLETED'
                                        THEN 'HIGH'
                                    ELSE 'MEDIUM'
                                END
                            ELSE 'LOW'
                        END AS source_confidence,
                        CASE
                            WHEN crl.campaign_track_id IS NOT NULL
                             AND drl.route_id IS NOT NULL
                                THEN 'SOURCE_CONFLICT'
                            WHEN (COALESCE(ri.is_complete, false)
                               OR ri.status = 'COMPLETED')
                              AND crl.campaign_track_id IS NULL
                              AND drl.route_id IS NULL
                                THEN 'NO_SOURCE_EVIDENCE'
                            ELSE NULL
                        END AS warning_code,
                        CASE
                            WHEN crl.campaign_track_id IS NOT NULL
                             AND drl.route_id IS NOT NULL
                                THEN 'MULTIPLE'
                            WHEN crl.campaign_track_id IS NOT NULL
                                THEN 'CAMPAIGN_REFERRAL_LINK'
                            WHEN drl.route_id IS NOT NULL
                                THEN 'ROUTE_REFERRAL_LINK'
                            ELSE 'NONE'
                        END AS attribution_source,
                        ri.created_at
                    FROM referral_instances ri
                    LEFT JOIN campaign_referral_links crl
                      ON crl.referral_track_id = ri.referral_track_id
                    LEFT JOIN campaign_attributions ca
                      ON ca.campaign_track_id = crl.campaign_track_id
                     AND ca.tenant_code = ri.tenant_code
                    LEFT JOIN distribution_route_referral_links drl
                      ON drl.referral_track_id = ri.referral_track_id
                     AND drl.tenant_code = ri.tenant_code
                    LEFT JOIN distribution_opportunities o
                      ON o.opportunity_id = drl.opportunity_id
                     AND o.tenant_code = ri.tenant_code
                    WHERE ri.tenant_code = $1
                      AND ($2::text IS NULL OR COALESCE(ca.campaign_code, o.campaign_code) = $2)
                      AND ($3::timestamptz IS NULL OR ri.created_at >= $3)
                      AND ($4::timestamptz IS NULL OR ri.created_at < $4)
                )
                SELECT
                    trace_status,
                    source_confidence,
                    warning_code,
                    attribution_source,
                    campaign_code,
                    COUNT(*)::int AS outcome_count
                FROM base
                WHERE ($5::text IS NULL OR trace_status = $5)
                  AND ($6::text IS NULL OR source_confidence = $6)
                GROUP BY
                    trace_status,
                    source_confidence,
                    warning_code,
                    attribution_source,
                    campaign_code
                ORDER BY trace_status, source_confidence, attribution_source
                """,
                tenant_code,
                safe_filters.get("campaign_code"),
                data_window_start,
                data_window_end,
                safe_filters.get("trace_status"),
                safe_filters.get("source_confidence"),
            )
    except Exception:
        return {
            "report_type": SOURCE_ATTRIBUTION_QUALITY,
            "tenant_scope": tenant_code,
            "external_tenant_ref": None,
            "filters": safe_filters,
            "dimensions": dimensions,
            "metric_class": "DERIVED_STATUS",
            "metrics": [],
            "data_window_start": analytics._iso(data_window_start),
            "data_window_end": analytics._iso(data_window_end),
            "generated_at": analytics._iso(generated_at),
            "freshness": analytics._freshness(
                status=analytics.FRESHNESS_UNAVAILABLE,
                generated_at=generated_at,
                source_family=SOURCE_ATTRIBUTION_QUALITY,
                data_window_start=data_window_start,
                data_window_end=data_window_end,
            ),
            "source_warnings": [
                {
                    "code": "SOURCE_UNAVAILABLE",
                    "severity": "WARNING",
                    "source": SOURCE_ATTRIBUTION_QUALITY,
                    "message": "Attribution quality source could not be read safely.",
                },
                *source_warnings,
            ],
            "redactions": redactions,
            "reconciliation_status": "NOT_APPLICABLE",
        }

    metrics: list[dict[str, Any]] = []
    metric_name_by_status = {
        "COMPLETE": "attribution.complete_count",
        "PARTIAL": "attribution.partial_count",
        "MISSING_EVIDENCE": "attribution.missing_evidence_count",
        "INCONSISTENT": "attribution.inconsistent_count",
        "UNATTRIBUTED": "attribution.unattributed_count",
    }
    for row in quality_rows:
        row_data = dict(row)
        trace_status = row_data.get("trace_status")
        metric_name = metric_name_by_status.get(
            trace_status, "attribution.unavailable_count"
        )
        campaign_code = row_data.get("campaign_code")
        metrics.append(
            _report_metric(
                name=metric_name,
                value=row_data.get("outcome_count"),
                source=SOURCE_ATTRIBUTION_QUALITY,
                metric_class="DERIVED_STATUS",
                dimensions={
                    "attribution_source": row_data.get("attribution_source"),
                    "campaign_code": campaign_code,
                    "campaign_ref": campaign_code,
                    "metric_name": metric_name,
                    "source_confidence": row_data.get("source_confidence"),
                    "trace_status": trace_status,
                    "warning_code": row_data.get("warning_code"),
                },
            )
        )

    return {
        "report_type": SOURCE_ATTRIBUTION_QUALITY,
        "tenant_scope": tenant_code,
        "external_tenant_ref": None,
        "filters": safe_filters,
        "dimensions": dimensions,
        "metric_class": "DERIVED_STATUS",
        "metrics": metrics,
        "data_window_start": analytics._iso(data_window_start),
        "data_window_end": analytics._iso(data_window_end),
        "generated_at": analytics._iso(generated_at),
        "freshness": analytics._freshness(
            status=analytics.FRESHNESS_FRESH,
            generated_at=generated_at,
            source_family=SOURCE_ATTRIBUTION_QUALITY,
            data_window_start=data_window_start,
            data_window_end=data_window_end,
        ),
        "source_warnings": source_warnings,
        "redactions": redactions,
        "reconciliation_status": "NOT_APPLICABLE",
    }


async def _safe_status_distribution_report(
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
        **_safe_status_distribution_filters(filters),
    }
    source_warnings = REFERRAL_SAAS_REPORT_CATALOG[
        REPORT_SAFE_STATUS_DISTRIBUTION
    ].get("source_warnings", [])

    try:
        async with db_connection() as conn:
            status_rows = await conn.fetch(
                """
                WITH base AS (
                    SELECT
                        COALESCE(NULLIF($2::text, ''), 'referrer') AS viewer_role,
                        'outcome' AS source_family,
                        CASE
                            WHEN COALESCE(ri.is_complete, false)
                              OR ri.status IN ('COMPLETED', 'COMPLETE')
                                THEN 'FULFILLED'
                            WHEN ri.status = 'VALIDATED'
                                THEN 'PENDING'
                            WHEN ri.status IN (
                                'UCN_CAPTURED',
                                'ACCOUNT_OPENED',
                                'ACCOUNT_ACTIVATED'
                            )
                                THEN 'IN_PROGRESS'
                            WHEN ri.status IN (
                                'FUNDED',
                                'DEBIT_ORDER_SWITCHED',
                                'SALARY_SWITCHED',
                                'FIRST_TRANSACTION_COMPLETED'
                            )
                                THEN 'QUALIFIED'
                            WHEN ri.status IN ('CANCELLED', 'FAILED')
                                THEN 'ACTION_REQUIRED'
                            ELSE 'UNAVAILABLE'
                        END AS safe_status,
                        CASE
                            WHEN COALESCE(ri.is_complete, false)
                              OR ri.status IN ('COMPLETED', 'COMPLETE')
                                THEN 'COMPLETED'
                            WHEN ri.status = 'VALIDATED'
                                THEN 'WAITING'
                            WHEN ri.status IN (
                                'UCN_CAPTURED',
                                'ACCOUNT_OPENED',
                                'ACCOUNT_ACTIVATED'
                            )
                                THEN 'IN_PROGRESS'
                            WHEN ri.status IN (
                                'FUNDED',
                                'DEBIT_ORDER_SWITCHED',
                                'SALARY_SWITCHED',
                                'FIRST_TRANSACTION_COMPLETED'
                            )
                                THEN 'QUALIFIED'
                            WHEN ri.status = 'CANCELLED'
                                THEN 'ACTION_NEEDED'
                            ELSE 'UNAVAILABLE'
                        END AS product_status,
                        CASE
                            WHEN ri.status = 'VALIDATED'
                                THEN 'WAITING_FOR_EVENT'
                            WHEN ri.status IN ('CANCELLED', 'FAILED')
                                THEN 'CONTACT_SUPPORT'
                            WHEN ri.status IS NULL
                                THEN 'NOT_AVAILABLE'
                            ELSE 'NONE'
                        END AS action_category,
                        ri.created_at
                    FROM referral_instances ri
                    WHERE ri.tenant_code = $1
                      AND ($6::timestamptz IS NULL OR ri.created_at >= $6)
                      AND ($7::timestamptz IS NULL OR ri.created_at < $7)
                )
                SELECT
                    viewer_role,
                    source_family,
                    safe_status,
                    product_status,
                    action_category,
                    COUNT(*)::int AS status_count
                FROM base
                WHERE ($3::text IS NULL OR safe_status = $3)
                  AND ($4::text IS NULL OR product_status = $4)
                  AND ($5::text IS NULL OR action_category = $5)
                GROUP BY
                    viewer_role,
                    source_family,
                    safe_status,
                    product_status,
                    action_category
                ORDER BY product_status, safe_status, action_category
                """,
                tenant_code,
                safe_filters.get("viewer_role"),
                safe_filters.get("safe_status"),
                safe_filters.get("product_status"),
                safe_filters.get("action_category"),
                data_window_start,
                data_window_end,
            )
    except Exception:
        return {
            "report_type": SOURCE_SAFE_STATUS_DISTRIBUTION,
            "tenant_scope": tenant_code,
            "external_tenant_ref": None,
            "filters": safe_filters,
            "dimensions": dimensions,
            "metric_class": "DERIVED_STATUS",
            "metrics": [],
            "data_window_start": analytics._iso(data_window_start),
            "data_window_end": analytics._iso(data_window_end),
            "generated_at": analytics._iso(generated_at),
            "freshness": analytics._freshness(
                status=analytics.FRESHNESS_UNAVAILABLE,
                generated_at=generated_at,
                source_family=SOURCE_SAFE_STATUS_DISTRIBUTION,
                data_window_start=data_window_start,
                data_window_end=data_window_end,
            ),
            "source_warnings": [
                {
                    "code": "SOURCE_UNAVAILABLE",
                    "severity": "WARNING",
                    "source": SOURCE_SAFE_STATUS_DISTRIBUTION,
                    "message": (
                        "Safe-status distribution source could not be read safely."
                    ),
                },
                *source_warnings,
            ],
            "redactions": redactions,
            "reconciliation_status": "NOT_APPLICABLE",
        }

    metrics = [
        _report_metric(
            name="status.safe_status_count",
            value=dict(row).get("status_count"),
            source=SOURCE_SAFE_STATUS_DISTRIBUTION,
            metric_class="DERIVED_STATUS",
            dimensions={
                "action_category": dict(row).get("action_category"),
                "metric_name": "status.safe_status_count",
                "product_status": dict(row).get("product_status"),
                "safe_status": dict(row).get("safe_status"),
                "source_family": dict(row).get("source_family"),
                "viewer_role": dict(row).get("viewer_role"),
            },
        )
        for row in status_rows
    ]

    return {
        "report_type": SOURCE_SAFE_STATUS_DISTRIBUTION,
        "tenant_scope": tenant_code,
        "external_tenant_ref": None,
        "filters": safe_filters,
        "dimensions": dimensions,
        "metric_class": "DERIVED_STATUS",
        "metrics": metrics,
        "data_window_start": analytics._iso(data_window_start),
        "data_window_end": analytics._iso(data_window_end),
        "generated_at": analytics._iso(generated_at),
        "freshness": analytics._freshness(
            status=analytics.FRESHNESS_FRESH,
            generated_at=generated_at,
            source_family=SOURCE_SAFE_STATUS_DISTRIBUTION,
            data_window_start=data_window_start,
            data_window_end=data_window_end,
        ),
        "source_warnings": source_warnings,
        "redactions": redactions,
        "reconciliation_status": "NOT_APPLICABLE",
    }


async def _reward_visibility_summary_report(
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
        **_reward_visibility_filters(filters),
    }
    source_warnings = REFERRAL_SAAS_REPORT_CATALOG[
        REPORT_REWARD_VISIBILITY_SUMMARY
    ].get("source_warnings", [])

    try:
        async with db_connection() as conn:
            reward_rows = await conn.fetch(
                """
                WITH reward_sources AS (
                    SELECT
                        'persisted_reward' AS source_family,
                        r.beneficiary_type,
                        r.reward_source,
                        r.reward_type,
                        r.status AS reward_status,
                        r.product,
                        r.sub_product,
                        date_trunc('day', r.created_at)::date::text
                            AS visibility_period,
                        r.created_at AS source_created_at
                    FROM rewards r
                    WHERE r.tenant_code = $1

                    UNION ALL

                    SELECT
                        'pending_mission_bonus' AS source_family,
                        ump.beneficiary_type,
                        'MISSION_BONUS' AS reward_source,
                        'BONUS' AS reward_type,
                        'PENDING' AS reward_status,
                        COALESCE(ri.product, md.product) AS product,
                        COALESCE(ri.sub_product, md.sub_product) AS sub_product,
                        date_trunc('day', ump.updated_at)::date::text
                            AS visibility_period,
                        ump.updated_at AS source_created_at
                    FROM user_mission_progress ump
                    JOIN mission_definitions md
                      ON md.mission_code = ump.mission_code
                    JOIN referral_instances ri
                      ON ri.referral_track_id = ump.referral_track_id
                    WHERE ri.tenant_code = $1
                      AND ump.is_complete = FALSE
                      AND ump.bonus_reward_applied = FALSE
                      AND md.is_active = TRUE
                      AND md.bonus_reward_amount > 0
                )
                SELECT
                    source_family,
                    beneficiary_type,
                    reward_source,
                    reward_type,
                    reward_status,
                    product,
                    sub_product,
                    visibility_period,
                    COUNT(*)::int AS reward_count
                FROM reward_sources
                WHERE ($2::text IS NULL OR beneficiary_type = $2)
                  AND ($3::text IS NULL OR reward_source = $3)
                  AND ($4::text IS NULL OR reward_status = $4)
                  AND ($5::text IS NULL OR reward_type = $5)
                  AND ($6::text IS NULL OR product = $6)
                  AND ($7::text IS NULL OR sub_product = $7)
                  AND ($8::timestamptz IS NULL OR source_created_at >= $8)
                  AND ($9::timestamptz IS NULL OR source_created_at < $9)
                GROUP BY
                    source_family,
                    beneficiary_type,
                    reward_source,
                    reward_type,
                    reward_status,
                    product,
                    sub_product,
                    visibility_period
                ORDER BY reward_status, beneficiary_type, reward_source
                """,
                tenant_code,
                safe_filters.get("beneficiary_type"),
                safe_filters.get("reward_source"),
                safe_filters.get("reward_status"),
                safe_filters.get("reward_type"),
                safe_filters.get("product"),
                safe_filters.get("sub_product"),
                data_window_start,
                data_window_end,
            )
    except Exception:
        return {
            "report_type": SOURCE_REWARD_VISIBILITY_SUMMARY,
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
                source_family=SOURCE_REWARD_VISIBILITY_SUMMARY,
                data_window_start=data_window_start,
                data_window_end=data_window_end,
            ),
            "source_warnings": [
                {
                    "code": "SOURCE_UNAVAILABLE",
                    "severity": "WARNING",
                    "source": SOURCE_REWARD_VISIBILITY_SUMMARY,
                    "message": "Reward visibility source could not be read safely.",
                },
                *source_warnings,
            ],
            "redactions": redactions,
            "reconciliation_status": "NOT_APPLICABLE",
        }

    metric_name_by_status = {
        "APPLIED": "rewards.applied_count",
        "EARNED": "rewards.earned_count",
        "FAILED": "rewards.failed_count",
        "FULFILLED": "rewards.fulfilled_count",
        "PENDING": "rewards.pending_count",
        "PENDING_FULFILMENT": "rewards.pending_fulfilment_count",
        "REVERSED": "rewards.reversed_count",
    }
    metrics: list[dict[str, Any]] = []
    for row in reward_rows:
        row_data = dict(row)
        reward_status = row_data.get("reward_status")
        metric_name = metric_name_by_status.get(
            reward_status, "rewards.visible_count"
        )
        metrics.append(
            _report_metric(
                name=metric_name,
                value=row_data.get("reward_count"),
                source=SOURCE_REWARD_VISIBILITY_SUMMARY,
                dimensions={
                    "beneficiary_type": row_data.get("beneficiary_type"),
                    "metric_name": metric_name,
                    "product": row_data.get("product"),
                    "reward_source": row_data.get("reward_source"),
                    "reward_status": reward_status,
                    "reward_type": row_data.get("reward_type"),
                    "source_family": row_data.get("source_family"),
                    "sub_product": row_data.get("sub_product"),
                    "visibility_period": row_data.get("visibility_period"),
                },
            )
        )

    return {
        "report_type": SOURCE_REWARD_VISIBILITY_SUMMARY,
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
            source_family=SOURCE_REWARD_VISIBILITY_SUMMARY,
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

    if report == REPORT_LINK_CODE_PERFORMANCE:
        source_report = await _link_code_performance_report(
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
    if report == REPORT_ATTRIBUTION_QUALITY:
        source_report = await _attribution_quality_report(
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
    if report == REPORT_SAFE_STATUS_DISTRIBUTION:
        source_report = await _safe_status_distribution_report(
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
    if report == REPORT_REWARD_VISIBILITY_SUMMARY:
        source_report = await _reward_visibility_summary_report(
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
