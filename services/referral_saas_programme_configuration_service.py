from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Mapping

from services.referral_saas_journey_configuration_service import (
    CustomerJourneyIncentiveBindingValidationError,
    _find_approved_incentive_catalogue_record,
)
from services.referral_saas_customer_product_catalogue_service import (
    list_referral_saas_customer_product_catalogue,
)
from utils.db import db_connection


PROGRAMME_CONFIGURATION_GUARDRAILS = (
    "ACCOUNT_SCOPED_PROGRAMME_CONFIGURATION",
    "PUBLISHED_CUSTOMER_JOURNEY_VERSION_REQUIRED",
    "ACTIVE_CUSTOMER_PRODUCT_OFFERING_REQUIRED",
    "APPROVED_BUILDING_BLOCKS_ONLY",
    "IDEMPOTENT_PROGRAMME_DRAFT_COMMANDS",
    "SAFE_PROGRAMME_PAYLOAD_ONLY",
    "NO_PROGRAMME_PUBLISH",
    "NO_CAMPAIGN_ACTIVATION",
    "NO_REFERRAL_RUNTIME_SWITCH",
    "NO_PROVIDER_DISPATCH",
    "NO_CREDENTIAL_OR_AUTH_MUTATION",
    "NO_BILLING_PAYOUT_SETTLEMENT_OR_MONEY_MOVEMENT",
)

PROGRAMME_LIFECYCLE_GUARDRAILS = (
    *PROGRAMME_CONFIGURATION_GUARDRAILS,
    "VALIDATED_DRAFT_REQUIRED",
    "APPROVED_REVIEW_REQUIRED",
    "IMMUTABLE_PROGRAMME_VERSION",
    "EXPLICIT_RETIREMENT_REQUIRED",
    "ROLLBACK_READINESS_ONLY",
)

PROGRAMME_INCENTIVE_BINDING_GUARDRAILS = (
    *PROGRAMME_CONFIGURATION_GUARDRAILS,
    "PUBLISHED_PROGRAMME_VERSION_REQUIRED",
    "APPROVED_INCENTIVE_OR_ENGAGEMENT_CATALOGUE_REFERENCE_REQUIRED",
    "PROGRAMME_EFFECTIVE_DATE_COMPATIBILITY_REQUIRED",
    "EXPLICIT_REPLACE_OR_RETIRE_REQUIRED",
    "IDEMPOTENT_PROGRAMME_INCENTIVE_BINDING_COMMANDS",
    "IMMUTABLE_PROGRAMME_VERSION_SNAPSHOT",
    "NO_REWARD_APPLICATION",
    "NO_BADGE_AWARD",
    "NO_MISSION_PROGRESS_MUTATION",
    "NO_LEADERBOARD_SCORING",
)

