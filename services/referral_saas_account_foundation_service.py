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
ACCOUNT_FOUNDATION_ACTIVATION_ROLES = frozenset(
    {"ADMIN", "SYSTEM_ADMIN", "DISTRIBUTION_ADMIN", "PLATFORM_ADMIN"}
)
ACCOUNT_FOUNDATION_ACTIVATION_GUARDRAILS = [
    "AMPLIFI_ADMIN_ONLY",
    "ACCOUNT_FOUNDATION_ONLY",
    "ACTIVE_TENANT_LINK_REQUIRED",
    "ACTIVE_EXTERNAL_REFERENCES_REQUIRED",
    "AVAILABLE_SEAT_CAPACITY_ONLY",
    "NO_MEMBERSHIP_WRITE",
    "NO_SEAT_ASSIGNMENT",
    "NO_INVITE_DELIVERY",
    "NO_AUTH_CLAIM_CHANGE",
    "NO_CREDENTIAL_LIFECYCLE",
    "NO_CAMPAIGN_ACTIVATION",
    "NO_GO_LIVE_ACTION",
    "NO_BILLING_OR_MONEY_MOVEMENT",
]
ACCOUNT_FOUNDATION_ACTIVATION_REDACTIONS = [
    "internal_tenant_identifier",
    "idempotency_key_hash",
    "raw_secret",
    "auth_claim",
    "credential",
]
ACCOUNT_FOUNDATION_ACTIVATION_EVENT_TYPE = "ACCOUNT_FOUNDATION_ACTIVATION_REQUESTED"
ACCOUNT_FOUNDATION_ACTIVATION_REASON = "CUSTOMER_ACCOUNT_FOUNDATION_ACTIVATION"
DEFAULT_ACCOUNT_FOUNDATION_SEAT_TYPES = ("ADMIN", "OPERATOR")
ALLOWED_ACCOUNT_FOUNDATION_SEAT_TYPES = frozenset(
    {"ADMIN", "OPERATOR", "PARTNER", "PRODUCER", "DISTRIBUTOR", "CONSUMER", "SUPPORT"}
)
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
COMMERCIAL_ENTITLEMENT_GUARDRAILS = [
    "REFERRAL_SAAS_H1_ENTITLEMENT_POSTURE",
    "READ_ONLY_COMMERCIAL_POSTURE",
    "PLAN_LIMIT_REFERENCE_ONLY",
    "NO_BILLING_RECORD_CREATED",
    "NO_INVOICE_CREATED",
    "NO_PAYMENT_OR_MONEY_MOVEMENT",
    "NO_DLAAS_FINANCE_SCOPE",
]
COMMERCIAL_ENTITLEMENT_REDACTIONS = [
    "internal_tenant_identifier",
    "billing_account_identifier",
    "invoice_identifier",
    "payment_method",
    "contract_document",
]
COMMERCIAL_FINANCE_H1_ENTITLEMENT_FIELDS = [
    "planCode",
    "planName",
    "contractSource",
    "launchAllowed",
    "productionActivationBlocked",
    "referenceLimits",
]
COMMERCIAL_FINANCE_H1_DEFERRED_CAPABILITIES = [
    "billingAccounts",
    "subscriptions",
    "invoices",
    "payments",
    "payouts",
    "funding",
    "settlement",
    "walletLedger",
    "commissionLedger",
    "treasuryMovement",
]
COMMERCIAL_FINANCE_DLAAS_STARTS_AT = [
    "sponsorBilling",
    "fundingOperations",
    "settlementBatches",
    "commissionSettlement",
    "payoutExecution",
    "walletLedgerMovement",
]
PRODUCTION_ACTIVATION_GUARDRAILS = [
    "BACKEND_PRODUCTION_ACTIVATION_DECISION_REQUIRED",
    "ACCOUNT_FOUNDATION_GATE_REQUIRED",
    "PEOPLE_ACCESS_GATE_REQUIRED",
    "INTEGRATIONS_GATE_REQUIRED",
    "CAMPAIGN_GATE_REQUIRED",
    "COMMERCIAL_ENTITLEMENT_GATE_REQUIRED",
    "EVIDENCE_FRESHNESS_GATE_REQUIRED",
    "NO_UI_ONLY_ACTIVATION",
    "NO_BILLING_OR_MONEY_MOVEMENT",
]
PRODUCTION_ACTIVATION_REDACTIONS = [
    "internal_tenant_identifier",
    "billing_account_identifier",
    "invoice_identifier",
    "payment_method",
    "contract_document",
    "raw_secret",
    "auth_claim",
    "credential",
]
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


class AccountFoundationActivationError(Exception):
    safe_code = "ACCOUNT_FOUNDATION_ACTIVATION_FAILED"

    def __init__(self, message: str, *, safe_code: str | None = None):
        super().__init__(message)
        if safe_code:
            self.safe_code = safe_code


class AccountFoundationActivationPermissionDenied(AccountFoundationActivationError):
    safe_code = "PERMISSION_DENIED"


class AccountFoundationActivationValidationError(AccountFoundationActivationError):
    safe_code = "VALIDATION_ERROR"


class AccountFoundationActivationNotFound(AccountFoundationActivationError):
    safe_code = "ACCOUNT_NOT_FOUND"


class AccountFoundationActivationNotReady(AccountFoundationActivationError):
    safe_code = "ACCOUNT_FOUNDATION_NOT_READY"


class AccountFoundationActivationIdempotencyConflict(
    AccountFoundationActivationError
):
    safe_code = "IDEMPOTENCY_CONFLICT"


@dataclass(frozen=True)
class AccountFoundationContext:
    account_id: str
    account_code: str
    account_name: str
    account_type: str
    account_status: str
    onboarding_status: str
    operating_jurisdiction_code: str
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
            "operatingJurisdictionCode": self.operating_jurisdiction_code,
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
class PartnerWorkspaceAccountContextItem:
    account_id: str
    account_code: str
    account_name: str
    account_type: str
    account_status: str
    onboarding_status: str
    operating_jurisdiction_code: str
    primary_external_tenant_ref: str | None
    external_references: tuple[dict[str, str], ...]
    role_families: tuple[str, ...]
    permission_sets: tuple[str, ...]
    membership_statuses: tuple[str, ...]
    source: str

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
            "actorAccess": {
                "roleFamilies": list(self.role_families),
                "permissionSets": list(self.permission_sets),
                "membershipStatuses": list(self.membership_statuses),
                "source": self.source,
            },
        }


@dataclass(frozen=True)
class PartnerWorkspaceAccountContext:
    actor_role: str
    accounts: tuple[PartnerWorkspaceAccountContextItem, ...]
    guardrails: tuple[str, ...]
    redactions: tuple[str, ...]

    def to_safe_dict(self) -> dict[str, Any]:
        return {
            "actor": {
                "role": self.actor_role,
                "accountCount": len(self.accounts),
            },
            "accounts": [account.to_safe_dict() for account in self.accounts],
            "guardrails": list(self.guardrails),
            "redactions": list(self.redactions),
            "noInternalTenantIdentifierExposureConfirmed": True,
            "noCrossAccountAccessConfirmed": True,
            "noCrossJurisdictionAccessConfirmed": True,
            "noMembershipWriteConfirmed": True,
            "noInviteDeliveryConfirmed": True,
            "noAuthClaimChangeConfirmed": True,
            "noMoneyMovementConfirmed": True,
        }


