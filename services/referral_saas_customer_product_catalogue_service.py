from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Mapping

from utils.db import db_connection


CUSTOMER_PRODUCT_CATALOGUE_GUARDRAILS = (
    "ACCOUNT_SCOPED_PRODUCT_CATALOGUE",
    "CUSTOMER_PRODUCT_LINE_REQUIRED",
    "CUSTOMER_PRODUCT_OFFERING_REQUIRED",
    "PRODUCT_AND_OFFERING_JURISDICTION_MUST_MATCH",
    "IDEMPOTENT_PRODUCT_CATALOGUE_COMMANDS",
    "SAFE_PRODUCT_CATALOGUE_PAYLOAD_ONLY",
    "NO_PROGRAMME_BINDING",
    "NO_CAMPAIGN_CREATION_OR_ACTIVATION",
    "NO_REFERRAL_RUNTIME_SWITCH",
    "NO_PROVIDER_DISPATCH",
    "NO_CREDENTIAL_OR_AUTH_MUTATION",
    "NO_BILLING_PAYOUT_SETTLEMENT_OR_MONEY_MOVEMENT",
)

CUSTOMER_PRODUCT_CATALOGUE_REDACTIONS = (
    "tenant_code",
    "internal_tenant_identifier",
    "raw_ucn",
    "ucn",
    "raw_event_payload",
    "provider_payload",
    "secret",
    "credential",
    "api_key",
    "password",
    "webhook_secret",
    "access_token",
    "refresh_token",
    "auth_claim",
    "billing",
    "wallet",
    "payout",
    "settlement",
    "invoice",
    "money",
    "payload_hash",
    "idempotency_key_hash",
)

CUSTOMER_PRODUCT_CATALOGUE_UNSAFE_KEY_TOKENS = tuple(
    item for item in CUSTOMER_PRODUCT_CATALOGUE_REDACTIONS if item not in {"payload_hash", "idempotency_key_hash"}
)

CUSTOMER_PRODUCT_CATALOGUE_LIFECYCLE_STATUSES = frozenset(
    {"DRAFT", "ACTIVE", "SUSPENDED", "RETIRED", "ARCHIVED"}
)

MAX_CUSTOMER_PRODUCT_CATALOGUE_LIMIT = 100


class CustomerProductCatalogueValidationError(ValueError):
    """Raised when customer product catalogue input is invalid."""


class CustomerProductCatalogueUnsafePayload(CustomerProductCatalogueValidationError):
    """Raised when customer product catalogue input contains platform-only fields."""


class CustomerProductCatalogueIdempotencyConflict(Exception):
    """Raised when an idempotency key is reused with different payload content."""


class CustomerProductCatalogueNotFound(Exception):
    """Raised when a product catalogue resource cannot be found."""


def _row_value(row: Mapping[str, Any], key: str) -> Any:
    try:
        return row[key]
    except (KeyError, TypeError):
        return getattr(row, key)


