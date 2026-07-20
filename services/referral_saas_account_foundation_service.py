from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any, Iterable

from utils.db import db_connection

ACTIVE_ACCOUNT_STATUSES = frozenset({"ACTIVE"})
ACTIVE_EXTERNAL_REFERENCE_STATUSES = frozenset({"ACTIVE"})
ACTIVE_TENANT_LINK_STATUSES = frozenset({"ACTIVE"})
SETUP_ACCOUNT_STATUSES = frozenset({"PENDING_ONBOARDING", "ACTIVE", "SUSPENDED"})
SETUP_TENANT_LINK_STATUSES = frozenset({"PENDING_SETUP", "ACTIVE", "SUSPENDED"})
PROFILE_MAINTENANCE_ROLES = frozenset(
    {"ADMIN", "SYSTEM_ADMIN", "DISTRIBUTION_ADMIN", "PLATFORM_ADMIN"}
)
PROFILE_MAINTENANCE_ACCOUNT_STATUSES = frozenset(
    {"PENDING_ONBOARDING", "ACTIVE", "SUSPENDED"}
)
PROFILE_MAINTENANCE_GUARDRAILS = [
    "DURABLE_PROFILE_FIELDS_ONLY",
    "NO_EXTERNAL_REFERENCE_ROTATION",
    "NO_ACCOUNT_ACTIVATION",
    "NO_MEMBERSHIP_WRITE",
    "NO_INVITE_DELIVERY",
    "NO_CREDENTIAL_LIFECYCLE",
    "NO_WEBHOOK_DISPATCH",
    "NO_CAMPAIGN_PUBLICATION",
    "NO_GO_LIVE_ACTION",
    "NO_MONEY_MOVEMENT",
]
PROFILE_MAINTENANCE_REDACTIONS = [
    "internal_tenant_identifier",
    "raw_secret",
    "idempotency_key_hash",
]
ALLOWED_PROFILE_ACCOUNT_TYPES = frozenset(
    {
        "ORGANISATION",
        "PRODUCER",
        "PARTNER",
        "DISTRIBUTOR",
        "SPONSOR",
        "MIXED",
    }
)
ALLOWED_PROFILE_JURISDICTIONS = frozenset({"ZA", "BW", "NA", "ZM", "OTHER"})
ALLOWED_CUSTOMER_TYPES = frozenset(
    {"DIRECT_CUSTOMER", "ENTERPRISE_CUSTOMER", "PARTNER_MANAGED_CUSTOMER"}
)
ALLOWED_INDUSTRIES = frozenset(
    {
        "BANKING_FINANCIAL_SERVICES",
        "INSURANCE",
        "TELECOMS",
        "RETAIL_ECOMMERCE",
        "AUTOMOTIVE",
        "REAL_ESTATE",
        "EDUCATION",
        "HEALTHCARE",
        "TRAVEL_HOSPITALITY",
        "OTHER",
    }
)

EXTERNAL_REFERENCE_TYPES = frozenset(
    {
        "external_tenant_ref",
        "organisation_ref",
        "producer_ref",
        "partner_ref",
        "distributor_ref",
        "sponsor_ref",
    }
)


class AccountFoundationResolutionError(Exception):
    """Base error for safe account foundation resolution failures."""

    safe_code = "ACCOUNT_RESOLUTION_FAILED"

    def __init__(self, message: str, *, safe_code: str | None = None):
        super().__init__(message)
        if safe_code:
            self.safe_code = safe_code


class InvalidExternalReferenceType(AccountFoundationResolutionError):
    safe_code = "INVALID_EXTERNAL_REFERENCE_TYPE"


class ExternalReferenceNotFound(AccountFoundationResolutionError):
    safe_code = "EXTERNAL_REFERENCE_NOT_FOUND"


class ExternalReferenceNotActive(AccountFoundationResolutionError):
    safe_code = "EXTERNAL_REFERENCE_NOT_ACTIVE"


