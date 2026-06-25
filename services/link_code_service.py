from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any
from uuid import UUID

from utils.db import db_connection

SOURCE_REFERRAL_CODE = "REFERRAL_CODE"
SOURCE_CAMPAIGN_CODE = "CAMPAIGN_CODE"
SOURCE_CAMPAIGN_REFERRAL_LINK = "CAMPAIGN_REFERRAL_LINK"
SOURCE_ROUTE_REFERRAL_LINK = "ROUTE_REFERRAL_LINK"
SOURCE_COMPOSITE_CODE = "COMPOSITE_CODE"

STATUS_ISSUED = "ISSUED"
STATUS_ACTIVE = "ACTIVE"
STATUS_LINKED = "LINKED"
STATUS_VOIDED = "VOIDED"
STATUS_EXPIRED = "EXPIRED"
STATUS_INVALID = "INVALID"
STATUS_UNKNOWN = "UNKNOWN"

SUPPORTED_SOURCE_TYPES = {
    SOURCE_REFERRAL_CODE,
    SOURCE_CAMPAIGN_CODE,
    SOURCE_CAMPAIGN_REFERRAL_LINK,
    SOURCE_ROUTE_REFERRAL_LINK,
    SOURCE_COMPOSITE_CODE,
}

SENSITIVE_KEY_PARTS = ("ucn", "secret", "token", "provider_payload", "raw")


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalise_tenant_code(tenant_code: str) -> str:
    tenant = str(tenant_code or "").strip().upper()
    if not tenant:
        raise ValueError("tenant_code is required")
    return tenant


def _normalise_source_type(source_type: str) -> str:
    source = str(source_type or "").strip().upper()
    if source not in SUPPORTED_SOURCE_TYPES:
        raise ValueError(f"Unsupported link/code source_type: {source_type}")
    return source


def _normalise_ref(value: str | None, *, field_name: str) -> str:
    ref = str(value or "").strip()
    if not ref:
        raise ValueError(f"{field_name} is required")
    return ref


def _row_value(row: Any, key: str, default: Any = None) -> Any:
    if row is None:
        return default
    try:
        return row[key]
    except Exception:
        return default


def _json_safe(value: Any) -> Any:
    if isinstance(value, (datetime, UUID, Decimal)):
        return str(value)
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    return value


def _redact_evidence(value: Any) -> Any:
    if isinstance(value, dict):
        redacted = {}
        for key, item in value.items():
            key_text = str(key)
            if any(part in key_text.lower() for part in SENSITIVE_KEY_PARTS):
                redacted[key_text] = "[REDACTED]"
            else:
                redacted[key_text] = _redact_evidence(item)
        return redacted
    if isinstance(value, list):
        return [_redact_evidence(item) for item in value]
    return _json_safe(value)


def _base_result(
    *,
    tenant_code: str,
    source_type: str,
    source: str,
    link_code_id: str,
    status: str,
    code: str | None = None,
    include_evidence: bool,
) -> dict[str, Any]:
    return {
        "link_code_id": link_code_id,
        "source_type": source_type,
        "source": source,
        "tenant_code": tenant_code,
        "status": status,
        "code": code,
        "campaign": {
            "campaign_code": None,
            "campaign_track_id": None,
        },
        "participant": {
            "participant_type": None,
            "participant_ref": None,
            "source": None,
        },
        "attribution": {
            "referral_track_id": None,
            "route_id": None,
            "opportunity_id": None,
        },
        "metadata": {},
        "evidence": {} if include_evidence else None,
        "missing_evidence": [],
        "source_warnings": [],
        "redactions": [],
        "created_at": None,
        "updated_at": None,
        "inspected_at": _utcnow(),
    }


def _not_found_result(
    *,
    tenant_code: str,
    source_type: str,
    source: str,
    lookup_ref: str,
    include_evidence: bool,
    tenant_mismatch: bool = False,
) -> dict[str, Any]:
    result = _base_result(
        tenant_code=tenant_code,
        source_type=source_type,
        source=source,
        link_code_id=f"{source_type.lower()}:{lookup_ref}",
        status=STATUS_INVALID,
        code=(
            lookup_ref
            if source_type in {SOURCE_REFERRAL_CODE, SOURCE_CAMPAIGN_CODE}
            else None
        ),
        include_evidence=include_evidence,
    )
    result["missing_evidence"].append(
        {
            "code": "TENANT_MISMATCH" if tenant_mismatch else "SOURCE_NOT_FOUND",
            "severity": "BLOCKER",
            "source": source,
            "message": (
                "Source evidence exists outside the requested tenant."
                if tenant_mismatch
                else "Source evidence was not found for the requested tenant."
            ),
        }
    )
    return result


def _campaign_status(row: Any) -> str:
    now = datetime.now(timezone.utc)
    if _row_value(row, "is_active") is not True:
        return STATUS_INVALID

    starts_at = _row_value(row, "starts_at")
    ends_at = _row_value(row, "ends_at")
    max_uses = _row_value(row, "max_uses")
    uses_count = _row_value(row, "uses_count") or 0

    if isinstance(starts_at, datetime) and starts_at > now:
        return STATUS_INVALID
    if isinstance(ends_at, datetime) and ends_at < now:
        return STATUS_EXPIRED
    if max_uses is not None and int(uses_count) >= int(max_uses):
        return STATUS_INVALID
    return STATUS_ISSUED


async def inspect_link_code(
    *,
    tenant_code: str,
    source_type: str,
    link_code_id: str | None = None,
    code_or_ref: str | None = None,
    include_evidence: bool = True,
) -> dict[str, Any]:
    tenant = _normalise_tenant_code(tenant_code)
    source = _normalise_source_type(source_type)
    lookup_ref = _normalise_ref(
        link_code_id or code_or_ref,
        field_name="link_code_id or code_or_ref",
    )

    try:
        async with db_connection() as conn:
            if source == SOURCE_REFERRAL_CODE:
                return await _inspect_referral_code(
                    conn,
                    tenant_code=tenant,
                    referral_code=lookup_ref,
                    include_evidence=include_evidence,
                )
            if source == SOURCE_CAMPAIGN_CODE:
                return await _inspect_campaign_code(
                    conn,
                    tenant_code=tenant,
                    campaign_code=lookup_ref,
                    include_evidence=include_evidence,
                )
            if source == SOURCE_CAMPAIGN_REFERRAL_LINK:
                return await _inspect_campaign_referral_link(
                    conn,
                    tenant_code=tenant,
                    lookup_ref=lookup_ref,
                    include_evidence=include_evidence,
                )
            if source == SOURCE_ROUTE_REFERRAL_LINK:
                return await _inspect_route_referral_link(
                    conn,
                    tenant_code=tenant,
                    lookup_ref=lookup_ref,
                    include_evidence=include_evidence,
                )
    except Exception:
        result = _base_result(
            tenant_code=tenant,
            source_type=source,
            source=_source_table(source),
            link_code_id=f"{source.lower()}:{lookup_ref}",
            status=STATUS_UNKNOWN,
            code=(
                lookup_ref
                if source in {SOURCE_REFERRAL_CODE, SOURCE_CAMPAIGN_CODE}
                else None
            ),
            include_evidence=include_evidence,
        )
        result["source_warnings"].append(
            {
                "code": "SOURCE_UNAVAILABLE",
                "severity": "WARNING",
                "source": _source_table(source),
                "message": "Source evidence could not be inspected safely.",
            }
        )
        return result

    return _inspect_composite_code(
        tenant_code=tenant,
        composite_code=lookup_ref,
        include_evidence=include_evidence,
    )


def _source_table(source_type: str) -> str:
    return {
        SOURCE_REFERRAL_CODE: "referrer_codes",
        SOURCE_CAMPAIGN_CODE: "marketing_campaigns",
        SOURCE_CAMPAIGN_REFERRAL_LINK: "campaign_referral_links",
        SOURCE_ROUTE_REFERRAL_LINK: "distribution_route_referral_links",
        SOURCE_COMPOSITE_CODE: "composite_code_service",
    }[source_type]


async def _inspect_referral_code(
    conn: Any,
    *,
    tenant_code: str,
    referral_code: str,
    include_evidence: bool,
) -> dict[str, Any]:
    row = await conn.fetchrow(
        """
        SELECT
            referrer_code_id,
            referral_code,
            gaming_handle,
            sticker,
            tenant_code,
            segment,
            created_at,
            updated_at,
            referrer_ucn,
            referrer_ucn_hash
        FROM referrer_codes
        WHERE tenant_code = $1
          AND referral_code = $2
        LIMIT 1
        """,
        tenant_code,
        referral_code,
    )
    if not row:
        other = await conn.fetchrow(
            """
            SELECT tenant_code
            FROM referrer_codes
            WHERE referral_code = $1
            LIMIT 1
            """,
            referral_code,
        )
        return _not_found_result(
            tenant_code=tenant_code,
            source_type=SOURCE_REFERRAL_CODE,
            source="referrer_codes",
            lookup_ref=referral_code,
            include_evidence=include_evidence,
            tenant_mismatch=bool(other),
        )

    result = _base_result(
        tenant_code=tenant_code,
        source_type=SOURCE_REFERRAL_CODE,
        source="referrer_codes",
        link_code_id=f"referrer_codes:{_row_value(row, 'referrer_code_id')}",
        status=STATUS_ISSUED,
        code=_row_value(row, "referral_code"),
        include_evidence=include_evidence,
    )
    result["participant"] = {
        "participant_type": "REFERRER",
        "participant_ref": _row_value(row, "gaming_handle"),
        "source": "referrer_codes",
    }
    result["metadata"] = {
        "sticker": _row_value(row, "sticker"),
        "segment": _row_value(row, "segment"),
    }
    result["created_at"] = _json_safe(_row_value(row, "created_at"))
    result["updated_at"] = _json_safe(_row_value(row, "updated_at"))
    if include_evidence:
        result["evidence"] = _redact_evidence(dict(row))
        result["redactions"] = ["referrer_ucn", "referrer_ucn_hash"]
    return result


async def _inspect_campaign_code(
    conn: Any,
    *,
    tenant_code: str,
    campaign_code: str,
    include_evidence: bool,
) -> dict[str, Any]:
    row = await conn.fetchrow(
        """
        SELECT
            campaign_code,
            campaign_id,
            name,
            segment,
            tenant_code,
            is_active,
            starts_at,
            ends_at,
            max_uses,
            uses_count,
            attributes,
            created_at,
            updated_at
        FROM marketing_campaigns
        WHERE campaign_code = $1
          AND (tenant_code = $2 OR tenant_code IS NULL)
        LIMIT 1
        """,
        campaign_code,
        tenant_code,
    )
    if not row:
        other = await conn.fetchrow(
            """
            SELECT tenant_code
            FROM marketing_campaigns
            WHERE campaign_code = $1
            LIMIT 1
            """,
            campaign_code,
        )
        return _not_found_result(
            tenant_code=tenant_code,
            source_type=SOURCE_CAMPAIGN_CODE,
            source="marketing_campaigns",
            lookup_ref=campaign_code,
            include_evidence=include_evidence,
            tenant_mismatch=bool(other),
        )

    result = _base_result(
        tenant_code=tenant_code,
        source_type=SOURCE_CAMPAIGN_CODE,
        source="marketing_campaigns",
        link_code_id=f"marketing_campaigns:{_row_value(row, 'campaign_code')}",
        status=_campaign_status(row),
        code=_row_value(row, "campaign_code"),
        include_evidence=include_evidence,
    )
    result["campaign"]["campaign_code"] = _row_value(row, "campaign_code")
    result["metadata"] = {
        "name": _row_value(row, "name"),
        "segment": _row_value(row, "segment"),
    }
    result["created_at"] = _json_safe(_row_value(row, "created_at"))
    result["updated_at"] = _json_safe(_row_value(row, "updated_at"))
    if include_evidence:
        result["evidence"] = _redact_evidence(dict(row))
    return result


async def _inspect_campaign_referral_link(
    conn: Any,
    *,
    tenant_code: str,
    lookup_ref: str,
    include_evidence: bool,
) -> dict[str, Any]:
    row = await conn.fetchrow(
        """
        SELECT
            crl.campaign_track_id,
            crl.referral_track_id,
            crl.created_at,
            ca.campaign_code,
            ca.tenant_code,
            ca.status AS campaign_track_status,
            ri.referral_code,
            ri.status AS referral_status
        FROM campaign_referral_links crl
        JOIN campaign_attributions ca
          ON ca.campaign_track_id = crl.campaign_track_id
        JOIN referral_instances ri
          ON ri.referral_track_id = crl.referral_track_id
        WHERE ca.tenant_code = $1
          AND (
            crl.campaign_track_id::text = $2
            OR crl.referral_track_id::text = $2
            OR CONCAT(crl.campaign_track_id::text, ':', crl.referral_track_id::text) = $2
          )
        LIMIT 1
        """,
        tenant_code,
        lookup_ref,
    )
    if not row:
        return _not_found_result(
            tenant_code=tenant_code,
            source_type=SOURCE_CAMPAIGN_REFERRAL_LINK,
            source="campaign_referral_links",
            lookup_ref=lookup_ref,
            include_evidence=include_evidence,
        )

    result = _base_result(
        tenant_code=tenant_code,
        source_type=SOURCE_CAMPAIGN_REFERRAL_LINK,
        source="campaign_referral_links",
        link_code_id=(
            f"campaign_referral_links:{_row_value(row, 'campaign_track_id')}:"
            f"{_row_value(row, 'referral_track_id')}"
        ),
        status=STATUS_LINKED,
        include_evidence=include_evidence,
    )
    result["code"] = _row_value(row, "referral_code")
    result["campaign"] = {
        "campaign_code": _row_value(row, "campaign_code"),
        "campaign_track_id": _json_safe(_row_value(row, "campaign_track_id")),
    }
    result["attribution"]["referral_track_id"] = _json_safe(
        _row_value(row, "referral_track_id")
    )
    result["created_at"] = _json_safe(_row_value(row, "created_at"))
    result["updated_at"] = _json_safe(_row_value(row, "created_at"))
    if include_evidence:
        result["evidence"] = _redact_evidence(dict(row))
    return result


async def _inspect_route_referral_link(
    conn: Any,
    *,
    tenant_code: str,
    lookup_ref: str,
    include_evidence: bool,
) -> dict[str, Any]:
    row = await conn.fetchrow(
        """
        SELECT
            route_id,
            referral_track_id,
            tenant_code,
            distributor_id,
            opportunity_id,
            link_status,
            metadata,
            created_at,
            updated_at
        FROM distribution_route_referral_links
        WHERE tenant_code = $1
          AND (
            route_id::text = $2
            OR referral_track_id::text = $2
            OR CONCAT(route_id::text, ':', referral_track_id::text) = $2
          )
        LIMIT 1
        """,
        tenant_code,
        lookup_ref,
    )
    if not row:
        other = await conn.fetchrow(
            """
            SELECT tenant_code
            FROM distribution_route_referral_links
            WHERE route_id::text = $1
               OR referral_track_id::text = $1
            LIMIT 1
            """,
            lookup_ref,
        )
        return _not_found_result(
            tenant_code=tenant_code,
            source_type=SOURCE_ROUTE_REFERRAL_LINK,
            source="distribution_route_referral_links",
            lookup_ref=lookup_ref,
            include_evidence=include_evidence,
            tenant_mismatch=bool(other),
        )

    source_status = str(_row_value(row, "link_status") or "").upper()
    status = STATUS_VOIDED if source_status == STATUS_VOIDED else STATUS_ACTIVE
    result = _base_result(
        tenant_code=tenant_code,
        source_type=SOURCE_ROUTE_REFERRAL_LINK,
        source="distribution_route_referral_links",
        link_code_id=(
            f"distribution_route_referral_links:{_row_value(row, 'route_id')}:"
            f"{_row_value(row, 'referral_track_id')}"
        ),
        status=status,
        include_evidence=include_evidence,
    )
    result["participant"] = {
        "participant_type": "DISTRIBUTOR",
        "participant_ref": _json_safe(_row_value(row, "distributor_id")),
        "source": "distribution_distributors",
    }
    result["attribution"] = {
        "referral_track_id": _json_safe(_row_value(row, "referral_track_id")),
        "route_id": _json_safe(_row_value(row, "route_id")),
        "opportunity_id": _json_safe(_row_value(row, "opportunity_id")),
    }
    result["metadata"] = _json_safe(_row_value(row, "metadata") or {})
    result["created_at"] = _json_safe(_row_value(row, "created_at"))
    result["updated_at"] = _json_safe(_row_value(row, "updated_at"))
    if include_evidence:
        result["evidence"] = _redact_evidence(dict(row))
    return result


def _inspect_composite_code(
    *,
    tenant_code: str,
    composite_code: str,
    include_evidence: bool,
) -> dict[str, Any]:
    result = _base_result(
        tenant_code=tenant_code,
        source_type=SOURCE_COMPOSITE_CODE,
        source="composite_code_service",
        link_code_id=f"composite_code_service:{composite_code}",
        status=STATUS_UNKNOWN,
        code=composite_code,
        include_evidence=include_evidence,
    )
    result["source_warnings"].append(
        {
            "code": "COMPATIBILITY_SOURCE_ONLY",
            "severity": "INFO",
            "source": "composite_code_service",
            "message": (
                "Composite codes are validated by an interim compatibility "
                "service and do not have durable source-table evidence."
            ),
        }
    )
    if include_evidence:
        result["evidence"] = {
            "source": "composite_code_service",
            "durable_source": False,
        }
    return result
