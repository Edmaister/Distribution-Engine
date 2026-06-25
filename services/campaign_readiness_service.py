from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from utils.db import db_connection

READINESS_READY = "READY"
READINESS_NOT_READY = "NOT_READY"
READINESS_READY_WITH_WARNINGS = "READY_WITH_WARNINGS"
READINESS_UNKNOWN = "UNKNOWN"

SEVERITY_BLOCKER = "BLOCKER"
SEVERITY_WARNING = "WARNING"
SEVERITY_UNKNOWN = "UNKNOWN"

OPERATIONS = {
    "CREATE_TRACK",
    "PUBLISH_OPPORTUNITY",
    "ROUTE_OPPORTUNITY",
    "GENERATE_LINKS",
    "ACTIVATE_CAMPAIGN",
    "CONTROL_PLANE_VIEW",
}

POLICY_REQUIRED_OPERATIONS = {
    "PUBLISH_OPPORTUNITY",
    "ACTIVATE_CAMPAIGN",
}

OPPORTUNITY_REQUIRED_OPERATIONS = {
    "PUBLISH_OPPORTUNITY",
    "ROUTE_OPPORTUNITY",
    "GENERATE_LINKS",
}


def _normalise_code(value: str | None, *, field_name: str) -> str:
    normalised = str(value or "").strip().upper()
    if not normalised:
        raise ValueError(f"{field_name} is required")
    return normalised


def _normalise_operation(operation: str | None) -> str:
    normalised = _normalise_code(operation, field_name="operation")
    if normalised not in OPERATIONS:
        raise ValueError(f"Unsupported campaign readiness operation: {operation}")
    return normalised


def _as_aware_utc(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)
    return None


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _record(
    *,
    code: str,
    severity: str,
    source: str,
    message: str,
) -> dict[str, str]:
    return {
        "code": code,
        "severity": severity,
        "source": source,
        "message": message,
    }


def _safe_campaign_evidence(campaign: dict[str, Any] | None) -> dict[str, Any]:
    if not campaign:
        return {}
    return {
        key: campaign.get(key)
        for key in [
            "campaign_code",
            "tenant_code",
            "segment",
            "name",
            "is_active",
            "starts_at",
            "ends_at",
            "max_uses",
            "uses_count",
        ]
        if campaign.get(key) is not None
    }


def _safe_policy_evidence(policy: dict[str, Any] | None) -> dict[str, Any]:
    if not policy:
        return {}
    return {
        key: policy.get(key)
        for key in [
            "campaign_code",
            "tenant_code",
            "version",
            "is_active",
            "rolling_window_days",
            "updated_at",
        ]
        if policy.get(key) is not None
    }


def _canonical_lifecycle(campaign: dict[str, Any] | None, now: datetime) -> str:
    if not campaign:
        return "UNKNOWN"
    starts_at = _as_aware_utc(campaign.get("starts_at"))
    ends_at = _as_aware_utc(campaign.get("ends_at"))
    if not campaign.get("is_active"):
        return "PAUSED"
    if starts_at and starts_at > now:
        return "SCHEDULED"
    if ends_at and ends_at < now:
        return "EXPIRED"
    return "ACTIVE"


def _readiness(
    *,
    blockers: list[dict[str, str]],
    warnings: list[dict[str, str]],
    unknowns: list[dict[str, str]],
) -> str:
    if blockers:
        return READINESS_NOT_READY
    if unknowns:
        return READINESS_UNKNOWN
    if warnings:
        return READINESS_READY_WITH_WARNINGS
    return READINESS_READY


async def _fetch_campaign(campaign_code: str) -> dict[str, Any] | None:
    async with db_connection() as conn:
        row = await conn.fetchrow(
            """
            SELECT
                campaign_code,
                tenant_code,
                segment,
                name,
                is_active,
                starts_at,
                ends_at,
                max_uses,
                uses_count
            FROM marketing_campaigns
            WHERE UPPER(campaign_code) = UPPER($1)
            """,
            campaign_code,
        )
    return dict(row) if row else None


async def _fetch_active_policy(
    *,
    tenant_code: str,
    campaign_code: str,
) -> dict[str, Any] | None:
    async with db_connection() as conn:
        row = await conn.fetchrow(
            """
            SELECT
                campaign_code,
                tenant_code,
                version,
                is_active,
                rolling_window_days,
                updated_at
            FROM marketing_campaign_policies
            WHERE is_active = TRUE
              AND UPPER(campaign_code) = UPPER($1)
              AND (
                    tenant_code IS NULL
                    OR UPPER(tenant_code) = UPPER($2)
                  )
            ORDER BY (tenant_code IS NOT NULL) DESC,
                     updated_at DESC,
                     version DESC
            LIMIT 1
            """,
            campaign_code,
            tenant_code,
        )
    return dict(row) if row else None