class ExternalReferenceConflict(AccountFoundationResolutionError):
    safe_code = "EXTERNAL_REFERENCE_CONFLICT"


class AccountNotResolvable(AccountFoundationResolutionError):
    safe_code = "ACCOUNT_NOT_RESOLVABLE"


class TenantLinkNotResolvable(AccountFoundationResolutionError):
    safe_code = "TENANT_LINK_NOT_RESOLVABLE"


class AccountProfileMaintenanceError(Exception):
    safe_code = "ACCOUNT_PROFILE_MAINTENANCE_FAILED"

    def __init__(self, message: str, *, safe_code: str | None = None):
        super().__init__(message)
        if safe_code:
            self.safe_code = safe_code


class AccountProfilePermissionDenied(AccountProfileMaintenanceError):
    safe_code = "PERMISSION_DENIED"


class AccountProfileValidationError(AccountProfileMaintenanceError):
    safe_code = "VALIDATION_ERROR"


class AccountProfileNotFound(AccountProfileMaintenanceError):
    safe_code = "ACCOUNT_NOT_FOUND"


class AccountProfileNotMaintainable(AccountProfileMaintenanceError):
    safe_code = "ACCOUNT_NOT_MAINTAINABLE"


class AccountProfileUnsafePayload(AccountProfileMaintenanceError):
    safe_code = "REJECTED_UNSAFE_PAYLOAD"


@dataclass(frozen=True)
class AccountFoundationContext:
    account_id: str
    account_code: str
    account_name: str
    account_type: str
    account_status: str
    onboarding_status: str
    external_ref_id: str
    ref_type: str
    external_ref: str
    reference_status: str
    tenant_code: str
    account_tenant_id: str | None
    relationship_type: str | None
    tenant_link_status: str | None
    is_primary: bool
    source: str = "external_reference"

    def to_safe_dict(self, *, include_internal: bool = False) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "accountId": self.account_id,
            "accountCode": self.account_code,
            "accountName": self.account_name,
            "accountType": self.account_type,
            "accountStatus": self.account_status,
            "onboardingStatus": self.onboarding_status,
            "externalRefId": self.external_ref_id,
            "refType": self.ref_type,
            "externalRef": self.external_ref,
            "referenceStatus": self.reference_status,
            "accountTenantId": self.account_tenant_id,
            "relationshipType": self.relationship_type,
            "tenantLinkStatus": self.tenant_link_status,
            "isPrimary": self.is_primary,
            "source": self.source,
        }
        if include_internal:
            payload["tenantCode"] = self.tenant_code
        return payload


@dataclass(frozen=True)
class AccountFoundationListItem:
    account_id: str
    account_code: str
    account_name: str
    account_type: str
    account_status: str
    onboarding_status: str
    operating_jurisdiction_code: str
    primary_external_tenant_ref: str | None
    external_references: tuple[dict[str, str], ...]
    created_at: str
    updated_at: str

    def to_safe_dict(self) -> dict[str, Any]:
        return {
            "accountId": self.account_id,
            "accountCode": self.account_code,
            "accountName": self.account_name,
            "accountType": self.account_type,
            "accountStatus": self.account_status,
            "onboardingStatus": self.onboarding_status,
            "operatingJurisdictionCode": self.operating_jurisdiction_code,
            "primaryExternalTenantRef": self.primary_external_tenant_ref,
            "externalReferences": list(self.external_references),
            "createdAt": self.created_at,
            "updatedAt": self.updated_at,
        }


@dataclass(frozen=True)
class AccountProfileMaintenanceResult:
    account_id: str
    account_code: str
    account_name: str
    account_type: str
    account_status: str
    onboarding_status: str
    operating_jurisdiction_code: str
    customer_type: str | None
    industry: str | None
    audit_event_id: str | None
    guardrails: list[str]
    redactions: list[str]

    def to_safe_dict(self) -> dict[str, Any]:
        return {
            "accountId": self.account_id,
            "accountCode": self.account_code,
            "accountName": self.account_name,
            "accountType": self.account_type,
            "accountStatus": self.account_status,
            "onboardingStatus": self.onboarding_status,
            "operatingJurisdictionCode": self.operating_jurisdiction_code,
            "customerType": self.customer_type,
            "industry": self.industry,
            "auditEventId": self.audit_event_id,
            "guardrails": list(self.guardrails),
            "redactions": list(self.redactions),
        }


def _normalise_ref_type(ref_type: str) -> str:
    normalised = str(ref_type or "").strip()
    if normalised not in EXTERNAL_REFERENCE_TYPES:
        raise InvalidExternalReferenceType(
            "External reference type is not supported for Referral SaaS account resolution."
        )
    return normalised


def _normalise_external_ref(external_ref: str) -> str:
    normalised = str(external_ref or "").strip()
    if not normalised:
        raise ExternalReferenceNotFound("External reference is required.")
    return normalised


def _normalise_status_set(values: Iterable[str]) -> frozenset[str]:
    return frozenset(str(value or "").strip().upper() for value in values if value)


def _as_context(row: dict[str, Any]) -> AccountFoundationContext:
    return AccountFoundationContext(
        account_id=str(row["account_id"]),
        account_code=str(row["account_code"]),
        account_name=str(row["account_name"]),
        account_type=str(row["account_type"]),
        account_status=str(row["account_status"]),
        onboarding_status=str(row["onboarding_status"]),
        external_ref_id=str(row["external_ref_id"]),
        ref_type=str(row["ref_type"]),
        external_ref=str(row["external_ref"]),
        reference_status=str(row["reference_status"]),
        tenant_code=str(row["tenant_code"]),
        account_tenant_id=(
            str(row["account_tenant_id"]) if row.get("account_tenant_id") else None
        ),
        relationship_type=(
            str(row["relationship_type"]) if row.get("relationship_type") else None
        ),
        tenant_link_status=(
            str(row["tenant_link_status"]) if row.get("tenant_link_status") else None
        ),
        is_primary=bool(row.get("is_primary")),
    )


async def resolve_account_by_external_reference(
    *,
    ref_type: str,
    external_ref: str,
    allowed_account_statuses: Iterable[str] = ACTIVE_ACCOUNT_STATUSES,
    allowed_reference_statuses: Iterable[str] = ACTIVE_EXTERNAL_REFERENCE_STATUSES,
    allowed_tenant_link_statuses: Iterable[str] = ACTIVE_TENANT_LINK_STATUSES,
) -> AccountFoundationContext:
    safe_ref_type = _normalise_ref_type(ref_type)
    safe_external_ref = _normalise_external_ref(external_ref)
    account_statuses = _normalise_status_set(allowed_account_statuses)
    reference_statuses = _normalise_status_set(allowed_reference_statuses)
    tenant_link_statuses = _normalise_status_set(allowed_tenant_link_statuses)

    async with db_connection() as conn:
        rows = await conn.fetch(
            """
            SELECT
                account.account_id,
                account.account_code,
                account.account_name,
                account.account_type,
                account.status AS account_status,
                account.onboarding_status,
                external_ref.external_ref_id,
                external_ref.ref_type,
                external_ref.external_ref,
                external_ref.status AS reference_status,
                external_ref.tenant_code,
                account_tenant.account_tenant_id,
                account_tenant.relationship_type,
                account_tenant.status AS tenant_link_status,
                COALESCE(account_tenant.is_primary, FALSE) AS is_primary
            FROM platform_external_tenant_refs external_ref
            JOIN platform_accounts account
                ON account.account_id = external_ref.account_id
            LEFT JOIN platform_account_tenants account_tenant
                ON account_tenant.account_tenant_id = external_ref.account_tenant_id
                OR (
                    account_tenant.account_id = external_ref.account_id
                    AND account_tenant.tenant_code = external_ref.tenant_code
                    AND account_tenant.status <> 'ARCHIVED'
                )
            WHERE external_ref.ref_type = $1
              AND external_ref.external_ref = $2
            ORDER BY
                CASE WHEN external_ref.status = 'ACTIVE' THEN 0 ELSE 1 END,
                external_ref.updated_at DESC
            LIMIT 2
            """,
            safe_ref_type,
            safe_external_ref,
        )

    if not rows:
        raise ExternalReferenceNotFound("External reference was not found.")

    active_reference_rows = [
        dict(row)
        for row in rows
        if str(row["reference_status"]).upper() in reference_statuses
    ]
    if len(active_reference_rows) > 1:
        raise ExternalReferenceConflict(
            "External reference resolved to multiple active account scopes."
        )
    if not active_reference_rows:
        raise ExternalReferenceNotActive(
            "External reference is not active for Referral SaaS account resolution."
        )

    context = _as_context(active_reference_rows[0])
    if context.account_status.upper() not in account_statuses:
        raise AccountNotResolvable(
            "Account is not in an allowed state for Referral SaaS account resolution."
        )
    if not context.account_tenant_id:
        raise TenantLinkNotResolvable(
            "Account does not have a tenant link for Referral SaaS account resolution."
        )
    if (context.tenant_link_status or "").upper() not in tenant_link_statuses:
        raise TenantLinkNotResolvable(
            "Account tenant link is not in an allowed state for Referral SaaS account resolution."
        )

    return context


async def resolve_setup_account_by_external_reference(
    *,
    ref_type: str,
    external_ref: str,
) -> AccountFoundationContext:
    return await resolve_account_by_external_reference(
        ref_type=ref_type,
        external_ref=external_ref,
        allowed_account_statuses=SETUP_ACCOUNT_STATUSES,
        allowed_tenant_link_statuses=SETUP_TENANT_LINK_STATUSES,
    )


async def list_referral_saas_accounts(*, limit: int = 50) -> list[AccountFoundationListItem]:
    safe_limit = max(1, min(int(limit or 50), 100))
    async with db_connection() as conn:
        rows = await conn.fetch(
            """
            SELECT
                account.account_id,
                account.account_code,
                account.account_name,
                account.account_type,
                account.status AS account_status,
                account.onboarding_status,
                COALESCE(account.operating_jurisdiction_code, 'ZA') AS operating_jurisdiction_code,
                account.primary_external_tenant_ref,
                account.created_at,
                account.updated_at,
                COALESCE(
                    jsonb_agg(
                        jsonb_build_object(
                            'refType', external_ref.ref_type,
                            'externalRef', external_ref.external_ref,
                            'referenceStatus', external_ref.status
                        )
                        ORDER BY
                            CASE external_ref.ref_type
                                WHEN 'external_tenant_ref' THEN 0
                                WHEN 'organisation_ref' THEN 1
                                ELSE 2
                            END,
                            external_ref.updated_at DESC
                    ) FILTER (WHERE external_ref.external_ref_id IS NOT NULL),
                    '[]'::jsonb
                ) AS external_references
            FROM platform_accounts account
            LEFT JOIN platform_external_tenant_refs external_ref
                ON external_ref.account_id = account.account_id
               AND external_ref.status = 'ACTIVE'
            WHERE account.status IN ('PENDING_ONBOARDING', 'ACTIVE', 'SUSPENDED')
              AND account.archived_at IS NULL
            GROUP BY account.account_id
            ORDER BY account.updated_at DESC, account.created_at DESC
            LIMIT $1
            """,
            safe_limit,
        )

    accounts: list[AccountFoundationListItem] = []
    for raw_row in rows:
        row = dict(raw_row)
        external_references = _normalise_external_reference_rows(
            row["external_references"]
        )
        accounts.append(
            AccountFoundationListItem(
                account_id=str(row["account_id"]),
                account_code=str(row["account_code"]),
                account_name=str(row["account_name"]),
                account_type=str(row["account_type"]),
                account_status=str(row["account_status"]),
                onboarding_status=str(row["onboarding_status"]),
                operating_jurisdiction_code=str(
                    row.get("operating_jurisdiction_code") or "ZA"
                ),
                primary_external_tenant_ref=(
                    str(row["primary_external_tenant_ref"])
                    if row.get("primary_external_tenant_ref")
                    else None
                ),
                external_references=tuple(
                    {
                        "refType": str(ref.get("refType") or ""),
                        "externalRef": str(ref.get("externalRef") or ""),
                        "referenceStatus": str(ref.get("referenceStatus") or ""),
                    }
                    for ref in external_references
                    if ref.get("refType") and ref.get("externalRef")
                ),
                created_at=row["created_at"].isoformat(),
                updated_at=row["updated_at"].isoformat(),
            )
        )
    return accounts


async def update_referral_saas_account_profile(
    *,
    account_ref: str,
    account_name: str,
    account_type: str,
    operating_jurisdiction_code: str,
    customer_type: str | None,
    industry: str | None,
    actor_ref: str,
    actor_role: str,
    correlation_id: str | None = None,
    idempotency_key_hash: str | None = None,
    command_payload_hash: str | None = None,
) -> AccountProfileMaintenanceResult:
    role = _safe_text(actor_role).upper()
    if role not in PROFILE_MAINTENANCE_ROLES:
        raise AccountProfilePermissionDenied(
            "Actor is not authorised to maintain Referral SaaS account profiles."
        )

    safe_account_ref = _safe_text(account_ref)
    safe_account_name = _safe_text(account_name)
    safe_account_type = _safe_text(account_type).upper()
    safe_jurisdiction = _safe_text(operating_jurisdiction_code).upper()
    safe_customer_type = _safe_text(customer_type).upper() if customer_type else None
    safe_industry = _safe_text(industry).upper() if industry else None

    if not safe_account_ref:
        raise AccountProfileNotFound("Account reference is required.")
    if len(safe_account_name) < 2 or len(safe_account_name) > 160:
        raise AccountProfileValidationError(
            "Customer name must be between 2 and 160 characters."
        )
    if safe_account_type not in ALLOWED_PROFILE_ACCOUNT_TYPES:
        raise AccountProfileValidationError("Account type is not supported.")
    if safe_jurisdiction not in ALLOWED_PROFILE_JURISDICTIONS:
        raise AccountProfileValidationError("Operating jurisdiction is not supported.")
    if safe_customer_type and safe_customer_type not in ALLOWED_CUSTOMER_TYPES:
        raise AccountProfileValidationError("Customer type is not supported.")
    if safe_industry and safe_industry not in ALLOWED_INDUSTRIES:
        raise AccountProfileValidationError("Industry is not supported.")

    profile_summary = {
        "customer_type": safe_customer_type,
        "industry": safe_industry,
        "source": "referral_saas_customer_profile_maintenance",
        "no_live_action_confirmed": True,
    }
    metadata = {
        "customer_type": safe_customer_type,
        "industry": safe_industry,
        "source": "TASK-238",
        "command_payload_hash": _safe_text(command_payload_hash) or None,
    }

    async with db_connection() as conn:
        current = await conn.fetchrow(
            """
            SELECT
                account_id,
                account_code,
                account_name,
                account_type,
                status AS account_status,
                onboarding_status,
                COALESCE(operating_jurisdiction_code, 'ZA') AS operating_jurisdiction_code
            FROM platform_accounts
            WHERE (account_id::text = $1 OR account_code = $1)
              AND archived_at IS NULL
            LIMIT 1
            """,
            safe_account_ref,
        )
        if not current:
            raise AccountProfileNotFound("Account was not found.")
        if str(current["account_status"]).upper() not in PROFILE_MAINTENANCE_ACCOUNT_STATUSES:
            raise AccountProfileNotMaintainable(
                "Account is not in a maintainable state for profile updates."
            )

        async with conn.transaction():
            updated = await conn.fetchrow(
                """
                UPDATE platform_accounts
                SET account_name = $2,
                    account_type = $3,
                    operating_jurisdiction_code = $4,
                    safe_summary = COALESCE(safe_summary, '{}'::jsonb) || $5::jsonb,
                    metadata = COALESCE(metadata, '{}'::jsonb) || $6::jsonb,
                    updated_by_ref = $7,
                    updated_at = NOW()
                WHERE account_id = $1
                RETURNING
                    account_id,
                    account_code,
                    account_name,
                    account_type,
                    status AS account_status,
                    onboarding_status,
                    operating_jurisdiction_code
                """,
                current["account_id"],
                safe_account_name,
                safe_account_type,
                safe_jurisdiction,
                _jsonb(profile_summary),
                _jsonb(metadata),
                _safe_text(actor_ref) or "REFERRAL_SAAS_ACCOUNT_OPERATOR",
            )
            audit_event = await conn.fetchrow(
                """
                INSERT INTO platform_account_audit_events (
                    account_id,
                    event_type,
                    event_status,
                    actor_ref,
                    actor_role,
                    previous_status,
                    next_status,
                    reason_code,
                    correlation_id,
                    idempotency_key_hash,
                    evidence_summary,
                    redactions
                )
                VALUES (
                    $1, 'ACCOUNT_PROFILE_UPDATED', 'RECORDED', $2, $3,
                    $4, $5, 'CUSTOMER_PROFILE_MAINTENANCE', $6, $7,
                    $8::jsonb, $9::jsonb
                )
                RETURNING account_audit_event_id
                """,
                current["account_id"],
                _safe_text(actor_ref) or "REFERRAL_SAAS_ACCOUNT_OPERATOR",
                role,
                str(current["account_status"]),
                str(updated["account_status"]),
                _safe_text(correlation_id) or None,
                _safe_text(idempotency_key_hash) or None,
                _jsonb(
                    {
                        "changed_fields": [
                            "account_name",
                            "account_type",
                            "operating_jurisdiction_code",
                            "customer_type",
                            "industry",
                        ],
                        "previous_account_name": str(current["account_name"]),
                        "previous_operating_jurisdiction_code": str(
                            current["operating_jurisdiction_code"]
                        ),
                        "no_external_reference_rotation_confirmed": True,
                        "no_live_action_confirmed": True,
                    }
                ),
                _jsonb(PROFILE_MAINTENANCE_REDACTIONS),
            )

    return AccountProfileMaintenanceResult(
        account_id=str(updated["account_id"]),
        account_code=str(updated["account_code"]),
        account_name=str(updated["account_name"]),
        account_type=str(updated["account_type"]),
        account_status=str(updated["account_status"]),
        onboarding_status=str(updated["onboarding_status"]),
        operating_jurisdiction_code=str(updated["operating_jurisdiction_code"]),
        customer_type=safe_customer_type,
        industry=safe_industry,
        audit_event_id=(
            str(audit_event["account_audit_event_id"]) if audit_event else None
        ),
        guardrails=list(PROFILE_MAINTENANCE_GUARDRAILS),
        redactions=list(PROFILE_MAINTENANCE_REDACTIONS),
    )


def _normalise_external_reference_rows(value: Any) -> list[dict[str, Any]]:
    if not value:
        return []
    if isinstance(value, str):
        decoded = json.loads(value)
        return decoded if isinstance(decoded, list) else []
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    return []


def _safe_text(value: Any) -> str:
    return str(value or "").strip()


def _jsonb(value: Any) -> str:
    return json.dumps(value, sort_keys=True)