def _isoformat(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return str(value)


def _jsonb(value: Any) -> str:
    return json.dumps(value, sort_keys=True, default=str)


def _json_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return dict(value)
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return {}
        return parsed if isinstance(parsed, dict) else {}
    return {}


def _redact_json(value: Any) -> Any:
    if isinstance(value, dict):
        redacted: dict[str, Any] = {}
        for key, child in value.items():
            key_text = str(key)
            if any(token in key_text.lower() for token in CUSTOMER_PRODUCT_CATALOGUE_UNSAFE_KEY_TOKENS):
                redacted[key_text] = "[REDACTED]"
            else:
                redacted[key_text] = _redact_json(child)
        return redacted
    if isinstance(value, list):
        return [_redact_json(item) for item in value]
    return value


def _reject_unsafe_product_catalogue_payload(value: Any) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if any(token in str(key).lower() for token in CUSTOMER_PRODUCT_CATALOGUE_UNSAFE_KEY_TOKENS):
                raise CustomerProductCatalogueUnsafePayload(
                    "Product catalogue payload contains a field reserved for tenant, "
                    "provider, auth, billing, credential, settlement, payout, or money workflows."
                )
            _reject_unsafe_product_catalogue_payload(child)
    elif isinstance(value, list):
        for item in value:
            _reject_unsafe_product_catalogue_payload(item)


def _normalise_safe_mapping(value: Any, field_name: str) -> dict[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, Mapping):
        raise CustomerProductCatalogueValidationError(f"{field_name} must be an object.")
    _reject_unsafe_product_catalogue_payload(value)
    return _redact_json(dict(value))


def _required_text(
    value: Any,
    field_name: str,
    *,
    max_length: int = 240,
) -> str:
    safe = str(value or "").strip()
    if not safe:
        raise CustomerProductCatalogueValidationError(f"{field_name} is required.")
    if len(safe) > max_length:
        raise CustomerProductCatalogueValidationError(
            f"{field_name} must be {max_length} characters or fewer."
        )
    return safe


def _optional_text(value: Any, *, max_length: int = 500) -> str | None:
    if value is None:
        return None
    safe = str(value).strip()
    if not safe:
        return None
    return safe[:max_length]


def _normalise_code(value: Any, field_name: str, *, max_length: int = 80) -> str:
    return (
        _required_text(value, field_name, max_length=max_length)
        .upper()
        .replace(" ", "_")
        .replace("-", "_")
    )


def _normalise_status(value: Any) -> str:
    safe = _normalise_code(value or "DRAFT", "lifecycle_status", max_length=40)
    if safe not in CUSTOMER_PRODUCT_CATALOGUE_LIFECYCLE_STATUSES:
        raise CustomerProductCatalogueValidationError(
            "lifecycleStatus must be one of DRAFT, ACTIVE, SUSPENDED, RETIRED, ARCHIVED."
        )
    return safe


def _safe_limit(limit: int) -> int:
    return max(1, min(int(limit), MAX_CUSTOMER_PRODUCT_CATALOGUE_LIMIT))


@dataclass(frozen=True)
class CustomerProductOffering:
    customer_product_offering_id: str
    account_id: str
    customer_product_line_id: str
    external_offering_ref: str
    offering_name: str
    offering_family: str | None
    operating_jurisdiction_code: str
    lifecycle_status: str
    description: str | None
    safe_summary: dict[str, Any]
    governance_metadata: dict[str, Any]
    created_at: datetime | str | None
    updated_at: datetime | str | None
    archived_at: datetime | str | None

    def to_safe_dict(self) -> dict[str, Any]:
        return {
            "customerProductOfferingId": self.customer_product_offering_id,
            "accountId": self.account_id,
            "customerProductLineId": self.customer_product_line_id,
            "externalOfferingRef": self.external_offering_ref,
            "offeringName": self.offering_name,
            "offeringFamily": self.offering_family,
            "operatingJurisdictionCode": self.operating_jurisdiction_code,
            "lifecycleStatus": self.lifecycle_status,
            "description": self.description,
            "safeSummary": _redact_json(self.safe_summary),
            "governanceMetadata": _redact_json(self.governance_metadata),
            "createdAt": _isoformat(self.created_at),
            "updatedAt": _isoformat(self.updated_at),
            "archivedAt": _isoformat(self.archived_at),
            "guardrails": list(CUSTOMER_PRODUCT_CATALOGUE_GUARDRAILS),
            "redactions": list(CUSTOMER_PRODUCT_CATALOGUE_REDACTIONS),
        }


@dataclass(frozen=True)
class CustomerProductLine:
    customer_product_line_id: str
    account_id: str
    external_product_line_ref: str
    product_line_name: str
    product_line_category: str
    operating_jurisdiction_code: str
    lifecycle_status: str
    description: str | None
    safe_summary: dict[str, Any]
    governance_metadata: dict[str, Any]
    created_at: datetime | str | None
    updated_at: datetime | str | None
    archived_at: datetime | str | None
    offerings: tuple[CustomerProductOffering, ...] = ()

    def to_safe_dict(self) -> dict[str, Any]:
        return {
            "customerProductLineId": self.customer_product_line_id,
            "accountId": self.account_id,
            "externalProductLineRef": self.external_product_line_ref,
            "productLineName": self.product_line_name,
            "productLineCategory": self.product_line_category,
            "operatingJurisdictionCode": self.operating_jurisdiction_code,
            "lifecycleStatus": self.lifecycle_status,
            "description": self.description,
            "safeSummary": _redact_json(self.safe_summary),
            "governanceMetadata": _redact_json(self.governance_metadata),
            "offerings": [offering.to_safe_dict() for offering in self.offerings],
            "createdAt": _isoformat(self.created_at),
            "updatedAt": _isoformat(self.updated_at),
            "archivedAt": _isoformat(self.archived_at),
            "guardrails": list(CUSTOMER_PRODUCT_CATALOGUE_GUARDRAILS),
            "redactions": list(CUSTOMER_PRODUCT_CATALOGUE_REDACTIONS),
        }


@dataclass(frozen=True)
class CustomerProductCatalogueCommandResult:
    command_status: str
    idempotency_status: str
    resource_type: str
    resource: CustomerProductLine | CustomerProductOffering

    def to_safe_dict(self) -> dict[str, Any]:
        return {
            "commandStatus": self.command_status,
            "idempotencyStatus": self.idempotency_status,
            "resourceType": self.resource_type,
            "resource": self.resource.to_safe_dict(),
            "guardrails": list(CUSTOMER_PRODUCT_CATALOGUE_GUARDRAILS),
            "redactions": list(CUSTOMER_PRODUCT_CATALOGUE_REDACTIONS),
            "noProgrammeBindingConfirmed": True,
            "noCampaignCreationOrActivationConfirmed": True,
            "noReferralRuntimeSwitchConfirmed": True,
            "noProviderDispatchConfirmed": True,
            "noCredentialOrAuthMutationConfirmed": True,
            "noBillingPayoutSettlementOrMoneyMovementConfirmed": True,
        }


def _line_from_row(
    row: Mapping[str, Any],
    *,
    offerings: tuple[CustomerProductOffering, ...] = (),
) -> CustomerProductLine:
    return CustomerProductLine(
        customer_product_line_id=str(_row_value(row, "customer_product_line_id")),
        account_id=str(_row_value(row, "account_id")),
        external_product_line_ref=str(_row_value(row, "external_product_line_ref")),
        product_line_name=str(_row_value(row, "product_line_name")),
        product_line_category=str(_row_value(row, "product_line_category")),
        operating_jurisdiction_code=str(_row_value(row, "operating_jurisdiction_code")),
        lifecycle_status=str(_row_value(row, "lifecycle_status")),
        description=_row_value(row, "description"),
        safe_summary=_json_dict(_row_value(row, "safe_summary")),
        governance_metadata=_json_dict(_row_value(row, "governance_metadata")),
        created_at=_row_value(row, "created_at"),
        updated_at=_row_value(row, "updated_at"),
        archived_at=_row_value(row, "archived_at"),
        offerings=offerings,
    )


def _offering_from_row(row: Mapping[str, Any]) -> CustomerProductOffering:
    return CustomerProductOffering(
        customer_product_offering_id=str(_row_value(row, "customer_product_offering_id")),
        account_id=str(_row_value(row, "account_id")),
        customer_product_line_id=str(_row_value(row, "customer_product_line_id")),
        external_offering_ref=str(_row_value(row, "external_offering_ref")),
        offering_name=str(_row_value(row, "offering_name")),
        offering_family=_row_value(row, "offering_family"),
        operating_jurisdiction_code=str(_row_value(row, "operating_jurisdiction_code")),
        lifecycle_status=str(_row_value(row, "lifecycle_status")),
        description=_row_value(row, "description"),
        safe_summary=_json_dict(_row_value(row, "safe_summary")),
        governance_metadata=_json_dict(_row_value(row, "governance_metadata")),
        created_at=_row_value(row, "created_at"),
        updated_at=_row_value(row, "updated_at"),
        archived_at=_row_value(row, "archived_at"),
    )


async def list_referral_saas_customer_product_catalogue(
    *,
    account_id: str,
    include_retired: bool = False,
    limit: int = 50,
) -> dict[str, Any]:
    status_filter = "" if include_retired else "AND lifecycle_status NOT IN ('RETIRED', 'ARCHIVED')"
    async with db_connection() as conn:
        line_rows = await conn.fetch(
            f"""
            SELECT *
            FROM referral_saas_customer_product_lines
            WHERE account_id = $1
              {status_filter}
            ORDER BY product_line_name, external_product_line_ref
            LIMIT $2
            """,
            account_id,
            _safe_limit(limit),
        )
        offering_rows = await conn.fetch(
            f"""
            SELECT *
            FROM referral_saas_customer_product_offerings
            WHERE account_id = $1
              {status_filter}
            ORDER BY offering_name, external_offering_ref
            """,
            account_id,
        )

    offerings_by_line: dict[str, list[CustomerProductOffering]] = {}
    for row in offering_rows:
        offering = _offering_from_row(row)
        offerings_by_line.setdefault(offering.customer_product_line_id, []).append(offering)

    lines = [
        _line_from_row(
            row,
            offerings=tuple(offerings_by_line.get(str(_row_value(row, "customer_product_line_id")), [])),
        )
        for row in line_rows
    ]
    return {
        "productLines": [line.to_safe_dict() for line in lines],
        "count": len(lines),
        "guardrails": list(CUSTOMER_PRODUCT_CATALOGUE_GUARDRAILS),
        "redactions": list(CUSTOMER_PRODUCT_CATALOGUE_REDACTIONS),
        "noProgrammeBindingConfirmed": True,
        "noCampaignCreationOrActivationConfirmed": True,
        "noReferralRuntimeSwitchConfirmed": True,
        "noBillingPayoutSettlementOrMoneyMovementConfirmed": True,
    }


async def get_referral_saas_customer_product_line(
    *,
    account_id: str,
    product_line_ref: str,
    include_retired: bool = False,
) -> CustomerProductLine:
    status_filter = "" if include_retired else "AND lifecycle_status NOT IN ('RETIRED', 'ARCHIVED')"
    async with db_connection() as conn:
        row = await conn.fetchrow(
            f"""
            SELECT *
            FROM referral_saas_customer_product_lines
            WHERE account_id = $1
              AND (
                customer_product_line_id::text = $2
                OR UPPER(external_product_line_ref) = UPPER($2)
              )
              {status_filter}
            """,
            account_id,
            product_line_ref,
        )
        if not row:
            raise CustomerProductCatalogueNotFound(product_line_ref)
        offering_rows = await conn.fetch(
            f"""
            SELECT *
            FROM referral_saas_customer_product_offerings
            WHERE account_id = $1
              AND customer_product_line_id = $2
              {status_filter}
            ORDER BY offering_name, external_offering_ref
            """,
            account_id,
            _row_value(row, "customer_product_line_id"),
        )
    return _line_from_row(row, offerings=tuple(_offering_from_row(item) for item in offering_rows))


async def _find_product_line_row(conn: Any, *, account_id: str, product_line_ref: str) -> Mapping[str, Any]:
    row = await conn.fetchrow(
        """
        SELECT *
        FROM referral_saas_customer_product_lines
        WHERE account_id = $1
          AND (
            customer_product_line_id::text = $2
            OR UPPER(external_product_line_ref) = UPPER($2)
          )
          AND lifecycle_status NOT IN ('RETIRED', 'ARCHIVED')
        """,
        account_id,
        product_line_ref,
    )
    if not row:
        raise CustomerProductCatalogueNotFound(product_line_ref)
    return row


async def _find_product_offering_row(
    conn: Any,
    *,
    account_id: str,
    product_line_ref: str,
    offering_ref: str,
) -> Mapping[str, Any]:
    line_row = await _find_product_line_row(
        conn,
        account_id=account_id,
        product_line_ref=product_line_ref,
    )
    row = await conn.fetchrow(
        """
        SELECT *
        FROM referral_saas_customer_product_offerings
        WHERE account_id = $1
          AND customer_product_line_id = $2
          AND (
            customer_product_offering_id::text = $3
            OR UPPER(external_offering_ref) = UPPER($3)
          )
          AND lifecycle_status NOT IN ('RETIRED', 'ARCHIVED')
        """,
        account_id,
        _row_value(line_row, "customer_product_line_id"),
        offering_ref,
    )
    if not row:
        raise CustomerProductCatalogueNotFound(offering_ref)
    return row


async def _ensure_idempotency(
    conn: Any,
    *,
    account_id: str,
    operation_type: str,
    idempotency_key_hash: str,
    request_payload_hash: str,
) -> Mapping[str, Any] | None:
    existing = await conn.fetchrow(
        """
        SELECT *
        FROM referral_saas_customer_product_catalogue_idempotency_keys
        WHERE account_id = $1
          AND operation_type = $2
          AND idempotency_key_hash = $3
        """,
        account_id,
        operation_type,
        idempotency_key_hash,
    )
    if existing and _row_value(existing, "request_payload_hash") != request_payload_hash:
        raise CustomerProductCatalogueIdempotencyConflict(
            "Idempotency key was reused with different product catalogue content."
        )
    return existing


async def _record_idempotency(
    conn: Any,
    *,
    account_id: str,
    operation_type: str,
    idempotency_key_hash: str,
    request_payload_hash: str,
    resource_type: str,
    resource_id: str,
) -> None:
    await conn.execute(
        """
        INSERT INTO referral_saas_customer_product_catalogue_idempotency_keys (
            account_id, operation_type, idempotency_key_hash,
            request_payload_hash, response_payload_hash, resource_type,
            resource_id, response_status
        )
        VALUES ($1, $2, $3, $4, $4, $5, $6, 'SUCCESS')
        ON CONFLICT DO NOTHING
        """,
        account_id,
        operation_type,
        idempotency_key_hash,
        request_payload_hash,
        resource_type,
        resource_id,
    )


async def _record_audit(
    conn: Any,
    *,
    account_id: str,
    product_line_id: str | None,
    offering_id: str | None,
    event_type: str,
    event_status: str,
    actor_ref: str,
    actor_role: str,
    previous_status: str | None,
    next_status: str | None,
    reason_code: str,
    correlation_id: str | None,
    idempotency_key_hash: str,
) -> None:
    await conn.execute(
        """
        INSERT INTO referral_saas_customer_product_catalogue_audit (
            account_id, customer_product_line_id, customer_product_offering_id,
            event_type, event_status, actor_ref, actor_role,
            previous_status, next_status, reason_code, correlation_id,
            idempotency_key_hash, evidence_summary, redactions
        )
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13::jsonb, $14::jsonb)
        """,
        account_id,
        product_line_id,
        offering_id,
        event_type,
        event_status,
        actor_ref,
        actor_role,
        previous_status,
        next_status,
        reason_code,
        correlation_id,
        idempotency_key_hash,
        _jsonb({"guardrails": list(CUSTOMER_PRODUCT_CATALOGUE_GUARDRAILS)}),
        _jsonb(list(CUSTOMER_PRODUCT_CATALOGUE_REDACTIONS)),
    )


async def upsert_referral_saas_customer_product_line(
    *,
    account_id: str,
    product_line_ref: str,
    product_line_name: str,
    product_line_category: str,
    operating_jurisdiction_code: str,
    lifecycle_status: str = "DRAFT",
    description: str | None = None,
    safe_summary: Mapping[str, Any] | None = None,
    governance_metadata: Mapping[str, Any] | None = None,
    idempotency_key_hash: str,
    request_payload_hash: str,
    actor_ref: str,
    actor_role: str,
    correlation_id: str | None = None,
) -> CustomerProductCatalogueCommandResult:
    safe_product_line_ref = _required_text(product_line_ref, "product_line_ref", max_length=120)
    safe_status = _normalise_status(lifecycle_status)
    safe_summary_dict = _normalise_safe_mapping(safe_summary, "safeSummary")
    governance_metadata_dict = _normalise_safe_mapping(governance_metadata, "governanceMetadata")
    async with db_connection() as conn:
        existing_idempotency = await _ensure_idempotency(
            conn,
            account_id=account_id,
            operation_type="UPSERT_PRODUCT_LINE",
            idempotency_key_hash=idempotency_key_hash,
            request_payload_hash=request_payload_hash,
        )
        if existing_idempotency:
            row = await _find_product_line_row(
                conn,
                account_id=account_id,
                product_line_ref=str(_row_value(existing_idempotency, "resource_id")),
            )
            return CustomerProductCatalogueCommandResult(
                command_status="PRODUCT_LINE_RECORDED",
                idempotency_status="REPLAY_SAME_PAYLOAD",
                resource_type="PRODUCT_LINE",
                resource=_line_from_row(row),
            )
        existing_row = await conn.fetchrow(
            """
            SELECT *
            FROM referral_saas_customer_product_lines
            WHERE account_id = $1
              AND UPPER(external_product_line_ref) = UPPER($2)
              AND lifecycle_status NOT IN ('RETIRED', 'ARCHIVED')
            """,
            account_id,
            safe_product_line_ref,
        )
        product_line_values = (
            account_id,
            safe_product_line_ref,
            _required_text(product_line_name, "productLineName"),
            _normalise_code(product_line_category, "productLineCategory"),
            _normalise_code(operating_jurisdiction_code, "operatingJurisdictionCode"),
            safe_status,
            _optional_text(description),
            _jsonb(safe_summary_dict),
            _jsonb(governance_metadata_dict),
            request_payload_hash,
            idempotency_key_hash,
            correlation_id,
            actor_ref,
        )
        if existing_row:
            row = await conn.fetchrow(
                """
                UPDATE referral_saas_customer_product_lines
                SET product_line_name = $3,
                    product_line_category = $4,
                    operating_jurisdiction_code = $5,
                    lifecycle_status = $6,
                    description = $7,
                    safe_summary = $8::jsonb,
                    governance_metadata = $9::jsonb,
                    payload_hash = $10,
                    idempotency_key_hash = $11,
                    correlation_id = $12,
                    updated_by_ref = $13,
                    updated_at = NOW(),
                    archived_at = CASE
                        WHEN $6 IN ('RETIRED', 'ARCHIVED') THEN NOW()
                        ELSE NULL
                    END
                WHERE account_id = $1
                  AND customer_product_line_id = $2
                RETURNING *
                """,
                account_id,
                _row_value(existing_row, "customer_product_line_id"),
                *product_line_values[2:],
            )
        else:
            row = await conn.fetchrow(
                """
                INSERT INTO referral_saas_customer_product_lines (
                    account_id, external_product_line_ref, product_line_name,
                    product_line_category, operating_jurisdiction_code,
                    lifecycle_status, description, safe_summary,
                    governance_metadata, payload_hash, idempotency_key_hash,
                    correlation_id, created_by_ref, updated_by_ref
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8::jsonb, $9::jsonb, $10, $11, $12, $13, $13)
                RETURNING *
                """,
                *product_line_values,
            )
        line = _line_from_row(row)
        await _record_idempotency(
            conn,
            account_id=account_id,
            operation_type="UPSERT_PRODUCT_LINE",
            idempotency_key_hash=idempotency_key_hash,
            request_payload_hash=request_payload_hash,
            resource_type="PRODUCT_LINE",
            resource_id=line.customer_product_line_id,
        )
        await _record_audit(
            conn,
            account_id=account_id,
            product_line_id=line.customer_product_line_id,
            offering_id=None,
            event_type="PRODUCT_LINE_RECORDED",
            event_status="RECORDED",
            actor_ref=actor_ref,
            actor_role=actor_role,
            previous_status=str(_row_value(existing_row, "lifecycle_status")) if existing_row else None,
            next_status=line.lifecycle_status,
            reason_code="UPSERT_PRODUCT_LINE",
            correlation_id=correlation_id,
            idempotency_key_hash=idempotency_key_hash,
        )
    return CustomerProductCatalogueCommandResult(
        command_status="PRODUCT_LINE_RECORDED",
        idempotency_status="NEW_REQUEST",
        resource_type="PRODUCT_LINE",
        resource=line,
    )


async def upsert_referral_saas_customer_product_offering(
    *,
    account_id: str,
    product_line_ref: str,
    offering_ref: str,
    offering_name: str,
    offering_family: str | None = None,
    operating_jurisdiction_code: str,
    lifecycle_status: str = "DRAFT",
    description: str | None = None,
    safe_summary: Mapping[str, Any] | None = None,
    governance_metadata: Mapping[str, Any] | None = None,
    idempotency_key_hash: str,
    request_payload_hash: str,
    actor_ref: str,
    actor_role: str,
    correlation_id: str | None = None,
) -> CustomerProductCatalogueCommandResult:
    safe_offering_ref = _required_text(offering_ref, "offering_ref", max_length=120)
    safe_status = _normalise_status(lifecycle_status)
    safe_summary_dict = _normalise_safe_mapping(safe_summary, "safeSummary")
    governance_metadata_dict = _normalise_safe_mapping(governance_metadata, "governanceMetadata")
    async with db_connection() as conn:
        existing_idempotency = await _ensure_idempotency(
            conn,
            account_id=account_id,
            operation_type="UPSERT_PRODUCT_OFFERING",
            idempotency_key_hash=idempotency_key_hash,
            request_payload_hash=request_payload_hash,
        )
        if existing_idempotency:
            row = await _find_product_offering_row(
                conn,
                account_id=account_id,
                product_line_ref=product_line_ref,
                offering_ref=str(_row_value(existing_idempotency, "resource_id")),
            )
            return CustomerProductCatalogueCommandResult(
                command_status="PRODUCT_OFFERING_RECORDED",
                idempotency_status="REPLAY_SAME_PAYLOAD",
                resource_type="PRODUCT_OFFERING",
                resource=_offering_from_row(row),
            )

        line_row = await _find_product_line_row(
            conn,
            account_id=account_id,
            product_line_ref=product_line_ref,
        )
        safe_jurisdiction = _normalise_code(operating_jurisdiction_code, "operatingJurisdictionCode")
        if str(_row_value(line_row, "operating_jurisdiction_code")) != safe_jurisdiction:
            raise CustomerProductCatalogueValidationError(
                "Product offering jurisdiction must match its product line jurisdiction."
            )
        existing_row = await conn.fetchrow(
            """
            SELECT *
            FROM referral_saas_customer_product_offerings
            WHERE account_id = $1
              AND customer_product_line_id = $2
              AND UPPER(external_offering_ref) = UPPER($3)
              AND lifecycle_status NOT IN ('RETIRED', 'ARCHIVED')
            """,
            account_id,
            _row_value(line_row, "customer_product_line_id"),
            safe_offering_ref,
        )
        offering_values = (
            account_id,
            _row_value(line_row, "customer_product_line_id"),
            safe_offering_ref,
            _required_text(offering_name, "offeringName"),
            _optional_text(offering_family, max_length=120),
            safe_jurisdiction,
            safe_status,
            _optional_text(description),
            _jsonb(safe_summary_dict),
            _jsonb(governance_metadata_dict),
            request_payload_hash,
            idempotency_key_hash,
            correlation_id,
            actor_ref,
        )
        if existing_row:
            row = await conn.fetchrow(
                """
                UPDATE referral_saas_customer_product_offerings
                SET offering_name = $4,
                    offering_family = $5,
                    operating_jurisdiction_code = $6,
                    lifecycle_status = $7,
                    description = $8,
                    safe_summary = $9::jsonb,
                    governance_metadata = $10::jsonb,
                    payload_hash = $11,
                    idempotency_key_hash = $12,
                    correlation_id = $13,
                    updated_by_ref = $14,
                    updated_at = NOW(),
                    archived_at = CASE
                        WHEN $7 IN ('RETIRED', 'ARCHIVED') THEN NOW()
                        ELSE NULL
                    END
                WHERE account_id = $1
                  AND customer_product_offering_id = $2
                  AND customer_product_line_id = $3
                RETURNING *
                """,
                account_id,
                _row_value(existing_row, "customer_product_offering_id"),
                _row_value(line_row, "customer_product_line_id"),
                *offering_values[3:],
            )
        else:
            row = await conn.fetchrow(
                """
                INSERT INTO referral_saas_customer_product_offerings (
                    account_id, customer_product_line_id, external_offering_ref,
                    offering_name, offering_family, operating_jurisdiction_code,
                    lifecycle_status, description, safe_summary,
                    governance_metadata, payload_hash, idempotency_key_hash,
                    correlation_id, created_by_ref, updated_by_ref
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9::jsonb, $10::jsonb, $11, $12, $13, $14, $14)
                RETURNING *
                """,
                *offering_values,
            )
        offering = _offering_from_row(row)
        await _record_idempotency(
            conn,
            account_id=account_id,
            operation_type="UPSERT_PRODUCT_OFFERING",
            idempotency_key_hash=idempotency_key_hash,
            request_payload_hash=request_payload_hash,
            resource_type="PRODUCT_OFFERING",
            resource_id=offering.customer_product_offering_id,
        )
        await _record_audit(
            conn,
            account_id=account_id,
            product_line_id=offering.customer_product_line_id,
            offering_id=offering.customer_product_offering_id,
            event_type="PRODUCT_OFFERING_RECORDED",
            event_status="RECORDED",
            actor_ref=actor_ref,
            actor_role=actor_role,
            previous_status=str(_row_value(existing_row, "lifecycle_status")) if existing_row else None,
            next_status=offering.lifecycle_status,
            reason_code="UPSERT_PRODUCT_OFFERING",
            correlation_id=correlation_id,
            idempotency_key_hash=idempotency_key_hash,
        )
    return CustomerProductCatalogueCommandResult(
        command_status="PRODUCT_OFFERING_RECORDED",
        idempotency_status="NEW_REQUEST",
        resource_type="PRODUCT_OFFERING",
        resource=offering,
    )


async def retire_referral_saas_customer_product_line(
    *,
    account_id: str,
    product_line_ref: str,
    retirement_reason: str,
    idempotency_key_hash: str,
    request_payload_hash: str,
    actor_ref: str,
    actor_role: str,
    correlation_id: str | None = None,
) -> CustomerProductCatalogueCommandResult:
    reason = _required_text(retirement_reason, "retirementReason", max_length=500)
    async with db_connection() as conn:
        existing_idempotency = await _ensure_idempotency(
            conn,
            account_id=account_id,
            operation_type="RETIRE_PRODUCT_LINE",
            idempotency_key_hash=idempotency_key_hash,
            request_payload_hash=request_payload_hash,
        )
        if existing_idempotency:
            row = await conn.fetchrow(
                """
                SELECT *
                FROM referral_saas_customer_product_lines
                WHERE account_id = $1
                  AND customer_product_line_id::text = $2
                """,
                account_id,
                str(_row_value(existing_idempotency, "resource_id")),
            )
            if not row:
                raise CustomerProductCatalogueNotFound(product_line_ref)
            return CustomerProductCatalogueCommandResult(
                command_status="PRODUCT_LINE_RETIRED",
                idempotency_status="REPLAY_SAME_PAYLOAD",
                resource_type="PRODUCT_LINE",
                resource=_line_from_row(row),
            )
        line_row = await _find_product_line_row(
            conn,
            account_id=account_id,
            product_line_ref=product_line_ref,
        )
        active_offering_count = await conn.fetchval(
            """
            SELECT COUNT(*)
            FROM referral_saas_customer_product_offerings
            WHERE account_id = $1
              AND customer_product_line_id = $2
              AND lifecycle_status NOT IN ('RETIRED', 'ARCHIVED')
            """,
            account_id,
            _row_value(line_row, "customer_product_line_id"),
        )
        if int(active_offering_count or 0) > 0:
            raise CustomerProductCatalogueValidationError(
                "Retire product offerings before retiring their product line."
            )
        row = await conn.fetchrow(
            """
            UPDATE referral_saas_customer_product_lines
            SET lifecycle_status = 'RETIRED',
                archived_at = NOW(),
                updated_at = NOW(),
                updated_by_ref = $3,
                correlation_id = $4,
                idempotency_key_hash = $5
            WHERE account_id = $1
              AND customer_product_line_id = $2
            RETURNING *
            """,
            account_id,
            _row_value(line_row, "customer_product_line_id"),
            actor_ref,
            correlation_id,
            idempotency_key_hash,
        )
        line = _line_from_row(row)
        await _record_idempotency(
            conn,
            account_id=account_id,
            operation_type="RETIRE_PRODUCT_LINE",
            idempotency_key_hash=idempotency_key_hash,
            request_payload_hash=request_payload_hash,
            resource_type="PRODUCT_LINE",
            resource_id=line.customer_product_line_id,
        )
        await _record_audit(
            conn,
            account_id=account_id,
            product_line_id=line.customer_product_line_id,
            offering_id=None,
            event_type="PRODUCT_LINE_RETIRED",
            event_status="RECORDED",
            actor_ref=actor_ref,
            actor_role=actor_role,
            previous_status=str(_row_value(line_row, "lifecycle_status")),
            next_status="RETIRED",
            reason_code=reason,
            correlation_id=correlation_id,
            idempotency_key_hash=idempotency_key_hash,
        )
    return CustomerProductCatalogueCommandResult(
        command_status="PRODUCT_LINE_RETIRED",
        idempotency_status="NEW_REQUEST",
        resource_type="PRODUCT_LINE",
        resource=line,
    )


async def retire_referral_saas_customer_product_offering(
    *,
    account_id: str,
    product_line_ref: str,
    offering_ref: str,
    retirement_reason: str,
    idempotency_key_hash: str,
    request_payload_hash: str,
    actor_ref: str,
    actor_role: str,
    correlation_id: str | None = None,
) -> CustomerProductCatalogueCommandResult:
    reason = _required_text(retirement_reason, "retirementReason", max_length=500)
    async with db_connection() as conn:
        existing_idempotency = await _ensure_idempotency(
            conn,
            account_id=account_id,
            operation_type="RETIRE_PRODUCT_OFFERING",
            idempotency_key_hash=idempotency_key_hash,
            request_payload_hash=request_payload_hash,
        )
        if existing_idempotency:
            row = await conn.fetchrow(
                """
                SELECT *
                FROM referral_saas_customer_product_offerings
                WHERE account_id = $1
                  AND customer_product_offering_id::text = $2
                """,
                account_id,
                str(_row_value(existing_idempotency, "resource_id")),
            )
            if not row:
                raise CustomerProductCatalogueNotFound(offering_ref)
            return CustomerProductCatalogueCommandResult(
                command_status="PRODUCT_OFFERING_RETIRED",
                idempotency_status="REPLAY_SAME_PAYLOAD",
                resource_type="PRODUCT_OFFERING",
                resource=_offering_from_row(row),
            )
        offering_row = await _find_product_offering_row(
            conn,
            account_id=account_id,
            product_line_ref=product_line_ref,
            offering_ref=offering_ref,
        )
        row = await conn.fetchrow(
            """
            UPDATE referral_saas_customer_product_offerings
            SET lifecycle_status = 'RETIRED',
                archived_at = NOW(),
                updated_at = NOW(),
                updated_by_ref = $3,
                correlation_id = $4,
                idempotency_key_hash = $5
            WHERE account_id = $1
              AND customer_product_offering_id = $2
            RETURNING *
            """,
            account_id,
            _row_value(offering_row, "customer_product_offering_id"),
            actor_ref,
            correlation_id,
            idempotency_key_hash,
        )
        offering = _offering_from_row(row)
        await _record_idempotency(
            conn,
            account_id=account_id,
            operation_type="RETIRE_PRODUCT_OFFERING",
            idempotency_key_hash=idempotency_key_hash,
            request_payload_hash=request_payload_hash,
            resource_type="PRODUCT_OFFERING",
            resource_id=offering.customer_product_offering_id,
        )
        await _record_audit(
            conn,
            account_id=account_id,
            product_line_id=offering.customer_product_line_id,
            offering_id=offering.customer_product_offering_id,
            event_type="PRODUCT_OFFERING_RETIRED",
            event_status="RECORDED",
            actor_ref=actor_ref,
            actor_role=actor_role,
            previous_status=str(_row_value(offering_row, "lifecycle_status")),
            next_status="RETIRED",
            reason_code=reason,
            correlation_id=correlation_id,
            idempotency_key_hash=idempotency_key_hash,
        )
    return CustomerProductCatalogueCommandResult(
        command_status="PRODUCT_OFFERING_RETIRED",
        idempotency_status="NEW_REQUEST",
        resource_type="PRODUCT_OFFERING",
        resource=offering,
    )