async def get_campaign_readiness(
    *,
    tenant_code: str,
    campaign_code: str,
    operation: str = "CONTROL_PLANE_VIEW",
    opportunity_id: str | None = None,
    include_evidence: bool = True,
) -> dict[str, Any]:
    tenant = _normalise_code(tenant_code, field_name="tenant_code")
    campaign = _normalise_code(campaign_code, field_name="campaign_code")
    resolved_operation = _normalise_operation(operation)
    now = _now_utc()

    blockers: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []
    unknowns: list[dict[str, str]] = []
    evidence: dict[str, Any] = {
        "campaign": {},
        "policy": {},
        "opportunity": {},
        "routing": {},
        "links": {},
        "funding": {},
        "audit": {},
    }

    try:
        campaign_row = await _fetch_campaign(campaign)
    except Exception:
        campaign_row = None
        unknowns.append(
            _record(
                code="SOURCE_UNAVAILABLE",
                severity=SEVERITY_UNKNOWN,
                source="marketing_campaigns",
                message="Campaign source evidence is currently unavailable.",
            )
        )

    if campaign_row is None and not unknowns:
        blockers.append(
            _record(
                code="CAMPAIGN_NOT_FOUND",
                severity=SEVERITY_BLOCKER,
                source="marketing_campaigns",
                message="No campaign definition was found for the requested campaign.",
            )
        )

    if campaign_row:
        evidence["campaign"] = _safe_campaign_evidence(campaign_row)
        campaign_tenant = str(campaign_row.get("tenant_code") or "").strip().upper()
        if campaign_tenant and campaign_tenant != tenant:
            blockers.append(
                _record(
                    code="TENANT_MISMATCH",
                    severity=SEVERITY_BLOCKER,
                    source="marketing_campaigns",
                    message="Campaign tenant does not match requested tenant scope.",
                )
            )

        if not campaign_row.get("is_active"):
            blockers.append(
                _record(
                    code="CAMPAIGN_INACTIVE",
                    severity=SEVERITY_BLOCKER,
                    source="marketing_campaigns",
                    message="Campaign definition is inactive.",
                )
            )

        starts_at = _as_aware_utc(campaign_row.get("starts_at"))
        ends_at = _as_aware_utc(campaign_row.get("ends_at"))
        if starts_at and starts_at > now:
            blockers.append(
                _record(
                    code="CAMPAIGN_NOT_STARTED",
                    severity=SEVERITY_BLOCKER,
                    source="marketing_campaigns",
                    message="Campaign start window is in the future.",
                )
            )
        if ends_at and ends_at < now:
            blockers.append(
                _record(
                    code="CAMPAIGN_EXPIRED",
                    severity=SEVERITY_BLOCKER,
                    source="marketing_campaigns",
                    message="Campaign end window has passed.",
                )
            )

        max_uses = campaign_row.get("max_uses")
        uses_count = campaign_row.get("uses_count") or 0
        if max_uses is not None and int(uses_count) >= int(max_uses):
            blockers.append(
                _record(
                    code="CAMPAIGN_CAP_EXHAUSTED",
                    severity=SEVERITY_BLOCKER,
                    source="marketing_campaigns",
                    message="Campaign usage cap has been exhausted.",
                )
            )

    policy_row: dict[str, Any] | None = None
    if campaign_row:
        try:
            policy_row = await _fetch_active_policy(
                tenant_code=tenant,
                campaign_code=campaign,
            )
        except Exception:
            unknowns.append(
                _record(
                    code="POLICY_UNKNOWN",
                    severity=SEVERITY_UNKNOWN,
                    source="marketing_campaign_policies",
                    message="Campaign policy source evidence is currently unavailable.",
                )
            )

        if policy_row:
            evidence["policy"] = _safe_policy_evidence(policy_row)
        elif resolved_operation in POLICY_REQUIRED_OPERATIONS:
            blockers.append(
                _record(
                    code="NO_ACTIVE_POLICY",
                    severity=SEVERITY_BLOCKER,
                    source="marketing_campaign_policies",
                    message="No active effective campaign policy was found.",
                )
            )
        elif resolved_operation in {"CREATE_TRACK", "CONTROL_PLANE_VIEW"}:
            warnings.append(
                _record(
                    code="NO_ACTIVE_POLICY",
                    severity=SEVERITY_WARNING,
                    source="marketing_campaign_policies",
                    message="No active effective campaign policy was found.",
                )
            )

    if resolved_operation in OPPORTUNITY_REQUIRED_OPERATIONS:
        if not opportunity_id:
            unknowns.append(
                _record(
                    code="SOURCE_UNAVAILABLE",
                    severity=SEVERITY_UNKNOWN,
                    source="distribution_opportunities",
                    message=(
                        "Opportunity-scoped readiness requires opportunity_id "
                        "and is outside this first campaign-definition slice."
                    ),
                )
            )
        else:
            unknowns.append(
                _record(
                    code="SOURCE_UNAVAILABLE",
                    severity=SEVERITY_UNKNOWN,
                    source="distribution_opportunities",
                    message=(
                        "Opportunity source checks are not implemented in this "
                        "first campaign-definition readiness slice."
                    ),
                )
            )

    lifecycle = _canonical_lifecycle(campaign_row, now)
    readiness = _readiness(
        blockers=blockers,
        warnings=warnings,
        unknowns=unknowns,
    )

    return {
        "tenant_code": tenant,
        "campaign_code": campaign,
        "opportunity_id": opportunity_id,
        "operation": resolved_operation,
        "canonical_lifecycle": lifecycle,
        "readiness": readiness,
        "can_proceed": readiness in {READINESS_READY, READINESS_READY_WITH_WARNINGS},
        "blockers": blockers,
        "warnings": warnings,
        "evidence": evidence if include_evidence else {},
        "unknowns": unknowns,
        "evaluated_at": now.replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }
