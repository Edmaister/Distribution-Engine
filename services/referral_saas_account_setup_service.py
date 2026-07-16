from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Final, Mapping

from services.onboarding import onboarding_draft_repository as draft_repo
from utils.db import db_connection

SOURCE_DRAFT_STATUS: Final = "READY_FOR_REVIEW"
ACCOUNT_STATUS_PENDING: Final = "PENDING_ONBOARDING"
ACCOUNT_ONBOARDING_STATUS: Final = "READY_FOR_REVIEW"
TENANT_LINK_STATUS: Final = "PENDING_SETUP"
REFERENCE_STATUS: Final = "ACTIVE"

ACCOUNT_TYPE_ORGANISATION: Final = "ORGANISATION"
ORGANISATION_TYPE_CUSTOMER: Final = "CUSTOMER_ORGANISATION"
RELATIONSHIP_OWNER: Final = "OWNER"

EVENT_ACCOUNT_FOUNDATION_CREATED: Final = "ACCOUNT_FOUNDATION_CREATED"
EVENT_RECORDED: Final = "RECORDED"

ONBOARDING_ACCOUNT_SETUP_ROLES: Final = frozenset(
    {
        "ADMIN",
        "SYSTEM_ADMIN",
        "DISTRIBUTION_ADMIN",
        "PLATFORM_ADMIN",
    }
)

NO_LIVE_ACTION_GUARDRAILS: Final = [
    "DURABLE_ACCOUNT_FOUNDATION_ONLY",
    "EXISTING_INTERNAL_TENANT_REQUIRED",
    "NO_TENANT_CREATION",
    "NO_MEMBERSHIP_WRITE",
    "NO_INVITE_DELIVERY",
    "NO_CAMPAIGN_PUBLICATION",
    "NO_CREDENTIAL_LIFECYCLE",
    "NO_WEBHOOK_DISPATCH",
    "NO_MONEY_MOVEMENT",
]


class AccountSetupCommandError(Exception):
    safe_code = "ACCOUNT_SETUP_COMMAND_FAILED"

    def __init__(self, message: str, *, safe_code: str | None = None):
        super().__init__(message)
        if safe_code:
            self.safe_code = safe_code


class AccountSetupPermissionDenied(AccountSetupCommandError):
    safe_code = "PERMISSION_DENIED"


class AccountSetupDraftNotFound(AccountSetupCommandError):
    safe_code = "DRAFT_NOT_FOUND"


class AccountSetupInvalidDraftState(AccountSetupCommandError):
    safe_code = "INVALID_DRAFT_STATE"


class AccountSetupMissingScope(AccountSetupCommandError):
    safe_code = "MISSING_ACCOUNT_SCOPE"


class AccountSetupDuplicateReference(AccountSetupCommandError):
    safe_code = "DUPLICATE_EXTERNAL_REFERENCE"


@dataclass(frozen=True)
class DurableAccountSetupResult:
    account_id: str
    account_code: str
    account_name: str
    account_status: str
    onboarding_status: str
    account_tenant_id: str
    tenant_link_status: str
    external_ref_id: str
    organisation_ref_id: str
    draft_ref: str
    audit_event_id: str | None
    guardrails: list[str]

    def to_safe_dict(self) -> dict[str, Any]:
        return {
            "accountId": self.account_id,
            "accountCode": self.account_code,
            "accountName": self.account_name,
            "accountStatus": self.account_status,
            "onboardingStatus": self.onboarding_status,
            "accountTenantId": self.account_tenant_id,
            "tenantLinkStatus": self.tenant_link_status,
            "externalRefId": self.external_ref_id,
            "organisationRefId": self.organisation_ref_id,
            "draftRef": self.draft_ref,
            "auditEventId": self.audit_event_id,
            "guardrails": list(self.guardrails),
            "redactions": ["internal_tenant_identifier"],
        }


async def create_durable_account_from_onboarding_draft(
    *,
    draft_ref: str,
    tenant_code: str,
    actor_ref: str,
    actor_role: str,
    correlation_id: str | None = None,
    idempotency_key_hash: str | None = None,
) -> DurableAccountSetupResult:
    role = _normalise_role(actor_role)
    if role not in ONBOARDING_ACCOUNT_SETUP_ROLES:
        raise AccountSetupPermissionDenied(
            "Actor is not authorised to create Referral SaaS account foundations."
        )

    safe_draft_ref = _safe_text(draft_ref)
    safe_tenant_code = _normalise_tenant_code(tenant_code)
    if not safe_draft_ref:
        raise AccountSetupDraftNotFound("Draft reference is required.")
    if not safe_tenant_code:
        raise AccountSetupMissingScope("Internal tenant scope is required.")

    draft = await draft_repo.get_draft_by_ref(safe_draft_ref)
    if not draft:
        raise AccountSetupDraftNotFound("Draft reference is missing or unavailable.")

    current_status = _safe_text(draft.get("status")).upper()
    if current_status != SOURCE_DRAFT_STATUS:
        raise AccountSetupInvalidDraftState(
            "Draft must be ready for review before durable account creation."
        )

    external_tenant_ref = _safe_text(draft.get("external_tenant_ref"))
    organisation_ref = _safe_text(draft.get("organisation_ref"))
    if not external_tenant_ref or not organisation_ref:
        raise AccountSetupMissingScope(
            "Draft external tenant and organisation references are required."
        )

    account_code = _account_code(external_tenant_ref, organisation_ref)
    account_name = _account_name(draft, organisation_ref)
    safe_summary = {
        "draft_ref": safe_draft_ref,
        "external_tenant_ref": external_tenant_ref,
        "organisation_ref": organisation_ref,
        "source": "referral_saas_account_setup",
        "no_live_action_confirmed": True,
    }
    metadata = {
        "source_draft_ref": safe_draft_ref,
        "source_draft_version": draft.get("draft_version"),
        "source": "TASK-203",
    }

    async with db_connection() as conn:
        duplicate_ref = await conn.fetchrow(
            """
            SELECT external_ref_id
            FROM platform_external_tenant_refs
            WHERE ref_type = $1
              AND external_ref = $2
              AND status IN ('PENDING', 'ACTIVE', 'SUSPENDED')
            LIMIT 1
            """,
            "external_tenant_ref",
            external_tenant_ref,
        )
        if duplicate_ref:
            raise AccountSetupDuplicateReference(
                "External tenant reference is already attached to an account."
            )

        async with conn.transaction():
            account = await conn.fetchrow(
                """
                INSERT INTO platform_accounts (
                    account_code,
                    account_name,
                    account_type,
                    status,
                    onboarding_status,
                    primary_external_tenant_ref,
                    safe_summary,
                    metadata,
                    created_by_ref,
                    updated_by_ref
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7::jsonb, $8::jsonb, $9, $9)
                RETURNING account_id, account_code, account_name, status, onboarding_status
                """,
                account_code,
                account_name,
                ACCOUNT_TYPE_ORGANISATION,
                ACCOUNT_STATUS_PENDING,
                ACCOUNT_ONBOARDING_STATUS,
                external_tenant_ref,
                _jsonb(safe_summary),
                _jsonb(metadata),
                _safe_text(actor_ref) or "ACCOUNT_SETUP_OPERATOR",
            )
            account_id = account["account_id"]

            await conn.fetchrow(
                """
                INSERT INTO platform_organisations (
                    account_id,
                    organisation_ref,
                    organisation_name,
                    organisation_type,
                    status,
                    safe_summary,
                    metadata
                )
                VALUES ($1, $2, $3, $4, 'ACTIVE', $5::jsonb, $6::jsonb)
                RETURNING organisation_id
                """,
                account_id,
                organisation_ref,
                account_name,
                ORGANISATION_TYPE_CUSTOMER,
                _jsonb(safe_summary),
                _jsonb(metadata),
            )

            account_tenant = await conn.fetchrow(
                """
                INSERT INTO platform_account_tenants (
                    account_id,
                    tenant_code,
                    relationship_type,
                    is_primary,
                    status,
                    safe_summary,
                    metadata
                )
                VALUES ($1, $2, $3, TRUE, $4, $5::jsonb, $6::jsonb)
                RETURNING account_tenant_id, status
                """,
                account_id,
                safe_tenant_code,
                RELATIONSHIP_OWNER,
                TENANT_LINK_STATUS,
                _jsonb(safe_summary),
                _jsonb(metadata),
            )
            account_tenant_id = account_tenant["account_tenant_id"]

            external_ref = await _insert_external_ref(
                conn=conn,
                account_id=account_id,
                account_tenant_id=account_tenant_id,
                tenant_code=safe_tenant_code,
                ref_type="external_tenant_ref",
                external_ref=external_tenant_ref,
                safe_summary=safe_summary,
                metadata=metadata,
            )
            organisation_external_ref = await _insert_external_ref(
                conn=conn,
                account_id=account_id,
                account_tenant_id=account_tenant_id,
                tenant_code=safe_tenant_code,
                ref_type="organisation_ref",
                external_ref=organisation_ref,
                safe_summary=safe_summary,
                metadata=metadata,
            )
            audit_event = await conn.fetchrow(
                """
                INSERT INTO platform_account_audit_events (
                    account_id,
                    account_tenant_id,
                    external_ref_id,
                    tenant_code,
                    event_type,
                    event_status,
                    actor_ref,
                    actor_role,
                    next_status,
                    reason_code,
                    correlation_id,
                    idempotency_key_hash,
                    evidence_summary,
                    redactions
                )
                VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8,
                    $9, $10, $11, $12, $13::jsonb, $14::jsonb
                )
                RETURNING account_audit_event_id
                """,
                account_id,
                account_tenant_id,
                external_ref["external_ref_id"],
                safe_tenant_code,
                EVENT_ACCOUNT_FOUNDATION_CREATED,
                EVENT_RECORDED,
                _safe_text(actor_ref) or "ACCOUNT_SETUP_OPERATOR",
                role,
                ACCOUNT_STATUS_PENDING,
                "APPROVED_SETUP_DRAFT",
                _safe_text(correlation_id) or None,
                _safe_text(idempotency_key_hash) or None,
                _jsonb(
                    {
                        "draft_ref": safe_draft_ref,
                        "account_code": account_code,
                        "external_reference_types": [
                            "external_tenant_ref",
                            "organisation_ref",
                        ],
                        "no_live_action_confirmed": True,
                    }
                ),
                _jsonb(["internal_tenant_identifier"]),
            )

    return DurableAccountSetupResult(
        account_id=str(account_id),
        account_code=str(account["account_code"]),
        account_name=str(account["account_name"]),
        account_status=str(account["status"]),
        onboarding_status=str(account["onboarding_status"]),
        account_tenant_id=str(account_tenant_id),
        tenant_link_status=str(account_tenant["status"]),
        external_ref_id=str(external_ref["external_ref_id"]),
        organisation_ref_id=str(organisation_external_ref["external_ref_id"]),
        draft_ref=safe_draft_ref,
        audit_event_id=(
            str(audit_event["account_audit_event_id"]) if audit_event else None
        ),
        guardrails=list(NO_LIVE_ACTION_GUARDRAILS),
    )


async def _insert_external_ref(
    *,
    conn: Any,
    account_id: str,
    account_tenant_id: str,
    tenant_code: str,
    ref_type: str,
    external_ref: str,
    safe_summary: Mapping[str, Any],
    metadata: Mapping[str, Any],
) -> Mapping[str, Any]:
    return await conn.fetchrow(
        """
        INSERT INTO platform_external_tenant_refs (
            account_id,
            account_tenant_id,
            tenant_code,
            ref_type,
            external_ref,
            status,
            source_system,
            safe_summary,
            metadata
        )
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8::jsonb, $9::jsonb)
        RETURNING external_ref_id, ref_type, external_ref, status
        """,
        account_id,
        account_tenant_id,
        tenant_code,
        ref_type,
        external_ref,
        REFERENCE_STATUS,
        "REFERRAL_SAAS_ACCOUNT_SETUP",
        _jsonb(safe_summary),
        _jsonb(metadata),
    )


def _account_code(external_tenant_ref: str, organisation_ref: str) -> str:
    digest = hashlib.sha256(
        f"{external_tenant_ref}|{organisation_ref}".encode("utf-8")
    ).hexdigest()
    return f"ACCT_{digest[:20].upper()}"


def _account_name(draft: Mapping[str, Any], organisation_ref: str) -> str:
    safe_summary = draft.get("safe_summary")
    if isinstance(safe_summary, Mapping):
        candidate = _safe_text(
            safe_summary.get("organisation_name") or safe_summary.get("account_name")
        )
        if candidate:
            return candidate
    return organisation_ref


def _normalise_role(value: Any) -> str:
    return _safe_text(value).upper()


def _normalise_tenant_code(value: Any) -> str:
    return _safe_text(value).upper()


def _safe_text(value: Any) -> str:
    return str(value or "").strip()


def _jsonb(value: Any) -> str:
    return json.dumps(value, sort_keys=True)