@dataclass(frozen=True)
class WorkspaceOverviewAction:
    action_ref: str
    label: str
    status: str
    priority: str
    route_hint: str
    reason: str
    required_capability: str

    def to_safe_dict(self) -> dict[str, str]:
        return {
            "actionRef": self.action_ref,
            "label": self.label,
            "status": self.status,
            "priority": self.priority,
            "routeHint": self.route_hint,
            "reason": self.reason,
            "requiredCapability": self.required_capability,
        }


@dataclass(frozen=True)
class WorkspaceOverviewProjection:
    actor_role: str
    selected_account: PartnerWorkspaceAccountContextItem | None
    visible_account_count: int
    readiness: dict[str, Any]
    primary_action: WorkspaceOverviewAction | None
    worklist: tuple[WorkspaceOverviewAction, ...]
    plain_language_summary: str
    safe_to_leave: dict[str, Any]
    guardrails: tuple[str, ...]
    redactions: tuple[str, ...]

    def to_safe_dict(self) -> dict[str, Any]:
        return {
            "actor": {
                "role": self.actor_role,
                "visibleAccountCount": self.visible_account_count,
            },
            "selectedAccount": (
                self.selected_account.to_safe_dict()
                if self.selected_account is not None
                else None
            ),
            "readiness": self.readiness,
            "primaryAction": (
                self.primary_action.to_safe_dict()
                if self.primary_action is not None
                else None
            ),
            "worklist": [action.to_safe_dict() for action in self.worklist],
            "plainLanguageSummary": self.plain_language_summary,
            "safeToLeave": self.safe_to_leave,
            "guardrails": list(self.guardrails),
            "redactions": list(self.redactions),
            "noInternalTenantIdentifierExposureConfirmed": True,
            "noUnscopedAccountEnumerationConfirmed": True,
            "noMembershipWriteConfirmed": True,
            "noInviteDeliveryConfirmed": True,
            "noSeatAssignmentConfirmed": True,
            "noAuthClaimChangeConfirmed": True,
            "noCampaignActivationConfirmed": True,
            "noMoneyMovementConfirmed": True,
        }


@dataclass(frozen=True)
class CommercialEntitlementFeature:
    feature_ref: str
    label: str
    status: str
    reason: str
    route_hint: str

    def to_safe_dict(self) -> dict[str, str]:
        return {
            "featureRef": self.feature_ref,
            "label": self.label,
            "status": self.status,
            "reason": self.reason,
            "routeHint": self.route_hint,
        }


@dataclass(frozen=True)
class CommercialEntitlementProjection:
    account_id: str
    account_code: str
    account_name: str
    overall_status: str
    commercial_status: str
    environment_status: str
    plan_code: str
    plan_name: str
    contract_source: str
    launch_allowed: bool
    production_activation_blocked: bool
    limits: dict[str, Any]
    features: tuple[CommercialEntitlementFeature, ...]
    disabled_reasons: tuple[str, ...]
    next_actions: tuple[WorkspaceOverviewAction, ...]
    plain_language_summary: str
    guardrails: tuple[str, ...]
    redactions: tuple[str, ...]

    def to_safe_dict(self) -> dict[str, Any]:
        return {
            "accountId": self.account_id,
            "accountCode": self.account_code,
            "accountName": self.account_name,
            "overallStatus": self.overall_status,
            "commercialStatus": self.commercial_status,
            "environmentStatus": self.environment_status,
            "plan": {
                "planCode": self.plan_code,
                "planName": self.plan_name,
                "contractSource": self.contract_source,
            },
            "launchAllowed": self.launch_allowed,
            "productionActivationBlocked": self.production_activation_blocked,
            "limits": self.limits,
            "features": [feature.to_safe_dict() for feature in self.features],
            "disabledReasons": list(self.disabled_reasons),
            "nextActions": [action.to_safe_dict() for action in self.next_actions],
            "plainLanguageSummary": self.plain_language_summary,
            "guardrails": list(self.guardrails),
            "redactions": list(self.redactions),
            "noBillingRecordCreatedConfirmed": True,
            "noInvoiceCreatedConfirmed": True,
            "noPaymentOrMoneyMovementConfirmed": True,
            "noDlaasFinanceScopeConfirmed": True,
            "commercialFinanceBoundary": {
                "scope": "SEPARATELY_CONTRACTED",
                "h1EntitlementFields": list(COMMERCIAL_FINANCE_H1_ENTITLEMENT_FIELDS),
                "h1DeferredCapabilities": list(COMMERCIAL_FINANCE_H1_DEFERRED_CAPABILITIES),
                "dlaasFinanceStartsAt": list(COMMERCIAL_FINANCE_DLAAS_STARTS_AT),
                "nextAction": (
                    "Keep Referral SaaS in safe setup/launch posture. Use a "
                    "separately contracted commercial-finance workstream for "
                    "billing, invoices, funding, settlement, payouts, or money "
                    "movement."
                ),
            },
        }


@dataclass(frozen=True)
class ProductionActivationGate:
    gate_ref: str
    label: str
    status: str
    reason: str
    next_action: str
    route_hint: str

    def to_safe_dict(self) -> dict[str, str]:
        return {
            "gateRef": self.gate_ref,
            "label": self.label,
            "status": self.status,
            "reason": self.reason,
            "nextAction": self.next_action,
            "routeHint": self.route_hint,
        }


