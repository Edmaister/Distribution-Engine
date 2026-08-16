from __future__ import annotations

import hashlib
import json
import random
import re
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple

from fastapi import status

from apps.api.schemas.progress import ProgressEventType, ProgressPostRequest
from services.progress_service import handle_progress_event
from utils.crypto import ucn_lookup_key
from utils.db import db_connection


_HANDLE_RE = re.compile(r"^[A-Za-z0-9_]{3,20}$")


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _identity_lookup_key(raw_value: str) -> str:
    return ucn_lookup_key(raw_value)


def _generate_referral_code() -> str:
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    return "".join(random.choice(alphabet) for _ in range(10))


def _campaign_programme_binding(attributes: Any) -> dict[str, Any] | None:
    if isinstance(attributes, str):
        try:
            attributes = json.loads(attributes)
        except json.JSONDecodeError:
            return None
    if not isinstance(attributes, dict):
        return None
    binding = attributes.get("referral_saas_programme_binding")
    return binding if isinstance(binding, dict) else None


def _campaign_override(attributes: Any) -> dict[str, Any]:
    if isinstance(attributes, str):
        try:
            attributes = json.loads(attributes)
        except json.JSONDecodeError:
            return {}
    if not isinstance(attributes, dict):
        return {}
    override = attributes.get("referral_saas_campaign_override")
    if isinstance(override, str):
        try:
            override = json.loads(override)
        except json.JSONDecodeError:
            return {}
    return override if isinstance(override, dict) else {}


def _json_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError:
            return {}
    return value if isinstance(value, dict) else {}


def _canonical_hash(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _safe_rule_keys(value: Any) -> list[str]:
    if isinstance(value, dict):
        return sorted(str(key) for key in value.keys())
    return []


def _safe_runtime_programme_context(binding: dict[str, Any] | None) -> dict[str, Any]:
    if not binding:
        return {}
    context = {
        "programmeVersionId": str(binding.get("programmeVersionId") or "").strip(),
        "programmeCode": str(binding.get("programmeCode") or "").strip(),
        "programmeName": str(binding.get("programmeName") or "").strip(),
        "versionNumber": binding.get("versionNumber"),
        "customerJourneyVersionId": str(
            binding.get("customerJourneyVersionId") or ""
        ).strip(),
        "source": "CAMPAIGN_PUBLISHED_PROGRAMME_BINDING",
        "capturedAt": _utcnow().isoformat().replace("+00:00", "Z"),
    }
    return {key: value for key, value in context.items() if value not in ("", None)}


def _safe_effective_rule_snapshot(
    *,
    tenant_code: str,
    campaign_code: str,
    programme_version: Any,
    campaign_attributes: Any,
) -> dict[str, Any]:
    programme_defaults = _json_dict(
        _row_value(programme_version, "campaign_defaults_snapshot")
    )
    safe_summary = _json_dict(_row_value(programme_version, "safe_summary"))
    customer_product_binding = {
        "customerProductLineId": str(
            _row_value(programme_version, "customer_product_line_id") or ""
        ).strip(),
        "customerProductOfferingId": str(
            _row_value(programme_version, "customer_product_offering_id") or ""
        ).strip(),
        "externalProductLineRef": str(
            _row_value(programme_version, "external_product_line_ref") or ""
        ).strip(),
        "productLineName": str(
            _row_value(programme_version, "product_line_name") or ""
        ).strip(),
        "productLineCategory": str(
            _row_value(programme_version, "product_line_category") or ""
        ).strip(),
        "externalOfferingRef": str(
            _row_value(programme_version, "external_offering_ref") or ""
        ).strip(),
        "offeringName": str(
            _row_value(programme_version, "offering_name") or ""
        ).strip(),
        "offeringFamily": str(
            _row_value(programme_version, "offering_family") or ""
        ).strip(),
        "operatingJurisdictionCode": str(
            _row_value(
                programme_version,
                "product_offering_operating_jurisdiction_code",
            )
            or _row_value(programme_version, "operating_jurisdiction_code")
            or ""
        ).strip(),
    }
    customer_product_binding = {
        key: value
        for key, value in customer_product_binding.items()
        if value not in ("", None)
    }
    override = _campaign_override(campaign_attributes)
    override_payload = _json_dict(override.get("overridePayload"))
    override_status = str(override.get("overrideStatus") or "").upper()
    approved_override = (
        override
        if override_status == "APPROVED"
        and str(override.get("programmeVersionId") or "").strip()
        == str(_row_value(programme_version, "programme_version_id") or "").strip()
        else {}
    )
    approved_override_payload = (
        override_payload if approved_override else {}
    )
    effective_source = {
        "programmeVersionId": str(_row_value(programme_version, "programme_version_id")),
        "campaignCode": campaign_code,
        "programmeDefaultsHash": _canonical_hash(programme_defaults),
        "approvedOverrideHash": _canonical_hash(approved_override_payload),
    }
    return {
        "snapshotVersion": 1,
        "snapshotType": "REFERRAL_SAAS_EFFECTIVE_RULE_CONTEXT",
        "source": "TASK-412_EFFECTIVE_RULE_RUNTIME_RESOLVER",
        "tenantScopeHash": _canonical_hash({"tenant_code": tenant_code}),
        "campaign": {"campaignCode": campaign_code},
        "customerProductBinding": customer_product_binding,
        "programme": {
            "programmeVersionId": str(
                _row_value(programme_version, "programme_version_id")
            ),
            "programmeCode": str(_row_value(programme_version, "programme_code")),
            "programmeName": str(_row_value(programme_version, "programme_name")),
            "versionNumber": int(_row_value(programme_version, "version_number") or 1),
            "customerJourneyVersionId": str(
                _row_value(programme_version, "customer_journey_version_id")
            ),
            "configurationChecksum": str(
                _row_value(programme_version, "configuration_checksum") or ""
            ).strip(),
            "safeSummary": safe_summary,
        },
        "programmeDefaultRules": {
            "present": bool(programme_defaults),
            "ruleKeys": _safe_rule_keys(programme_defaults),
            "checksum": _canonical_hash(programme_defaults),
        },
        "campaignOverrideRules": {
            "present": bool(approved_override),
            "approved": bool(approved_override),
            "overrideKeys": _safe_rule_keys(approved_override_payload),
            "overrideReasonPresent": bool(approved_override.get("overrideReason")),
            "approvedAt": approved_override.get("approvedAt"),
            "checksum": _canonical_hash(approved_override_payload),
        },
        "effectiveRulesChecksum": _canonical_hash(effective_source),
        "capturedAt": _utcnow().isoformat().replace("+00:00", "Z"),
        "configurationPayloadRedacted": True,
        "noProviderDispatchConfirmed": True,
        "noInviteOrSeatChangeConfirmed": True,
        "noCredentialCreationConfirmed": True,
        "noBillingOrMoneyMovementConfirmed": True,
    }


def _row_value(row: Any, key: str, default: Any = None) -> Any:
    if hasattr(row, "get"):
        return row.get(key, default)
    try:
        return row[key]
    except (KeyError, IndexError, TypeError):
        return default


async def _fetch_campaign_programme_runtime_context(
    conn: Any,
    *,
    tenant_code: str,
    campaign_code: str,
) -> tuple[str | None, dict[str, Any]]:
    if not campaign_code:
        return None, {}
    row = await conn.fetchrow(
        """
        SELECT campaign_code, attributes
        FROM marketing_campaigns
        WHERE UPPER(tenant_code) = UPPER($1)
          AND UPPER(campaign_code) = UPPER($2)
        LIMIT 1
        """,
        tenant_code,
        campaign_code,
    )
    if not row:
        return None, {}
    attributes = _row_value(row, "attributes")
    binding = _campaign_programme_binding(attributes)
    context = _safe_runtime_programme_context(binding)
    programme_version_id = str(context.get("programmeVersionId") or "").strip()
    if programme_version_id:
        programme_row = await conn.fetchrow(
            """
            SELECT
                v.programme_version_id,
                v.programme_code,
                v.programme_name,
                v.version_number,
                v.version_status,
                v.customer_journey_version_id,
                v.operating_jurisdiction_code,
                v.customer_product_line_id,
                v.customer_product_offering_id,
                v.campaign_defaults_snapshot,
                v.configuration_checksum,
                v.safe_summary,
                v.retired_at,
                l.external_product_line_ref,
                l.product_line_name,
                l.product_line_category,
                o.external_offering_ref,
                o.offering_name,
                o.offering_family,
                o.operating_jurisdiction_code
                    AS product_offering_operating_jurisdiction_code
            FROM referral_saas_programme_versions v
            LEFT JOIN referral_saas_customer_product_lines l
                ON l.customer_product_line_id = v.customer_product_line_id
               AND l.account_id = v.account_id
            LEFT JOIN referral_saas_customer_product_offerings o
                ON o.customer_product_offering_id = v.customer_product_offering_id
               AND o.customer_product_line_id = v.customer_product_line_id
               AND o.account_id = v.account_id
            WHERE v.programme_version_id = $1
            LIMIT 1
            """,
            programme_version_id,
        )
        if not programme_row:
            raise ValueError("Campaign programme binding references a missing programme version.")
        if str(_row_value(programme_row, "version_status") or "").upper() != "PUBLISHED":
            raise ValueError("Campaign programme binding must resolve to a published programme version.")
        if _row_value(programme_row, "retired_at") is not None:
            raise ValueError("Campaign programme binding cannot resolve to a retired programme version.")
        context["effectiveRuleSnapshot"] = _safe_effective_rule_snapshot(
            tenant_code=tenant_code,
            campaign_code=str(_row_value(row, "campaign_code") or campaign_code),
            programme_version=programme_row,
            campaign_attributes=attributes,
        )
    return programme_version_id or None, context


def _generate_handle() -> str:
    adjectives = ["Swift", "Brave", "Neon", "Epic", "Storm", "Iron", "Shadow", "Nova", "Viper", "Blaze"]
    nouns = ["Falcon", "Tiger", "Knight", "Rider", "Wizard", "Ninja", "Lion", "Wolf", "Dragon", "Hawk"]
    return f"{random.choice(adjectives)}{random.choice(nouns)}{random.randint(10, 999)}"


def _is_handle_valid(h: str) -> bool:
    return bool(h and _HANDLE_RE.match(h))


async def _handle_available(conn, handle: str) -> bool:
    row = await conn.fetchrow(
        "SELECT 1 FROM referrer_codes WHERE gaming_handle = $1 LIMIT 1",
        handle,
    )
    return row is None


async def _pick_handle(conn, preferred: Optional[str]) -> str:
    if preferred:
        preferred = preferred.strip()
        if _is_handle_valid(preferred) and await _handle_available(conn, preferred):
            return preferred

    for _ in range(50):
        candidate = _generate_handle()
        if await _handle_available(conn, candidate):
            return candidate

    return f"Player{random.randint(100000, 999999)}"


def _normalize_alias(value: Optional[str]) -> str:
    if not isinstance(value, str):
        return ""

    cleaned = value.strip()
    if not cleaned:
        return ""

    if cleaned.lower() in {"string", "null", "none", "n/a", "na", "unknown", "test"}:
        return ""

    return cleaned


def _generate_alias() -> str:
    adjectives = ["Brave", "Lucky", "Swift", "Silver", "Bold", "Clever"]
    nouns = ["Falcon", "Lion", "Wolf", "Raven", "Tiger", "Panda"]

    return f"{random.choice(adjectives)}{random.choice(nouns)}{random.randint(10,99)}"


def _validate_alias(alias: str) -> tuple[bool, Optional[str], Optional[str]]:
    alias = _normalize_alias(alias)

    if not alias:
        return False, "ALIAS_REQUIRED", None

    if len(alias) < 3:
        return False, "ALIAS_TOO_SHORT", None

    if len(alias) > 30:
        return False, "ALIAS_TOO_LONG", None

    if not re.fullmatch(r"[A-Za-z0-9 _\\-]+", alias):
        return False, "ALIAS_INVALID_FORMAT", None

    normalized = alias.lower()

    blocked_words = {"admin", "support", "fnb", "fuck", "shit"}
    for word in blocked_words:
        if word in normalized:
            return False, "ALIAS_NOT_ALLOWED", None

    return True, None, normalized


async def get_or_create_referrer_code(
    *,
    referrer_ucn: str,
    tenant: str,
    sticker: str,
    segment: str,
    accepted_terms: bool,
    preferred_handle: Optional[str] = None,
) -> Tuple[Dict[str, Any], int]:

    raw_ucn = str(referrer_ucn).strip()
    tenant = str(tenant).strip()
    sticker = str(sticker).strip()
    segment = str(segment).strip()
    preferred_handle = preferred_handle.strip() if isinstance(preferred_handle, str) else None

    if not raw_ucn or not tenant or not sticker or not segment:
        return {
            "message": "Missing required fields",
            "error_code": "MISSING_FIELDS",
            "created": False,
        }, status.HTTP_400_BAD_REQUEST

    if accepted_terms is not True:
        return {
            "message": "Terms and conditions must be accepted before a referral code can be created.",
            "error_code": "ACCEPTED_TERMS_REQUIRED",
            "created": False,
        }, status.HTTP_400_BAD_REQUEST

    referrer_ucn_hash = _identity_lookup_key(raw_ucn)
    now = _utcnow()

    async with db_connection() as conn:
        async with conn.transaction():
            row = await conn.fetchrow(
                """
                SELECT referral_code, gaming_handle
                FROM referrer_codes
                WHERE tenant_code = $1
                  AND sticker = $2
                  AND referrer_ucn_hash = $3
                LIMIT 1
                """,
                tenant,
                sticker,
                referrer_ucn_hash,
            )

            if row:
                return {
                    "referral_code": row["referral_code"],
                    "gaming_handle": row["gaming_handle"],
                    "created": False,
                    "error_code": None,
                }, status.HTTP_200_OK

            referral_code_id = str(uuid.uuid4())
            referral_code = _generate_referral_code()
            gaming_handle = await _pick_handle(conn, preferred_handle)

            await conn.execute(
                """
                INSERT INTO referrer_codes
                    (
                        referrer_code_id,
                        referrer_ucn,
                        referrer_ucn_hash,
                        referral_code,
                        gaming_handle,
                        sticker,
                        tenant_code,
                        segment,
                        accepted_terms,
                        accepted_terms_at
                    )
                VALUES
                    (
                        $1, $2, $3, $4, $5,
                        $6, $7, $8, $9, $10
                    )
                """,
                referral_code_id,
                raw_ucn,
                referrer_ucn_hash,
                referral_code,
                gaming_handle,
                sticker,
                tenant,
                segment,
                True,
                now,
            )

    return {
        "referral_code": referral_code,
        "gaming_handle": gaming_handle,
        "created": True,
        "error_code": None,
    }, status.HTTP_201_CREATED


async def validate_referral_code(
    *,
    tenant_code: str,
    referral_code: str,
    accepted_terms: bool,
    alias: Optional[str] = None,
    device_fingerprint: Optional[str] = None,
    ip_address: Optional[str] = None,
    qr_code: Optional[str] = None,
) -> Tuple[Dict[str, Any], int]:

    tenant_code = str(tenant_code).strip() if tenant_code else ""
    code = str(referral_code).strip() if referral_code else ""

    if not tenant_code:
        return _fail("TENANT_CODE_REQUIRED", "tenant_code is required")

    if not code:
        return _fail("REFERRAL_CODE_REQUIRED", "referral_code is required")

    if accepted_terms is not True:
        return _fail("ACCEPTED_TERMS_REQUIRED", "accepted_terms must be true")

    alias_input = _normalize_alias(alias)
    alias_source = "USER_PROVIDED" if alias_input else "AUTO_GENERATED"
    alias_value = alias_input or _generate_alias()

    alias_ok, alias_error, alias_normalized = _validate_alias(alias_value)
    if not alias_ok:
        return {
            "valid": False,
            "referral_track_id": None,
            "message": "alias is invalid",
            "error_code": alias_error,
            "validation_outcome": "FAILED",
            "alias": None,
            "attributes": {"aliasSource": alias_source},
        }, status.HTTP_400_BAD_REQUEST

    device_fingerprint = device_fingerprint.strip() if isinstance(device_fingerprint, str) else None
    ip_address = ip_address.strip() if isinstance(ip_address, str) else None
    qr_code = qr_code.strip() if isinstance(qr_code, str) else None

    referral_track_id = None
    referrer_code_id = None
    programme_version_id = None

    try:
        async with db_connection() as conn:
            async with conn.transaction():
                row = await conn.fetchrow(
                    """
                    SELECT referrer_code_id, referrer_ucn, sticker
                    FROM referrer_codes
                    WHERE tenant_code = $1
                      AND referral_code = $2
                    LIMIT 1
                    """,
                    tenant_code,
                    code,
                )

                if not row:
                    return {
                        "valid": False,
                        "referral_track_id": None,
                        "message": "Referral code not found",
                        "error_code": "REFERRAL_CODE_NOT_FOUND",
                        "validation_outcome": "FAILED",
                        "alias": None,
                        "attributes": {
                            "tenant_code": tenant_code,
                            "aliasSource": alias_source,
                        },
                    }, status.HTTP_404_NOT_FOUND

                referrer_code_id = _row_value(row, "referrer_code_id")
                referrer_ucn = _row_value(row, "referrer_ucn")
                campaign_context_code = str(_row_value(row, "sticker") or "").strip()
                referral_track_id = str(uuid.uuid4())
                now = _utcnow()
                programme_version_id, programme_context = (
                    await _fetch_campaign_programme_runtime_context(
                        conn,
                        tenant_code=tenant_code,
                        campaign_code=campaign_context_code,
                    )
                )

                await conn.execute(
                    """
                    INSERT INTO referral_instances
                        (
                            referral_track_id,
                            referrer_code_id,
                            referral_code,
                            referrer_ucn,
                            tenant_code,
                            status,
                            validated_at,
                            accepted_terms,
                            accepted_terms_at,
                            referee_alias,
                            referee_alias_normalized,
                            programme_version_id,
                            programme_runtime_context,
                            created_at,
                            updated_at
                        )
                    VALUES
                        (
                            $1, $2, $3, $4,
                            $5,
                            'VALIDATED', $6,
                            $7, $8,
                            $9, $10,
                            $11, $12::jsonb,
                            $13, $14
                        )
                    """,
                    referral_track_id,
                    referrer_code_id,
                    code,
                    referrer_ucn,
                    tenant_code,
                    now,
                    True,
                    now,
                    alias_value,
                    alias_normalized,
                    programme_version_id,
                    json.dumps(programme_context),
                    now,
                    now,
                )

                await conn.execute(
                    """
                    INSERT INTO referral_qr_scans
                        (referral_code, qr_code, referral_track_id, device_fingerprint, ip_address, status)
                    VALUES
                        ($1, $2, $3, $4, $5, 'VALIDATED')
                    """,
                    code,
                    qr_code,
                    referral_track_id,
                    device_fingerprint,
                    ip_address,
                )

    except Exception:
        return {
            "valid": True,
            "referral_track_id": referral_track_id,
            "message": "Referral code valid but instance or scan logging failed",
            "error_code": "REFERRAL_LOG_FAILED",
            "validation_outcome": "FAILED",
            "alias": None,
            "attributes": {
                "tenant_code": tenant_code,
                "referrer_code_id": referrer_code_id,
                "aliasSource": alias_source,
                "programmeRuntimeBinding": {
                    "bound": bool(programme_version_id),
                    "programmeVersionId": programme_version_id,
                },
            },
        }, status.HTTP_200_OK

    return {
        "valid": True,
        "referral_track_id": referral_track_id,
        "message": "Referral code validated",
        "error_code": None,
        "validation_outcome": "VALIDATED",
        "alias": alias_value,
        "attributes": {
            "tenant_code": tenant_code,
            "referrer_code_id": referrer_code_id,
            "aliasSource": alias_source,
            "programmeRuntimeBinding": {
                "bound": bool(programme_version_id),
                "programmeVersionId": programme_version_id,
            },
        },
    }, status.HTTP_200_OK


def _fail(error_code: str, message: str):
    return {
        "valid": False,
        "referral_track_id": None,
        "message": message,
        "error_code": error_code,
        "validation_outcome": "FAILED",
        "alias": None,
        "attributes": {},
    }, status.HTTP_400_BAD_REQUEST


async def capture_referee_ucn(
    *,
    referral_track_id: str,
    referee_ucn: str,
    tenant_code: str,
) -> Tuple[Dict[str, Any], int]:

    track_id = str(referral_track_id).strip()
    raw_ucn = str(referee_ucn).strip()

    if not track_id or not raw_ucn:
        return {
            "message": "referral_track_id and referee_ucn are required",
            "error_code": "REFEREE_UCN_REQUIRED",
        }, status.HTTP_400_BAD_REQUEST

    now = _utcnow()
    referee_ucn_hash = _identity_lookup_key(raw_ucn)

    async with db_connection() as conn:
        async with conn.transaction():
            row = await conn.fetchrow(
                """
                SELECT
                    ri.product,
                    ri.sub_product,
                    rc.tenant_code,
                    COALESCE(t.is_active, TRUE) AS tenant_is_active
                FROM referral_instances ri
                JOIN referrer_codes rc
                  ON rc.referrer_code_id = ri.referrer_code_id
                LEFT JOIN tenants t
                  ON t.tenant_code = rc.tenant_code
                WHERE ri.referral_track_id = $1
                AND rc.tenant_code = $2
                LIMIT 1
                """,
                track_id,
                tenant_code,
            )

            if row is None:
                return {
                    "message": "referral_track_id not found",
                    "error_code": "REFERRAL_TRACK_NOT_FOUND",
                }, status.HTTP_404_NOT_FOUND

            product = row["product"]
            sub_product = row["sub_product"]
            tenant_code = row["tenant_code"]
            tenant_is_active = row["tenant_is_active"]

            if tenant_is_active is not True:
                return {
                    "message": "Tenant is inactive",
                    "referral_track_id": track_id,
                    "tenant_code": tenant_code,
                    "error_code": "TENANT_INACTIVE",
                }, status.HTTP_403_FORBIDDEN

            await conn.execute(
                """
                UPDATE referral_instances
                SET referee_ucn = $1,
                    referee_ucn_hash = $2,
                    updated_at = $3
                WHERE referral_track_id = $4
                AND tenant_code = $5
                """,
                raw_ucn,
                referee_ucn_hash,
                now,
                track_id,
                tenant_code,
            )

    try:
        progress_req = ProgressPostRequest(
            referralTrackId=track_id,
            product=product,
            subProduct=sub_product,
            eventType=ProgressEventType.UCN_CAPTURED,
            occurredAt=now.isoformat().replace("+00:00", "Z"),
            refereeUCN=raw_ucn,
            meta={
                "trigger": "capture_referee_ucn",
                "tenant_code": tenant_code,
            },
            sourceSystem="REFEREE_SERVICE",
            sourceEventId=f"ucn-captured:{track_id}",
        )

        body, code = await handle_progress_event(progress_req, tenant_code=tenant_code)

        if code not in (200, 201):
            return {
                "message": "Referee UCN captured, but lifecycle event recording failed",
                "referral_track_id": track_id,
                "error_code": "REFEREE_UCN_PROGRESS_EVENT_FAILED",
                "progress_response": body,
            }, status.HTTP_500_INTERNAL_SERVER_ERROR

    except Exception:
        return {
            "message": "Referee UCN captured, but lifecycle event recording failed",
            "referral_track_id": track_id,
            "error_code": "REFEREE_UCN_PROGRESS_EVENT_FAILED",
        }, status.HTTP_500_INTERNAL_SERVER_ERROR

    return {
        "message": "Referee UCN captured",
        "referral_track_id": track_id,
        "tenant_code": tenant_code,
        "error_code": None,
    }, status.HTTP_200_OK