PROGRAMME_CONFIGURATION_REDACTIONS = (
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

PROGRAMME_UNSAFE_KEY_TOKENS = (
    "tenant_code",
    "internal_tenant",
    "raw_ucn",
    "ucn",
    "raw_event",
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
)

PROGRAMME_SUB_PRODUCT_CODES = frozenset(
    {
        "REFERRAL_MANAGEMENT",
        "CAMPAIGN_ATTRIBUTION",
        "RMCA_BUNDLE",
    }
)

MAX_PROGRAMME_LIMIT = 100
MAX_PROGRAMME_INCENTIVE_BINDING_LIMIT = 100

PROGRAMME_INCENTIVE_BINDING_TYPES = frozenset({"INCENTIVE", "ENGAGEMENT"})
PROGRAMME_INCENTIVE_CATALOGUE_TYPES = frozenset(
    {"REWARD_POLICY", "MISSION", "BADGE", "LEADERBOARD"}
)


class ProgrammeConfigurationValidationError(ValueError):
    """Raised when a programme command fails safe validation."""


class ProgrammeConfigurationUnsafePayload(ProgrammeConfigurationValidationError):
    """Raised when a programme payload includes unsafe platform fields."""


class ProgrammeConfigurationLifecycleLocked(Exception):
    """Raised when a programme draft state blocks ordinary editing."""


class ProgrammeConfigurationNotFound(Exception):
    """Raised when an account-scoped programme resource cannot be found."""


class ProgrammeConfigurationIdempotencyConflict(Exception):
    """Raised when an idempotency key is reused with different content."""


PROGRAMME_DRAFT_EDITABLE_STATUSES = frozenset(
    {"DRAFT", "VALIDATION_FAILED", "VALIDATED"}
)


def _ensure_programme_draft_editable(programme_status: str) -> str:
    safe_status = str(programme_status or "").strip().upper()
    if safe_status not in PROGRAMME_DRAFT_EDITABLE_STATUSES:
        raise ProgrammeConfigurationLifecycleLocked(
            "Programme draft is locked in "
            f"{safe_status or 'UNKNOWN'} state. Use a governed return-to-draft "
            "action before editing reviewed programme evidence."
        )
    return safe_status


def _row_value(row: Mapping[str, Any], key: str) -> Any:
    try:
        return row[key]
    except (KeyError, TypeError):
        return getattr(row, key)


def _optional_row_value(row: Mapping[str, Any], key: str) -> Any:
    try:
        return row[key]
    except (AttributeError, KeyError, TypeError):
        return None


def _isoformat(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return str(value)


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def _payload_hash(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


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


def _json_list(value: Any) -> list[dict[str, Any] | str]:
    if isinstance(value, list):
        return [item for item in value if isinstance(item, (dict, str))]
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return []
        if isinstance(parsed, list):
            return [item for item in parsed if isinstance(item, (dict, str))]
        return []
    return []


def _redact_json(value: Any) -> Any:
    if isinstance(value, dict):
        redacted: dict[str, Any] = {}
        for key, child in value.items():
            key_text = str(key)
            if any(token in key_text.lower() for token in PROGRAMME_UNSAFE_KEY_TOKENS):
                redacted[key_text] = "[REDACTED]"
            else:
                redacted[key_text] = _redact_json(child)
        return redacted
    if isinstance(value, list):
        return [_redact_json(item) for item in value]
    return value


def _required_text(
    value: Any,
    field_name: str,
    *,
    min_length: int = 1,
    max_length: int = 240,
) -> str:
    safe = str(value or "").strip()
    if len(safe) < min_length:
        raise ProgrammeConfigurationValidationError(f"{field_name} is required.")
    if len(safe) > max_length:
        raise ProgrammeConfigurationValidationError(
            f"{field_name} must be {max_length} characters or fewer."
        )
    return safe


def _optional_text(value: Any, *, max_length: int = 240) -> str | None:
    if value is None:
        return None
    safe = str(value).strip()
    return safe[:max_length] if safe else None


def _normalise_code(value: Any, field_name: str, *, max_length: int = 80) -> str:
    return (
        _required_text(value, field_name, max_length=max_length)
        .upper()
        .replace(" ", "_")
        .replace("-", "_")
    )


def _safe_limit(limit: int) -> int:
    return max(1, min(int(limit), MAX_PROGRAMME_LIMIT))


def _reject_unsafe_programme_payload(value: Any) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if any(token in str(key).lower() for token in PROGRAMME_UNSAFE_KEY_TOKENS):
                raise ProgrammeConfigurationUnsafePayload(
                    "Programme configuration contains a field reserved for tenant, "
                    "provider, auth, billing, credential, settlement, payout, or money workflows."
                )
            _reject_unsafe_programme_payload(child)
    elif isinstance(value, list):
        for item in value:
            _reject_unsafe_programme_payload(item)


def _normalise_safe_mapping(value: Any, field_name: str) -> dict[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, Mapping):
        raise ProgrammeConfigurationValidationError(f"{field_name} must be an object.")
    _reject_unsafe_programme_payload(value)
    return _redact_json(dict(value))


def _normalise_safe_list(value: Any, field_name: str) -> list[Any]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ProgrammeConfigurationValidationError(f"{field_name} must be a list.")
    _reject_unsafe_programme_payload(value)
    return _redact_json(value)


def _issue(
    *,
    code: str,
    title: str,
    plain_language: str,
    next_action: str,
    area: str,
    can_wait: bool,
) -> dict[str, Any]:
    return {
        "code": code,
        "title": title,
        "plainLanguage": plain_language,
        "nextAction": next_action,
        "area": area,
        "canWait": can_wait,
    }


def _optional_iso_date(value: Any) -> date | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    safe = str(value).strip()
    if not safe:
        return None
    return date.fromisoformat(safe[:10])


def _snapshot_has_negative_signal(snapshot: Mapping[str, Any]) -> bool:
    negative_values = {
        "BLOCKED",
        "DENIED",
        "DISABLED",
        "FAILED",
        "MISSING",
        "NOT_APPROVED",
        "NOT_READY",
        "REQUIRED",
    }

    def walk(value: Any) -> bool:
        if isinstance(value, Mapping):
            for key, child in value.items():
                key_text = str(key).lower()
                if isinstance(child, bool) and (
                    key_text.endswith("allowed")
                    or key_text.endswith("approved")
                    or key_text.endswith("enabled")
                    or key_text.endswith("ready")
                ):
                    if child is False:
                        return True
                if isinstance(child, str) and child.upper() in negative_values:
                    return True
                if walk(child):
                    return True
        elif isinstance(value, list):
            return any(walk(item) for item in value)
        return False

    return walk(snapshot)


@dataclass(frozen=True)
class ProgrammeJourneyCatalogueItem:
    customer_journey_version_id: str
    customer_journey_code: str
    version_number: int
    version_status: str
    template_code: str
    template_version: str
    safe_summary: dict[str, Any]
    governance_metadata: dict[str, Any]
    published_at: datetime | str | None

    def to_safe_dict(self) -> dict[str, Any]:
        return {
            "customerJourneyVersionId": self.customer_journey_version_id,
            "customerJourneyCode": self.customer_journey_code,
            "versionNumber": self.version_number,
            "versionStatus": self.version_status,
            "templateCode": self.template_code,
            "templateVersion": self.template_version,
            "safeSummary": _redact_json(self.safe_summary),
            "governanceMetadata": _redact_json(self.governance_metadata),
            "publishedAt": _isoformat(self.published_at),
        }


@dataclass(frozen=True)
class ProgrammeVersionSummary:
    programme_version_id: str
    account_id: str
    programme_code: str
    programme_name: str
    programme_description: str | None
    operating_jurisdiction_code: str
    product_code: str
    sub_product_code: str
    customer_product_line_id: str | None
    customer_product_offering_id: str | None
    customer_product_binding: dict[str, Any]
    version_number: int
    version_status: str
    customer_journey_version_id: str
    campaign_defaults_snapshot: dict[str, Any]
    incentive_refs_snapshot: list[Any]
    engagement_refs_snapshot: list[Any]
    integration_readiness_snapshot: dict[str, Any]
    commercial_entitlement_snapshot: dict[str, Any]
    effective_from: date | str | None
    effective_to: date | str | None
    safe_summary: dict[str, Any]
    governance_metadata: dict[str, Any]
    published_at: datetime | str | None
    retired_at: datetime | str | None

    def to_safe_dict(self) -> dict[str, Any]:
        return {
            "programmeVersionId": self.programme_version_id,
            "accountId": self.account_id,
            "programmeCode": self.programme_code,
            "programmeName": self.programme_name,
            "programmeDescription": self.programme_description,
            "operatingJurisdictionCode": self.operating_jurisdiction_code,
            "productCode": self.product_code,
            "subProductCode": self.sub_product_code,
            "customerProductLineId": self.customer_product_line_id,
            "customerProductOfferingId": self.customer_product_offering_id,
            "customerProductBinding": _redact_json(self.customer_product_binding),
            "versionNumber": self.version_number,
            "versionStatus": self.version_status,
            "customerJourneyVersionId": self.customer_journey_version_id,
            "campaignDefaultsSnapshot": _redact_json(self.campaign_defaults_snapshot),
            "incentiveRefsSnapshot": _redact_json(self.incentive_refs_snapshot),
            "engagementRefsSnapshot": _redact_json(self.engagement_refs_snapshot),
            "integrationReadinessSnapshot": _redact_json(self.integration_readiness_snapshot),
            "commercialEntitlementSnapshot": _redact_json(self.commercial_entitlement_snapshot),
            "effectiveFrom": _isoformat(self.effective_from),
            "effectiveTo": _isoformat(self.effective_to),
            "safeSummary": _redact_json(self.safe_summary),
            "governanceMetadata": _redact_json(self.governance_metadata),
            "publishedAt": _isoformat(self.published_at),
            "retiredAt": _isoformat(self.retired_at),
            "guardrails": list(PROGRAMME_CONFIGURATION_GUARDRAILS),
            "redactions": list(PROGRAMME_CONFIGURATION_REDACTIONS),
            "noCampaignActivationConfirmed": True,
            "noProviderDispatchConfirmed": True,
            "noAuthBillingOrMoneyActionConfirmed": True,
        }


@dataclass(frozen=True)
class ProgrammeDraft:
    programme_draft_id: str
    account_id: str
    source_programme_version_id: str | None
    customer_journey_version_id: str
    programme_name: str
    programme_description: str | None
    operating_jurisdiction_code: str
    product_code: str
    sub_product_code: str
    customer_product_line_id: str | None
    customer_product_offering_id: str | None
    customer_product_binding: dict[str, Any]
    programme_status: str
    draft_version: int
    campaign_defaults: dict[str, Any]
    incentive_refs: list[Any]
    engagement_refs: list[Any]
    integration_readiness_snapshot: dict[str, Any]
    commercial_entitlement_snapshot: dict[str, Any]
    last_validation_status: str
    review_status: str
    effective_from: date | str | None
    effective_to: date | str | None
    configuration_checksum: str | None
    created_by_ref: str
    updated_by_ref: str | None
    created_at: datetime | str | None
    updated_at: datetime | str | None
    archived_at: datetime | str | None

    def to_safe_dict(self) -> dict[str, Any]:
        return {
            "programmeDraftId": self.programme_draft_id,
            "accountId": self.account_id,
            "sourceProgrammeVersionId": self.source_programme_version_id,
            "customerJourneyVersionId": self.customer_journey_version_id,
            "programmeName": self.programme_name,
            "programmeDescription": self.programme_description,
            "operatingJurisdictionCode": self.operating_jurisdiction_code,
            "productCode": self.product_code,
            "subProductCode": self.sub_product_code,
            "customerProductLineId": self.customer_product_line_id,
            "customerProductOfferingId": self.customer_product_offering_id,
            "customerProductBinding": _redact_json(self.customer_product_binding),
            "programmeStatus": self.programme_status,
            "draftVersion": self.draft_version,
            "campaignDefaults": _redact_json(self.campaign_defaults),
            "incentiveRefs": _redact_json(self.incentive_refs),
            "engagementRefs": _redact_json(self.engagement_refs),
            "integrationReadinessSnapshot": _redact_json(self.integration_readiness_snapshot),
            "commercialEntitlementSnapshot": _redact_json(self.commercial_entitlement_snapshot),
            "lastValidationStatus": self.last_validation_status,
            "reviewStatus": self.review_status,
            "effectiveFrom": _isoformat(self.effective_from),
            "effectiveTo": _isoformat(self.effective_to),
            "configurationChecksum": self.configuration_checksum,
            "createdByRef": self.created_by_ref,
            "updatedByRef": self.updated_by_ref,
            "createdAt": _isoformat(self.created_at),
            "updatedAt": _isoformat(self.updated_at),
            "archivedAt": _isoformat(self.archived_at),
            "guardrails": list(PROGRAMME_CONFIGURATION_GUARDRAILS),
            "redactions": list(PROGRAMME_CONFIGURATION_REDACTIONS),
            "noProgrammePublishConfirmed": True,
            "noCampaignActivationConfirmed": True,
            "noReferralRuntimeSwitchConfirmed": True,
            "noProviderDispatchConfirmed": True,
            "noCredentialOrAuthMutationConfirmed": True,
            "noBillingPayoutSettlementOrMoneyMovementConfirmed": True,
        }


@dataclass(frozen=True)
class ProgrammeDraftCommandResult:
    command_status: str
    draft: ProgrammeDraft
    idempotency_status: str

    def to_safe_dict(self) -> dict[str, Any]:
        return {
            "commandStatus": self.command_status,
            "idempotencyStatus": self.idempotency_status,
            "draft": self.draft.to_safe_dict(),
            "guardrails": list(PROGRAMME_CONFIGURATION_GUARDRAILS),
            "redactions": list(PROGRAMME_CONFIGURATION_REDACTIONS),
            "noProgrammePublishConfirmed": True,
            "noCampaignActivationConfirmed": True,
            "noReferralRuntimeSwitchConfirmed": True,
            "noProviderDispatchConfirmed": True,
            "noCredentialOrAuthMutationConfirmed": True,
            "noBillingPayoutSettlementOrMoneyMovementConfirmed": True,
        }


@dataclass(frozen=True)
class ProgrammeLifecycleCommandResult:
    command_status: str
    resource: ProgrammeDraft | ProgrammeVersionSummary | dict[str, Any]
    idempotency_status: str
    plain_language_summary: str

    def to_safe_dict(self) -> dict[str, Any]:
        if isinstance(self.resource, (ProgrammeDraft, ProgrammeVersionSummary)):
            resource = self.resource.to_safe_dict()
        else:
            resource = _redact_json(self.resource)
        return {
            "commandStatus": self.command_status,
            "idempotencyStatus": self.idempotency_status,
            "resource": resource,
            "plainLanguageSummary": self.plain_language_summary,
            "guardrails": list(PROGRAMME_LIFECYCLE_GUARDRAILS),
            "redactions": list(PROGRAMME_CONFIGURATION_REDACTIONS),
            "noCampaignActivationConfirmed": True,
            "noReferralRuntimeSwitchConfirmed": True,
            "noProviderDispatchConfirmed": True,
            "noCredentialOrAuthMutationConfirmed": True,
            "noBillingPayoutSettlementOrMoneyMovementConfirmed": True,
        }


@dataclass(frozen=True)
class ProgrammeIncentiveBinding:
    programme_incentive_binding_id: str
    account_id: str
    programme_version_id: str
    programme_code: str
    programme_name: str
    version_number: int
    version_status: str
    binding_type: str
    catalogue_type: str
    catalogue_ref: str
    catalogue_version_ref: str | None
    effective_from: date | str | None
    effective_to: date | str | None
    binding_status: str
    binding_payload_hash: str
    bound_by_ref: str
    bound_at: datetime | str | None
    archived_by_ref: str | None
    archived_at: datetime | str | None
    safe_summary: dict[str, Any]
    governance_metadata: dict[str, Any]

    def to_safe_dict(self) -> dict[str, Any]:
        return {
            "programmeIncentiveBindingId": self.programme_incentive_binding_id,
            "accountId": self.account_id,
            "programmeVersionId": self.programme_version_id,
            "programmeCode": self.programme_code,
            "programmeName": self.programme_name,
            "versionNumber": self.version_number,
            "versionStatus": self.version_status,
            "bindingType": self.binding_type,
            "catalogueType": self.catalogue_type,
            "catalogueRef": self.catalogue_ref,
            "catalogueVersionRef": self.catalogue_version_ref,
            "effectiveFrom": _isoformat(self.effective_from),
            "effectiveTo": _isoformat(self.effective_to),
            "bindingStatus": self.binding_status,
            "bindingPayloadHash": self.binding_payload_hash,
            "boundByRef": self.bound_by_ref,
            "boundAt": _isoformat(self.bound_at),
            "archivedByRef": self.archived_by_ref,
            "archivedAt": _isoformat(self.archived_at),
            "safeSummary": _redact_json(self.safe_summary),
            "governanceMetadata": _redact_json(self.governance_metadata),
            "guardrails": list(PROGRAMME_INCENTIVE_BINDING_GUARDRAILS),
            "redactions": list(PROGRAMME_CONFIGURATION_REDACTIONS),
            "noRewardApplicationConfirmed": True,
            "noBadgeAwardConfirmed": True,
            "noMissionProgressMutationConfirmed": True,
            "noLeaderboardScoringConfirmed": True,
            "noCampaignActivationConfirmed": True,
            "noProviderDispatchConfirmed": True,
            "noCredentialOrAuthMutationConfirmed": True,
            "noBillingPayoutSettlementOrMoneyMovementConfirmed": True,
        }


@dataclass(frozen=True)
class ProgrammeIncentiveBindingCommandResult:
    command_status: str
    binding: ProgrammeIncentiveBinding
    idempotency_status: str

    def to_safe_dict(self) -> dict[str, Any]:
        return {
            "commandStatus": self.command_status,
            "idempotencyStatus": self.idempotency_status,
            "binding": self.binding.to_safe_dict(),
            "guardrails": list(PROGRAMME_INCENTIVE_BINDING_GUARDRAILS),
            "redactions": list(PROGRAMME_CONFIGURATION_REDACTIONS),
            "noRewardApplicationConfirmed": True,
            "noBadgeAwardConfirmed": True,
            "noMissionProgressMutationConfirmed": True,
            "noLeaderboardScoringConfirmed": True,
            "noCampaignActivationConfirmed": True,
            "noProviderDispatchConfirmed": True,
            "noCredentialOrAuthMutationConfirmed": True,
            "noBillingPayoutSettlementOrMoneyMovementConfirmed": True,
        }


@dataclass(frozen=True)
class ProgrammeValidationResult:
    programme_validation_result_id: str
    account_id: str
    programme_draft_id: str
    customer_journey_version_id: str
    validation_status: str
    publish_allowed: bool
    campaign_binding_allowed: bool
    plain_language_summary: str
    blockers: list[Any]
    warnings: list[Any]
    configuration_snapshot: dict[str, Any]
    guardrails: list[Any]
    payload_hash: str
    idempotency_key_hash: str | None
    correlation_id: str | None
    validated_by_ref: str
    created_at: datetime | str | None

    def to_safe_dict(self) -> dict[str, Any]:
        return {
            "programmeValidationResultId": self.programme_validation_result_id,
            "accountId": self.account_id,
            "programmeDraftId": self.programme_draft_id,
            "customerJourneyVersionId": self.customer_journey_version_id,
            "validationStatus": self.validation_status,
            "publishAllowed": self.publish_allowed,
            "campaignBindingAllowed": self.campaign_binding_allowed,
            "plainLanguageSummary": self.plain_language_summary,
            "blockers": _redact_json(self.blockers),
            "warnings": _redact_json(self.warnings),
            "configurationSnapshot": _redact_json(self.configuration_snapshot),
            "simulation": {
                "programmePublish": "NOT_PERFORMED",
                "campaignActivation": "NOT_PERFORMED",
                "referralRuntimeSwitch": "NOT_PERFORMED",
                "providerDispatch": "NOT_PERFORMED",
                "credentialOrAuthMutation": "NOT_PERFORMED",
                "billingPayoutSettlementOrMoneyMovement": "NOT_PERFORMED",
            },
            "guardrails": list(self.guardrails),
            "redactions": list(PROGRAMME_CONFIGURATION_REDACTIONS),
            "payloadHash": self.payload_hash,
            "correlationId": self.correlation_id,
            "validatedByRef": self.validated_by_ref,
            "createdAt": _isoformat(self.created_at),
            "noProgrammePublishConfirmed": True,
            "noCampaignActivationConfirmed": True,
            "noReferralRuntimeSwitchConfirmed": True,
            "noProviderDispatchConfirmed": True,
            "noCredentialOrAuthMutationConfirmed": True,
            "noBillingPayoutSettlementOrMoneyMovementConfirmed": True,
        }


def _customer_product_binding_from_row(row: Mapping[str, Any]) -> dict[str, Any]:
    product_line_id = _optional_row_value(row, "customer_product_line_id")
    product_offering_id = _optional_row_value(row, "customer_product_offering_id")
    if not product_line_id and not product_offering_id:
        return {}
    return {
        "customerProductLineId": str(product_line_id) if product_line_id else None,
        "customerProductOfferingId": str(product_offering_id) if product_offering_id else None,
        "externalProductLineRef": _optional_row_value(row, "external_product_line_ref"),
        "productLineName": _optional_row_value(row, "product_line_name"),
        "productLineCategory": _optional_row_value(row, "product_line_category"),
        "externalOfferingRef": _optional_row_value(row, "external_offering_ref"),
        "offeringName": _optional_row_value(row, "offering_name"),
        "offeringFamily": _optional_row_value(row, "offering_family"),
        "operatingJurisdictionCode": _optional_row_value(
            row,
            "product_offering_operating_jurisdiction_code",
        )
        or _optional_row_value(row, "operating_jurisdiction_code"),
        "productLineStatus": _optional_row_value(row, "product_line_status"),
        "offeringStatus": _optional_row_value(row, "product_offering_status"),
    }


async def _get_active_customer_product_offering_binding(
    conn: Any,
    *,
    account_id: str,
    operating_jurisdiction_code: str,
    customer_product_line_id: str | None,
    customer_product_offering_id: str | None,
    required: bool,
) -> dict[str, Any]:
    if not customer_product_line_id and not customer_product_offering_id:
        if required:
            raise ProgrammeConfigurationValidationError(
                "Programme must be bound to a customer product line and product offering."
            )
        return {}
    if not customer_product_line_id or not customer_product_offering_id:
        raise ProgrammeConfigurationValidationError(
            "Programme product binding needs both customer_product_line_id and customer_product_offering_id."
        )

    row = await conn.fetchrow(
        """
        SELECT
            l.customer_product_line_id,
            l.external_product_line_ref,
            l.product_line_name,
            l.product_line_category,
            l.lifecycle_status AS product_line_status,
            o.customer_product_offering_id,
            o.external_offering_ref,
            o.offering_name,
            o.offering_family,
            o.lifecycle_status AS product_offering_status,
            o.operating_jurisdiction_code AS product_offering_operating_jurisdiction_code
        FROM referral_saas_customer_product_offerings o
        JOIN referral_saas_customer_product_lines l
            ON l.customer_product_line_id = o.customer_product_line_id
           AND l.account_id = o.account_id
        WHERE o.account_id = $1
          AND l.account_id = $1
          AND l.customer_product_line_id = $2
          AND o.customer_product_offering_id = $3
          AND l.operating_jurisdiction_code = $4
          AND o.operating_jurisdiction_code = $4
          AND l.archived_at IS NULL
          AND o.archived_at IS NULL
        LIMIT 1
        """,
        account_id,
        customer_product_line_id,
        customer_product_offering_id,
        operating_jurisdiction_code,
    )
    if not row:
        raise ProgrammeConfigurationValidationError(
            "Programme product/offering binding must reference the same account and jurisdiction."
        )
    if (
        str(_row_value(row, "product_line_status")) != "ACTIVE"
        or str(_row_value(row, "product_offering_status")) != "ACTIVE"
    ):
        raise ProgrammeConfigurationValidationError(
            "Programme product/offering binding must reference an active product line and active offering."
        )
    return _customer_product_binding_from_row(row)


def _draft_from_row(row: Mapping[str, Any]) -> ProgrammeDraft:
    return ProgrammeDraft(
        programme_draft_id=str(_row_value(row, "programme_draft_id")),
        account_id=str(_row_value(row, "account_id")),
        source_programme_version_id=str(_row_value(row, "source_programme_version_id"))
        if _row_value(row, "source_programme_version_id")
        else None,
        customer_journey_version_id=str(_row_value(row, "customer_journey_version_id")),
        programme_name=str(_row_value(row, "programme_name")),
        programme_description=_row_value(row, "programme_description"),
        operating_jurisdiction_code=str(_row_value(row, "operating_jurisdiction_code")),
        product_code=str(_row_value(row, "product_code")),
        sub_product_code=str(_row_value(row, "sub_product_code")),
        customer_product_line_id=str(_optional_row_value(row, "customer_product_line_id"))
        if _optional_row_value(row, "customer_product_line_id")
        else None,
        customer_product_offering_id=str(
            _optional_row_value(row, "customer_product_offering_id")
        )
        if _optional_row_value(row, "customer_product_offering_id")
        else None,
        customer_product_binding=_customer_product_binding_from_row(row),
        programme_status=str(_row_value(row, "programme_status")),
        draft_version=int(_row_value(row, "draft_version") or 1),
        campaign_defaults=_json_dict(_row_value(row, "campaign_defaults")),
        incentive_refs=_json_list(_row_value(row, "incentive_refs")),
        engagement_refs=_json_list(_row_value(row, "engagement_refs")),
        integration_readiness_snapshot=_json_dict(_row_value(row, "integration_readiness_snapshot")),
        commercial_entitlement_snapshot=_json_dict(_row_value(row, "commercial_entitlement_snapshot")),
        last_validation_status=str(_row_value(row, "last_validation_status")),
        review_status=str(_row_value(row, "review_status")),
        effective_from=_row_value(row, "effective_from"),
        effective_to=_row_value(row, "effective_to"),
        configuration_checksum=_row_value(row, "configuration_checksum"),
        created_by_ref=str(_row_value(row, "created_by_ref")),
        updated_by_ref=_row_value(row, "updated_by_ref"),
        created_at=_row_value(row, "created_at"),
        updated_at=_row_value(row, "updated_at"),
        archived_at=_row_value(row, "archived_at"),
    )


def _programme_validation_result_from_row(
    row: Mapping[str, Any],
) -> ProgrammeValidationResult:
    return ProgrammeValidationResult(
        programme_validation_result_id=str(
            _row_value(row, "programme_validation_result_id")
        ),
        account_id=str(_row_value(row, "account_id")),
        programme_draft_id=str(_row_value(row, "programme_draft_id")),
        customer_journey_version_id=str(_row_value(row, "customer_journey_version_id")),
        validation_status=str(_row_value(row, "validation_status")),
        publish_allowed=bool(_row_value(row, "publish_allowed")),
        campaign_binding_allowed=bool(_row_value(row, "campaign_binding_allowed")),
        plain_language_summary=str(_row_value(row, "plain_language_summary")),
        blockers=_json_list(_row_value(row, "blockers")),
        warnings=_json_list(_row_value(row, "warnings")),
        configuration_snapshot=_json_dict(_row_value(row, "configuration_snapshot")),
        guardrails=_json_list(_row_value(row, "guardrails")),
        payload_hash=str(_row_value(row, "payload_hash")),
        idempotency_key_hash=_row_value(row, "idempotency_key_hash"),
        correlation_id=_row_value(row, "correlation_id"),
        validated_by_ref=str(_row_value(row, "validated_by_ref")),
        created_at=_row_value(row, "created_at"),
    )


def _version_from_row(row: Mapping[str, Any]) -> ProgrammeVersionSummary:
    return ProgrammeVersionSummary(
        programme_version_id=str(_row_value(row, "programme_version_id")),
        account_id=str(_row_value(row, "account_id")),
        programme_code=str(_row_value(row, "programme_code")),
        programme_name=str(_row_value(row, "programme_name")),
        programme_description=_row_value(row, "programme_description"),
        operating_jurisdiction_code=str(_row_value(row, "operating_jurisdiction_code")),
        product_code=str(_row_value(row, "product_code")),
        sub_product_code=str(_row_value(row, "sub_product_code")),
        customer_product_line_id=str(_optional_row_value(row, "customer_product_line_id"))
        if _optional_row_value(row, "customer_product_line_id")
        else None,
        customer_product_offering_id=str(
            _optional_row_value(row, "customer_product_offering_id")
        )
        if _optional_row_value(row, "customer_product_offering_id")
        else None,
        customer_product_binding=_customer_product_binding_from_row(row),
        version_number=int(_row_value(row, "version_number") or 1),
        version_status=str(_row_value(row, "version_status")),
        customer_journey_version_id=str(_row_value(row, "customer_journey_version_id")),
        campaign_defaults_snapshot=_json_dict(_row_value(row, "campaign_defaults_snapshot")),
        incentive_refs_snapshot=_json_list(_row_value(row, "incentive_refs_snapshot")),
        engagement_refs_snapshot=_json_list(_row_value(row, "engagement_refs_snapshot")),
        integration_readiness_snapshot=_json_dict(_row_value(row, "integration_readiness_snapshot")),
        commercial_entitlement_snapshot=_json_dict(_row_value(row, "commercial_entitlement_snapshot")),
        effective_from=_row_value(row, "effective_from"),
        effective_to=_row_value(row, "effective_to"),
        safe_summary=_json_dict(_row_value(row, "safe_summary")),
        governance_metadata=_json_dict(_row_value(row, "governance_metadata")),
        published_at=_row_value(row, "published_at"),
        retired_at=_row_value(row, "retired_at"),
    )


def _programme_incentive_binding_from_row(
    row: Mapping[str, Any],
) -> ProgrammeIncentiveBinding:
    return ProgrammeIncentiveBinding(
        programme_incentive_binding_id=str(
            _row_value(row, "programme_incentive_binding_id")
        ),
        account_id=str(_row_value(row, "account_id")),
        programme_version_id=str(_row_value(row, "programme_version_id")),
        programme_code=str(_row_value(row, "programme_code")),
        programme_name=str(_row_value(row, "programme_name")),
        version_number=int(_row_value(row, "version_number") or 1),
        version_status=str(_row_value(row, "version_status")),
        binding_type=str(_row_value(row, "binding_type")),
        catalogue_type=str(_row_value(row, "catalogue_type")),
        catalogue_ref=str(_row_value(row, "catalogue_ref")),
        catalogue_version_ref=_row_value(row, "catalogue_version_ref"),
        effective_from=_row_value(row, "effective_from"),
        effective_to=_row_value(row, "effective_to"),
        binding_status=str(_row_value(row, "binding_status")),
        binding_payload_hash=str(_row_value(row, "binding_payload_hash")),
        bound_by_ref=str(_row_value(row, "bound_by_ref")),
        bound_at=_row_value(row, "bound_at"),
        archived_by_ref=_row_value(row, "archived_by_ref"),
        archived_at=_row_value(row, "archived_at"),
        safe_summary=_json_dict(_row_value(row, "safe_summary")),
        governance_metadata=_json_dict(_row_value(row, "governance_metadata")),
    )


def _normalise_programme_binding_type(value: Any) -> str:
    binding_type = _normalise_code(value, "binding_type", max_length=40)
    if binding_type not in PROGRAMME_INCENTIVE_BINDING_TYPES:
        raise ProgrammeConfigurationValidationError(
            "binding_type must be INCENTIVE or ENGAGEMENT."
        )
    return binding_type


def _normalise_programme_catalogue_type(value: Any) -> str:
    catalogue_type = _normalise_code(value, "catalogue_type", max_length=40)
    if catalogue_type not in PROGRAMME_INCENTIVE_CATALOGUE_TYPES:
        raise ProgrammeConfigurationValidationError(
            "catalogue_type must be REWARD_POLICY, MISSION, BADGE, or LEADERBOARD."
        )
    return catalogue_type


def _safe_incentive_binding_limit(limit: int) -> int:
    return max(1, min(int(limit), MAX_PROGRAMME_INCENTIVE_BINDING_LIMIT))


async def _find_published_programme_version(
    conn: Any,
    *,
    account_id: str,
    programme_version_id: str,
) -> Mapping[str, Any]:
    row = await conn.fetchrow(
        """
        SELECT *
        FROM referral_saas_programme_versions
        WHERE account_id = $1
          AND programme_version_id = $2
        LIMIT 1
        """,
        account_id,
        programme_version_id,
    )
    if not row:
        raise ProgrammeConfigurationNotFound(programme_version_id)
    if (
        str(_row_value(row, "version_status")) != "PUBLISHED"
        or _row_value(row, "retired_at") is not None
    ):
        raise ProgrammeConfigurationValidationError(
            "Incentive and engagement bindings can attach only to published, unretired programme versions."
        )
    return row


def _validate_programme_binding_effective_dates(
    *,
    programme_row: Mapping[str, Any],
    effective_from: date | None,
    effective_to: date | None,
) -> tuple[date, date | None]:
    programme_from = _row_value(programme_row, "effective_from")
    programme_to = _row_value(programme_row, "effective_to")
    if isinstance(programme_from, datetime):
        programme_from = programme_from.date()
    if isinstance(programme_to, datetime):
        programme_to = programme_to.date()
    if not isinstance(programme_from, date):
        raise ProgrammeConfigurationValidationError(
            "Programme version effective_from is required before binding incentives."
        )

    safe_from = effective_from or programme_from
    safe_to = effective_to or programme_to
    if safe_from < programme_from:
        raise ProgrammeConfigurationValidationError(
            "binding effective_from cannot be earlier than the programme version effective_from."
        )
    if safe_to is not None and safe_to <= safe_from:
        raise ProgrammeConfigurationValidationError(
            "binding effective_to must be after binding effective_from."
        )
    if programme_to is not None and safe_to is not None and safe_to > programme_to:
        raise ProgrammeConfigurationValidationError(
            "binding effective_to cannot be later than the programme version effective_to."
        )
    return safe_from, safe_to


def _programme_binding_window_matches(
    *,
    row: Mapping[str, Any],
    effective_from: date | None,
    effective_to: date | None,
) -> bool:
    row_from = _row_value(row, "effective_from")
    row_to = _row_value(row, "effective_to")
    if isinstance(row_from, datetime):
        row_from = row_from.date()
    if isinstance(row_to, datetime):
        row_to = row_to.date()
    return row_from == effective_from and row_to == effective_to


def _catalogue_item_from_row(row: Mapping[str, Any]) -> ProgrammeJourneyCatalogueItem:
    return ProgrammeJourneyCatalogueItem(
        customer_journey_version_id=str(_row_value(row, "customer_journey_version_id")),
        customer_journey_code=str(_row_value(row, "customer_journey_code")),
        version_number=int(_row_value(row, "version_number") or 1),
        version_status=str(_row_value(row, "version_status")),
        template_code=str(_row_value(row, "template_code")),
        template_version=str(_row_value(row, "template_version")),
        safe_summary=_json_dict(_row_value(row, "safe_summary")),
        governance_metadata=_json_dict(_row_value(row, "governance_metadata")),
        published_at=_row_value(row, "published_at"),
    )


async def list_referral_saas_programme_versions(
    *,
    account_id: str,
    include_retired: bool = False,
    limit: int = 50,
) -> tuple[ProgrammeVersionSummary, ...]:
    safe_account_id = _required_text(account_id, "account_id", max_length=80)
    retired_clause = "" if include_retired else "AND v.version_status <> 'RETIRED'"

    async with db_connection() as conn:
        rows = await conn.fetch(
            f"""
            SELECT
                v.*,
                l.external_product_line_ref,
                l.product_line_name,
                l.product_line_category,
                l.lifecycle_status AS product_line_status,
                o.external_offering_ref,
                o.offering_name,
                o.offering_family,
                o.lifecycle_status AS product_offering_status,
                o.operating_jurisdiction_code AS product_offering_operating_jurisdiction_code
            FROM referral_saas_programme_versions v
            LEFT JOIN referral_saas_customer_product_lines l
                ON l.customer_product_line_id = v.customer_product_line_id
               AND l.account_id = v.account_id
            LEFT JOIN referral_saas_customer_product_offerings o
                ON o.customer_product_offering_id = v.customer_product_offering_id
               AND o.customer_product_line_id = v.customer_product_line_id
               AND o.account_id = v.account_id
            WHERE v.account_id = $1
              {retired_clause}
            ORDER BY v.published_at DESC, v.version_number DESC
            LIMIT $2
            """,
            safe_account_id,
            _safe_limit(limit),
        )
    return tuple(_version_from_row(row) for row in rows)


async def list_referral_saas_programme_incentive_bindings(
    *,
    account_id: str,
    programme_version_id: str,
    include_archived: bool = False,
    limit: int = 50,
) -> tuple[ProgrammeIncentiveBinding, ...]:
    safe_account_id = _required_text(account_id, "account_id", max_length=80)
    safe_version_id = _required_text(
        programme_version_id, "programme_version_id", max_length=80
    )
    archived_filter = "" if include_archived else "AND b.binding_status = 'ACTIVE'"

    async with db_connection() as conn:
        rows = await conn.fetch(
            f"""
            SELECT
                b.*,
                v.programme_code,
                v.programme_name,
                v.version_number,
                v.version_status
            FROM referral_saas_programme_incentive_bindings b
            JOIN referral_saas_programme_versions v
                ON v.programme_version_id = b.programme_version_id
            WHERE b.account_id = $1
              AND b.programme_version_id = $2
              {archived_filter}
            ORDER BY b.bound_at DESC
            LIMIT $3
            """,
            safe_account_id,
            safe_version_id,
            _safe_incentive_binding_limit(limit),
        )
    return tuple(_programme_incentive_binding_from_row(row) for row in rows)


async def _programme_binding_snapshot(
    conn: Any,
    *,
    account_id: str,
    programme_version_id: str,
    binding_type: str,
) -> list[dict[str, Any]]:
    rows = await conn.fetch(
        """
        SELECT
            binding_type,
            catalogue_type,
            catalogue_ref,
            catalogue_version_ref,
            effective_from,
            effective_to,
            binding_status,
            safe_summary,
            governance_metadata,
            bound_at
        FROM referral_saas_programme_incentive_bindings
        WHERE account_id = $1
          AND programme_version_id = $2
          AND binding_type = $3
          AND binding_status = 'ACTIVE'
        ORDER BY catalogue_type ASC, catalogue_ref ASC
        """,
        account_id,
        programme_version_id,
        binding_type,
    )
    return [
        {
            "bindingType": str(_row_value(row, "binding_type")),
            "catalogueType": str(_row_value(row, "catalogue_type")),
            "catalogueRef": str(_row_value(row, "catalogue_ref")),
            "catalogueVersionRef": _row_value(row, "catalogue_version_ref"),
            "effectiveFrom": _isoformat(_row_value(row, "effective_from")),
            "effectiveTo": _isoformat(_row_value(row, "effective_to")),
            "bindingStatus": str(_row_value(row, "binding_status")),
            "safeSummary": _json_dict(_row_value(row, "safe_summary")),
            "governanceMetadata": _redact_json(
                _json_dict(_row_value(row, "governance_metadata"))
            ),
            "boundAt": _isoformat(_row_value(row, "bound_at")),
        }
        for row in rows
    ]


async def bind_referral_saas_programme_incentive(
    *,
    account_id: str,
    programme_version_id: str,
    binding_type: str,
    catalogue_type: str,
    catalogue_ref: str,
    catalogue_version_ref: str | None,
    effective_from: str | date | None,
    effective_to: str | date | None,
    idempotency_key_hash: str,
    request_payload_hash: str,
    actor_ref: str,
    actor_role: str | None = None,
    correlation_id: str | None = None,
    replace_existing: bool = False,
    replacement_reason: str | None = None,
) -> ProgrammeIncentiveBindingCommandResult:
    safe_account_id = _required_text(account_id, "account_id", max_length=80)
    safe_version_id = _required_text(
        programme_version_id, "programme_version_id", max_length=80
    )
    safe_binding_type = _normalise_programme_binding_type(binding_type)
    safe_catalogue_type = _normalise_programme_catalogue_type(catalogue_type)
    safe_catalogue_ref = _required_text(
        catalogue_ref, "catalogue_ref", max_length=160
    )
    safe_catalogue_version_ref = _optional_text(catalogue_version_ref, max_length=120)
    requested_from = _optional_iso_date(effective_from)
    requested_to = _optional_iso_date(effective_to)
    safe_idempotency_hash = _required_text(
        idempotency_key_hash, "idempotency_key_hash", max_length=256
    )
    safe_request_hash = _required_text(
        request_payload_hash, "request_payload_hash", max_length=256
    )
    safe_actor_ref = _required_text(actor_ref, "actor_ref", max_length=160)
    safe_actor_role = _optional_text(actor_role, max_length=80)
    safe_correlation_id = (
        _optional_text(correlation_id, max_length=160)
        or "programme-incentive-binding"
    )
    safe_replace_existing = bool(replace_existing)
    safe_replacement_reason = _optional_text(replacement_reason, max_length=500)

    async with db_connection() as conn:
        existing_idempotency = await conn.fetchrow(
            """
            SELECT resource_id, request_payload_hash
            FROM referral_saas_programme_configuration_idempotency_keys
            WHERE account_id = $1
              AND operation_type = 'PROGRAMME_INCENTIVE_BIND'
              AND idempotency_key_hash = $2
            ORDER BY created_at DESC
            LIMIT 1
            """,
            safe_account_id,
            safe_idempotency_hash,
        )
        if existing_idempotency:
            if _row_value(existing_idempotency, "request_payload_hash") != safe_request_hash:
                raise ProgrammeConfigurationIdempotencyConflict(
                    "Idempotency key was reused with different programme incentive binding content."
                )
            binding_row = await conn.fetchrow(
                """
                SELECT
                    b.*,
                    v.programme_code,
                    v.programme_name,
                    v.version_number,
                    v.version_status
                FROM referral_saas_programme_incentive_bindings b
                JOIN referral_saas_programme_versions v
                    ON v.programme_version_id = b.programme_version_id
                WHERE b.programme_incentive_binding_id = $1
                  AND b.account_id = $2
                LIMIT 1
                """,
                _row_value(existing_idempotency, "resource_id"),
                safe_account_id,
            )
            if not binding_row:
                raise ProgrammeConfigurationNotFound(
                    str(_row_value(existing_idempotency, "resource_id"))
                )
            return ProgrammeIncentiveBindingCommandResult(
                command_status="PROGRAMME_INCENTIVE_BOUND",
                binding=_programme_incentive_binding_from_row(binding_row),
                idempotency_status="REPLAY_SAME_PAYLOAD",
            )

        programme_row = await _find_published_programme_version(
            conn,
            account_id=safe_account_id,
            programme_version_id=safe_version_id,
        )
        safe_effective_from, safe_effective_to = _validate_programme_binding_effective_dates(
            programme_row=programme_row,
            effective_from=requested_from,
            effective_to=requested_to,
        )
        try:
            catalogue_record = await _find_approved_incentive_catalogue_record(
                conn,
                incentive_type=safe_catalogue_type,
                catalogue_ref=safe_catalogue_ref,
            )
        except CustomerJourneyIncentiveBindingValidationError as exc:
            raise ProgrammeConfigurationValidationError(str(exc)) from exc

        overlapping_rows = await conn.fetch(
            """
            SELECT
                b.*,
                v.programme_code,
                v.programme_name,
                v.version_number,
                v.version_status
            FROM referral_saas_programme_incentive_bindings b
            JOIN referral_saas_programme_versions v
                ON v.programme_version_id = b.programme_version_id
            WHERE b.account_id = $1
              AND b.programme_version_id = $2
              AND b.binding_type = $3
              AND b.catalogue_type = $4
              AND b.binding_status = 'ACTIVE'
              AND b.effective_from < COALESCE($6::date, '9999-12-31'::date)
              AND COALESCE(b.effective_to, '9999-12-31'::date) > $5::date
            """,
            safe_account_id,
            safe_version_id,
            safe_binding_type,
            safe_catalogue_type,
            safe_effective_from,
            safe_effective_to,
        )
        same_active_row = next(
            (
                row
                for row in overlapping_rows
                if str(_row_value(row, "catalogue_ref")).upper()
                == str(catalogue_record["catalogueRef"]).upper()
                and _programme_binding_window_matches(
                    row=row,
                    effective_from=safe_effective_from,
                    effective_to=safe_effective_to,
                )
            ),
            None,
        )
        replacement_rows = tuple(
            row
            for row in overlapping_rows
            if same_active_row is None
            or str(_row_value(row, "programme_incentive_binding_id"))
            != str(_row_value(same_active_row, "programme_incentive_binding_id"))
        )
        if replacement_rows and not safe_replace_existing:
            raise ProgrammeConfigurationValidationError(
                "An active programme incentive or engagement binding already overlaps "
                "this effective period. Use replaceExisting with a replacement reason, "
                "or retire the existing binding first."
            )
        if replacement_rows and not safe_replacement_reason:
            raise ProgrammeConfigurationValidationError(
                "replacementReason is required when replaceExisting is true."
            )

        safe_summary = {
            "bindingType": safe_binding_type,
            "catalogueType": safe_catalogue_type,
            "catalogueRef": catalogue_record["catalogueRef"],
            "catalogueVersionRef": safe_catalogue_version_ref,
            "catalogueLabel": catalogue_record.get("label"),
            "programmeVersionId": safe_version_id,
            "programmeCode": _row_value(programme_row, "programme_code"),
            "programmeName": _row_value(programme_row, "programme_name"),
            "versionNumber": int(_row_value(programme_row, "version_number") or 1),
            "effectiveFrom": _isoformat(safe_effective_from),
            "effectiveTo": _isoformat(safe_effective_to),
            "bindingStatus": "ACTIVE",
            "catalogueApproved": True,
            "noRewardApplicationConfirmed": True,
            "noBadgeAwardConfirmed": True,
            "noMissionProgressMutationConfirmed": True,
            "noLeaderboardScoringConfirmed": True,
            "noCampaignActivationConfirmed": True,
            "noProviderDispatchConfirmed": True,
            "noCredentialOrAuthMutationConfirmed": True,
            "noBillingPayoutSettlementOrMoneyMovementConfirmed": True,
        }
        governance_metadata = {
            "source": "TASK-417",
            "bindingControl": "APPROVED_CATALOGUE_REFERENCE_REQUIRED",
            "publishedProgrammeVersionRequired": True,
            "effectiveDateCompatibleWithProgramme": True,
            "replaceExisting": safe_replace_existing,
            "replacementReason": safe_replacement_reason,
            "catalogueRecord": catalogue_record,
        }

        async with conn.transaction():
            if same_active_row and not replacement_rows:
                binding_row = same_active_row
                command_status = "PROGRAMME_INCENTIVE_ALREADY_BOUND"
            else:
                archived_binding_ids: list[str] = []
                if replacement_rows:
                    await conn.execute(
                        """
                        UPDATE referral_saas_programme_incentive_bindings
                        SET binding_status = 'ARCHIVED',
                            archived_by_ref = $5,
                            archived_at = now(),
                            governance_metadata = COALESCE(governance_metadata, '{}'::jsonb)
                                || $6::jsonb
                        WHERE account_id = $1
                          AND programme_version_id = $2
                          AND binding_type = $3
                          AND catalogue_type = $4
                          AND binding_status = 'ACTIVE'
                          AND effective_from < COALESCE($8::date, '9999-12-31'::date)
                          AND COALESCE(effective_to, '9999-12-31'::date) > $7::date
                        """,
                        safe_account_id,
                        safe_version_id,
                        safe_binding_type,
                        safe_catalogue_type,
                        safe_actor_ref,
                        _jsonb(
                            {
                                "lifecycleAction": "REPLACED",
                                "replacementReason": safe_replacement_reason,
                                "replacedByCatalogueRef": catalogue_record["catalogueRef"],
                            }
                        ),
                        safe_effective_from,
                        safe_effective_to,
                    )
                    archived_binding_ids = [
                        str(_row_value(row, "programme_incentive_binding_id"))
                        for row in replacement_rows
                    ]

                binding_row = await conn.fetchrow(
                    """
                    INSERT INTO referral_saas_programme_incentive_bindings (
                        account_id,
                        programme_version_id,
                        binding_type,
                        catalogue_type,
                        catalogue_ref,
                        catalogue_version_ref,
                        effective_from,
                        effective_to,
                        binding_status,
                        binding_payload_hash,
                        idempotency_key_hash,
                        correlation_id,
                        bound_by_ref,
                        safe_summary,
                        governance_metadata
                    )
                    VALUES (
                        $1, $2, $3, $4, $5, $6, $7, $8, 'ACTIVE',
                        $9, $10, $11, $12, $13::jsonb, $14::jsonb
                    )
                    RETURNING *
                    """,
                    safe_account_id,
                    safe_version_id,
                    safe_binding_type,
                    safe_catalogue_type,
                    catalogue_record["catalogueRef"],
                    safe_catalogue_version_ref,
                    safe_effective_from,
                    safe_effective_to,
                    safe_request_hash,
                    safe_idempotency_hash,
                    safe_correlation_id,
                    safe_actor_ref,
                    _jsonb(safe_summary),
                    _jsonb(governance_metadata),
                )
                command_status = (
                    "PROGRAMME_INCENTIVE_REPLACED"
                    if archived_binding_ids
                    else "PROGRAMME_INCENTIVE_BOUND"
                )

            incentive_snapshot = await _programme_binding_snapshot(
                conn,
                account_id=safe_account_id,
                programme_version_id=safe_version_id,
                binding_type="INCENTIVE",
            )
            engagement_snapshot = await _programme_binding_snapshot(
                conn,
                account_id=safe_account_id,
                programme_version_id=safe_version_id,
                binding_type="ENGAGEMENT",
            )
            await conn.execute(
                """
                UPDATE referral_saas_programme_versions
                SET incentive_refs_snapshot = $3::jsonb,
                    engagement_refs_snapshot = $4::jsonb
                WHERE account_id = $1
                  AND programme_version_id = $2
                """,
                safe_account_id,
                safe_version_id,
                _jsonb(incentive_snapshot),
                _jsonb(engagement_snapshot),
            )

            binding_id = str(_row_value(binding_row, "programme_incentive_binding_id"))
            await conn.execute(
                """
                INSERT INTO referral_saas_programme_configuration_idempotency_keys (
                    account_id,
                    operation_type,
                    idempotency_key_hash,
                    request_payload_hash,
                    response_payload_hash,
                    resource_type,
                    resource_id,
                    response_status
                )
                VALUES ($1, 'PROGRAMME_INCENTIVE_BIND', $2, $3, $4,
                        'PROGRAMME_INCENTIVE_BINDING', $5, 'SUCCESS')
                """,
                safe_account_id,
                safe_idempotency_hash,
                safe_request_hash,
                _payload_hash({"programmeIncentiveBindingId": binding_id}),
                binding_id,
            )
            await conn.execute(
                """
                INSERT INTO referral_saas_programme_configuration_audit (
                    account_id,
                    programme_version_id,
                    customer_journey_version_id,
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
                    $1, $2, $3, $10, 'RECORDED',
                    $4, $5, NULL, 'ACTIVE', 'PROGRAMME_INCENTIVE_BIND',
                    $6, $7, $8::jsonb, $9::jsonb
                )
                """,
                safe_account_id,
                safe_version_id,
                _row_value(programme_row, "customer_journey_version_id"),
                safe_actor_ref,
                safe_actor_role,
                safe_correlation_id,
                safe_idempotency_hash,
                _jsonb(safe_summary),
                _jsonb(PROGRAMME_CONFIGURATION_REDACTIONS),
                command_status,
            )
            binding_row = dict(binding_row)
            binding_row.update(
                {
                    "programme_code": _row_value(programme_row, "programme_code"),
                    "programme_name": _row_value(programme_row, "programme_name"),
                    "version_number": _row_value(programme_row, "version_number"),
                    "version_status": _row_value(programme_row, "version_status"),
                }
            )

    return ProgrammeIncentiveBindingCommandResult(
        command_status=command_status,
        binding=_programme_incentive_binding_from_row(binding_row),
        idempotency_status="NEW_REQUEST",
    )


async def retire_referral_saas_programme_incentive_binding(
    *,
    account_id: str,
    programme_version_id: str,
    programme_incentive_binding_id: str,
    retirement_reason: str,
    idempotency_key_hash: str,
    request_payload_hash: str,
    actor_ref: str,
    actor_role: str | None = None,
    correlation_id: str | None = None,
) -> ProgrammeIncentiveBindingCommandResult:
    safe_account_id = _required_text(account_id, "account_id", max_length=80)
    safe_version_id = _required_text(
        programme_version_id, "programme_version_id", max_length=80
    )
    safe_binding_id = _required_text(
        programme_incentive_binding_id,
        "programme_incentive_binding_id",
        max_length=80,
    )
    safe_reason = _required_text(retirement_reason, "retirement_reason", max_length=500)
    safe_idempotency_hash = _required_text(
        idempotency_key_hash, "idempotency_key_hash", max_length=256
    )
    safe_request_hash = _required_text(
        request_payload_hash, "request_payload_hash", max_length=256
    )
    safe_actor_ref = _required_text(actor_ref, "actor_ref", max_length=160)
    safe_actor_role = _optional_text(actor_role, max_length=80)
    safe_correlation_id = (
        _optional_text(correlation_id, max_length=160)
        or "programme-incentive-binding-retire"
    )

    async with db_connection() as conn:
        existing_idempotency = await conn.fetchrow(
            """
            SELECT resource_id, request_payload_hash
            FROM referral_saas_programme_configuration_idempotency_keys
            WHERE account_id = $1
              AND operation_type = 'PROGRAMME_INCENTIVE_RETIRE'
              AND idempotency_key_hash = $2
            ORDER BY created_at DESC
            LIMIT 1
            """,
            safe_account_id,
            safe_idempotency_hash,
        )
        if existing_idempotency:
            if _row_value(existing_idempotency, "request_payload_hash") != safe_request_hash:
                raise ProgrammeConfigurationIdempotencyConflict(
                    "Idempotency key was reused with different programme incentive retirement content."
                )
            binding_row = await conn.fetchrow(
                """
                SELECT
                    b.*,
                    v.programme_code,
                    v.programme_name,
                    v.version_number,
                    v.version_status
                FROM referral_saas_programme_incentive_bindings b
                JOIN referral_saas_programme_versions v
                    ON v.programme_version_id = b.programme_version_id
                WHERE b.programme_incentive_binding_id = $1
                  AND b.account_id = $2
                LIMIT 1
                """,
                _row_value(existing_idempotency, "resource_id"),
                safe_account_id,
            )
            if not binding_row:
                raise ProgrammeConfigurationNotFound(
                    str(_row_value(existing_idempotency, "resource_id"))
                )
            return ProgrammeIncentiveBindingCommandResult(
                command_status="PROGRAMME_INCENTIVE_RETIRED",
                binding=_programme_incentive_binding_from_row(binding_row),
                idempotency_status="REPLAY_SAME_PAYLOAD",
            )

        binding_row = await conn.fetchrow(
            """
            SELECT
                b.*,
                v.programme_code,
                v.programme_name,
                v.version_number,
                v.version_status,
                v.customer_journey_version_id
            FROM referral_saas_programme_incentive_bindings b
            JOIN referral_saas_programme_versions v
                ON v.programme_version_id = b.programme_version_id
            WHERE b.account_id = $1
              AND b.programme_version_id = $2
              AND b.programme_incentive_binding_id = $3
            LIMIT 1
            """,
            safe_account_id,
            safe_version_id,
            safe_binding_id,
        )
        if not binding_row:
            raise ProgrammeConfigurationNotFound(safe_binding_id)
        if str(_row_value(binding_row, "binding_status")) == "ARCHIVED":
            raise ProgrammeConfigurationValidationError(
                "Programme incentive or engagement binding is already retired."
            )

        safe_summary = {
            "programmeIncentiveBindingId": safe_binding_id,
            "programmeVersionId": safe_version_id,
            "bindingType": str(_row_value(binding_row, "binding_type")),
            "catalogueType": str(_row_value(binding_row, "catalogue_type")),
            "catalogueRef": str(_row_value(binding_row, "catalogue_ref")),
            "previousBindingStatus": str(_row_value(binding_row, "binding_status")),
            "nextBindingStatus": "ARCHIVED",
            "retirementReason": safe_reason,
            "noRewardApplicationConfirmed": True,
            "noBadgeAwardConfirmed": True,
            "noMissionProgressMutationConfirmed": True,
            "noLeaderboardScoringConfirmed": True,
            "noCampaignActivationConfirmed": True,
            "noProviderDispatchConfirmed": True,
            "noCredentialOrAuthMutationConfirmed": True,
            "noBillingPayoutSettlementOrMoneyMovementConfirmed": True,
        }

        async with conn.transaction():
            retired_row = await conn.fetchrow(
                """
                UPDATE referral_saas_programme_incentive_bindings
                SET binding_status = 'ARCHIVED',
                    archived_by_ref = $4,
                    archived_at = now(),
                    governance_metadata = COALESCE(governance_metadata, '{}'::jsonb)
                        || $5::jsonb
                WHERE account_id = $1
                  AND programme_version_id = $2
                  AND programme_incentive_binding_id = $3
                RETURNING *
                """,
                safe_account_id,
                safe_version_id,
                safe_binding_id,
                safe_actor_ref,
                _jsonb(
                    {
                        "lifecycleAction": "RETIRED",
                        "retirementReason": safe_reason,
                    }
                ),
            )
            incentive_snapshot = await _programme_binding_snapshot(
                conn,
                account_id=safe_account_id,
                programme_version_id=safe_version_id,
                binding_type="INCENTIVE",
            )
            engagement_snapshot = await _programme_binding_snapshot(
                conn,
                account_id=safe_account_id,
                programme_version_id=safe_version_id,
                binding_type="ENGAGEMENT",
            )
            await conn.execute(
                """
                UPDATE referral_saas_programme_versions
                SET incentive_refs_snapshot = $3::jsonb,
                    engagement_refs_snapshot = $4::jsonb
                WHERE account_id = $1
                  AND programme_version_id = $2
                """,
                safe_account_id,
                safe_version_id,
                _jsonb(incentive_snapshot),
                _jsonb(engagement_snapshot),
            )
            await conn.execute(
                """
                INSERT INTO referral_saas_programme_configuration_idempotency_keys (
                    account_id,
                    operation_type,
                    idempotency_key_hash,
                    request_payload_hash,
                    response_payload_hash,
                    resource_type,
                    resource_id,
                    response_status
                )
                VALUES ($1, 'PROGRAMME_INCENTIVE_RETIRE', $2, $3, $4,
                        'PROGRAMME_INCENTIVE_BINDING', $5, 'SUCCESS')
                """,
                safe_account_id,
                safe_idempotency_hash,
                safe_request_hash,
                _payload_hash({"programmeIncentiveBindingId": safe_binding_id}),
                safe_binding_id,
            )
            await conn.execute(
                """
                INSERT INTO referral_saas_programme_configuration_audit (
                    account_id,
                    programme_version_id,
                    customer_journey_version_id,
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
                    $1, $2, $3, 'PROGRAMME_INCENTIVE_RETIRED', 'RECORDED',
                    $4, $5, $6, 'ARCHIVED', 'PROGRAMME_INCENTIVE_RETIRE',
                    $7, $8, $9::jsonb, $10::jsonb
                )
                """,
                safe_account_id,
                safe_version_id,
                _row_value(binding_row, "customer_journey_version_id"),
                safe_actor_ref,
                safe_actor_role,
                str(_row_value(binding_row, "binding_status")),
                safe_correlation_id,
                safe_idempotency_hash,
                _jsonb(safe_summary),
                _jsonb(PROGRAMME_CONFIGURATION_REDACTIONS),
            )
            retired_row = dict(retired_row)
            retired_row.update(
                {
                    "programme_code": _row_value(binding_row, "programme_code"),
                    "programme_name": _row_value(binding_row, "programme_name"),
                    "version_number": _row_value(binding_row, "version_number"),
                    "version_status": _row_value(binding_row, "version_status"),
                }
            )

    return ProgrammeIncentiveBindingCommandResult(
        command_status="PROGRAMME_INCENTIVE_RETIRED",
        binding=_programme_incentive_binding_from_row(retired_row),
        idempotency_status="NEW_REQUEST",
    )


async def list_referral_saas_programme_drafts(
    *,
    account_id: str,
    include_archived: bool = False,
    limit: int = 50,
) -> tuple[ProgrammeDraft, ...]:
    safe_account_id = _required_text(account_id, "account_id", max_length=80)
    archived_clause = "" if include_archived else "AND d.archived_at IS NULL"

    async with db_connection() as conn:
        rows = await conn.fetch(
            f"""
            SELECT
                d.*,
                l.external_product_line_ref,
                l.product_line_name,
                l.product_line_category,
                l.lifecycle_status AS product_line_status,
                o.external_offering_ref,
                o.offering_name,
                o.offering_family,
                o.lifecycle_status AS product_offering_status,
                o.operating_jurisdiction_code AS product_offering_operating_jurisdiction_code
            FROM referral_saas_programme_drafts d
            LEFT JOIN referral_saas_customer_product_lines l
                ON l.customer_product_line_id = d.customer_product_line_id
               AND l.account_id = d.account_id
            LEFT JOIN referral_saas_customer_product_offerings o
                ON o.customer_product_offering_id = d.customer_product_offering_id
               AND o.customer_product_line_id = d.customer_product_line_id
               AND o.account_id = d.account_id
            WHERE d.account_id = $1
              {archived_clause}
            ORDER BY d.updated_at DESC, d.created_at DESC
            LIMIT $2
            """,
            safe_account_id,
            _safe_limit(limit),
        )
    return tuple(_draft_from_row(row) for row in rows)


async def get_referral_saas_programme_draft(
    *,
    account_id: str,
    programme_draft_id: str,
) -> ProgrammeDraft:
    safe_account_id = _required_text(account_id, "account_id", max_length=80)
    safe_draft_id = _required_text(programme_draft_id, "programme_draft_id", max_length=80)

    async with db_connection() as conn:
        row = await conn.fetchrow(
            """
            SELECT
                d.*,
                l.external_product_line_ref,
                l.product_line_name,
                l.product_line_category,
                l.lifecycle_status AS product_line_status,
                o.external_offering_ref,
                o.offering_name,
                o.offering_family,
                o.lifecycle_status AS product_offering_status,
                o.operating_jurisdiction_code AS product_offering_operating_jurisdiction_code
            FROM referral_saas_programme_drafts d
            LEFT JOIN referral_saas_customer_product_lines l
                ON l.customer_product_line_id = d.customer_product_line_id
               AND l.account_id = d.account_id
            LEFT JOIN referral_saas_customer_product_offerings o
                ON o.customer_product_offering_id = d.customer_product_offering_id
               AND o.customer_product_line_id = d.customer_product_line_id
               AND o.account_id = d.account_id
            WHERE d.account_id = $1
              AND d.programme_draft_id = $2
              AND d.archived_at IS NULL
            LIMIT 1
            """,
            safe_account_id,
            safe_draft_id,
        )
    if not row:
        raise ProgrammeConfigurationNotFound(safe_draft_id)
    return _draft_from_row(row)


async def get_referral_saas_programme_catalogue(
    *,
    account_id: str,
    limit: int = 50,
) -> dict[str, Any]:
    safe_account_id = _required_text(account_id, "account_id", max_length=80)

    async with db_connection() as conn:
        rows = await conn.fetch(
            """
            SELECT
                cv.customer_journey_version_id,
                cv.customer_journey_code,
                cv.version_number,
                cv.version_status,
                cv.safe_summary,
                cv.governance_metadata,
                cv.published_at,
                tv.template_code,
                tv.template_version
            FROM referral_saas_customer_journey_versions cv
            JOIN referral_saas_journey_template_versions tv
                ON tv.journey_template_version_id = cv.journey_template_version_id
            WHERE cv.account_id = $1
              AND cv.archived_at IS NULL
              AND cv.version_status IN ('PUBLISHED', 'ACTIVE')
            ORDER BY cv.published_at DESC, cv.version_number DESC
            LIMIT $2
            """,
            safe_account_id,
            _safe_limit(limit),
        )
    product_catalogue = await list_referral_saas_customer_product_catalogue(
        account_id=safe_account_id,
        include_retired=False,
        limit=limit,
    )

    return {
        "productCode": "REFERRAL_SAAS",
        "subProductCodes": sorted(PROGRAMME_SUB_PRODUCT_CODES),
        "customerProductLines": product_catalogue["productLines"],
        "customerJourneyVersions": [
            _catalogue_item_from_row(row).to_safe_dict() for row in rows
        ],
        "guardrails": list(PROGRAMME_CONFIGURATION_GUARDRAILS),
        "redactions": list(PROGRAMME_CONFIGURATION_REDACTIONS),
        "noProgrammePublishConfirmed": True,
        "noCampaignActivationConfirmed": True,
        "noReferralRuntimeSwitchConfirmed": True,
        "noProviderDispatchConfirmed": True,
        "noCredentialOrAuthMutationConfirmed": True,
        "noBillingPayoutSettlementOrMoneyMovementConfirmed": True,
    }


async def _assert_published_customer_journey_version(
    conn: Any,
    *,
    account_id: str,
    customer_journey_version_id: str,
) -> None:
    row = await conn.fetchrow(
        """
        SELECT customer_journey_version_id
        FROM referral_saas_customer_journey_versions
        WHERE account_id = $1
          AND customer_journey_version_id = $2
          AND archived_at IS NULL
          AND version_status IN ('PUBLISHED', 'ACTIVE')
        LIMIT 1
        """,
        account_id,
        customer_journey_version_id,
    )
    if not row:
        raise ProgrammeConfigurationNotFound(
            "Published customer journey version is unavailable for this account."
        )


async def save_referral_saas_programme_draft(
    *,
    account_id: str,
    programme_name: str,
    programme_description: str | None,
    operating_jurisdiction_code: str,
    sub_product_code: str,
    customer_journey_version_id: str,
    campaign_defaults: Mapping[str, Any] | None,
    incentive_refs: list[Any] | None,
    engagement_refs: list[Any] | None,
    integration_readiness_snapshot: Mapping[str, Any] | None,
    commercial_entitlement_snapshot: Mapping[str, Any] | None,
    source_programme_version_id: str | None = None,
    programme_draft_id: str | None = None,
    product_code: str = "REFERRAL_SAAS",
    customer_product_line_id: str | None = None,
    customer_product_offering_id: str | None = None,
    effective_from: str | None = None,
    effective_to: str | None = None,
    idempotency_key_hash: str,
    request_payload_hash: str,
    actor_ref: str,
    actor_role: str | None,
    correlation_id: str | None = None,
) -> ProgrammeDraftCommandResult:
    safe_account_id = _required_text(account_id, "account_id", max_length=80)
    safe_programme_name = _required_text(programme_name, "programme_name", max_length=180)
    safe_programme_description = _optional_text(programme_description, max_length=500)
    safe_jurisdiction = _normalise_code(
        operating_jurisdiction_code,
        "operating_jurisdiction_code",
        max_length=40,
    )
    safe_product_code = _normalise_code(product_code, "product_code", max_length=80)
    if safe_product_code != "REFERRAL_SAAS":
        raise ProgrammeConfigurationValidationError(
            "product_code must be REFERRAL_SAAS for this product surface."
        )
    safe_sub_product_code = _normalise_code(
        sub_product_code,
        "sub_product_code",
        max_length=80,
    )
    if safe_sub_product_code not in PROGRAMME_SUB_PRODUCT_CODES:
        raise ProgrammeConfigurationValidationError(
            "sub_product_code must be one of REFERRAL_MANAGEMENT, CAMPAIGN_ATTRIBUTION, or RMCA_BUNDLE."
        )
    safe_customer_journey_version_id = _required_text(
        customer_journey_version_id,
        "customer_journey_version_id",
        max_length=80,
    )
    safe_customer_product_line_id = _optional_text(
        customer_product_line_id,
        max_length=80,
    )
    safe_customer_product_offering_id = _optional_text(
        customer_product_offering_id,
        max_length=80,
    )
    safe_source_programme_version_id = _optional_text(
        source_programme_version_id,
        max_length=80,
    )
    safe_programme_draft_id = _optional_text(programme_draft_id, max_length=80)
    safe_effective_from = _optional_text(effective_from, max_length=40)
    safe_effective_to = _optional_text(effective_to, max_length=40)
    safe_campaign_defaults = _normalise_safe_mapping(
        campaign_defaults,
        "campaign_defaults",
    )
    safe_incentive_refs = _normalise_safe_list(incentive_refs, "incentive_refs")
    safe_engagement_refs = _normalise_safe_list(engagement_refs, "engagement_refs")
    safe_integration_snapshot = _normalise_safe_mapping(
        integration_readiness_snapshot,
        "integration_readiness_snapshot",
    )
    safe_commercial_snapshot = _normalise_safe_mapping(
        commercial_entitlement_snapshot,
        "commercial_entitlement_snapshot",
    )
    safe_idempotency_hash = _required_text(
        idempotency_key_hash,
        "idempotency_key_hash",
        max_length=256,
    )
    safe_request_hash = _required_text(
        request_payload_hash,
        "request_payload_hash",
        max_length=256,
    )
    safe_actor_ref = _required_text(actor_ref, "actor_ref", max_length=160)
    safe_actor_role = _optional_text(actor_role, max_length=80)
    safe_correlation_id = _optional_text(correlation_id, max_length=160)

    canonical_payload = {
        "programmeName": safe_programme_name,
        "programmeDescription": safe_programme_description,
        "operatingJurisdictionCode": safe_jurisdiction,
        "productCode": safe_product_code,
        "subProductCode": safe_sub_product_code,
        "customerProductLineId": safe_customer_product_line_id,
        "customerProductOfferingId": safe_customer_product_offering_id,
        "customerJourneyVersionId": safe_customer_journey_version_id,
        "sourceProgrammeVersionId": safe_source_programme_version_id,
        "campaignDefaults": safe_campaign_defaults,
        "incentiveRefs": safe_incentive_refs,
        "engagementRefs": safe_engagement_refs,
        "integrationReadinessSnapshot": safe_integration_snapshot,
        "commercialEntitlementSnapshot": safe_commercial_snapshot,
        "effectiveFrom": safe_effective_from,
        "effectiveTo": safe_effective_to,
    }
    payload_hash = _payload_hash(canonical_payload)

    async with db_connection() as conn:
        existing_idempotency = await conn.fetchrow(
            """
            SELECT *
            FROM referral_saas_programme_configuration_idempotency_keys
            WHERE account_id = $1
              AND operation_type = 'PROGRAMME_DRAFT_SAVE'
              AND idempotency_key_hash = $2
            LIMIT 1
            """,
            safe_account_id,
            safe_idempotency_hash,
        )
        if existing_idempotency:
            if _row_value(existing_idempotency, "request_payload_hash") != safe_request_hash:
                raise ProgrammeConfigurationIdempotencyConflict(
                    "Idempotency key was reused with different programme draft content."
                )
            replay_row = await conn.fetchrow(
                """
                SELECT *
                FROM referral_saas_programme_drafts
                WHERE account_id = $1
                  AND programme_draft_id = $2
                  AND archived_at IS NULL
                LIMIT 1
                """,
                safe_account_id,
                str(_row_value(existing_idempotency, "resource_id")),
            )
            if not replay_row:
                raise ProgrammeConfigurationNotFound(
                    str(_row_value(existing_idempotency, "resource_id"))
                )
            return ProgrammeDraftCommandResult(
                command_status="REPLAY_SAME_PAYLOAD",
                draft=_draft_from_row(replay_row),
                idempotency_status="REPLAY_SAME_PAYLOAD",
            )

        await _assert_published_customer_journey_version(
            conn,
            account_id=safe_account_id,
            customer_journey_version_id=safe_customer_journey_version_id,
        )
        product_binding = await _get_active_customer_product_offering_binding(
            conn,
            account_id=safe_account_id,
            operating_jurisdiction_code=safe_jurisdiction,
            customer_product_line_id=safe_customer_product_line_id,
            customer_product_offering_id=safe_customer_product_offering_id,
            required=False,
        )

        async with conn.transaction():
            previous_status: str | None = None
            if safe_programme_draft_id:
                existing_draft_row = await conn.fetchrow(
                    """
                    SELECT programme_status
                    FROM referral_saas_programme_drafts
                    WHERE programme_draft_id = $1
                      AND account_id = $2
                      AND archived_at IS NULL
                    LIMIT 1
                    """,
                    safe_programme_draft_id,
                    safe_account_id,
                )
                if not existing_draft_row:
                    raise ProgrammeConfigurationNotFound(safe_programme_draft_id)
                previous_status = _ensure_programme_draft_editable(
                    str(_row_value(existing_draft_row, "programme_status"))
                )
                row = await conn.fetchrow(
                    """
                    UPDATE referral_saas_programme_drafts
                    SET source_programme_version_id = $3,
                        customer_journey_version_id = $4,
                        programme_name = $5,
                        programme_description = $6,
                        operating_jurisdiction_code = $7,
                        product_code = $8,
                        sub_product_code = $9,
                        customer_product_line_id = $10,
                        customer_product_offering_id = $11,
                        programme_status = 'DRAFT',
                        draft_version = draft_version + 1,
                        campaign_defaults = $12::jsonb,
                        incentive_refs = $13::jsonb,
                        engagement_refs = $14::jsonb,
                        integration_readiness_snapshot = $15::jsonb,
                        commercial_entitlement_snapshot = $16::jsonb,
                        validation_result_id = NULL,
                        last_validation_status = 'NOT_VALIDATED',
                        review_status = 'NOT_SUBMITTED',
                        effective_from = $17,
                        effective_to = $18,
                        configuration_checksum = $19,
                        payload_hash = $19,
                        idempotency_key_hash = $20,
                        correlation_id = $21,
                        updated_by_ref = $22,
                        updated_at = now()
                    WHERE programme_draft_id = $1
                      AND account_id = $2
                      AND archived_at IS NULL
                      AND programme_status IN ('DRAFT', 'VALIDATION_FAILED', 'VALIDATED')
                    RETURNING *
                    """,
                    safe_programme_draft_id,
                    safe_account_id,
                    safe_source_programme_version_id,
                    safe_customer_journey_version_id,
                    safe_programme_name,
                    safe_programme_description,
                    safe_jurisdiction,
                    safe_product_code,
                    safe_sub_product_code,
                    safe_customer_product_line_id,
                    safe_customer_product_offering_id,
                    _jsonb(safe_campaign_defaults),
                    _jsonb(safe_incentive_refs),
                    _jsonb(safe_engagement_refs),
                    _jsonb(safe_integration_snapshot),
                    _jsonb(safe_commercial_snapshot),
                    safe_effective_from,
                    safe_effective_to,
                    payload_hash,
                    safe_idempotency_hash,
                    safe_correlation_id,
                    safe_actor_ref,
                )
                if not row:
                    raise ProgrammeConfigurationLifecycleLocked(
                        "Programme draft state changed before the update could be "
                        "recorded. Refresh the draft and use the governed lifecycle "
                        "action before editing reviewed programme evidence."
                    )
                event_type = "PROGRAMME_DRAFT_UPDATED"
            else:
                row = await conn.fetchrow(
                    """
                    INSERT INTO referral_saas_programme_drafts (
                        account_id,
                        source_programme_version_id,
                        customer_journey_version_id,
                        programme_name,
                        programme_description,
                        operating_jurisdiction_code,
                        product_code,
                        sub_product_code,
                        customer_product_line_id,
                        customer_product_offering_id,
                        programme_status,
                        draft_version,
                        campaign_defaults,
                        incentive_refs,
                        engagement_refs,
                        integration_readiness_snapshot,
                        commercial_entitlement_snapshot,
                        last_validation_status,
                        review_status,
                        effective_from,
                        effective_to,
                        configuration_checksum,
                        payload_hash,
                        idempotency_key_hash,
                        correlation_id,
                        created_by_ref,
                        updated_by_ref
                    )
                    VALUES (
                        $1, $2, $3, $4, $5, $6, $7, $8, $9, $10,
                        'DRAFT', 1, $11::jsonb, $12::jsonb, $13::jsonb,
                        $14::jsonb, $15::jsonb, 'NOT_VALIDATED',
                        'NOT_SUBMITTED', $16, $17, $18, $18, $19, $20,
                        $21, $21
                    )
                    RETURNING *
                    """,
                    safe_account_id,
                    safe_source_programme_version_id,
                    safe_customer_journey_version_id,
                    safe_programme_name,
                    safe_programme_description,
                    safe_jurisdiction,
                    safe_product_code,
                    safe_sub_product_code,
                    safe_customer_product_line_id,
                    safe_customer_product_offering_id,
                    _jsonb(safe_campaign_defaults),
                    _jsonb(safe_incentive_refs),
                    _jsonb(safe_engagement_refs),
                    _jsonb(safe_integration_snapshot),
                    _jsonb(safe_commercial_snapshot),
                    safe_effective_from,
                    safe_effective_to,
                    payload_hash,
                    safe_idempotency_hash,
                    safe_correlation_id,
                    safe_actor_ref,
                )
                event_type = "PROGRAMME_DRAFT_CREATED"

            draft_id = str(_row_value(row, "programme_draft_id"))
            await conn.execute(
                """
                INSERT INTO referral_saas_programme_configuration_idempotency_keys (
                    account_id,
                    operation_type,
                    idempotency_key_hash,
                    request_payload_hash,
                    response_payload_hash,
                    resource_type,
                    resource_id,
                    response_status
                )
                VALUES ($1, 'PROGRAMME_DRAFT_SAVE', $2, $3, $4,
                        'PROGRAMME_DRAFT', $5, 'SUCCESS')
                """,
                safe_account_id,
                safe_idempotency_hash,
                safe_request_hash,
                _payload_hash({"programmeDraftId": draft_id}),
                draft_id,
            )
            await conn.execute(
                """
                INSERT INTO referral_saas_programme_configuration_audit (
                    account_id,
                    programme_draft_id,
                    customer_journey_version_id,
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
                    $1, $2, $3, $4, 'RECORDED', $5, $6, $11, 'DRAFT',
                    'PROGRAMME_DRAFT_SAVE', $7, $8, $9::jsonb, $10::jsonb
                )
                """,
                safe_account_id,
                draft_id,
                safe_customer_journey_version_id,
                event_type,
                safe_actor_ref,
                safe_actor_role,
                safe_correlation_id,
                safe_idempotency_hash,
                _jsonb(
                    {
                        "programmeName": safe_programme_name,
                        "productCode": safe_product_code,
                        "subProductCode": safe_sub_product_code,
                        "customerProductBinding": product_binding,
                        "configurationChecksum": payload_hash,
                        "ordinarySaveAllowedFromStatus": previous_status,
                    }
                ),
                _jsonb(PROGRAMME_CONFIGURATION_REDACTIONS),
                previous_status,
            )

    return ProgrammeDraftCommandResult(
        command_status="DRAFT_SAVED",
        draft=_draft_from_row(row),
        idempotency_status="NEW_REQUEST",
    )


async def validate_referral_saas_programme_draft(
    *,
    account_id: str,
    programme_draft_id: str,
    idempotency_key_hash: str,
    request_payload_hash: str,
    actor_ref: str,
    actor_role: str | None,
    correlation_id: str | None = None,
) -> ProgrammeValidationResult:
    safe_account_id = _required_text(account_id, "account_id", max_length=80)
    safe_draft_id = _required_text(
        programme_draft_id,
        "programme_draft_id",
        max_length=80,
    )
    safe_idempotency_hash = _required_text(
        idempotency_key_hash,
        "idempotency_key_hash",
        max_length=256,
    )
    safe_request_hash = _required_text(
        request_payload_hash,
        "request_payload_hash",
        max_length=256,
    )
    safe_actor_ref = _required_text(actor_ref, "actor_ref", max_length=160)
    safe_actor_role = _optional_text(actor_role, max_length=80)
    safe_correlation_id = _optional_text(correlation_id, max_length=160)

    async with db_connection() as conn:
        existing_idempotency = await conn.fetchrow(
            """
            SELECT *
            FROM referral_saas_programme_configuration_idempotency_keys
            WHERE account_id = $1
              AND operation_type = 'PROGRAMME_DRAFT_VALIDATE'
              AND idempotency_key_hash = $2
            LIMIT 1
            """,
            safe_account_id,
            safe_idempotency_hash,
        )
        if existing_idempotency:
            if _row_value(existing_idempotency, "request_payload_hash") != safe_request_hash:
                raise ProgrammeConfigurationIdempotencyConflict(
                    "Idempotency key was reused with different programme validation content."
                )
            validation_row = await conn.fetchrow(
                """
                SELECT *
                FROM referral_saas_programme_validation_results
                WHERE account_id = $1
                  AND programme_validation_result_id = $2
                LIMIT 1
                """,
                safe_account_id,
                _row_value(existing_idempotency, "resource_id"),
            )
            if not validation_row:
                raise ProgrammeConfigurationNotFound(
                    str(_row_value(existing_idempotency, "resource_id"))
                )
            return _programme_validation_result_from_row(validation_row)

        draft_row = await conn.fetchrow(
            """
            SELECT
                d.*,
                cv.customer_journey_code,
                cv.version_status AS journey_version_status,
                cv.archived_at AS journey_archived_at,
                cv.safe_summary AS journey_safe_summary
            FROM referral_saas_programme_drafts d
            LEFT JOIN referral_saas_customer_journey_versions cv
                ON cv.customer_journey_version_id = d.customer_journey_version_id
               AND cv.account_id = d.account_id
            WHERE d.account_id = $1
              AND d.programme_draft_id = $2
              AND d.archived_at IS NULL
            LIMIT 1
            """,
            safe_account_id,
            safe_draft_id,
        )
        if not draft_row:
            raise ProgrammeConfigurationNotFound(safe_draft_id)

        blockers: list[dict[str, Any]] = []
        warnings: list[dict[str, Any]] = []
        journey_status = str(_row_value(draft_row, "journey_version_status") or "")
        if journey_status not in {"PUBLISHED", "ACTIVE"} or _row_value(
            draft_row, "journey_archived_at"
        ):
            blockers.append(
                _issue(
                    code="PUBLISHED_JOURNEY_VERSION_REQUIRED",
                    title="Published journey version required",
                    plain_language=(
                        "Choose an approved and published customer journey version "
                        "before this programme can be published."
                    ),
                    next_action="Select a published customer journey version.",
                    area="journey",
                    can_wait=False,
                )
            )
        product_binding: dict[str, Any] = {}
        try:
            product_binding = await _get_active_customer_product_offering_binding(
                conn,
                account_id=safe_account_id,
                operating_jurisdiction_code=str(
                    _row_value(draft_row, "operating_jurisdiction_code")
                ),
                customer_product_line_id=str(
                    _optional_row_value(draft_row, "customer_product_line_id")
                )
                if _optional_row_value(draft_row, "customer_product_line_id")
                else None,
                customer_product_offering_id=str(
                    _optional_row_value(draft_row, "customer_product_offering_id")
                )
                if _optional_row_value(draft_row, "customer_product_offering_id")
                else None,
                required=True,
            )
        except ProgrammeConfigurationValidationError as exc:
            blockers.append(
                _issue(
                    code="ACTIVE_CUSTOMER_PRODUCT_OFFERING_REQUIRED",
                    title="Customer product and offering required",
                    plain_language=str(exc),
                    next_action=(
                        "Choose an active customer product line and offering for this programme."
                    ),
                    area="customer_product_offering",
                    can_wait=False,
                )
            )

        effective_from = _row_value(draft_row, "effective_from")
        effective_to = _row_value(draft_row, "effective_to")
        try:
            parsed_from = _optional_iso_date(effective_from)
            parsed_to = _optional_iso_date(effective_to)
        except ValueError:
            blockers.append(
                _issue(
                    code="INVALID_EFFECTIVE_DATE",
                    title="Effective date is invalid",
                    plain_language="Use valid effective dates before publishing the programme.",
                    next_action="Correct the programme effective dates.",
                    area="effective_dates",
                    can_wait=False,
                )
            )
        else:
            if parsed_from and parsed_to and parsed_to <= parsed_from:
                blockers.append(
                    _issue(
                        code="INVALID_EFFECTIVE_DATE_RANGE",
                        title="Effective dates are out of order",
                        plain_language=(
                            "The programme end date must be after the start date "
                            "before it can be published."
                        ),
                        next_action="Set an end date after the start date.",
                        area="effective_dates",
                        can_wait=False,
                    )
                )
            if not parsed_from:
                blockers.append(
                    _issue(
                        code="EFFECTIVE_START_REQUIRED",
                        title="Start date required",
                        plain_language=(
                            "Set the date this programme version becomes effective "
                            "before publishing."
                        ),
                        next_action="Add an effective start date.",
                        area="effective_dates",
                        can_wait=False,
                    )
                )

        campaign_defaults = _json_dict(_row_value(draft_row, "campaign_defaults"))
        incentive_refs = _json_list(_row_value(draft_row, "incentive_refs"))
        engagement_refs = _json_list(_row_value(draft_row, "engagement_refs"))
        integration_snapshot = _json_dict(
            _row_value(draft_row, "integration_readiness_snapshot")
        )
        entitlement_snapshot = _json_dict(
            _row_value(draft_row, "commercial_entitlement_snapshot")
        )
        try:
            _reject_unsafe_programme_payload(
                {
                    "campaignDefaults": campaign_defaults,
                    "incentiveRefs": incentive_refs,
                    "engagementRefs": engagement_refs,
                    "integrationReadinessSnapshot": integration_snapshot,
                    "commercialEntitlementSnapshot": entitlement_snapshot,
                }
            )
        except ProgrammeConfigurationUnsafePayload as exc:
            blockers.append(
                _issue(
                    code="UNSAFE_PROGRAMME_PAYLOAD",
                    title="Unsafe configuration field",
                    plain_language=str(exc),
                    next_action="Remove reserved platform fields from the programme draft.",
                    area="configuration",
                    can_wait=False,
                )
            )

        if not campaign_defaults:
            warnings.append(
                _issue(
                    code="CAMPAIGN_DEFAULTS_EMPTY",
                    title="Campaign defaults are empty",
                    plain_language=(
                        "The programme can be published, but campaign setup will "
                        "be faster if default channels and naming are prepared."
                    ),
                    next_action="Add default campaign setup values before launch.",
                    area="campaign_defaults",
                    can_wait=True,
                )
            )
        if not incentive_refs:
            warnings.append(
                _issue(
                    code="INCENTIVE_REFS_EMPTY",
                    title="No approved incentive reference",
                    plain_language=(
                        "The programme can be published, but customer campaigns "
                        "will still need an approved reward or incentive reference."
                    ),
                    next_action="Attach an approved incentive catalogue reference.",
                    area="incentives",
                    can_wait=True,
                )
            )
        if not engagement_refs:
            warnings.append(
                _issue(
                    code="ENGAGEMENT_REFS_EMPTY",
                    title="No engagement references",
                    plain_language=(
                        "The programme can be published, but communication and "
                        "engagement content still needs to be connected before live use."
                    ),
                    next_action="Attach approved engagement or message references.",
                    area="engagement",
                    can_wait=True,
                )
            )
        if _snapshot_has_negative_signal(integration_snapshot):
            warnings.append(
                _issue(
                    code="INTEGRATION_READINESS_NEEDS_WORK",
                    title="Integration readiness needs work",
                    plain_language=(
                        "Programme publish can continue, but campaign binding and "
                        "live delivery should wait until required providers are ready."
                    ),
                    next_action="Resolve provider and message-channel readiness.",
                    area="integrations",
                    can_wait=True,
                )
            )
        if _snapshot_has_negative_signal(entitlement_snapshot):
            blockers.append(
                _issue(
                    code="COMMERCIAL_ENTITLEMENT_BLOCKED",
                    title="Commercial entitlement is not ready",
                    plain_language=(
                        "The customer is not entitled for this programme setup yet, "
                        "so publishing is blocked."
                    ),
                    next_action="Approve the customer commercial entitlement first.",
                    area="commercial_entitlement",
                    can_wait=False,
                )
            )

        publish_allowed = not blockers
        campaign_binding_allowed = publish_allowed and not any(
            warning["area"] in {"campaign_defaults", "integrations"}
            for warning in warnings
        )
        validation_status = (
            "BLOCKED"
            if blockers
            else "NEEDS_ATTENTION"
            if warnings
            else "READY"
        )
        next_programme_status = (
            "VALIDATION_FAILED" if blockers else "VALIDATED"
        )
        plain_language_summary = (
            "Programme is ready to publish and bind to campaigns."
            if validation_status == "READY"
            else (
                f"Programme has {len(blockers)} publish blocker(s) and "
                f"{len(warnings)} item(s) that can wait."
                if blockers
                else (
                    "Programme can be published, but "
                    f"{len(warnings)} setup item(s) should be finished before launch."
                )
            )
        )
        configuration_snapshot = {
            "programmeDraftId": safe_draft_id,
            "programmeName": str(_row_value(draft_row, "programme_name")),
            "programmeStatus": str(_row_value(draft_row, "programme_status")),
            "customerJourneyVersionId": str(
                _row_value(draft_row, "customer_journey_version_id")
            ),
            "customerJourneyCode": _row_value(draft_row, "customer_journey_code"),
            "journeyVersionStatus": journey_status,
            "operatingJurisdictionCode": str(
                _row_value(draft_row, "operating_jurisdiction_code")
            ),
            "productCode": str(_row_value(draft_row, "product_code")),
            "subProductCode": str(_row_value(draft_row, "sub_product_code")),
            "customerProductLineId": str(
                _optional_row_value(draft_row, "customer_product_line_id")
            )
            if _optional_row_value(draft_row, "customer_product_line_id")
            else None,
            "customerProductOfferingId": str(
                _optional_row_value(draft_row, "customer_product_offering_id")
            )
            if _optional_row_value(draft_row, "customer_product_offering_id")
            else None,
            "customerProductBinding": product_binding,
            "effectiveFrom": _isoformat(effective_from),
            "effectiveTo": _isoformat(effective_to),
            "blockerCount": len(blockers),
            "warningCount": len(warnings),
            "publishAllowed": publish_allowed,
            "campaignBindingAllowed": campaign_binding_allowed,
            "noSideEffectsConfirmed": True,
        }
        validation_payload_hash = _payload_hash(
            {
                "draftPayloadHash": _row_value(draft_row, "payload_hash"),
                "validationStatus": validation_status,
                "blockers": blockers,
                "warnings": warnings,
                "configurationSnapshot": configuration_snapshot,
            }
        )

        async with conn.transaction():
            validation_row = await conn.fetchrow(
                """
                INSERT INTO referral_saas_programme_validation_results (
                    account_id,
                    programme_draft_id,
                    customer_journey_version_id,
                    validation_status,
                    publish_allowed,
                    campaign_binding_allowed,
                    plain_language_summary,
                    blockers,
                    warnings,
                    configuration_snapshot,
                    guardrails,
                    payload_hash,
                    idempotency_key_hash,
                    correlation_id,
                    validated_by_ref
                )
                VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8::jsonb, $9::jsonb,
                    $10::jsonb, $11::jsonb, $12, $13, $14, $15
                )
                RETURNING *
                """,
                safe_account_id,
                safe_draft_id,
                str(_row_value(draft_row, "customer_journey_version_id")),
                validation_status,
                publish_allowed,
                campaign_binding_allowed,
                plain_language_summary,
                _jsonb(blockers),
                _jsonb(warnings),
                _jsonb(configuration_snapshot),
                _jsonb(PROGRAMME_CONFIGURATION_GUARDRAILS),
                validation_payload_hash,
                safe_idempotency_hash,
                safe_correlation_id,
                safe_actor_ref,
            )
            validation_id = str(
                _row_value(validation_row, "programme_validation_result_id")
            )
            await conn.execute(
                """
                UPDATE referral_saas_programme_drafts
                SET validation_result_id = $3,
                    last_validation_status = $4,
                    programme_status = $5,
                    updated_by_ref = $6,
                    updated_at = now()
                WHERE account_id = $1
                  AND programme_draft_id = $2
                """,
                safe_account_id,
                safe_draft_id,
                validation_id,
                validation_status,
                next_programme_status,
                safe_actor_ref,
            )
            await conn.execute(
                """
                INSERT INTO referral_saas_programme_configuration_idempotency_keys (
                    account_id,
                    operation_type,
                    idempotency_key_hash,
                    request_payload_hash,
                    response_payload_hash,
                    resource_type,
                    resource_id,
                    response_status
                )
                VALUES ($1, 'PROGRAMME_DRAFT_VALIDATE', $2, $3, $4,
                        'PROGRAMME_VALIDATION_RESULT', $5, 'SUCCESS')
                """,
                safe_account_id,
                safe_idempotency_hash,
                safe_request_hash,
                _payload_hash({"programmeValidationResultId": validation_id}),
                validation_id,
            )
            await conn.execute(
                """
                INSERT INTO referral_saas_programme_configuration_audit (
                    account_id,
                    programme_draft_id,
                    programme_validation_result_id,
                    customer_journey_version_id,
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
                    $1, $2, $3, $4, 'PROGRAMME_DRAFT_VALIDATED',
                    'RECORDED', $5, $6, $7, $8,
                    'PROGRAMME_DRAFT_VALIDATE', $9, $10, $11::jsonb,
                    $12::jsonb
                )
                """,
                safe_account_id,
                safe_draft_id,
                validation_id,
                str(_row_value(draft_row, "customer_journey_version_id")),
                safe_actor_ref,
                safe_actor_role,
                str(_row_value(draft_row, "programme_status")),
                next_programme_status,
                safe_correlation_id,
                safe_idempotency_hash,
                _jsonb(configuration_snapshot),
                _jsonb(PROGRAMME_CONFIGURATION_REDACTIONS),
            )

    return _programme_validation_result_from_row(validation_row)


def _programme_code_from_draft(draft_id: str) -> str:
    return f"PRG_{draft_id.replace('-', '')[:16].upper()}"


async def submit_referral_saas_programme_draft_for_review(
    *,
    account_id: str,
    programme_draft_id: str,
    review_reason: str,
    idempotency_key_hash: str,
    request_payload_hash: str,
    actor_ref: str,
    actor_role: str | None,
    correlation_id: str | None = None,
) -> ProgrammeLifecycleCommandResult:
    safe_account_id = _required_text(account_id, "account_id", max_length=80)
    safe_draft_id = _required_text(programme_draft_id, "programme_draft_id", max_length=80)
    safe_reason = _required_text(review_reason, "review_reason", max_length=500)
    safe_idempotency_hash = _required_text(idempotency_key_hash, "idempotency_key_hash", max_length=256)
    safe_request_hash = _required_text(request_payload_hash, "request_payload_hash", max_length=256)
    safe_actor_ref = _required_text(actor_ref, "actor_ref", max_length=160)
    safe_actor_role = _optional_text(actor_role, max_length=80)
    safe_correlation_id = _optional_text(correlation_id, max_length=160)

    async with db_connection() as conn:
        existing_idempotency = await conn.fetchrow(
            """
            SELECT *
            FROM referral_saas_programme_configuration_idempotency_keys
            WHERE account_id = $1
              AND operation_type = 'PROGRAMME_DRAFT_SUBMIT_REVIEW'
              AND idempotency_key_hash = $2
            LIMIT 1
            """,
            safe_account_id,
            safe_idempotency_hash,
        )
        if existing_idempotency:
            if _row_value(existing_idempotency, "request_payload_hash") != safe_request_hash:
                raise ProgrammeConfigurationIdempotencyConflict(
                    "Idempotency key was reused with different programme review submission content."
                )
            replay_row = await conn.fetchrow(
                """
                SELECT *
                FROM referral_saas_programme_drafts
                WHERE account_id = $1
                  AND programme_draft_id = $2
                  AND archived_at IS NULL
                LIMIT 1
                """,
                safe_account_id,
                _row_value(existing_idempotency, "resource_id"),
            )
            if not replay_row:
                raise ProgrammeConfigurationNotFound(str(_row_value(existing_idempotency, "resource_id")))
            return ProgrammeLifecycleCommandResult(
                command_status="REPLAY_SAME_PAYLOAD",
                resource=_draft_from_row(replay_row),
                idempotency_status="REPLAY_SAME_PAYLOAD",
                plain_language_summary="Programme draft review submission was already recorded.",
            )

        draft_row = await conn.fetchrow(
            """
            SELECT d.*, vr.publish_allowed
            FROM referral_saas_programme_drafts d
            LEFT JOIN referral_saas_programme_validation_results vr
              ON vr.programme_validation_result_id = d.validation_result_id
            WHERE d.account_id = $1
              AND d.programme_draft_id = $2
              AND d.archived_at IS NULL
            LIMIT 1
            """,
            safe_account_id,
            safe_draft_id,
        )
        if not draft_row:
            raise ProgrammeConfigurationNotFound(safe_draft_id)
        if str(_row_value(draft_row, "programme_status")) != "VALIDATED" or not bool(
            _row_value(draft_row, "publish_allowed")
        ):
            raise ProgrammeConfigurationValidationError(
                "Programme draft must be validated with publish allowed before review submission."
            )
        await _get_active_customer_product_offering_binding(
            conn,
            account_id=safe_account_id,
            operating_jurisdiction_code=str(_row_value(draft_row, "operating_jurisdiction_code")),
            customer_product_line_id=str(
                _optional_row_value(draft_row, "customer_product_line_id")
            )
            if _optional_row_value(draft_row, "customer_product_line_id")
            else None,
            customer_product_offering_id=str(
                _optional_row_value(draft_row, "customer_product_offering_id")
            )
            if _optional_row_value(draft_row, "customer_product_offering_id")
            else None,
            required=True,
        )

        async with conn.transaction():
            row = await conn.fetchrow(
                """
                UPDATE referral_saas_programme_drafts
                SET programme_status = 'READY_FOR_REVIEW',
                    review_status = 'READY_FOR_REVIEW',
                    updated_by_ref = $3,
                    updated_at = now()
                WHERE account_id = $1
                  AND programme_draft_id = $2
                  AND archived_at IS NULL
                RETURNING *
                """,
                safe_account_id,
                safe_draft_id,
                safe_actor_ref,
            )
            await conn.execute(
                """
                INSERT INTO referral_saas_programme_configuration_idempotency_keys (
                    account_id, operation_type, idempotency_key_hash,
                    request_payload_hash, response_payload_hash, resource_type,
                    resource_id, response_status
                )
                VALUES ($1, 'PROGRAMME_DRAFT_SUBMIT_REVIEW', $2, $3, $4,
                        'PROGRAMME_DRAFT', $5, 'SUCCESS')
                """,
                safe_account_id,
                safe_idempotency_hash,
                safe_request_hash,
                _payload_hash({"programmeDraftId": safe_draft_id}),
                safe_draft_id,
            )
            await conn.execute(
                """
                INSERT INTO referral_saas_programme_configuration_audit (
                    account_id, programme_draft_id, customer_journey_version_id,
                    event_type, event_status, actor_ref, actor_role,
                    previous_status, next_status, reason_code, correlation_id,
                    idempotency_key_hash, evidence_summary, redactions
                )
                VALUES (
                    $1, $2, $3, 'PROGRAMME_DRAFT_SUBMITTED_FOR_REVIEW',
                    'RECORDED', $4, $5, $6, 'READY_FOR_REVIEW',
                    'PROGRAMME_REVIEW_REQUESTED', $7, $8, $9::jsonb, $10::jsonb
                )
                """,
                safe_account_id,
                safe_draft_id,
                str(_row_value(draft_row, "customer_journey_version_id")),
                safe_actor_ref,
                safe_actor_role,
                str(_row_value(draft_row, "programme_status")),
                safe_correlation_id,
                safe_idempotency_hash,
                _jsonb({"reviewReason": safe_reason, "noSideEffectsConfirmed": True}),
                _jsonb(PROGRAMME_CONFIGURATION_REDACTIONS),
            )

    return ProgrammeLifecycleCommandResult(
        command_status="READY_FOR_REVIEW",
        resource=_draft_from_row(row),
        idempotency_status="NEW_REQUEST",
        plain_language_summary="Programme draft is ready for an explicit review decision.",
    )


async def decide_referral_saas_programme_draft_review(
    *,
    account_id: str,
    programme_draft_id: str,
    decision: str,
    review_reason: str,
    idempotency_key_hash: str,
    request_payload_hash: str,
    actor_ref: str,
    actor_role: str | None,
    correlation_id: str | None = None,
) -> ProgrammeLifecycleCommandResult:
    safe_account_id = _required_text(account_id, "account_id", max_length=80)
    safe_draft_id = _required_text(programme_draft_id, "programme_draft_id", max_length=80)
    safe_decision = _normalise_code(decision, "decision", max_length=40)
    if safe_decision not in {"APPROVE", "BLOCK", "REQUEST_CHANGES"}:
        raise ProgrammeConfigurationValidationError(
            "decision must be APPROVE, BLOCK, or REQUEST_CHANGES."
        )
    safe_reason = _required_text(review_reason, "review_reason", max_length=500)
    safe_idempotency_hash = _required_text(idempotency_key_hash, "idempotency_key_hash", max_length=256)
    safe_request_hash = _required_text(request_payload_hash, "request_payload_hash", max_length=256)
    safe_actor_ref = _required_text(actor_ref, "actor_ref", max_length=160)
    safe_actor_role = _optional_text(actor_role, max_length=80)
    safe_correlation_id = _optional_text(correlation_id, max_length=160)

    status_map = {
        "APPROVE": ("APPROVED_FOR_PUBLISH", "APPROVED", "PROGRAMME_REVIEW_APPROVED"),
        "BLOCK": ("BLOCKED", "BLOCKED", "PROGRAMME_REVIEW_BLOCKED"),
        "REQUEST_CHANGES": ("DRAFT", "CHANGES_REQUESTED", "PROGRAMME_REVIEW_CHANGES_REQUESTED"),
    }
    next_programme_status, next_review_status, reason_code = status_map[safe_decision]

    async with db_connection() as conn:
        existing_idempotency = await conn.fetchrow(
            """
            SELECT *
            FROM referral_saas_programme_configuration_idempotency_keys
            WHERE account_id = $1
              AND operation_type = 'PROGRAMME_DRAFT_REVIEW_DECISION'
              AND idempotency_key_hash = $2
            LIMIT 1
            """,
            safe_account_id,
            safe_idempotency_hash,
        )
        if existing_idempotency:
            if _row_value(existing_idempotency, "request_payload_hash") != safe_request_hash:
                raise ProgrammeConfigurationIdempotencyConflict(
                    "Idempotency key was reused with different programme review decision content."
                )
            replay_row = await conn.fetchrow(
                """
                SELECT *
                FROM referral_saas_programme_drafts
                WHERE account_id = $1
                  AND programme_draft_id = $2
                  AND archived_at IS NULL
                LIMIT 1
                """,
                safe_account_id,
                _row_value(existing_idempotency, "resource_id"),
            )
            if not replay_row:
                raise ProgrammeConfigurationNotFound(str(_row_value(existing_idempotency, "resource_id")))
            return ProgrammeLifecycleCommandResult(
                command_status="REPLAY_SAME_PAYLOAD",
                resource=_draft_from_row(replay_row),
                idempotency_status="REPLAY_SAME_PAYLOAD",
                plain_language_summary="Programme review decision was already recorded.",
            )

        draft_row = await conn.fetchrow(
            """
            SELECT d.*, vr.publish_allowed
            FROM referral_saas_programme_drafts d
            LEFT JOIN referral_saas_programme_validation_results vr
              ON vr.programme_validation_result_id = d.validation_result_id
            WHERE d.account_id = $1
              AND d.programme_draft_id = $2
              AND d.archived_at IS NULL
            LIMIT 1
            """,
            safe_account_id,
            safe_draft_id,
        )
        if not draft_row:
            raise ProgrammeConfigurationNotFound(safe_draft_id)
        if str(_row_value(draft_row, "programme_status")) != "READY_FOR_REVIEW":
            raise ProgrammeConfigurationValidationError(
                "Programme draft must be submitted for review before a review decision."
            )
        if safe_decision == "APPROVE" and not bool(_row_value(draft_row, "publish_allowed")):
            raise ProgrammeConfigurationValidationError(
                "Programme draft cannot be approved because publish is not allowed."
            )
        if safe_decision == "APPROVE":
            await _get_active_customer_product_offering_binding(
                conn,
                account_id=safe_account_id,
                operating_jurisdiction_code=str(_row_value(draft_row, "operating_jurisdiction_code")),
                customer_product_line_id=str(
                    _optional_row_value(draft_row, "customer_product_line_id")
                )
                if _optional_row_value(draft_row, "customer_product_line_id")
                else None,
                customer_product_offering_id=str(
                    _optional_row_value(draft_row, "customer_product_offering_id")
                )
                if _optional_row_value(draft_row, "customer_product_offering_id")
                else None,
                required=True,
            )

        async with conn.transaction():
            row = await conn.fetchrow(
                """
                UPDATE referral_saas_programme_drafts
                SET programme_status = $3,
                    review_status = $4,
                    updated_by_ref = $5,
                    updated_at = now()
                WHERE account_id = $1
                  AND programme_draft_id = $2
                  AND archived_at IS NULL
                RETURNING *
                """,
                safe_account_id,
                safe_draft_id,
                next_programme_status,
                next_review_status,
                safe_actor_ref,
            )
            await conn.execute(
                """
                INSERT INTO referral_saas_programme_configuration_idempotency_keys (
                    account_id, operation_type, idempotency_key_hash,
                    request_payload_hash, response_payload_hash, resource_type,
                    resource_id, response_status
                )
                VALUES ($1, 'PROGRAMME_DRAFT_REVIEW_DECISION', $2, $3, $4,
                        'PROGRAMME_DRAFT', $5, 'SUCCESS')
                """,
                safe_account_id,
                safe_idempotency_hash,
                safe_request_hash,
                _payload_hash({"programmeDraftId": safe_draft_id, "decision": safe_decision}),
                safe_draft_id,
            )
            await conn.execute(
                """
                INSERT INTO referral_saas_programme_configuration_audit (
                    account_id, programme_draft_id, customer_journey_version_id,
                    event_type, event_status, actor_ref, actor_role,
                    previous_status, next_status, reason_code, correlation_id,
                    idempotency_key_hash, evidence_summary, redactions
                )
                VALUES (
                    $1, $2, $3, 'PROGRAMME_DRAFT_REVIEW_DECIDED',
                    'RECORDED', $4, $5, $6, $7, $8, $9, $10,
                    $11::jsonb, $12::jsonb
                )
                """,
                safe_account_id,
                safe_draft_id,
                str(_row_value(draft_row, "customer_journey_version_id")),
                safe_actor_ref,
                safe_actor_role,
                str(_row_value(draft_row, "programme_status")),
                next_programme_status,
                reason_code,
                safe_correlation_id,
                safe_idempotency_hash,
                _jsonb({"decision": safe_decision, "reviewReason": safe_reason}),
                _jsonb(PROGRAMME_CONFIGURATION_REDACTIONS),
            )

    return ProgrammeLifecycleCommandResult(
        command_status=next_programme_status,
        resource=_draft_from_row(row),
        idempotency_status="NEW_REQUEST",
        plain_language_summary=(
            "Programme draft is approved for publishing."
            if safe_decision == "APPROVE"
            else "Programme draft review decision has been recorded."
        ),
    )


async def publish_referral_saas_programme_version(
    *,
    account_id: str,
    programme_draft_id: str,
    publish_reason: str,
    idempotency_key_hash: str,
    request_payload_hash: str,
    actor_ref: str,
    actor_role: str | None,
    correlation_id: str | None = None,
) -> ProgrammeLifecycleCommandResult:
    safe_account_id = _required_text(account_id, "account_id", max_length=80)
    safe_draft_id = _required_text(programme_draft_id, "programme_draft_id", max_length=80)
    safe_reason = _required_text(publish_reason, "publish_reason", max_length=500)
    safe_idempotency_hash = _required_text(idempotency_key_hash, "idempotency_key_hash", max_length=256)
    safe_request_hash = _required_text(request_payload_hash, "request_payload_hash", max_length=256)
    safe_actor_ref = _required_text(actor_ref, "actor_ref", max_length=160)
    safe_actor_role = _optional_text(actor_role, max_length=80)
    safe_correlation_id = _optional_text(correlation_id, max_length=160)

    async with db_connection() as conn:
        existing_idempotency = await conn.fetchrow(
            """
            SELECT *
            FROM referral_saas_programme_configuration_idempotency_keys
            WHERE account_id = $1
              AND operation_type = 'PROGRAMME_VERSION_PUBLISH'
              AND idempotency_key_hash = $2
            LIMIT 1
            """,
            safe_account_id,
            safe_idempotency_hash,
        )
        if existing_idempotency:
            if _row_value(existing_idempotency, "request_payload_hash") != safe_request_hash:
                raise ProgrammeConfigurationIdempotencyConflict(
                    "Idempotency key was reused with different programme publish content."
                )
            replay_row = await conn.fetchrow(
                """
                SELECT *
                FROM referral_saas_programme_versions
                WHERE account_id = $1
                  AND programme_version_id = $2
                LIMIT 1
                """,
                safe_account_id,
                _row_value(existing_idempotency, "resource_id"),
            )
            if not replay_row:
                raise ProgrammeConfigurationNotFound(str(_row_value(existing_idempotency, "resource_id")))
            return ProgrammeLifecycleCommandResult(
                command_status="REPLAY_SAME_PAYLOAD",
                resource=_version_from_row(replay_row),
                idempotency_status="REPLAY_SAME_PAYLOAD",
                plain_language_summary="Programme version publish was already recorded.",
            )

        draft_row = await conn.fetchrow(
            """
            SELECT d.*, vr.publish_allowed, vr.payload_hash AS validation_payload_hash
            FROM referral_saas_programme_drafts d
            LEFT JOIN referral_saas_programme_validation_results vr
              ON vr.programme_validation_result_id = d.validation_result_id
            WHERE d.account_id = $1
              AND d.programme_draft_id = $2
              AND d.archived_at IS NULL
            LIMIT 1
            """,
            safe_account_id,
            safe_draft_id,
        )
        if not draft_row:
            raise ProgrammeConfigurationNotFound(safe_draft_id)
        if (
            str(_row_value(draft_row, "programme_status")) != "APPROVED_FOR_PUBLISH"
            or str(_row_value(draft_row, "review_status")) != "APPROVED"
            or not bool(_row_value(draft_row, "publish_allowed"))
        ):
            raise ProgrammeConfigurationValidationError(
                "Programme draft must be validated and approved before publishing."
            )
        if not _row_value(draft_row, "effective_from"):
            raise ProgrammeConfigurationValidationError(
                "Programme draft needs an effective start date before publishing."
            )
        product_binding = await _get_active_customer_product_offering_binding(
            conn,
            account_id=safe_account_id,
            operating_jurisdiction_code=str(_row_value(draft_row, "operating_jurisdiction_code")),
            customer_product_line_id=str(
                _optional_row_value(draft_row, "customer_product_line_id")
            )
            if _optional_row_value(draft_row, "customer_product_line_id")
            else None,
            customer_product_offering_id=str(
                _optional_row_value(draft_row, "customer_product_offering_id")
            )
            if _optional_row_value(draft_row, "customer_product_offering_id")
            else None,
            required=True,
        )

        programme_code = _programme_code_from_draft(safe_draft_id)
        next_version_number = int(
            await conn.fetchval(
                """
                SELECT COALESCE(MAX(version_number), 0) + 1
                FROM referral_saas_programme_versions
                WHERE account_id = $1
                  AND programme_code = $2
                """,
                safe_account_id,
                programme_code,
            )
            or 1
        )
        safe_summary = {
            "plainLanguageSummary": "Programme version published for account-scoped campaign setup.",
            "programmeName": str(_row_value(draft_row, "programme_name")),
            "subProductCode": str(_row_value(draft_row, "sub_product_code")),
            "customerProductBinding": product_binding,
            "versionNumber": next_version_number,
            "noSideEffectsConfirmed": True,
        }
        governance_metadata = {
            "publishReason": safe_reason,
            "reviewStatus": "APPROVED",
            "validatedResultId": str(_row_value(draft_row, "validation_result_id")),
            "customerProductBinding": product_binding,
            "immutableVersion": True,
        }

        async with conn.transaction():
            version_row = await conn.fetchrow(
                """
                INSERT INTO referral_saas_programme_versions (
                    account_id,
                    programme_draft_id,
                    source_programme_version_id,
                    customer_journey_version_id,
                    programme_code,
                    programme_name,
                    programme_description,
                    operating_jurisdiction_code,
                    product_code,
                    sub_product_code,
                    customer_product_line_id,
                    customer_product_offering_id,
                    version_number,
                    version_status,
                    published_configuration_snapshot,
                    campaign_defaults_snapshot,
                    incentive_refs_snapshot,
                    engagement_refs_snapshot,
                    integration_readiness_snapshot,
                    commercial_entitlement_snapshot,
                    validation_result_id,
                    review_status,
                    reviewed_by_ref,
                    reviewed_at,
                    review_reason,
                    effective_from,
                    effective_to,
                    configuration_checksum,
                    payload_hash,
                    published_by_ref,
                    safe_summary,
                    governance_metadata
                )
                VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10,
                    $11, $12, $13, 'PUBLISHED', $14::jsonb, $15::jsonb,
                    $16::jsonb, $17::jsonb, $18::jsonb, $19::jsonb, $20,
                    'APPROVED', $21, now(), $22, $23, $24, $25, $26, $21,
                    $27::jsonb, $28::jsonb
                )
                RETURNING *
                """,
                safe_account_id,
                safe_draft_id,
                _row_value(draft_row, "source_programme_version_id"),
                str(_row_value(draft_row, "customer_journey_version_id")),
                programme_code,
                str(_row_value(draft_row, "programme_name")),
                _row_value(draft_row, "programme_description"),
                str(_row_value(draft_row, "operating_jurisdiction_code")),
                str(_row_value(draft_row, "product_code")),
                str(_row_value(draft_row, "sub_product_code")),
                _optional_row_value(draft_row, "customer_product_line_id"),
                _optional_row_value(draft_row, "customer_product_offering_id"),
                next_version_number,
                _jsonb(
                    {
                        "draftPayloadHash": str(_row_value(draft_row, "payload_hash")),
                        "validationPayloadHash": _row_value(draft_row, "validation_payload_hash"),
                        "customerProductLineId": str(
                            _row_value(draft_row, "customer_product_line_id")
                        ),
                        "customerProductOfferingId": str(
                            _row_value(draft_row, "customer_product_offering_id")
                        ),
                        "customerProductBinding": product_binding,
                    }
                ),
                _jsonb(_json_dict(_row_value(draft_row, "campaign_defaults"))),
                _jsonb(_json_list(_row_value(draft_row, "incentive_refs"))),
                _jsonb(_json_list(_row_value(draft_row, "engagement_refs"))),
                _jsonb(_json_dict(_row_value(draft_row, "integration_readiness_snapshot"))),
                _jsonb(_json_dict(_row_value(draft_row, "commercial_entitlement_snapshot"))),
                str(_row_value(draft_row, "validation_result_id")),
                safe_actor_ref,
                safe_reason,
                _row_value(draft_row, "effective_from"),
                _row_value(draft_row, "effective_to"),
                str(_row_value(draft_row, "configuration_checksum")),
                str(_row_value(draft_row, "payload_hash")),
                _jsonb(safe_summary),
                _jsonb(governance_metadata),
            )
            version_id = str(_row_value(version_row, "programme_version_id"))
            await conn.execute(
                """
                UPDATE referral_saas_programme_drafts
                SET programme_status = 'ARCHIVED',
                    archived_at = now(),
                    updated_by_ref = $3,
                    updated_at = now()
                WHERE account_id = $1
                  AND programme_draft_id = $2
                """,
                safe_account_id,
                safe_draft_id,
                safe_actor_ref,
            )
            await conn.execute(
                """
                INSERT INTO referral_saas_programme_configuration_idempotency_keys (
                    account_id, operation_type, idempotency_key_hash,
                    request_payload_hash, response_payload_hash, resource_type,
                    resource_id, response_status
                )
                VALUES ($1, 'PROGRAMME_VERSION_PUBLISH', $2, $3, $4,
                        'PROGRAMME_VERSION', $5, 'SUCCESS')
                """,
                safe_account_id,
                safe_idempotency_hash,
                safe_request_hash,
                _payload_hash({"programmeVersionId": version_id}),
                version_id,
            )
            await conn.execute(
                """
                INSERT INTO referral_saas_programme_configuration_audit (
                    account_id, programme_draft_id, programme_version_id,
                    customer_journey_version_id, event_type, event_status,
                    actor_ref, actor_role, previous_status, next_status,
                    reason_code, correlation_id, idempotency_key_hash,
                    evidence_summary, redactions
                )
                VALUES (
                    $1, $2, $3, $4, 'PROGRAMME_VERSION_PUBLISHED',
                    'RECORDED', $5, $6, 'APPROVED_FOR_PUBLISH',
                    'PUBLISHED', 'PROGRAMME_VERSION_PUBLISH', $7, $8,
                    $9::jsonb, $10::jsonb
                )
                """,
                safe_account_id,
                safe_draft_id,
                version_id,
                str(_row_value(draft_row, "customer_journey_version_id")),
                safe_actor_ref,
                safe_actor_role,
                safe_correlation_id,
                safe_idempotency_hash,
                _jsonb(governance_metadata),
                _jsonb(PROGRAMME_CONFIGURATION_REDACTIONS),
            )

    return ProgrammeLifecycleCommandResult(
        command_status="PROGRAMME_VERSION_PUBLISHED",
        resource=_version_from_row(version_row),
        idempotency_status="NEW_REQUEST",
        plain_language_summary=(
            "Programme version published as immutable account configuration. "
            "No campaign, provider, auth, billing, settlement, payout, or money workflow ran."
        ),
    )


async def retire_referral_saas_programme_version(
    *,
    account_id: str,
    programme_version_id: str,
    retirement_reason: str,
    idempotency_key_hash: str,
    request_payload_hash: str,
    actor_ref: str,
    actor_role: str | None,
    correlation_id: str | None = None,
) -> ProgrammeLifecycleCommandResult:
    safe_account_id = _required_text(account_id, "account_id", max_length=80)
    safe_version_id = _required_text(programme_version_id, "programme_version_id", max_length=80)
    safe_reason = _required_text(retirement_reason, "retirement_reason", max_length=500)
    safe_idempotency_hash = _required_text(idempotency_key_hash, "idempotency_key_hash", max_length=256)
    safe_request_hash = _required_text(request_payload_hash, "request_payload_hash", max_length=256)
    safe_actor_ref = _required_text(actor_ref, "actor_ref", max_length=160)
    safe_actor_role = _optional_text(actor_role, max_length=80)
    safe_correlation_id = _optional_text(correlation_id, max_length=160)

    async with db_connection() as conn:
        existing_idempotency = await conn.fetchrow(
            """
            SELECT *
            FROM referral_saas_programme_configuration_idempotency_keys
            WHERE account_id = $1
              AND operation_type = 'PROGRAMME_VERSION_RETIRE'
              AND idempotency_key_hash = $2
            LIMIT 1
            """,
            safe_account_id,
            safe_idempotency_hash,
        )
        if existing_idempotency:
            if _row_value(existing_idempotency, "request_payload_hash") != safe_request_hash:
                raise ProgrammeConfigurationIdempotencyConflict(
                    "Idempotency key was reused with different programme retirement content."
                )
            replay_row = await conn.fetchrow(
                """
                SELECT *
                FROM referral_saas_programme_versions
                WHERE account_id = $1
                  AND programme_version_id = $2
                LIMIT 1
                """,
                safe_account_id,
                _row_value(existing_idempotency, "resource_id"),
            )
            if not replay_row:
                raise ProgrammeConfigurationNotFound(str(_row_value(existing_idempotency, "resource_id")))
            return ProgrammeLifecycleCommandResult(
                command_status="REPLAY_SAME_PAYLOAD",
                resource=_version_from_row(replay_row),
                idempotency_status="REPLAY_SAME_PAYLOAD",
                plain_language_summary="Programme version retirement was already recorded.",
            )

        version_row = await conn.fetchrow(
            """
            SELECT *
            FROM referral_saas_programme_versions
            WHERE account_id = $1
              AND programme_version_id = $2
            LIMIT 1
            """,
            safe_account_id,
            safe_version_id,
        )
        if not version_row:
            raise ProgrammeConfigurationNotFound(safe_version_id)
        if str(_row_value(version_row, "version_status")) in {"RETIRED", "ARCHIVED"}:
            raise ProgrammeConfigurationValidationError(
                "Programme version is already retired or archived."
            )

        async with conn.transaction():
            row = await conn.fetchrow(
                """
                UPDATE referral_saas_programme_versions
                SET version_status = 'RETIRED',
                    retired_by_ref = $3,
                    retired_at = now(),
                    retirement_reason = $4
                WHERE account_id = $1
                  AND programme_version_id = $2
                RETURNING *
                """,
                safe_account_id,
                safe_version_id,
                safe_actor_ref,
                safe_reason,
            )
            await conn.execute(
                """
                INSERT INTO referral_saas_programme_configuration_idempotency_keys (
                    account_id, operation_type, idempotency_key_hash,
                    request_payload_hash, response_payload_hash, resource_type,
                    resource_id, response_status
                )
                VALUES ($1, 'PROGRAMME_VERSION_RETIRE', $2, $3, $4,
                        'PROGRAMME_VERSION', $5, 'SUCCESS')
                """,
                safe_account_id,
                safe_idempotency_hash,
                safe_request_hash,
                _payload_hash({"programmeVersionId": safe_version_id, "status": "RETIRED"}),
                safe_version_id,
            )
            await conn.execute(
                """
                INSERT INTO referral_saas_programme_configuration_audit (
                    account_id, programme_version_id, customer_journey_version_id,
                    event_type, event_status, actor_ref, actor_role,
                    previous_status, next_status, reason_code, correlation_id,
                    idempotency_key_hash, evidence_summary, redactions
                )
                VALUES (
                    $1, $2, $3, 'PROGRAMME_VERSION_RETIRED', 'RECORDED',
                    $4, $5, $6, 'RETIRED', 'PROGRAMME_VERSION_RETIRE',
                    $7, $8, $9::jsonb, $10::jsonb
                )
                """,
                safe_account_id,
                safe_version_id,
                str(_row_value(version_row, "customer_journey_version_id")),
                safe_actor_ref,
                safe_actor_role,
                str(_row_value(version_row, "version_status")),
                safe_correlation_id,
                safe_idempotency_hash,
                _jsonb({"retirementReason": safe_reason, "noSideEffectsConfirmed": True}),
                _jsonb(PROGRAMME_CONFIGURATION_REDACTIONS),
            )

    return ProgrammeLifecycleCommandResult(
        command_status="PROGRAMME_VERSION_RETIRED",
        resource=_version_from_row(row),
        idempotency_status="NEW_REQUEST",
        plain_language_summary="Programme version retired without changing active campaigns or referral runtime.",
    )


async def prepare_referral_saas_programme_rollback_readiness(
    *,
    account_id: str,
    programme_version_id: str,
    rollback_reason: str,
    idempotency_key_hash: str,
    request_payload_hash: str,
    actor_ref: str,
    actor_role: str | None,
    correlation_id: str | None = None,
) -> ProgrammeLifecycleCommandResult:
    safe_account_id = _required_text(account_id, "account_id", max_length=80)
    safe_version_id = _required_text(programme_version_id, "programme_version_id", max_length=80)
    safe_reason = _required_text(rollback_reason, "rollback_reason", max_length=500)
    safe_idempotency_hash = _required_text(idempotency_key_hash, "idempotency_key_hash", max_length=256)
    safe_request_hash = _required_text(request_payload_hash, "request_payload_hash", max_length=256)
    safe_actor_ref = _required_text(actor_ref, "actor_ref", max_length=160)
    safe_actor_role = _optional_text(actor_role, max_length=80)
    safe_correlation_id = _optional_text(correlation_id, max_length=160)

    async with db_connection() as conn:
        existing_idempotency = await conn.fetchrow(
            """
            SELECT *
            FROM referral_saas_programme_configuration_idempotency_keys
            WHERE account_id = $1
              AND operation_type = 'PROGRAMME_ROLLBACK_READINESS'
              AND idempotency_key_hash = $2
            LIMIT 1
            """,
            safe_account_id,
            safe_idempotency_hash,
        )
        if existing_idempotency:
            if _row_value(existing_idempotency, "request_payload_hash") != safe_request_hash:
                raise ProgrammeConfigurationIdempotencyConflict(
                    "Idempotency key was reused with different programme rollback readiness content."
                )
            return ProgrammeLifecycleCommandResult(
                command_status="REPLAY_SAME_PAYLOAD",
                resource={
                    "programmeVersionId": safe_version_id,
                    "rollbackReadiness": "RECORDED",
                    "rollbackActivation": "NOT_PERFORMED",
                },
                idempotency_status="REPLAY_SAME_PAYLOAD",
                plain_language_summary="Programme rollback readiness was already recorded.",
            )

        version_row = await conn.fetchrow(
            """
            SELECT *
            FROM referral_saas_programme_versions
            WHERE account_id = $1
              AND programme_version_id = $2
              AND version_status <> 'ARCHIVED'
            LIMIT 1
            """,
            safe_account_id,
            safe_version_id,
        )
        if not version_row:
            raise ProgrammeConfigurationNotFound(safe_version_id)

        readiness = {
            "programmeVersionId": safe_version_id,
            "programmeCode": str(_row_value(version_row, "programme_code")),
            "currentVersionStatus": str(_row_value(version_row, "version_status")),
            "rollbackReadiness": "RECORDED",
            "rollbackActivation": "NOT_PERFORMED",
            "campaignRuntimeSwitch": "NOT_PERFORMED",
            "providerDispatch": "NOT_PERFORMED",
            "authBillingOrMoneyAction": "NOT_PERFORMED",
            "nextAction": "Use a separate reviewed campaign-binding workflow before changing any live campaign.",
        }
        async with conn.transaction():
            await conn.execute(
                """
                INSERT INTO referral_saas_programme_configuration_idempotency_keys (
                    account_id, operation_type, idempotency_key_hash,
                    request_payload_hash, response_payload_hash, resource_type,
                    resource_id, response_status
                )
                VALUES ($1, 'PROGRAMME_ROLLBACK_READINESS', $2, $3, $4,
                        'PROGRAMME_VERSION', $5, 'SUCCESS')
                """,
                safe_account_id,
                safe_idempotency_hash,
                safe_request_hash,
                _payload_hash(readiness),
                safe_version_id,
            )
            await conn.execute(
                """
                INSERT INTO referral_saas_programme_configuration_audit (
                    account_id, programme_version_id, customer_journey_version_id,
                    event_type, event_status, actor_ref, actor_role,
                    previous_status, next_status, reason_code, correlation_id,
                    idempotency_key_hash, evidence_summary, redactions
                )
                VALUES (
                    $1, $2, $3, 'PROGRAMME_ROLLBACK_READINESS_RECORDED',
                    'RECORDED', $4, $5, $6, $6,
                    'PROGRAMME_ROLLBACK_READINESS', $7, $8, $9::jsonb,
                    $10::jsonb
                )
                """,
                safe_account_id,
                safe_version_id,
                str(_row_value(version_row, "customer_journey_version_id")),
                safe_actor_ref,
                safe_actor_role,
                str(_row_value(version_row, "version_status")),
                safe_correlation_id,
                safe_idempotency_hash,
                _jsonb({"rollbackReason": safe_reason, **readiness}),
                _jsonb(PROGRAMME_CONFIGURATION_REDACTIONS),
            )

    return ProgrammeLifecycleCommandResult(
        command_status="PROGRAMME_ROLLBACK_READINESS_RECORDED",
        resource=readiness,
        idempotency_status="NEW_REQUEST",
        plain_language_summary=(
            "Rollback readiness recorded only. No campaign, referral runtime, provider, auth, "
            "billing, settlement, payout, or money workflow ran."
        ),
    )