@dataclass(frozen=True)
class ProductionActivationDecision:
    account_id: str
    account_code: str
    account_name: str
    decision_status: str
    launch_allowed: bool
    blocked_gate_count: int
    stale_evidence_count: int
    gates: tuple[ProductionActivationGate, ...]
    disabled_reasons: tuple[str, ...]
    next_action: WorkspaceOverviewAction
    plain_language_summary: str
    guardrails: tuple[str, ...]
    redactions: tuple[str, ...]

    def to_safe_dict(self) -> dict[str, Any]:
        return {
            "accountId": self.account_id,
            "accountCode": self.account_code,
            "accountName": self.account_name,
            "decisionStatus": self.decision_status,
            "launchAllowed": self.launch_allowed,
            "blockedGateCount": self.blocked_gate_count,
            "staleEvidenceCount": self.stale_evidence_count,
            "gates": [gate.to_safe_dict() for gate in self.gates],
            "disabledReasons": list(self.disabled_reasons),
            "nextAction": self.next_action.to_safe_dict(),
            "plainLanguageSummary": self.plain_language_summary,
            "guardrails": list(self.guardrails),
            "redactions": list(self.redactions),
            "noUiOnlyActivationConfirmed": True,
            "noCampaignActivationConfirmed": True,
            "noGoLiveActionConfirmed": True,
            "noBillingOrMoneyMovementConfirmed": True,
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


@dataclass(frozen=True)
class AccountFoundationActivationResult:
    account_id: str
    account_code: str
    account_name: str
    previous_account_status: str
    account_status: str
    previous_onboarding_status: str
    onboarding_status: str
    previous_tenant_link_status: str | None
    tenant_link_status: str | None
    activated_seat_types: tuple[str, ...]
    created_seat_count: int
    command_status: str
    audit_event_id: str | None
    idempotency_status: str
    guardrails: list[str]
    redactions: list[str]

    def to_safe_dict(self) -> dict[str, Any]:
        return {
            "accountId": self.account_id,
            "accountCode": self.account_code,
            "accountName": self.account_name,
            "previousAccountStatus": self.previous_account_status,
            "accountStatus": self.account_status,
            "previousOnboardingStatus": self.previous_onboarding_status,
            "onboardingStatus": self.onboarding_status,
            "previousTenantLinkStatus": self.previous_tenant_link_status,
            "tenantLinkStatus": self.tenant_link_status,
            "seatCapacity": {
                "seatTypes": list(self.activated_seat_types),
                "createdSeatCount": self.created_seat_count,
            },
            "commandStatus": self.command_status,
            "auditEventId": self.audit_event_id,
            "idempotency": {"status": self.idempotency_status},
            "guardrails": list(self.guardrails),
            "redactions": list(self.redactions),
            "noMembershipWriteConfirmed": True,
            "noSeatAssignmentConfirmed": True,
            "noInviteDeliveryConfirmed": True,
            "noAuthClaimChangeConfirmed": True,
            "noCredentialCreationConfirmed": True,
            "noCampaignActivationConfirmed": True,
            "noGoLiveActionConfirmed": True,
            "noBillingOrMoneyMovementConfirmed": True,
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
        operating_jurisdiction_code=str(
            row.get("operating_jurisdiction_code") or "ZA"
        ),
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
                COALESCE(account.operating_jurisdiction_code, 'ZA') AS operating_jurisdiction_code,
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


async def build_referral_saas_partner_workspace_account_context(
    *,
    actor_role: str,
    actor_tenant_code: str | None = None,
    actor_subjects: Iterable[str] = (),
    actor_client_ids: Iterable[str] = (),
    account_refs: Iterable[str] = (),
    external_tenant_refs: Iterable[str] = (),
    organisation_refs: Iterable[str] = (),
    operating_jurisdictions: Iterable[str] = (),
    limit: int = 50,
) -> PartnerWorkspaceAccountContext:
    safe_role = _safe_text(actor_role).upper()
    safe_tenant_code = _safe_text(actor_tenant_code).upper()
    safe_limit = max(1, min(int(limit or 50), 100))
    subjects = sorted({_safe_text(value) for value in actor_subjects if _safe_text(value)})
    client_ids = sorted({_safe_text(value) for value in actor_client_ids if _safe_text(value)})
    safe_account_refs = sorted({_safe_text(value) for value in account_refs if _safe_text(value)})
    external_refs = sorted(
        {_safe_text(value) for value in external_tenant_refs if _safe_text(value)}
    )
    organisation_reference_values = sorted(
        {_safe_text(value) for value in organisation_refs if _safe_text(value)}
    )
    jurisdictions = sorted(
        {_safe_text(value).upper() for value in operating_jurisdictions if _safe_text(value)}
    )

    if not any(
        [
            safe_tenant_code,
            subjects,
            client_ids,
            safe_account_refs,
            external_refs,
            organisation_reference_values,
        ]
    ):
        return PartnerWorkspaceAccountContext(
            actor_role=safe_role,
            accounts=(),
            guardrails=(
                "PARTNER_WORKSPACE_ACCOUNT_CONTEXT",
                "NO_UNSCOPED_ACCOUNT_ENUMERATION",
                "NO_INTERNAL_TENANT_IDENTIFIER_EXPOSURE",
            ),
            redactions=("internal_tenant_identifier", "tenant_code", "auth_claims"),
        )

    async with db_connection() as conn:
        rows = await conn.fetch(
            """
            WITH actor_memberships AS (
                SELECT
                    membership.account_id,
                    array_agg(DISTINCT membership.role_family) AS role_families,
                    array_agg(DISTINCT membership.permission_set) AS permission_sets,
                    array_agg(DISTINCT membership.status) AS membership_statuses,
                    'membership'::text AS source
                FROM platform_memberships membership
                LEFT JOIN platform_users actor_user
                    ON actor_user.user_id = membership.user_id
                WHERE membership.status = 'ACTIVE'
                  AND membership.archived_at IS NULL
                  AND (
                    membership.client_id = ANY($1::text[])
                    OR actor_user.subject = ANY($2::text[])
                  )
                GROUP BY membership.account_id
            ),
            tenant_link_accounts AS (
                SELECT
                    account_tenant.account_id,
                    ARRAY[]::text[] AS role_families,
                    ARRAY[]::text[] AS permission_sets,
                    ARRAY['TENANT_LINK']::text[] AS membership_statuses,
                    'tenant_link'::text AS source
                FROM platform_account_tenants account_tenant
                WHERE account_tenant.tenant_code = $3
                  AND account_tenant.status IN ('ACTIVE', 'SUSPENDED')
                  AND account_tenant.archived_at IS NULL
                  AND $3 <> ''
            ),
            account_claims AS (
                SELECT
                    account.account_id,
                    ARRAY[]::text[] AS role_families,
                    ARRAY[]::text[] AS permission_sets,
                    ARRAY['CLAIMED']::text[] AS membership_statuses,
                    'account_claim'::text AS source
                FROM platform_accounts account
                WHERE account.account_id::text = ANY($4::text[])
                   OR account.account_code = ANY($4::text[])
            ),
            external_ref_claims AS (
                SELECT
                    external_ref.account_id,
                    ARRAY[]::text[] AS role_families,
                    ARRAY[]::text[] AS permission_sets,
                    ARRAY['CLAIMED']::text[] AS membership_statuses,
                    'external_reference_claim'::text AS source
                FROM platform_external_tenant_refs external_ref
                WHERE external_ref.status = 'ACTIVE'
                  AND (
                    (
                        external_ref.ref_type = 'external_tenant_ref'
                        AND external_ref.external_ref = ANY($5::text[])
                    )
                    OR (
                        external_ref.ref_type = 'organisation_ref'
                        AND external_ref.external_ref = ANY($6::text[])
                    )
                  )
            ),
            permitted_accounts AS (
                SELECT * FROM actor_memberships
                UNION ALL SELECT * FROM tenant_link_accounts
                UNION ALL SELECT * FROM account_claims
                UNION ALL SELECT * FROM external_ref_claims
            ),
            collapsed_permissions AS (
                SELECT
                    permitted.account_id,
                    COALESCE(
                        array_agg(DISTINCT role_family.role_family) FILTER (
                            WHERE role_family.role_family IS NOT NULL
                              AND role_family.role_family <> ''
                        ),
                        ARRAY[]::text[]
                    ) AS role_families,
                    COALESCE(
                        array_agg(DISTINCT permission_set.permission_set) FILTER (
                            WHERE permission_set.permission_set IS NOT NULL
                              AND permission_set.permission_set <> ''
                        ),
                        ARRAY[]::text[]
                    ) AS permission_sets,
                    COALESCE(
                        array_agg(DISTINCT membership_status.membership_status) FILTER (
                            WHERE membership_status.membership_status IS NOT NULL
                              AND membership_status.membership_status <> ''
                        ),
                        ARRAY[]::text[]
                    ) AS membership_statuses,
                    string_agg(DISTINCT permitted.source, ',') AS source
                FROM permitted_accounts permitted
                LEFT JOIN LATERAL unnest(permitted.role_families) AS role_family(role_family)
                    ON TRUE
                LEFT JOIN LATERAL unnest(permitted.permission_sets) AS permission_set(permission_set)
                    ON TRUE
                LEFT JOIN LATERAL unnest(permitted.membership_statuses) AS membership_status(membership_status)
                    ON TRUE
                GROUP BY permitted.account_id
            )
            SELECT
                account.account_id,
                account.account_code,
                account.account_name,
                account.account_type,
                account.status AS account_status,
                account.onboarding_status,
                COALESCE(account.operating_jurisdiction_code, 'ZA') AS operating_jurisdiction_code,
                account.primary_external_tenant_ref,
                COALESCE(collapsed_permissions.role_families, ARRAY[]::text[]) AS role_families,
                COALESCE(collapsed_permissions.permission_sets, ARRAY[]::text[]) AS permission_sets,
                COALESCE(collapsed_permissions.membership_statuses, ARRAY[]::text[]) AS membership_statuses,
                COALESCE(collapsed_permissions.source, 'unknown') AS source,
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
            FROM collapsed_permissions
            JOIN platform_accounts account
                ON account.account_id = collapsed_permissions.account_id
            LEFT JOIN platform_external_tenant_refs external_ref
                ON external_ref.account_id = account.account_id
               AND external_ref.status = 'ACTIVE'
            WHERE account.status IN ('ACTIVE', 'SUSPENDED')
              AND account.archived_at IS NULL
              AND (
                cardinality($7::text[]) = 0
                OR COALESCE(account.operating_jurisdiction_code, 'ZA') = ANY($7::text[])
              )
            GROUP BY
                account.account_id,
                collapsed_permissions.role_families,
                collapsed_permissions.permission_sets,
                collapsed_permissions.membership_statuses,
                collapsed_permissions.source
            ORDER BY account.updated_at DESC, account.created_at DESC
            LIMIT $8
            """,
            client_ids,
            subjects,
            safe_tenant_code,
            safe_account_refs,
            external_refs,
            organisation_reference_values,
            jurisdictions,
            safe_limit,
        )

    accounts: list[PartnerWorkspaceAccountContextItem] = []
    for raw_row in rows:
        row = dict(raw_row)
        external_references = _normalise_external_reference_rows(
            row["external_references"]
        )
        accounts.append(
            PartnerWorkspaceAccountContextItem(
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
                role_families=tuple(sorted(row.get("role_families") or [])),
                permission_sets=tuple(sorted(row.get("permission_sets") or [])),
                membership_statuses=tuple(
                    sorted(row.get("membership_statuses") or [])
                ),
                source=str(row.get("source") or "unknown"),
            )
        )

    return PartnerWorkspaceAccountContext(
        actor_role=safe_role,
        accounts=tuple(accounts),
        guardrails=(
            "PARTNER_WORKSPACE_ACCOUNT_CONTEXT",
            "SELECTED_CUSTOMER_ACCOUNT_PRIMITIVES_REUSED",
            "SERVER_SIDE_ACCOUNT_CONTEXT_ENFORCEMENT",
            "SERVER_SIDE_ACCOUNT_JURISDICTION_ENFORCEMENT",
            "NO_UNSCOPED_ACCOUNT_ENUMERATION",
            "NO_INTERNAL_TENANT_IDENTIFIER_EXPOSURE",
            "NO_MEMBERSHIP_WRITE",
        ),
        redactions=("internal_tenant_identifier", "tenant_code", "auth_claims"),
    )


def build_referral_saas_workspace_overview_projection(
    *,
    account_context: PartnerWorkspaceAccountContext,
    selected_account_ref: str | None = None,
) -> WorkspaceOverviewProjection:
    safe_selected_ref = _safe_text(selected_account_ref)
    selected_account = _select_workspace_overview_account(
        account_context.accounts,
        safe_selected_ref,
    )
    role = _safe_text(account_context.actor_role).upper()

    if selected_account is None:
        primary = WorkspaceOverviewAction(
            action_ref="request_customer_access",
            label="Ask for access to a customer",
            status="BLOCKED",
            priority="FIRST",
            route_hint="/admin/referral-saas/account-maintenance",
            reason="No customer workspace is visible to this session.",
            required_capability="REFERRAL_SAAS_WORKSPACE_READ",
        )
        return WorkspaceOverviewProjection(
            actor_role=role,
            selected_account=None,
            visible_account_count=len(account_context.accounts),
            readiness={"green": 0, "red": 1, "amber": 0, "status": "NO_CUSTOMER"},
            primary_action=primary,
            worklist=(primary,),
            plain_language_summary=(
                "No customer workspace is available for this session. Ask an "
                "Amplifi admin to add this user to a customer before working."
            ),
            safe_to_leave={
                "canLeaveSafely": True,
                "reason": "This page has not performed any setup or live action.",
            },
            guardrails=(
                "CUSTOMER_PARTNER_WORKSPACE_OVERVIEW",
                "NO_UNSCOPED_ACCOUNT_ENUMERATION",
                "NO_INTERNAL_TENANT_IDENTIFIER_EXPOSURE",
                "NO_LIVE_ACTION",
            ),
            redactions=account_context.redactions,
        )

    account_status = selected_account.account_status.upper()
    membership_statuses = {status.upper() for status in selected_account.membership_statuses}
    permission_sets = {value.upper() for value in selected_account.permission_sets}
    role_families = {value.upper() for value in selected_account.role_families}
    account_ready = account_status == "ACTIVE"
    access_ready = "ACTIVE" in membership_statuses or role in {
        "ADMIN",
        "SYSTEM_ADMIN",
        "DISTRIBUTION_ADMIN",
        "PLATFORM_ADMIN",
    }
    can_manage_access = bool(
        permission_sets.intersection(
            {
                "REFERRAL_SAAS_ACCOUNT_ADMIN",
                "REFERRAL_SAAS_ADMIN",
                "REFERRAL_SAAS_OWNER",
            }
        )
        or role_families.intersection(
            {"DISTRIBUTION_ADMIN", "PLATFORM_ADMIN", "ADMIN", "SYSTEM_ADMIN"}
        )
        or role
        in {"ADMIN", "SYSTEM_ADMIN", "DISTRIBUTION_ADMIN", "PLATFORM_ADMIN"}
    )
    can_manage_campaigns = bool(
        can_manage_access
        or permission_sets.intersection(
            {"REFERRAL_SAAS_CAMPAIGN_MANAGER", "REFERRAL_SAAS_ACCOUNT_ADMIN"}
        )
        or role_families.intersection({"CAMPAIGN_MANAGER", "DISTRIBUTION_ADMIN"})
    )

    actions: list[WorkspaceOverviewAction] = []
    if not account_ready:
        actions.append(
            WorkspaceOverviewAction(
                action_ref="activate_customer_foundation",
                label="Activate the customer foundation",
                status="BLOCKED",
                priority="FIRST",
                route_hint="account-health",
                reason="The selected customer is not active yet.",
                required_capability="REFERRAL_SAAS_ACCOUNT_ADMIN",
            )
        )
    if not access_ready:
        actions.append(
            WorkspaceOverviewAction(
                action_ref="confirm_people_access",
                label="Confirm who can manage this customer",
                status="BLOCKED",
                priority="FIRST",
                route_hint="people",
                reason="This session does not have active customer access evidence.",
                required_capability="REFERRAL_SAAS_WORKSPACE_READ",
            )
        )
    if can_manage_access:
        actions.append(
            WorkspaceOverviewAction(
                action_ref="review_people_access",
                label="Review people and access",
                status="READY" if access_ready else "NEEDS_ATTENTION",
                priority="NEXT",
                route_hint="people",
                reason="Keep the required owner and campaign manager clear.",
                required_capability="REFERRAL_SAAS_ACCOUNT_ADMIN",
            )
        )
    actions.append(
        WorkspaceOverviewAction(
            action_ref="check_integrations",
            label="Check integrations",
            status="NEEDS_ATTENTION",
            priority="NEXT" if access_ready else "LATER",
            route_hint="integrations",
            reason="Invite delivery and referral-message providers need readiness evidence.",
            required_capability="REFERRAL_SAAS_WORKSPACE_READ",
        )
    )
    if can_manage_campaigns:
        actions.append(
            WorkspaceOverviewAction(
                action_ref="open_campaigns",
                label="Open campaigns",
                status="READY" if account_ready and access_ready else "WAIT",
                priority="NEXT" if account_ready and access_ready else "LATER",
                route_hint="campaigns",
                reason="Set up or review referral campaigns for this customer.",
                required_capability="REFERRAL_SAAS_CAMPAIGN_READ",
            )
        )

    red = sum(1 for action in actions if action.status == "BLOCKED")
    amber = sum(1 for action in actions if action.status in {"NEEDS_ATTENTION", "WAIT"})
    green = sum(1 for action in actions if action.status == "READY")
    primary = next(
        (action for action in actions if action.priority == "FIRST"),
        actions[0] if actions else None,
    )
    summary_status = "READY" if red == 0 else "NEEDS_ATTENTION"
    summary = (
        f"{selected_account.account_name} is ready for customer work. "
        f"{amber} item{'s' if amber != 1 else ''} can wait."
        if red == 0
        else (
            f"{selected_account.account_name} needs {red} item"
            f"{'s' if red != 1 else ''} fixed before safe referral work."
        )
    )

    return WorkspaceOverviewProjection(
        actor_role=role,
        selected_account=selected_account,
        visible_account_count=len(account_context.accounts),
        readiness={
            "green": green,
            "red": red,
            "amber": amber,
            "status": summary_status,
        },
        primary_action=primary,
        worklist=tuple(actions[:5]),
        plain_language_summary=summary,
        safe_to_leave={
            "canLeaveSafely": True,
            "reason": (
                "This overview is read-only. It did not change people, "
                "integrations, campaigns, go-live, billing, or money."
            ),
        },
        guardrails=(
            "CUSTOMER_PARTNER_WORKSPACE_OVERVIEW",
            "ACCOUNT_SCOPED_SUMMARY",
            "CAPABILITY_AWARE_ACTIONS",
            "NO_UNSCOPED_ACCOUNT_ENUMERATION",
            "NO_INTERNAL_TENANT_IDENTIFIER_EXPOSURE",
            "NO_LIVE_ACTION",
        ),
        redactions=tuple(
            sorted(
                {
                    *account_context.redactions,
                    "internal_tenant_identifier",
                    "tenant_code",
                    "auth_claims",
                }
            )
        ),
    )


def build_referral_saas_commercial_entitlement_projection(
    *,
    account_context: AccountFoundationContext,
) -> CommercialEntitlementProjection:
    account_status = _safe_text(account_context.account_status).upper()
    tenant_link_status = _safe_text(account_context.tenant_link_status).upper()
    reference_status = _safe_text(account_context.reference_status).upper()
    account_active = account_status == "ACTIVE"
    tenant_link_active = tenant_link_status == "ACTIVE"
    reference_active = reference_status == "ACTIVE"
    production_foundation_ready = account_active and tenant_link_active and reference_active

    disabled_reasons: list[str] = []
    if not account_active:
        disabled_reasons.append("ACCOUNT_FOUNDATION_NOT_ACTIVE")
    if not tenant_link_active:
        disabled_reasons.append("TENANT_LINK_NOT_ACTIVE")
    if not reference_active:
        disabled_reasons.append("CUSTOMER_REFERENCE_NOT_ACTIVE")

    # H1 has entitlement posture, not a billing/subscription system. Keep this
    # visible so production activation cannot imply an invoice or payment exists.
    disabled_reasons.append("COMMERCIAL_ENTITLEMENT_SOURCE_NOT_CONFIGURED")

    launch_allowed = False
    overall_status = "COMMERCIAL_SETUP_REQUIRED"
    commercial_status = "REFERENCE_POSTURE_ONLY"
    environment_status = (
        "CUSTOMER_FOUNDATION_READY"
        if production_foundation_ready
        else "CUSTOMER_FOUNDATION_NOT_READY"
    )

    feature_status = "AVAILABLE_FOR_SETUP" if production_foundation_ready else "WAIT_FOR_ACCOUNT_FOUNDATION"
    features = (
        CommercialEntitlementFeature(
            feature_ref="ACCOUNT_SETUP",
            label="Account setup",
            status="READY",
            reason="Customer foundation work is inside the Referral SaaS H1 scope.",
            route_hint="settings",
        ),
        CommercialEntitlementFeature(
            feature_ref="PEOPLE_ACCESS",
            label="People and access",
            status=feature_status,
            reason="Customer responsibilities can be managed before platform login is completed.",
            route_hint="people",
        ),
        CommercialEntitlementFeature(
            feature_ref="INTEGRATIONS_SETUP",
            label="Integrations setup",
            status=feature_status,
            reason="Non-secret integration evidence can be planned and verified in customer context.",
            route_hint="integrations",
        ),
        CommercialEntitlementFeature(
            feature_ref="CAMPAIGN_SETUP",
            label="Campaign setup",
            status=feature_status,
            reason="Campaign drafts and review can proceed when customer setup gates allow it.",
            route_hint="campaigns",
        ),
        CommercialEntitlementFeature(
            feature_ref="PRODUCTION_ACTIVATION",
            label="Production activation",
            status="BLOCKED",
            reason="A contracted plan or launch entitlement source has not been configured.",
            route_hint="commercial",
        ),
        CommercialEntitlementFeature(
            feature_ref="BILLING_AND_MONEY",
            label="Billing and money",
            status="OUT_OF_SCOPE",
            reason="Billing, invoices, payments, payouts, funding, and settlement are outside H1.",
            route_hint="commercial",
        ),
    )
    next_actions = (
        WorkspaceOverviewAction(
            action_ref="record_commercial_entitlement_source",
            label="Record the commercial entitlement source",
            status="BLOCKED",
            priority="FIRST",
            route_hint="commercial",
            reason="Production-capable actions need an explicit plan or entitlement source before launch.",
            required_capability="REFERRAL_SAAS_ACCOUNT_ADMIN",
        ),
        WorkspaceOverviewAction(
            action_ref="keep_setup_in_reference_mode",
            label="Keep this customer in setup mode",
            status="READY",
            priority="NEXT",
            route_hint="health",
            reason="Safe setup and testing can continue without billing or money movement.",
            required_capability="REFERRAL_SAAS_ACCOUNT_READ",
        ),
    )
    plain_summary = (
        f"{account_context.account_name} can stay in safe setup mode, but production activation is blocked until a "
        "commercial entitlement source is configured. No billing, invoice, payment, or money movement exists here."
    )

    return CommercialEntitlementProjection(
        account_id=account_context.account_id,
        account_code=account_context.account_code,
        account_name=account_context.account_name,
        overall_status=overall_status,
        commercial_status=commercial_status,
        environment_status=environment_status,
        plan_code="REFERRAL_SAAS_H1_REFERENCE",
        plan_name="Referral SaaS H1 reference posture",
        contract_source="NOT_CONFIGURED",
        launch_allowed=launch_allowed,
        production_activation_blocked=True,
        limits={
            "source": "REFERENCE_POSTURE_NOT_BILLING",
            "operatingJurisdictionCode": account_context.operating_jurisdiction_code,
            "campaignsPerCustomer": "REVIEW_REQUIRED",
            "monthlyReferralEvents": "REVIEW_REQUIRED",
            "reportExportRows": 50000,
            "messageChannels": "CONFIGURED_IN_INTEGRATIONS",
        },
        features=features,
        disabled_reasons=tuple(disabled_reasons),
        next_actions=next_actions,
        plain_language_summary=plain_summary,
        guardrails=tuple(COMMERCIAL_ENTITLEMENT_GUARDRAILS),
        redactions=tuple(COMMERCIAL_ENTITLEMENT_REDACTIONS),
    )


def build_referral_saas_production_activation_decision(
    *,
    account_context: AccountFoundationContext,
    commercial_entitlement: CommercialEntitlementProjection | None = None,
    people_access_status: str | None = None,
    integrations_status: str | None = None,
    campaign_status: str | None = None,
    evidence_freshness_status: str | None = None,
) -> ProductionActivationDecision:
    commercial = commercial_entitlement or build_referral_saas_commercial_entitlement_projection(
        account_context=account_context,
    )
    account_ready = (
        _safe_text(account_context.account_status).upper() == "ACTIVE"
        and _safe_text(account_context.tenant_link_status).upper() == "ACTIVE"
        and _safe_text(account_context.reference_status).upper() == "ACTIVE"
    )
    people_ready = _safe_text(people_access_status).upper() == "ACCESS_READY"
    integrations_ready = _safe_text(integrations_status).upper() == "READY"
    campaign_ready = _safe_text(campaign_status).upper() == "READY_TO_ACTIVATE"
    commercial_ready = commercial.launch_allowed and not commercial.production_activation_blocked
    evidence_ready = _safe_text(evidence_freshness_status).upper() == "FRESH"

    gates = (
        ProductionActivationGate(
            gate_ref="ACCOUNT_FOUNDATION",
            label="Customer foundation",
            status="PASS" if account_ready else "BLOCKED",
            reason=(
                "Account, tenant link, and customer reference are active."
                if account_ready
                else "Activate the customer account foundation before production launch."
            ),
            next_action="Open Account health",
            route_hint="health",
        ),
        ProductionActivationGate(
            gate_ref="PEOPLE_ACCESS",
            label="People who manage this customer",
            status="PASS" if people_ready else "BLOCKED",
            reason=(
                "Required customer access responsibilities are accepted."
                if people_ready
                else "Confirm the account owner and campaign manager before production launch."
            ),
            next_action="Open People and access",
            route_hint="people",
        ),
        ProductionActivationGate(
            gate_ref="INTEGRATIONS",
            label="Integrations",
            status="PASS" if integrations_ready else "BLOCKED",
            reason=(
                "Required integration providers are ready."
                if integrations_ready
                else "Complete provider and execution readiness before production launch."
            ),
            next_action="Open Integrations",
            route_hint="integrations",
        ),
        ProductionActivationGate(
            gate_ref="CAMPAIGN_READINESS",
            label="Campaign readiness",
            status="PASS" if campaign_ready else "BLOCKED",
            reason=(
                "Campaign readiness has been checked for activation."
                if campaign_ready
                else "Select a reviewed campaign and run the campaign activation checklist."
            ),
            next_action="Open Campaigns",
            route_hint="campaigns",
        ),
        ProductionActivationGate(
            gate_ref="COMMERCIAL_ENTITLEMENT",
            label="Plan and entitlement",
            status="PASS" if commercial_ready else "BLOCKED",
            reason=(
                "A production launch entitlement source is configured."
                if commercial_ready
                else "Record a commercial entitlement source before production launch."
            ),
            next_action="Open Plan and entitlement",
            route_hint="commercial",
        ),
        ProductionActivationGate(
            gate_ref="EVIDENCE_FRESHNESS",
            label="Evidence freshness",
            status="PASS" if evidence_ready else "STALE",
            reason=(
                "The production decision is based on current evidence."
                if evidence_ready
                else "Refresh readiness evidence before production launch."
            ),
            next_action="Refresh customer readiness",
            route_hint="health",
        ),
    )
    blocked = tuple(gate for gate in gates if gate.status == "BLOCKED")
    stale = tuple(gate for gate in gates if gate.status == "STALE")
    launch_allowed = not blocked and not stale
    decision_status = "PRODUCTION_ACTIVATION_ALLOWED" if launch_allowed else "PRODUCTION_ACTIVATION_BLOCKED"
    disabled_reasons = tuple(
        gate.gate_ref for gate in gates if gate.status in {"BLOCKED", "STALE"}
    )
    next_gate = blocked[0] if blocked else stale[0] if stale else None
    next_action = WorkspaceOverviewAction(
        action_ref=(
            "production_activation_ready"
            if next_gate is None
            else f"resolve_{next_gate.gate_ref.lower()}"
        ),
        label=(
            "Production activation can proceed"
            if next_gate is None
            else next_gate.next_action
        ),
        status="READY" if launch_allowed else "BLOCKED",
        priority="FIRST",
        route_hint="campaigns" if next_gate is None else next_gate.route_hint,
        reason=(
            "All production activation gates passed."
            if next_gate is None
            else next_gate.reason
        ),
        required_capability="REFERRAL_SAAS_ACCOUNT_ADMIN",
    )
    summary = (
        f"{account_context.account_name} is clear for production activation."
        if launch_allowed
        else (
            f"{account_context.account_name} cannot be production activated yet. "
            f"{len(blocked)} gate(s) are blocked and {len(stale)} evidence check(s) need refresh."
        )
    )

    return ProductionActivationDecision(
        account_id=account_context.account_id,
        account_code=account_context.account_code,
        account_name=account_context.account_name,
        decision_status=decision_status,
        launch_allowed=launch_allowed,
        blocked_gate_count=len(blocked),
        stale_evidence_count=len(stale),
        gates=gates,
        disabled_reasons=disabled_reasons,
        next_action=next_action,
        plain_language_summary=summary,
        guardrails=tuple(PRODUCTION_ACTIVATION_GUARDRAILS),
        redactions=tuple(PRODUCTION_ACTIVATION_REDACTIONS),
    )


def _select_workspace_overview_account(
    accounts: tuple[PartnerWorkspaceAccountContextItem, ...],
    selected_account_ref: str,
) -> PartnerWorkspaceAccountContextItem | None:
    if not accounts:
        return None
    if not selected_account_ref:
        return accounts[0]
    for account in accounts:
        refs = {
            account.account_id,
            account.account_code,
            account.primary_external_tenant_ref or "",
            *(
                str(ref.get("externalRef") or "")
                for ref in account.external_references
            ),
        }
        if selected_account_ref in refs:
            return account
    return None


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


async def activate_referral_saas_account_foundation(
    *,
    account_id: str,
    tenant_code: str,
    account_tenant_id: str | None,
    external_ref_id: str,
    seat_types: Iterable[str] | None = None,
    actor_ref: str,
    actor_role: str,
    reason_code: str | None = None,
    correlation_id: str | None = None,
    idempotency_key_hash: str | None = None,
    command_payload_hash: str | None = None,
) -> AccountFoundationActivationResult:
    role = _safe_text(actor_role).upper()
    if role not in ACCOUNT_FOUNDATION_ACTIVATION_ROLES:
        raise AccountFoundationActivationPermissionDenied(
            "Actor is not authorised to activate Referral SaaS account foundations."
        )

    safe_account_id = _safe_text(account_id)
    safe_tenant_code = _safe_text(tenant_code)
    safe_account_tenant_id = _safe_text(account_tenant_id) or None
    safe_external_ref_id = _safe_text(external_ref_id)
    safe_actor_ref = _safe_text(actor_ref) or "REFERRAL_SAAS_ACCOUNT_OPERATOR"
    safe_reason_code = (
        _safe_text(reason_code) or ACCOUNT_FOUNDATION_ACTIVATION_REASON
    )
    safe_idempotency_hash = _safe_text(idempotency_key_hash) or None
    safe_payload_hash = _safe_text(command_payload_hash) or None
    requested_seat_types = _normalise_activation_seat_types(seat_types)

    if not safe_account_id or not safe_tenant_code or not safe_external_ref_id:
        raise AccountFoundationActivationValidationError(
            "Account, tenant, and external reference scope are required."
        )

    async with db_connection() as conn:
        if safe_idempotency_hash:
            replay = await conn.fetchrow(
                """
                SELECT
                    account_audit_event_id,
                    evidence_summary
                FROM platform_account_audit_events
                WHERE event_type = $1
                  AND idempotency_key_hash = $2
                ORDER BY created_at DESC
                LIMIT 1
                """,
                ACCOUNT_FOUNDATION_ACTIVATION_EVENT_TYPE,
                safe_idempotency_hash,
            )
            if replay:
                evidence = _json_object(replay["evidence_summary"])
                if (
                    safe_payload_hash
                    and evidence.get("command_payload_hash")
                    and evidence.get("command_payload_hash") != safe_payload_hash
                ):
                    raise AccountFoundationActivationIdempotencyConflict(
                        "Idempotency key was reused with different account activation content."
                    )
                return _activation_result_from_evidence(
                    evidence,
                    audit_event_id=str(replay["account_audit_event_id"]),
                    idempotency_status="REPLAYED",
                )

        current = await conn.fetchrow(
            """
            SELECT
                account.account_id,
                account.account_code,
                account.account_name,
                account.status AS account_status,
                account.onboarding_status,
                account_tenant.account_tenant_id,
                account_tenant.status AS tenant_link_status,
                external_ref.external_ref_id,
                external_ref.status AS reference_status
            FROM platform_accounts account
            LEFT JOIN platform_account_tenants account_tenant
                ON account_tenant.account_id = account.account_id
               AND account_tenant.tenant_code = $2
               AND account_tenant.relationship_type = 'OWNER'
               AND account_tenant.status <> 'ARCHIVED'
            LEFT JOIN platform_external_tenant_refs external_ref
                ON external_ref.account_id = account.account_id
               AND external_ref.external_ref_id = $4::uuid
               AND external_ref.tenant_code = $2
               AND external_ref.status <> 'ARCHIVED'
            WHERE account.account_id = $1::uuid
              AND ($3::uuid IS NULL OR account_tenant.account_tenant_id = $3::uuid)
              AND account.archived_at IS NULL
            LIMIT 1
            """,
            safe_account_id,
            safe_tenant_code,
            safe_account_tenant_id,
            safe_external_ref_id,
        )
        if not current:
            raise AccountFoundationActivationNotFound("Account foundation was not found.")
        if not current.get("account_tenant_id"):
            raise AccountFoundationActivationNotReady(
                "Account owner tenant link was not found for activation."
            )
        if not current.get("external_ref_id"):
            raise AccountFoundationActivationNotReady(
                "Account external reference was not found for activation."
            )

        previous_account_status = _safe_text(current["account_status"]).upper()
        previous_onboarding_status = _safe_text(current["onboarding_status"]).upper()
        previous_tenant_link_status = _safe_text(
            current["tenant_link_status"]
        ).upper()
        reference_status = _safe_text(current["reference_status"]).upper()

        if previous_account_status not in {"PENDING_ONBOARDING", "ACTIVE"}:
            raise AccountFoundationActivationNotReady(
                "Account foundation is not in an activatable state."
            )
        if previous_tenant_link_status not in {"PENDING_SETUP", "ACTIVE"}:
            raise AccountFoundationActivationNotReady(
                "Account owner tenant link is not in an activatable state."
            )
        if reference_status != "ACTIVE":
            raise AccountFoundationActivationNotReady(
                "Account external reference must be active before activation."
            )

        async with conn.transaction():
            updated_account = await conn.fetchrow(
                """
                UPDATE platform_accounts
                SET
                    status = 'ACTIVE',
                    onboarding_status = 'APPROVED',
                    metadata = COALESCE(metadata, '{}'::jsonb) || jsonb_build_object(
                        'account_foundation_activation_status',
                        'ACCOUNT_FOUNDATION_ACTIVATED',
                        'no_membership_write_confirmed', true,
                        'no_seat_assignment_confirmed', true,
                        'no_auth_claim_change_confirmed', true,
                        'no_billing_or_money_movement_confirmed', true
                    ),
                    updated_by_ref = $2,
                    updated_at = NOW()
                WHERE account_id = $1::uuid
                  AND status IN ('PENDING_ONBOARDING', 'ACTIVE')
                RETURNING account_id, account_code, account_name, status, onboarding_status
                """,
                safe_account_id,
                safe_actor_ref,
            )
            updated_tenant = await conn.fetchrow(
                """
                UPDATE platform_account_tenants
                SET
                    status = 'ACTIVE',
                    metadata = COALESCE(metadata, '{}'::jsonb) || jsonb_build_object(
                        'account_foundation_activation_status',
                        'TENANT_LINK_ACTIVATED'
                    ),
                    updated_at = NOW()
                WHERE account_tenant_id = $1::uuid
                  AND status IN ('PENDING_SETUP', 'ACTIVE')
                RETURNING account_tenant_id, status
                """,
                str(current["account_tenant_id"]),
            )
            inserted_seats = await conn.fetchrow(
                """
                WITH requested AS (
                    SELECT DISTINCT unnest($2::text[]) AS seat_type
                ),
                inserted AS (
                    INSERT INTO platform_seats (
                        account_id,
                        seat_type,
                        status,
                        metadata
                    )
                    SELECT
                        $1::uuid,
                        requested.seat_type,
                        'AVAILABLE',
                        jsonb_build_object(
                            'source',
                            'referral_saas_account_foundation_activation',
                            'no_membership_assignment_confirmed',
                            true,
                            'no_auth_claim_change_confirmed',
                            true
                        )
                    FROM requested
                    WHERE NOT EXISTS (
                        SELECT 1
                        FROM platform_seats existing
                        WHERE existing.account_id = $1::uuid
                          AND existing.seat_type = requested.seat_type
                          AND existing.status IN ('AVAILABLE', 'ASSIGNED', 'SUSPENDED')
                    )
                    RETURNING seat_type
                )
                SELECT
                    COALESCE(jsonb_agg(seat_type ORDER BY seat_type), '[]'::jsonb)
                        AS created_seat_types,
                    COUNT(*)::int AS created_seat_count
                FROM inserted
                """,
                safe_account_id,
                list(requested_seat_types),
            )
            evidence = {
                "account_id": safe_account_id,
                "account_code": str(updated_account["account_code"]),
                "account_name": str(updated_account["account_name"]),
                "previous_account_status": previous_account_status,
                "account_status": str(updated_account["status"]),
                "previous_onboarding_status": previous_onboarding_status,
                "onboarding_status": str(updated_account["onboarding_status"]),
                "previous_tenant_link_status": previous_tenant_link_status,
                "tenant_link_status": str(updated_tenant["status"]),
                "requested_seat_types": list(requested_seat_types),
                "created_seat_types": _json_list(
                    inserted_seats["created_seat_types"] if inserted_seats else []
                ),
                "created_seat_count": int(
                    inserted_seats["created_seat_count"] if inserted_seats else 0
                ),
                "command_status": "ACCOUNT_FOUNDATION_ACTIVATED",
                "command_payload_hash": safe_payload_hash,
                "no_membership_write_confirmed": True,
                "no_seat_assignment_confirmed": True,
                "no_invite_delivery_confirmed": True,
                "no_auth_claim_change_confirmed": True,
                "no_credential_creation_confirmed": True,
                "no_campaign_activation_confirmed": True,
                "no_go_live_action_confirmed": True,
                "no_billing_or_money_movement_confirmed": True,
            }
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
                    previous_status,
                    next_status,
                    reason_code,
                    correlation_id,
                    idempotency_key_hash,
                    evidence_summary,
                    redactions
                )
                VALUES (
                    $1::uuid, $2::uuid, $3::uuid, $4, $5, 'RECORDED', $6, $7,
                    $8, $9, $10, $11, $12, $13::jsonb, $14::jsonb
                )
                RETURNING account_audit_event_id
                """,
                safe_account_id,
                str(current["account_tenant_id"]),
                safe_external_ref_id,
                safe_tenant_code,
                ACCOUNT_FOUNDATION_ACTIVATION_EVENT_TYPE,
                safe_actor_ref,
                role,
                previous_account_status,
                "ACCOUNT_FOUNDATION_ACTIVATED",
                safe_reason_code,
                _safe_text(correlation_id) or None,
                safe_idempotency_hash,
                _jsonb(evidence),
                _jsonb(ACCOUNT_FOUNDATION_ACTIVATION_REDACTIONS),
            )

    return _activation_result_from_evidence(
        evidence,
        audit_event_id=(
            str(audit_event["account_audit_event_id"]) if audit_event else None
        ),
        idempotency_status="RECORDED",
    )


def _normalise_activation_seat_types(values: Iterable[str] | None) -> tuple[str, ...]:
    if isinstance(values, str):
        values = [values]
    requested = tuple(
        dict.fromkeys(
            (
                _safe_text(value).upper()
                for value in (values or DEFAULT_ACCOUNT_FOUNDATION_SEAT_TYPES)
            )
        )
    )
    if not requested:
        raise AccountFoundationActivationValidationError(
            "At least one seat type is required for account activation capacity."
        )
    unsupported = [
        value for value in requested if value not in ALLOWED_ACCOUNT_FOUNDATION_SEAT_TYPES
    ]
    if unsupported:
        raise AccountFoundationActivationValidationError(
            "Seat type is not supported for Referral SaaS account activation."
        )
    return requested


def _activation_result_from_evidence(
    evidence: dict[str, Any],
    *,
    audit_event_id: str | None,
    idempotency_status: str,
) -> AccountFoundationActivationResult:
    return AccountFoundationActivationResult(
        account_id=_safe_text(evidence.get("account_id")),
        account_code=_safe_text(evidence.get("account_code")),
        account_name=_safe_text(evidence.get("account_name")),
        previous_account_status=_safe_text(evidence.get("previous_account_status")),
        account_status=_safe_text(evidence.get("account_status")),
        previous_onboarding_status=_safe_text(
            evidence.get("previous_onboarding_status")
        ),
        onboarding_status=_safe_text(evidence.get("onboarding_status")),
        previous_tenant_link_status=_safe_text(
            evidence.get("previous_tenant_link_status")
        )
        or None,
        tenant_link_status=_safe_text(evidence.get("tenant_link_status")) or None,
        activated_seat_types=tuple(
            _safe_text(value)
            for value in _json_list(evidence.get("requested_seat_types"))
            if _safe_text(value)
        ),
        created_seat_count=int(evidence.get("created_seat_count") or 0),
        command_status=_safe_text(evidence.get("command_status")),
        audit_event_id=audit_event_id,
        idempotency_status=idempotency_status,
        guardrails=list(ACCOUNT_FOUNDATION_ACTIVATION_GUARDRAILS),
        redactions=list(ACCOUNT_FOUNDATION_ACTIVATION_REDACTIONS),
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


def _json_object(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        decoded = json.loads(value)
        return decoded if isinstance(decoded, dict) else {}
    return {}


def _json_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        decoded = json.loads(value)
        return decoded if isinstance(decoded, list) else []
    return []


def _safe_text(value: Any) -> str:
    return str(value or "").strip()


def _jsonb(value: Any) -> str:
    return json.dumps(value, sort_keys=True)
