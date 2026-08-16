from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from utils.db import db_connection


MAX_CAMPAIGN_LIST_LIMIT = 100
CAMPAIGN_SETUP_CREATE_EVENT = "CAMPAIGN_SETUP_DRAFT_RECORDED"
CAMPAIGN_SETUP_RECORDED = "RECORDED"
CAMPAIGN_SETUP_REPLAYED = "REPLAYED"
CAMPAIGN_PROGRAMME_BINDING_EVENT = "CAMPAIGN_PROGRAMME_BINDING_RECORDED"
CAMPAIGN_PROGRAMME_BINDING_RECORDED = "RECORDED"
CAMPAIGN_PROGRAMME_BINDING_REPLAYED = "REPLAYED"
CAMPAIGN_SETUP_GUARDRAILS = [
    "NO_TENANT_CODE_EXPOSURE",
    "NO_CAMPAIGN_ACTIVATION",
    "NO_LINK_GENERATION",
    "NO_VALIDATION_TRACK_CREATED",
    "NO_POLICY_WRITE",
    "NO_WEBHOOK_DELIVERY",
    "NO_MONEY_MOVEMENT",
]
CAMPAIGN_SETUP_REDACTIONS = [
    "internal_tenant_identifier",
    "idempotency_key_hash",
    "payload_hash",
]
CAMPAIGN_POLICY_SETTINGS_EVENT = "CAMPAIGN_POLICY_SETTINGS_RECORDED"
CAMPAIGN_POLICY_SETTINGS_RECORDED = "RECORDED"
CAMPAIGN_POLICY_SETTINGS_REPLAYED = "REPLAYED"
CAMPAIGN_POLICY_SETTINGS_GUARDRAILS = [
    "NO_TENANT_CODE_EXPOSURE",
    "NO_CAMPAIGN_ACTIVATION",
    "NO_LINK_GENERATION",
    "NO_VALIDATION_TRACK_CREATED",
    "NO_WEBHOOK_DELIVERY",
    "NO_MONEY_MOVEMENT",
]
CAMPAIGN_POLICY_SETTINGS_REDACTIONS = [
    "internal_tenant_identifier",
    "idempotency_key_hash",
    "payload_hash",
]
CAMPAIGN_REVIEW_SUBMIT_EVENT = "CAMPAIGN_REVIEW_SUBMITTED"
CAMPAIGN_REVIEW_DECISION_EVENT = "CAMPAIGN_REVIEW_DECISION_RECORDED"
CAMPAIGN_REVIEW_SUBMITTED = "RECORDED"
CAMPAIGN_REVIEW_REPLAYED = "REPLAYED"
CAMPAIGN_REVIEW_GUARDRAILS = [
    "NO_TENANT_CODE_EXPOSURE",
    "NO_CAMPAIGN_ACTIVATION",
    "NO_LINK_GENERATION",
    "NO_VALIDATION_TRACK_CREATED",
    "NO_WEBHOOK_DELIVERY",
    "NO_INVITE_OR_SEAT_CHANGE",
    "NO_MONEY_MOVEMENT",
]
CAMPAIGN_REVIEW_REDACTIONS = [
    "internal_tenant_identifier",
    "idempotency_key_hash",
    "payload_hash",
]
CAMPAIGN_ACTIVATION_EVENT = "CAMPAIGN_ACTIVATION_REQUESTED"
CAMPAIGN_ACTIVATION_RECORDED = "RECORDED"
CAMPAIGN_ACTIVATION_REPLAYED = "REPLAYED"
CAMPAIGN_ACTIVATION_GUARDRAILS = [
    "NO_TENANT_CODE_EXPOSURE",
    "PUBLISHED_JOURNEY_VERSION_BINDING_REQUIRED",
    "NO_LINK_GENERATION",
    "NO_VALIDATION_TRACK_CREATED",
    "NO_WEBHOOK_DELIVERY",
    "NO_INVITE_OR_SEAT_CHANGE",
    "NO_CREDENTIAL_CREATION",
    "NO_BILLING_OR_MONEY_MOVEMENT",
]
CAMPAIGN_ACTIVATION_REDACTIONS = [
    "internal_tenant_identifier",
    "idempotency_key_hash",
    "payload_hash",
]
CAMPAIGN_LIFECYCLE_EVENT = "CAMPAIGN_LIFECYCLE_COMMAND_RECORDED"
CAMPAIGN_LIFECYCLE_RECORDED = "RECORDED"
CAMPAIGN_LIFECYCLE_REPLAYED = "REPLAYED"
CAMPAIGN_LIFECYCLE_ACTIONS = {"PAUSE", "RESUME", "END", "ARCHIVE"}
CAMPAIGN_LIFECYCLE_GUARDRAILS = [
    "NO_TENANT_CODE_EXPOSURE",
    "NO_LINK_GENERATION",
    "NO_VALIDATION_TRACK_CREATED",
    "NO_WEBHOOK_DELIVERY",
    "NO_INVITE_OR_SEAT_CHANGE",
    "NO_CREDENTIAL_CREATION",
    "NO_BILLING_OR_MONEY_MOVEMENT",
]
CAMPAIGN_LIFECYCLE_REDACTIONS = [
    "internal_tenant_identifier",
    "idempotency_key_hash",
    "payload_hash",
]
CAMPAIGN_ATTRIBUTION_GUARDRAILS = [
    "CUSTOMER_SCOPED_ATTRIBUTION_ONLY",
    "NO_TENANT_CODE_EXPOSURE",
    "NO_RAW_UCN_EXPOSURE",
    "NO_RAW_EVENT_PAYLOAD_EXPOSURE",
    "NO_EVENT_HASH_EXPOSURE",
    "NO_ATTRIBUTION_MUTATION",
    "NO_CAMPAIGN_ACTIVATION",
    "NO_WEBHOOK_DELIVERY",
    "NO_BILLING_OR_MONEY_MOVEMENT",
]
CAMPAIGN_ATTRIBUTION_REDACTIONS = [
    "internal_tenant_identifier",
    "raw_ucn",
    "raw_event_payload",
    "event_hash",
    "device_fingerprint",
    "ip_address",
    "qr_payload",
]
CAMPAIGN_REVIEW_SOD_PENDING = "PENDING_REVIEW_DECISION"
CAMPAIGN_REVIEW_SOD_CONFIRMED = "SEPARATION_OF_DUTIES_CONFIRMED"
CAMPAIGN_REVIEW_SOD_BLOCKED = "SEPARATION_OF_DUTIES_BLOCKED"
CAMPAIGN_POLICY_EVIDENCE_CURRENT = "CURRENT_AT_REVIEW"
CAMPAIGN_POLICY_EVIDENCE_STALE = "STALE_AFTER_REVIEW"


class ReferralSaasCampaignCommandError(Exception):
    safe_code = "CAMPAIGN_COMMAND_ERROR"


class CampaignSetupValidationError(ReferralSaasCampaignCommandError):
    safe_code = "VALIDATION_ERROR"


class CampaignSetupAccountNotReady(ReferralSaasCampaignCommandError):
    safe_code = "ACCOUNT_NOT_READY_FOR_CAMPAIGN_SETUP"


class CampaignSetupDuplicate(ReferralSaasCampaignCommandError):
    safe_code = "CAMPAIGN_SETUP_ALREADY_EXISTS"


class CampaignSetupIdempotencyConflict(ReferralSaasCampaignCommandError):
    safe_code = "IDEMPOTENCY_CONFLICT"


class CampaignPolicySettingsValidationError(ReferralSaasCampaignCommandError):
    safe_code = "VALIDATION_ERROR"


class CampaignPolicySettingsAccountNotReady(ReferralSaasCampaignCommandError):
    safe_code = "ACCOUNT_NOT_READY_FOR_CAMPAIGN_POLICY_SETTINGS"


class CampaignPolicySettingsCampaignNotFound(ReferralSaasCampaignCommandError):
    safe_code = "CAMPAIGN_NOT_FOUND_FOR_SELECTED_CUSTOMER"


class CampaignPolicySettingsIdempotencyConflict(ReferralSaasCampaignCommandError):
    safe_code = "IDEMPOTENCY_CONFLICT"


class CampaignReviewValidationError(ReferralSaasCampaignCommandError):
    safe_code = "VALIDATION_ERROR"


class CampaignReviewCampaignNotFound(ReferralSaasCampaignCommandError):
    safe_code = "CAMPAIGN_NOT_FOUND_FOR_SELECTED_CUSTOMER"


class CampaignReviewNotReady(ReferralSaasCampaignCommandError):
    safe_code = "CAMPAIGN_REVIEW_NOT_READY"


class CampaignReviewInvalidState(ReferralSaasCampaignCommandError):
    safe_code = "CAMPAIGN_REVIEW_INVALID_STATE"


class CampaignReviewIdempotencyConflict(ReferralSaasCampaignCommandError):
    safe_code = "IDEMPOTENCY_CONFLICT"


class CampaignActivationValidationError(ReferralSaasCampaignCommandError):
    safe_code = "VALIDATION_ERROR"


class CampaignActivationCampaignNotFound(ReferralSaasCampaignCommandError):
    safe_code = "CAMPAIGN_NOT_FOUND_FOR_SELECTED_CUSTOMER"


class CampaignActivationNotReady(ReferralSaasCampaignCommandError):
    safe_code = "CAMPAIGN_ACTIVATION_NOT_READY"


class CampaignActivationAlreadyActive(ReferralSaasCampaignCommandError):
    safe_code = "CAMPAIGN_ALREADY_ACTIVE"


class CampaignActivationIdempotencyConflict(ReferralSaasCampaignCommandError):
    safe_code = "IDEMPOTENCY_CONFLICT"


class CampaignLifecycleValidationError(ReferralSaasCampaignCommandError):
    safe_code = "VALIDATION_ERROR"


class CampaignLifecycleCampaignNotFound(ReferralSaasCampaignCommandError):
    safe_code = "CAMPAIGN_NOT_FOUND_FOR_SELECTED_CUSTOMER"


class CampaignLifecycleInvalidTransition(ReferralSaasCampaignCommandError):
    safe_code = "CAMPAIGN_LIFECYCLE_INVALID_TRANSITION"


class CampaignLifecycleIdempotencyConflict(ReferralSaasCampaignCommandError):
    safe_code = "IDEMPOTENCY_CONFLICT"


@dataclass(frozen=True)
class ReferralSaasCampaignSummary:
    campaign_code: str
    name: str
    segment: str
    status: str
    lifecycle: str
    starts_at: str | None
    ends_at: str | None
    max_uses: int | None
    uses_count: int
    policy_status: str
    created_at: str | None
    updated_at: str | None
    programme_binding: dict[str, Any] | None = None

    def to_safe_dict(self) -> dict[str, Any]:
        return {
            "campaignCode": self.campaign_code,
            "name": self.name,
            "segment": self.segment,
            "status": self.status,
            "lifecycle": self.lifecycle,
            "startsAt": self.starts_at,
            "endsAt": self.ends_at,
            "maxUses": self.max_uses,
            "usesCount": self.uses_count,
            "policyStatus": self.policy_status,
            "programmeBinding": self.programme_binding,
            "createdAt": self.created_at,
            "updatedAt": self.updated_at,
        }


@dataclass(frozen=True)
class ReferralSaasCampaignAttributionProjection:
    campaign_code: str
    campaign_name: str
    segment: str
    campaign_status: str
    source_channel: str
    attribution_status: str
    confidence: str
    interaction_count: int
    linked_referral_count: int
    event_count: int
    first_seen_at: str | None
    last_seen_at: str | None
    evidence: list[str]
    gaps: list[str]
    explanation: str

    def to_safe_dict(self) -> dict[str, Any]:
        return {
            "campaignCode": self.campaign_code,
            "campaignName": self.campaign_name,
            "segment": self.segment,
            "campaignStatus": self.campaign_status,
            "sourceChannel": self.source_channel,
            "attributionStatus": self.attribution_status,
            "confidence": self.confidence,
            "interactionCount": self.interaction_count,
            "linkedReferralCount": self.linked_referral_count,
            "eventCount": self.event_count,
            "firstSeenAt": self.first_seen_at,
            "lastSeenAt": self.last_seen_at,
            "evidence": list(self.evidence),
            "gaps": list(self.gaps),
            "explanation": self.explanation,
        }


@dataclass(frozen=True)
class ReferralSaasCampaignAttributionSummary:
    status: str
    campaign_count: int
    source_count: int
    total_interactions: int
    high_confidence_count: int
    missing_evidence_count: int
    conflict_count: int
    plain_language: str
    projections: list[ReferralSaasCampaignAttributionProjection]

    def to_safe_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "campaignCount": self.campaign_count,
            "sourceCount": self.source_count,
            "totalInteractions": self.total_interactions,
            "highConfidenceCount": self.high_confidence_count,
            "missingEvidenceCount": self.missing_evidence_count,
            "conflictCount": self.conflict_count,
            "plainLanguage": self.plain_language,
            "projections": [projection.to_safe_dict() for projection in self.projections],
            "guardrails": list(CAMPAIGN_ATTRIBUTION_GUARDRAILS),
            "redactions": list(CAMPAIGN_ATTRIBUTION_REDACTIONS),
        }


@dataclass(frozen=True)
class ReferralSaasCampaignSetupResult:
    command_status: str
    account_id: str
    campaign_code: str
    name: str
    segment: str
    setup_status: str
    is_active: bool
    starts_at: str | None
    ends_at: str | None
    max_uses: int | None
    idempotency_status: str
    audit_event_id: str | None
    programme_binding: dict[str, Any] | None = None

    def to_safe_dict(self) -> dict[str, Any]:
        return {
            "commandStatus": self.command_status,
            "accountRef": self.account_id,
            "campaign": {
                "campaignRef": self.campaign_code,
                "campaignCode": self.campaign_code,
                "name": self.name,
                "segment": self.segment,
                "setupStatus": self.setup_status,
                "isActive": self.is_active,
                "startsAt": self.starts_at,
                "endsAt": self.ends_at,
                "maxUses": self.max_uses,
                "programmeBinding": self.programme_binding,
            },
            "idempotency": {"status": self.idempotency_status},
            "audit": {"accountAuditEventId": self.audit_event_id},
            "nextActions": [
                "Complete policy and attribution settings",
                "Run campaign readiness",
                "Review before activation",
            ],
            "guardrails": list(CAMPAIGN_SETUP_GUARDRAILS),
            "redactions": list(CAMPAIGN_SETUP_REDACTIONS),
        }


@dataclass(frozen=True)
class ReferralSaasCampaignPolicySettingsResult:
    command_status: str
    account_id: str
    campaign_code: str
    version: int
    setup_status: str
    attribution_window_days: int | None
    eligibility_rule_count: int
    product_window_count: int
    product_rule_count: int
    reward_visibility_status: str
    idempotency_status: str
    audit_event_id: str | None

    def to_safe_dict(self) -> dict[str, Any]:
        return {
            "commandStatus": self.command_status,
            "accountRef": self.account_id,
            "campaignRef": self.campaign_code,
            "policySettings": {
                "version": self.version,
                "setupStatus": self.setup_status,
                "attributionWindowDays": self.attribution_window_days,
                "eligibilityRuleCount": self.eligibility_rule_count,
                "productWindowCount": self.product_window_count,
                "productRuleCount": self.product_rule_count,
                "rewardVisibilityStatus": self.reward_visibility_status,
            },
            "idempotency": {"status": self.idempotency_status},
            "audit": {"accountAuditEventId": self.audit_event_id},
            "nextActions": [
                "Run campaign readiness",
                "Review before activation",
                "Generate links only after activation is approved",
            ],
            "guardrails": list(CAMPAIGN_POLICY_SETTINGS_GUARDRAILS),
            "redactions": list(CAMPAIGN_POLICY_SETTINGS_REDACTIONS),
        }


@dataclass(frozen=True)
class ReferralSaasCampaignReviewResult:
    command_status: str
    account_id: str
    campaign_code: str
    review_status: str
    setup_status: str
    readiness_status: str
    activation_eligibility: str
    activation_status: str
    reviewer_action: str
    idempotency_status: str
    audit_event_id: str | None
    pre_activation_decision: dict[str, Any] | None = None

    def to_safe_dict(self) -> dict[str, Any]:
        return {
            "commandStatus": self.command_status,
            "accountRef": self.account_id,
            "campaignRef": self.campaign_code,
            "campaignReview": {
                "reviewStatus": self.review_status,
                "setupStatus": self.setup_status,
                "readinessStatus": self.readiness_status,
                "activationEligibility": self.activation_eligibility,
                "activationStatus": self.activation_status,
                "reviewerAction": self.reviewer_action,
                "preActivationDecision": self.pre_activation_decision,
            },
            "idempotency": {"status": self.idempotency_status},
            "audit": {"accountAuditEventId": self.audit_event_id},
            "nextActions": (
                [
                    "Review campaign setup evidence",
                    "Record campaign review decision",
                    "Activate only through a later activation command",
                ]
                if self.review_status == "READY_FOR_REVIEW"
                else [
                    "Open activation checklist",
                    "Confirm links and delivery setup after activation",
                    "Keep campaign inactive until activation is approved",
                ]
            ),
            "guardrails": list(CAMPAIGN_REVIEW_GUARDRAILS),
            "redactions": list(CAMPAIGN_REVIEW_REDACTIONS),
        }


@dataclass(frozen=True)
class ReferralSaasCampaignActivationResult:
    command_status: str
    account_id: str
    campaign_code: str
    previous_lifecycle: str
    lifecycle: str
    review_status: str
    activation_eligibility: str
    activation_status: str
    readiness_status: str
    idempotency_status: str
    audit_event_id: str | None
    pre_activation_decision: dict[str, Any] | None = None

    def to_safe_dict(self) -> dict[str, Any]:
        return {
            "commandStatus": self.command_status,
            "accountRef": self.account_id,
            "campaignRef": self.campaign_code,
            "campaignActivation": {
                "previousLifecycle": self.previous_lifecycle,
                "lifecycle": self.lifecycle,
                "reviewStatus": self.review_status,
                "activationEligibility": self.activation_eligibility,
                "activationStatus": self.activation_status,
                "readinessStatus": self.readiness_status,
                "preActivationDecision": self.pre_activation_decision,
            },
            "idempotency": {"status": self.idempotency_status},
            "audit": {"accountAuditEventId": self.audit_event_id},
            "nextActions": [
                "Open customer campaign operations",
                "Create or issue links and codes through the customer-scoped Links module",
                "Monitor readiness, attribution, progress, and reporting separately",
            ],
            "guardrails": list(CAMPAIGN_ACTIVATION_GUARDRAILS),
            "redactions": list(CAMPAIGN_ACTIVATION_REDACTIONS),
        }


@dataclass(frozen=True)
class ReferralSaasCampaignLifecycleResult:
    command_status: str
    account_id: str
    campaign_code: str
    action: str | None
    previous_lifecycle: str | None
    lifecycle: str
    is_active: bool
    allowed_actions: list[str]
    plain_language: str
    idempotency_status: str | None = None
    audit_event_id: str | None = None

    def to_safe_dict(self) -> dict[str, Any]:
        return {
            "commandStatus": self.command_status,
            "accountRef": self.account_id,
            "campaignRef": self.campaign_code,
            "campaignLifecycle": {
                "action": self.action,
                "previousLifecycle": self.previous_lifecycle,
                "lifecycle": self.lifecycle,
                "isActive": self.is_active,
                "allowedActions": list(self.allowed_actions),
                "plainLanguage": self.plain_language,
            },
            "idempotency": {"status": self.idempotency_status},
            "audit": {"accountAuditEventId": self.audit_event_id},
            "nextActions": [
                "Use lifecycle controls only from the selected customer campaign workspace",
                "Issue links only while the campaign is active",
                "Keep reporting, attribution, and support read-only against the selected customer",
            ],
            "guardrails": list(CAMPAIGN_LIFECYCLE_GUARDRAILS),
            "redactions": list(CAMPAIGN_LIFECYCLE_REDACTIONS),
        }


def _as_iso(value: Any) -> str | None:
    if isinstance(value, datetime):
        return value.isoformat()
    return None


def _as_aware_utc(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)
    return None


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_iso_datetime(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return _as_aware_utc(value)
    safe_value = _optional_text(value)
    if not safe_value:
        return None
    try:
        parsed = datetime.fromisoformat(safe_value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return _as_aware_utc(parsed)


def _campaign_lifecycle(*, is_active: bool, starts_at: Any, ends_at: Any) -> str:
    now = datetime.now(timezone.utc)
    safe_starts_at = _as_aware_utc(starts_at)
    safe_ends_at = _as_aware_utc(ends_at)
    if not is_active:
        return "PAUSED"
    if safe_starts_at and safe_starts_at > now:
        return "SCHEDULED"
    if safe_ends_at and safe_ends_at < now:
        return "EXPIRED"
    return "ACTIVE"


def _campaign_attributes(value: Any) -> dict[str, Any]:
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except ValueError:
            return {}
    return value if isinstance(value, dict) else {}


def _campaign_effective_lifecycle(
    *,
    is_active: bool,
    starts_at: Any,
    ends_at: Any,
    attributes: Any,
) -> str:
    safe_attributes = _campaign_attributes(attributes)
    lifecycle_state = safe_attributes.get("referral_saas_lifecycle") or {}
    if isinstance(lifecycle_state, dict):
        stored_lifecycle = _optional_text(lifecycle_state.get("lifecycle")).upper()
        if stored_lifecycle in {"PAUSED", "ENDED", "ARCHIVED"}:
            return stored_lifecycle
        if stored_lifecycle == "ACTIVE" and is_active:
            return _campaign_lifecycle(
                is_active=is_active,
                starts_at=starts_at,
                ends_at=ends_at,
            )

    activation_state = safe_attributes.get("referral_saas_activation") or {}
    if not is_active and not activation_state:
        return "DRAFT"
    return _campaign_lifecycle(is_active=is_active, starts_at=starts_at, ends_at=ends_at)


def _campaign_status(*, lifecycle: str, policy_status: str) -> str:
    if lifecycle in {"DRAFT", "PAUSED", "ENDED", "ARCHIVED", "EXPIRED"}:
        return lifecycle
    if policy_status != "ACTIVE_POLICY":
        return "NEEDS_POLICY"
    return lifecycle


def _campaign_allowed_lifecycle_actions(lifecycle: str) -> list[str]:
    safe_lifecycle = _optional_text(lifecycle).upper()
    if safe_lifecycle in {"ACTIVE", "SCHEDULED"}:
        return ["PAUSE", "END"]
    if safe_lifecycle == "PAUSED":
        return ["RESUME", "END", "ARCHIVE"]
    if safe_lifecycle == "ENDED":
        return ["ARCHIVE"]
    return []


def _campaign_lifecycle_plain_language(action: str | None, lifecycle: str) -> str:
    if not action:
        return f"Campaign lifecycle is {lifecycle}. No campaign state was changed."
    if action == "PAUSE":
        return "Campaign paused. Link issuing and active campaign checks stay blocked until the campaign is resumed."
    if action == "RESUME":
        return "Campaign resumed. Active campaign checks can pass again when policy and readiness remain valid."
    if action == "END":
        return "Campaign ended. It cannot be used for new referral activity."
    if action == "ARCHIVE":
        return "Campaign archived. It is retained for history and reporting, not day-to-day referral work."
    return f"Campaign lifecycle changed to {lifecycle}."


def _required_text(value: Any, field_name: str) -> str:
    safe_value = str(value or "").strip()
    if not safe_value:
        raise CampaignSetupValidationError(f"{field_name} is required.")
    return safe_value


def _required_review_text(value: Any, field_name: str) -> str:
    safe_value = str(value or "").strip()
    if not safe_value:
        raise CampaignReviewValidationError(f"{field_name} is required.")
    return safe_value


def _required_activation_text(value: Any, field_name: str) -> str:
    safe_value = str(value or "").strip()
    if not safe_value:
        raise CampaignActivationValidationError(f"{field_name} is required.")
    return safe_value


def _required_lifecycle_text(value: Any, field_name: str) -> str:
    safe_value = str(value or "").strip()
    if not safe_value:
        raise CampaignLifecycleValidationError(f"{field_name} is required.")
    return safe_value


def _optional_text(value: Any) -> str:
    return str(value or "").strip()


def _jsonb(value: Any) -> str:
    return json.dumps(value, sort_keys=True)


def _json_dict(value: Any, field_name: str) -> dict[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise CampaignPolicySettingsValidationError(f"{field_name} must be an object.")
    return value


def _json_list(value: Any, field_name: str) -> list[Any]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise CampaignPolicySettingsValidationError(f"{field_name} must be a list.")
    return value


def _positive_int(value: Any, field_name: str) -> int:
    try:
        safe_value = int(value)
    except (TypeError, ValueError) as exc:
        raise CampaignPolicySettingsValidationError(
            f"{field_name} must be a number."
        ) from exc
    if safe_value < 1:
        raise CampaignPolicySettingsValidationError(
            f"{field_name} must be at least 1."
        )
    return safe_value


def _reward_visibility_status(value: dict[str, Any]) -> str:
    mode = _optional_text(value.get("mode")).upper()
    if not mode:
        return "NOT_CONFIGURED"
    if mode != "CONFIGURED_WITHOUT_PAYMENT":
        raise CampaignPolicySettingsValidationError(
            "policySettings.rewardVisibility.mode must be configured_without_payment."
        )
    return mode


def _campaign_review_state(attributes: Any) -> dict[str, Any]:
    attributes = _campaign_attributes(attributes)
    review_state = attributes.get("referral_saas_review") or {}
    return review_state if isinstance(review_state, dict) else {}


def _campaign_programme_binding(attributes: Any) -> dict[str, Any] | None:
    attributes = _campaign_attributes(attributes)
    binding = attributes.get("referral_saas_programme_binding")
    return binding if isinstance(binding, dict) else None


def _programme_binding_from_row(
    row: dict[str, Any],
    *,
    actor_ref: str | None,
) -> dict[str, Any]:
    return {
        "programmeVersionId": str(row["programme_version_id"]),
        "programmeCode": str(row["programme_code"]),
        "programmeName": str(row["programme_name"]),
        "versionNumber": int(row.get("version_number") or 1),
        "versionStatus": str(row["version_status"]),
        "customerJourneyVersionId": str(row["customer_journey_version_id"]),
        "boundAt": _iso_now(),
        "boundByRef": _optional_text(actor_ref) or "REFERRAL_SAAS_ACCOUNT_OPERATOR",
        "source": "PUBLISHED_PROGRAMME_VERSION",
    }


async def _fetch_published_programme_version_for_binding(
    conn: Any,
    *,
    account_id: str,
    programme_version_id: str,
    error_cls: type[ReferralSaasCampaignCommandError],
) -> dict[str, Any]:
    safe_programme_version_id = _required_text(
        programme_version_id,
        "programmeVersionId",
    )
    row = await conn.fetchrow(
        """
        SELECT
            programme_version_id,
            account_id,
            programme_code,
            programme_name,
            version_number,
            version_status,
            customer_journey_version_id,
            effective_from,
            effective_to,
            retired_at
        FROM referral_saas_programme_versions
        WHERE account_id = $1
          AND programme_version_id = $2
        LIMIT 1
        """,
        account_id,
        safe_programme_version_id,
    )
    if not row:
        raise error_cls(
            "Campaign programme binding must use a programme version published for the selected customer."
        )
    safe_row = dict(row)
    if str(safe_row.get("version_status") or "").upper() != "PUBLISHED":
        raise error_cls(
            "Campaign programme binding must use a published programme version."
        )
    if safe_row.get("retired_at") is not None:
        raise error_cls("Retired programme versions cannot be bound to campaigns.")
    return safe_row


def _generate_campaign_code(tenant_code: str, segment: str, name: str) -> str:
    tenant = (_optional_text(tenant_code) or "GEN").upper().replace(" ", "-")
    safe_segment = (_optional_text(segment) or "GENERAL").upper().replace(" ", "-")
    safe_name = (_optional_text(name) or "CAMPAIGN").upper().replace(" ", "-")
    token = str(uuid4())[:8].upper()
    return f"{tenant}-{safe_segment}-{safe_name[:30]}-{token}"


def _to_campaign_summary(row: dict[str, Any]) -> ReferralSaasCampaignSummary:
    is_active = bool(row.get("is_active"))
    lifecycle = _campaign_effective_lifecycle(
        is_active=is_active,
        starts_at=row.get("starts_at"),
        ends_at=row.get("ends_at"),
        attributes=row.get("attributes"),
    )
    active_policy_count = int(row.get("active_policy_count") or 0)
    policy_status = "ACTIVE_POLICY" if active_policy_count > 0 else "NO_ACTIVE_POLICY"
    return ReferralSaasCampaignSummary(
        campaign_code=str(row["campaign_code"]),
        name=str(row["name"]),
        segment=str(row["segment"]),
        status=_campaign_status(lifecycle=lifecycle, policy_status=policy_status),
        lifecycle=lifecycle,
        starts_at=_as_iso(row.get("starts_at")),
        ends_at=_as_iso(row.get("ends_at")),
        max_uses=int(row["max_uses"]) if row.get("max_uses") is not None else None,
        uses_count=int(row.get("uses_count") or 0),
        policy_status=policy_status,
        created_at=_as_iso(row.get("created_at")),
        updated_at=_as_iso(row.get("updated_at")),
        programme_binding=_campaign_programme_binding(row.get("attributes")),
    )


def _attribution_status_from_row(row: dict[str, Any]) -> str:
    interaction_count = int(row.get("interaction_count") or 0)
    linked_referral_count = int(row.get("linked_referral_count") or 0)
    status_values = set(row.get("status_values") or [])
    if not interaction_count:
        return "MISSING_EVIDENCE"
    if "INVALID" in status_values or "BLOCKED" in status_values:
        return "CONFLICT"
    if linked_referral_count > 0 and (
        "ATTRIBUTED" in status_values or "COMPLETED" in status_values
    ):
        return "ATTRIBUTED"
    if "VALIDATED" in status_values:
        return "PARTIAL"
    return "UNATTRIBUTED"


def _attribution_confidence(status: str, row: dict[str, Any]) -> str:
    if status == "ATTRIBUTED":
        return "HIGH"
    if status == "PARTIAL":
        return "MEDIUM"
    if status == "CONFLICT":
        return "CONFLICT"
    if int(row.get("interaction_count") or 0) == 0:
        return "MISSING"
    return "LOW"


def _attribution_evidence(status: str, row: dict[str, Any]) -> list[str]:
    evidence: list[str] = []
    if int(row.get("interaction_count") or 0) > 0:
        evidence.append("Campaign interaction evidence exists.")
    if int(row.get("linked_referral_count") or 0) > 0:
        evidence.append("Referral link evidence connects campaign activity to referrals.")
    if int(row.get("event_count") or 0) > 0:
        evidence.append("Campaign event evidence is present.")
    if status == "MISSING_EVIDENCE":
        evidence.append("No attribution evidence has been captured for this source yet.")
    return evidence


def _attribution_gaps(status: str, row: dict[str, Any]) -> list[str]:
    gaps: list[str] = []
    if int(row.get("interaction_count") or 0) == 0:
        gaps.append("No campaign interactions found.")
    if int(row.get("linked_referral_count") or 0) == 0:
        gaps.append("No referral link evidence connects this source to referrals yet.")
    if int(row.get("event_count") or 0) == 0:
        gaps.append("No campaign event detail is available for explainability yet.")
    if status == "CONFLICT":
        gaps.append("Attribution evidence contains blocked or invalid statuses.")
    return gaps


def _attribution_explanation(status: str, row: dict[str, Any]) -> str:
    campaign_name = str(row.get("campaign_name") or row.get("campaign_code") or "Campaign")
    source_channel = str(row.get("source_channel") or "Unknown source")
    interactions = int(row.get("interaction_count") or 0)
    linked_referrals = int(row.get("linked_referral_count") or 0)
    if status == "ATTRIBUTED":
        return (
            f"{campaign_name} has campaign attribution evidence from "
            f"{source_channel} and {linked_referrals} linked referral record(s)."
        )
    if status == "PARTIAL":
        return (
            f"{campaign_name} has {interactions} validated interaction(s) from "
            f"{source_channel}, but referral link evidence is still incomplete."
        )
    if status == "CONFLICT":
        return (
            f"{campaign_name} has attribution evidence from {source_channel}, "
            "but some evidence is blocked or invalid and should be reviewed."
        )
    if status == "MISSING_EVIDENCE":
        return (
            f"{campaign_name} has no campaign attribution evidence for "
            f"{source_channel} yet."
        )
    return (
        f"{campaign_name} has early campaign interaction evidence from "
        f"{source_channel}, but attribution is not complete yet."
    )


def _to_campaign_attribution_projection(
    row: dict[str, Any],
) -> ReferralSaasCampaignAttributionProjection:
    status = _attribution_status_from_row(row)
    return ReferralSaasCampaignAttributionProjection(
        campaign_code=str(row.get("campaign_code") or ""),
        campaign_name=str(row.get("campaign_name") or row.get("campaign_code") or ""),
        segment=str(row.get("segment") or "Unsegmented"),
        campaign_status=str(row.get("campaign_status") or "UNKNOWN"),
        source_channel=str(row.get("source_channel") or "Unknown source"),
        attribution_status=status,
        confidence=_attribution_confidence(status, row),
        interaction_count=int(row.get("interaction_count") or 0),
        linked_referral_count=int(row.get("linked_referral_count") or 0),
        event_count=int(row.get("event_count") or 0),
        first_seen_at=_as_iso(row.get("first_seen_at")),
        last_seen_at=_as_iso(row.get("last_seen_at")),
        evidence=_attribution_evidence(status, row),
        gaps=_attribution_gaps(status, row),
        explanation=_attribution_explanation(status, row),
    )


def _campaign_attribution_plain_language(
    *,
    total_interactions: int,
    high_confidence_count: int,
    missing_evidence_count: int,
    conflict_count: int,
) -> str:
    if total_interactions == 0:
        return "No campaign attribution evidence has been captured for this customer yet."
    if conflict_count:
        return (
            f"{total_interactions} campaign interaction(s) found. "
            f"{conflict_count} source(s) need evidence review before attribution is trusted."
        )
    if missing_evidence_count:
        return (
            f"{total_interactions} campaign interaction(s) found. "
            f"{missing_evidence_count} source(s) still need referral or event evidence."
        )
    return (
        f"{total_interactions} campaign interaction(s) found. "
        f"{high_confidence_count} source(s) have high-confidence attribution evidence."
    )


async def create_referral_saas_account_campaign_setup(
    *,
    account_id: str,
    tenant_code: str,
    account_tenant_id: str | None,
    external_ref_id: str | None,
    account_status: str,
    tenant_link_status: str,
    external_reference_status: str,
    name: str,
    segment: str,
    starts_at: datetime | None = None,
    ends_at: datetime | None = None,
    max_uses: int | None = None,
    programme_version_id: str | None = None,
    reason_code: str,
    correlation_id: str,
    idempotency_key_hash: str,
    command_payload_hash: str,
    command_payload: dict[str, Any] | None = None,
    command_actor_ref: str | None = None,
    command_actor_role: str | None = None,
) -> ReferralSaasCampaignSetupResult:
    safe_account_id = _required_text(account_id, "account_id")
    safe_tenant_code = _required_text(tenant_code, "tenant_code")
    safe_name = _required_text(name, "campaign.name")
    safe_segment = _required_text(segment, "campaign.segment")
    safe_reason_code = _required_text(reason_code, "reason_code").upper()
    safe_correlation_id = _required_text(correlation_id, "correlation_id")
    safe_idempotency_hash = _required_text(
        idempotency_key_hash,
        "idempotency_key_hash",
    )
    safe_payload_hash = _required_text(command_payload_hash, "command_payload_hash")
    safe_account_status = _optional_text(account_status).upper()
    safe_tenant_link_status = _optional_text(tenant_link_status).upper()
    safe_external_reference_status = _optional_text(external_reference_status).upper()

    if safe_account_status not in {"PENDING_ONBOARDING", "ACTIVE"}:
        raise CampaignSetupAccountNotReady(
            "Account must exist before campaign setup can start."
        )
    if safe_tenant_link_status not in {"PENDING_SETUP", "ACTIVE"}:
        raise CampaignSetupAccountNotReady(
            "Account tenant link must exist before campaign setup can start."
        )
    if safe_external_reference_status not in {"ACTIVE"}:
        raise CampaignSetupAccountNotReady(
            "Selected customer reference must be active before campaign setup can start."
        )
    if starts_at and ends_at and ends_at < starts_at:
        raise CampaignSetupValidationError("campaign.endsAt must be after startsAt.")
    if max_uses is not None and int(max_uses) < 1:
        raise CampaignSetupValidationError("campaign.maxUses must be at least 1.")

    async with db_connection() as conn:
        existing_audit = await conn.fetchrow(
            """
            SELECT
                account_audit_event_id,
                event_status,
                evidence_summary
            FROM platform_account_audit_events
            WHERE account_id = $1
              AND event_type = $2
              AND idempotency_key_hash = $3
            ORDER BY created_at DESC
            LIMIT 1
            """,
            safe_account_id,
            CAMPAIGN_SETUP_CREATE_EVENT,
            safe_idempotency_hash,
        )
        if existing_audit:
            evidence = existing_audit.get("evidence_summary") or {}
            if isinstance(evidence, str):
                evidence = json.loads(evidence)
            if _optional_text(evidence.get("command_payload_hash")) != safe_payload_hash:
                raise CampaignSetupIdempotencyConflict(
                    "Idempotency key was reused with different campaign setup content."
                )
            return ReferralSaasCampaignSetupResult(
                command_status="CAMPAIGN_SETUP_DRAFT_REPLAYED",
                account_id=safe_account_id,
                campaign_code=_optional_text(evidence.get("campaign_code")),
                name=_optional_text(evidence.get("name")) or safe_name,
                segment=_optional_text(evidence.get("segment")) or safe_segment,
                setup_status=_optional_text(evidence.get("setup_status")) or "DRAFT",
                is_active=False,
                starts_at=_optional_text(evidence.get("starts_at")) or None,
                ends_at=_optional_text(evidence.get("ends_at")) or None,
                max_uses=(
                    int(evidence["max_uses"])
                    if evidence.get("max_uses") is not None
                    else None
                ),
                idempotency_status=CAMPAIGN_SETUP_REPLAYED,
                audit_event_id=_optional_text(
                    existing_audit.get("account_audit_event_id")
                )
                or None,
            )

        duplicate_campaign = await conn.fetchrow(
            """
            SELECT campaign_code
            FROM marketing_campaigns
            WHERE UPPER(tenant_code) = UPPER($1)
              AND UPPER(name) = UPPER($2)
              AND UPPER(segment) = UPPER($3)
            LIMIT 1
            """,
            safe_tenant_code,
            safe_name,
            safe_segment,
        )
        if duplicate_campaign:
            raise CampaignSetupDuplicate(
                "A campaign setup already exists for this selected customer, name, and segment."
            )

        programme_binding = None
        if _optional_text(programme_version_id):
            programme_version = await _fetch_published_programme_version_for_binding(
                conn,
                account_id=safe_account_id,
                programme_version_id=str(programme_version_id),
                error_cls=CampaignSetupValidationError,
            )
            programme_binding = _programme_binding_from_row(
                programme_version,
                actor_ref=command_actor_ref,
            )

        campaign_code = _generate_campaign_code(safe_tenant_code, safe_segment, safe_name)
        attributes = {
            "source": "TASK-256",
            "referral_saas_setup_status": "DRAFT",
            "account_id": safe_account_id,
            "command_payload_hash": safe_payload_hash,
            "no_campaign_activation_confirmed": True,
            "no_link_generation_confirmed": True,
            "no_validation_track_created_confirmed": True,
            "no_policy_write_confirmed": True,
            "no_money_movement_confirmed": True,
        }
        if programme_binding:
            attributes["referral_saas_programme_binding"] = programme_binding

        async with conn.transaction():
            campaign = await conn.fetchrow(
                """
                INSERT INTO marketing_campaigns (
                    campaign_code,
                    tenant_code,
                    segment,
                    name,
                    is_active,
                    starts_at,
                    ends_at,
                    max_uses,
                    attributes
                )
                VALUES ($1, $2, $3, $4, FALSE, $5, $6, $7, $8::jsonb)
                RETURNING
                    campaign_code,
                    name,
                    segment,
                    is_active,
                    starts_at,
                    ends_at,
                    max_uses
                """,
                campaign_code,
                safe_tenant_code,
                safe_segment,
                safe_name,
                starts_at,
                ends_at,
                max_uses,
                _jsonb(attributes),
            )
            audit_evidence = {
                "campaign_code": str(campaign["campaign_code"]),
                "name": str(campaign["name"]),
                "segment": str(campaign["segment"]),
                "setup_status": "DRAFT",
                "is_active": bool(campaign["is_active"]),
                "starts_at": _as_iso(campaign.get("starts_at")),
                "ends_at": _as_iso(campaign.get("ends_at")),
                "max_uses": (
                    int(campaign["max_uses"])
                    if campaign.get("max_uses") is not None
                    else None
                ),
                "command_payload_hash": safe_payload_hash,
                "programme_binding": programme_binding,
                "no_tenant_code_exposure_confirmed": True,
                "no_campaign_activation_confirmed": True,
                "no_link_generation_confirmed": True,
                "no_validation_track_created_confirmed": True,
                "no_policy_write_confirmed": True,
                "no_webhook_delivery_confirmed": True,
                "no_money_movement_confirmed": True,
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
                    $1, $2, $3, $4, $5, $6, $7, $8,
                    NULL, 'DRAFT', $9, $10, $11, $12::jsonb, $13::jsonb
                )
                RETURNING account_audit_event_id
                """,
                safe_account_id,
                _optional_text(account_tenant_id) or None,
                _optional_text(external_ref_id) or None,
                safe_tenant_code,
                CAMPAIGN_SETUP_CREATE_EVENT,
                CAMPAIGN_SETUP_RECORDED,
                _optional_text(command_actor_ref)
                or "REFERRAL_SAAS_ACCOUNT_OPERATOR",
                _optional_text(command_actor_role) or "UNKNOWN",
                safe_reason_code,
                safe_correlation_id,
                safe_idempotency_hash,
                _jsonb(audit_evidence),
                _jsonb(CAMPAIGN_SETUP_REDACTIONS),
            )

    return ReferralSaasCampaignSetupResult(
        command_status="CAMPAIGN_SETUP_DRAFT_RECORDED",
        account_id=safe_account_id,
        campaign_code=str(campaign["campaign_code"]),
        name=str(campaign["name"]),
        segment=str(campaign["segment"]),
        setup_status="DRAFT",
        is_active=bool(campaign["is_active"]),
        starts_at=_as_iso(campaign.get("starts_at")),
        ends_at=_as_iso(campaign.get("ends_at")),
        max_uses=(
            int(campaign["max_uses"])
            if campaign.get("max_uses") is not None
            else None
        ),
        idempotency_status=CAMPAIGN_SETUP_RECORDED,
        audit_event_id=(
            str(audit_event["account_audit_event_id"]) if audit_event else None
        ),
        programme_binding=programme_binding,
    )


async def bind_referral_saas_account_campaign_programme_version(
    *,
    account_id: str,
    tenant_code: str,
    campaign_code: str,
    programme_version_id: str,
    idempotency_key_hash: str,
    request_payload_hash: str,
    actor_ref: str | None = None,
    actor_role: str | None = None,
    correlation_id: str | None = None,
) -> ReferralSaasCampaignSetupResult:
    safe_account_id = _required_text(account_id, "account_id")
    safe_tenant_code = _required_text(tenant_code, "tenant_code")
    safe_campaign_code = _required_text(campaign_code, "campaign_code")
    safe_idempotency_hash = _required_text(
        idempotency_key_hash,
        "idempotency_key_hash",
    )
    safe_payload_hash = _required_text(request_payload_hash, "request_payload_hash")

    async with db_connection() as conn:
        existing_audit = await conn.fetchrow(
            """
            SELECT account_audit_event_id, evidence_summary
            FROM platform_account_audit_events
            WHERE account_id = $1
              AND event_type = $2
              AND idempotency_key_hash = $3
            ORDER BY created_at DESC
            LIMIT 1
            """,
            safe_account_id,
            CAMPAIGN_PROGRAMME_BINDING_EVENT,
            safe_idempotency_hash,
        )
        if existing_audit:
            evidence = existing_audit.get("evidence_summary") or {}
            if isinstance(evidence, str):
                evidence = json.loads(evidence)
            if _optional_text(evidence.get("request_payload_hash")) != safe_payload_hash:
                raise CampaignSetupIdempotencyConflict(
                    "Idempotency key was reused with different campaign programme binding content."
                )
            return ReferralSaasCampaignSetupResult(
                command_status="CAMPAIGN_PROGRAMME_BINDING_REPLAYED",
                account_id=safe_account_id,
                campaign_code=safe_campaign_code,
                name=_optional_text(evidence.get("name")) or "",
                segment=_optional_text(evidence.get("segment")) or "",
                setup_status=_optional_text(evidence.get("setup_status")) or "DRAFT",
                is_active=False,
                starts_at=_optional_text(evidence.get("starts_at")) or None,
                ends_at=_optional_text(evidence.get("ends_at")) or None,
                max_uses=None,
                idempotency_status=CAMPAIGN_PROGRAMME_BINDING_REPLAYED,
                audit_event_id=_optional_text(existing_audit.get("account_audit_event_id"))
                or None,
                programme_binding=evidence.get("programme_binding"),
            )

        campaign = await conn.fetchrow(
            """
            SELECT campaign_code, name, segment, is_active, starts_at, ends_at, max_uses, attributes
            FROM marketing_campaigns
            WHERE UPPER(tenant_code) = UPPER($1)
              AND UPPER(campaign_code) = UPPER($2)
            LIMIT 1
            """,
            safe_tenant_code,
            safe_campaign_code,
        )
        if not campaign:
            raise CampaignSetupValidationError(
                "Campaign was not found for the selected customer."
            )
        if bool(campaign.get("is_active")):
            raise CampaignSetupValidationError(
                "Programme binding can only be changed while the campaign is inactive."
            )

        programme_version = await _fetch_published_programme_version_for_binding(
            conn,
            account_id=safe_account_id,
            programme_version_id=programme_version_id,
            error_cls=CampaignSetupValidationError,
        )
        programme_binding = _programme_binding_from_row(
            programme_version,
            actor_ref=actor_ref,
        )
        attributes = _campaign_attributes(campaign.get("attributes"))
        attributes["referral_saas_programme_binding"] = programme_binding

        async with conn.transaction():
            updated = await conn.fetchrow(
                """
                UPDATE marketing_campaigns
                SET attributes = $3::jsonb,
                    updated_at = NOW()
                WHERE UPPER(tenant_code) = UPPER($1)
                  AND UPPER(campaign_code) = UPPER($2)
                RETURNING campaign_code, name, segment, is_active, starts_at, ends_at, max_uses
                """,
                safe_tenant_code,
                safe_campaign_code,
                _jsonb(attributes),
            )
            audit_evidence = {
                "campaign_code": safe_campaign_code,
                "name": str(updated["name"]),
                "segment": str(updated["segment"]),
                "setup_status": "DRAFT",
                "is_active": bool(updated["is_active"]),
                "starts_at": _as_iso(updated.get("starts_at")),
                "ends_at": _as_iso(updated.get("ends_at")),
                "programme_binding": programme_binding,
                "request_payload_hash": safe_payload_hash,
                "no_campaign_activation_confirmed": True,
                "no_runtime_journey_mutation_confirmed": True,
                "no_money_movement_confirmed": True,
            }
            audit_event = await conn.fetchrow(
                """
                INSERT INTO platform_account_audit_events (
                    account_id,
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
                    $1, $2, $3, $4, $5, $6,
                    NULL, 'PROGRAMME_BOUND', 'CUSTOMER_CAMPAIGN_PROGRAMME_BINDING',
                    $7, $8, $9::jsonb, $10::jsonb
                )
                RETURNING account_audit_event_id
                """,
                safe_account_id,
                safe_tenant_code,
                CAMPAIGN_PROGRAMME_BINDING_EVENT,
                CAMPAIGN_PROGRAMME_BINDING_RECORDED,
                _optional_text(actor_ref) or "REFERRAL_SAAS_ACCOUNT_OPERATOR",
                _optional_text(actor_role) or "UNKNOWN",
                _optional_text(correlation_id) or _iso_now(),
                safe_idempotency_hash,
                _jsonb(audit_evidence),
                _jsonb(CAMPAIGN_SETUP_REDACTIONS),
            )

    return ReferralSaasCampaignSetupResult(
        command_status="CAMPAIGN_PROGRAMME_BINDING_RECORDED",
        account_id=safe_account_id,
        campaign_code=str(updated["campaign_code"]),
        name=str(updated["name"]),
        segment=str(updated["segment"]),
        setup_status="DRAFT",
        is_active=bool(updated["is_active"]),
        starts_at=_as_iso(updated.get("starts_at")),
        ends_at=_as_iso(updated.get("ends_at")),
        max_uses=(
            int(updated["max_uses"])
            if updated.get("max_uses") is not None
            else None
        ),
        idempotency_status=CAMPAIGN_PROGRAMME_BINDING_RECORDED,
        audit_event_id=str(audit_event["account_audit_event_id"]) if audit_event else None,
        programme_binding=programme_binding,
    )


async def upsert_referral_saas_account_campaign_policy_settings(
    *,
    account_id: str,
    tenant_code: str,
    account_tenant_id: str | None,
    external_ref_id: str | None,
    account_status: str,
    tenant_link_status: str,
    external_reference_status: str,
    campaign_code: str,
    version: int,
    attribution_window_days: int | None,
    eligibility_rules: list[Any] | None = None,
    product_windows: dict[str, Any] | None = None,
    product_rules: dict[str, Any] | None = None,
    reward_visibility: dict[str, Any] | None = None,
    reason_code: str = "CUSTOMER_PROFILE_CAMPAIGN_POLICY_SETTINGS",
    correlation_id: str = "",
    idempotency_key_hash: str = "",
    command_payload_hash: str = "",
    command_payload: dict[str, Any] | None = None,
    command_actor_ref: str | None = None,
    command_actor_role: str | None = None,
) -> ReferralSaasCampaignPolicySettingsResult:
    safe_account_id = _required_text(account_id, "account_id")
    safe_tenant_code = _required_text(tenant_code, "tenant_code")
    safe_campaign_code = _required_text(campaign_code, "campaign_code")
    safe_version = _positive_int(version, "policySettings.version")
    safe_attribution_window = (
        _positive_int(attribution_window_days, "policySettings.attributionWindowDays")
        if attribution_window_days is not None
        else None
    )
    safe_eligibility_rules = _json_list(
        eligibility_rules,
        "policySettings.eligibilityRules",
    )
    safe_product_windows = _json_dict(
        product_windows,
        "policySettings.productWindows",
    )
    safe_product_rules = _json_dict(product_rules, "policySettings.productRules")
    safe_reward_visibility = _json_dict(
        reward_visibility,
        "policySettings.rewardVisibility",
    )
    reward_visibility_status = _reward_visibility_status(safe_reward_visibility)
    safe_reason_code = _required_text(reason_code, "reason_code").upper()
    safe_correlation_id = _required_text(correlation_id, "correlation_id")
    safe_idempotency_hash = _required_text(
        idempotency_key_hash,
        "idempotency_key_hash",
    )
    safe_payload_hash = _required_text(command_payload_hash, "command_payload_hash")
    safe_account_status = _optional_text(account_status).upper()
    safe_tenant_link_status = _optional_text(tenant_link_status).upper()
    safe_external_reference_status = _optional_text(external_reference_status).upper()

    if safe_account_status not in {"PENDING_ONBOARDING", "ACTIVE"}:
        raise CampaignPolicySettingsAccountNotReady(
            "Account must exist before campaign policy settings can be saved."
        )
    if safe_tenant_link_status not in {"PENDING_SETUP", "ACTIVE"}:
        raise CampaignPolicySettingsAccountNotReady(
            "Account tenant link must exist before campaign policy settings can be saved."
        )
    if safe_external_reference_status not in {"ACTIVE"}:
        raise CampaignPolicySettingsAccountNotReady(
            "Selected customer reference must be active before campaign policy settings can be saved."
        )

    async with db_connection() as conn:
        existing_audit = await conn.fetchrow(
            """
            SELECT
                account_audit_event_id,
                event_status,
                evidence_summary
            FROM platform_account_audit_events
            WHERE account_id = $1
              AND event_type = $2
              AND idempotency_key_hash = $3
            ORDER BY created_at DESC
            LIMIT 1
            """,
            safe_account_id,
            CAMPAIGN_POLICY_SETTINGS_EVENT,
            safe_idempotency_hash,
        )
        if existing_audit:
            evidence = existing_audit.get("evidence_summary") or {}
            if isinstance(evidence, str):
                evidence = json.loads(evidence)
            if _optional_text(evidence.get("command_payload_hash")) != safe_payload_hash:
                raise CampaignPolicySettingsIdempotencyConflict(
                    "Idempotency key was reused with different campaign policy settings."
                )
            return ReferralSaasCampaignPolicySettingsResult(
                command_status="POLICY_SETTINGS_REPLAYED",
                account_id=safe_account_id,
                campaign_code=_optional_text(evidence.get("campaign_code"))
                or safe_campaign_code,
                version=int(evidence.get("version") or safe_version),
                setup_status=_optional_text(evidence.get("setup_status"))
                or "POLICY_SETTINGS_RECORDED",
                attribution_window_days=(
                    int(evidence["attribution_window_days"])
                    if evidence.get("attribution_window_days") is not None
                    else None
                ),
                eligibility_rule_count=int(
                    evidence.get("eligibility_rule_count") or 0
                ),
                product_window_count=int(evidence.get("product_window_count") or 0),
                product_rule_count=int(evidence.get("product_rule_count") or 0),
                reward_visibility_status=_optional_text(
                    evidence.get("reward_visibility_status")
                )
                or reward_visibility_status,
                idempotency_status=CAMPAIGN_POLICY_SETTINGS_REPLAYED,
                audit_event_id=_optional_text(
                    existing_audit.get("account_audit_event_id")
                )
                or None,
            )

        campaign = await conn.fetchrow(
            """
            SELECT campaign_code, is_active
            FROM marketing_campaigns
            WHERE UPPER(tenant_code) = UPPER($1)
              AND UPPER(campaign_code) = UPPER($2)
            LIMIT 1
            """,
            safe_tenant_code,
            safe_campaign_code,
        )
        if not campaign:
            raise CampaignPolicySettingsCampaignNotFound(
                "Campaign was not found for the selected customer."
            )

        rules_json = {
            "eligibilityRules": safe_eligibility_rules,
            "rewardVisibility": safe_reward_visibility,
            "source": "TASK-259",
            "no_campaign_activation_confirmed": True,
            "no_link_generation_confirmed": True,
            "no_validation_track_created_confirmed": True,
            "no_webhook_delivery_confirmed": True,
            "no_money_movement_confirmed": True,
        }
        reward_amounts_json = {
            "visibility": safe_reward_visibility,
            "paymentStatus": "NOT_CONFIGURED",
            "no_money_movement_confirmed": True,
        }

        async with conn.transaction():
            policy = await conn.fetchrow(
                """
                INSERT INTO marketing_campaign_policies (
                    campaign_code,
                    tenant_code,
                    version,
                    is_active,
                    rolling_window_days,
                    rules_json,
                    product_windows_json,
                    reward_amounts_json,
                    product_rules_json
                )
                VALUES ($1, $2, $3, TRUE, $4, $5::jsonb, $6::jsonb, $7::jsonb, $8::jsonb)
                ON CONFLICT (campaign_code, tenant_code, version)
                DO UPDATE SET
                    is_active = TRUE,
                    rolling_window_days = EXCLUDED.rolling_window_days,
                    rules_json = EXCLUDED.rules_json,
                    product_windows_json = EXCLUDED.product_windows_json,
                    reward_amounts_json = EXCLUDED.reward_amounts_json,
                    product_rules_json = EXCLUDED.product_rules_json,
                    updated_at = NOW()
                RETURNING
                    campaign_code,
                    version,
                    rolling_window_days
                """,
                safe_campaign_code,
                safe_tenant_code,
                safe_version,
                safe_attribution_window,
                _jsonb(rules_json),
                _jsonb(safe_product_windows),
                _jsonb(reward_amounts_json),
                _jsonb(safe_product_rules),
            )
            audit_evidence = {
                "campaign_code": str(policy["campaign_code"]),
                "version": int(policy["version"]),
                "setup_status": "POLICY_SETTINGS_RECORDED",
                "attribution_window_days": (
                    int(policy["rolling_window_days"])
                    if policy.get("rolling_window_days") is not None
                    else None
                ),
                "eligibility_rule_count": len(safe_eligibility_rules),
                "product_window_count": len(safe_product_windows),
                "product_rule_count": len(safe_product_rules),
                "reward_visibility_status": reward_visibility_status,
                "campaign_was_active_before_policy_settings": bool(
                    campaign.get("is_active")
                ),
                "command_payload_hash": safe_payload_hash,
                "no_tenant_code_exposure_confirmed": True,
                "no_campaign_activation_confirmed": True,
                "no_link_generation_confirmed": True,
                "no_validation_track_created_confirmed": True,
                "no_webhook_delivery_confirmed": True,
                "no_money_movement_confirmed": True,
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
                    $1, $2, $3, $4, $5, $6, $7, $8,
                    NULL, 'POLICY_SETTINGS_RECORDED', $9, $10, $11, $12::jsonb, $13::jsonb
                )
                RETURNING account_audit_event_id
                """,
                safe_account_id,
                _optional_text(account_tenant_id) or None,
                _optional_text(external_ref_id) or None,
                safe_tenant_code,
                CAMPAIGN_POLICY_SETTINGS_EVENT,
                CAMPAIGN_POLICY_SETTINGS_RECORDED,
                _optional_text(command_actor_ref)
                or "REFERRAL_SAAS_ACCOUNT_OPERATOR",
                _optional_text(command_actor_role) or "UNKNOWN",
                safe_reason_code,
                safe_correlation_id,
                safe_idempotency_hash,
                _jsonb(audit_evidence),
                _jsonb(CAMPAIGN_POLICY_SETTINGS_REDACTIONS),
            )

    return ReferralSaasCampaignPolicySettingsResult(
        command_status="POLICY_SETTINGS_RECORDED",
        account_id=safe_account_id,
        campaign_code=str(policy["campaign_code"]),
        version=int(policy["version"]),
        setup_status="POLICY_SETTINGS_RECORDED",
        attribution_window_days=(
            int(policy["rolling_window_days"])
            if policy.get("rolling_window_days") is not None
            else None
        ),
        eligibility_rule_count=len(safe_eligibility_rules),
        product_window_count=len(safe_product_windows),
        product_rule_count=len(safe_product_rules),
        reward_visibility_status=reward_visibility_status,
        idempotency_status=CAMPAIGN_POLICY_SETTINGS_RECORDED,
        audit_event_id=(
            str(audit_event["account_audit_event_id"]) if audit_event else None
        ),
    )


async def submit_referral_saas_account_campaign_review(
    *,
    account_id: str,
    tenant_code: str,
    account_tenant_id: str | None,
    external_ref_id: str | None,
    campaign_code: str,
    setup_summary: str,
    operator_notes: str | None = None,
    requested_review_status: str = "READY_FOR_REVIEW",
    reason_code: str = "CUSTOMER_PROFILE_CAMPAIGN_REVIEW_SUBMIT",
    correlation_id: str = "",
    idempotency_key_hash: str = "",
    command_payload_hash: str = "",
    command_actor_ref: str | None = None,
    command_actor_role: str | None = None,
) -> ReferralSaasCampaignReviewResult:
    safe_account_id = _required_review_text(account_id, "account_id")
    safe_tenant_code = _required_review_text(tenant_code, "tenant_code")
    safe_campaign_code = _required_review_text(campaign_code, "campaign_code")
    safe_summary = _required_review_text(
        setup_summary,
        "reviewSubmission.setupSummary",
    )
    safe_requested_status = (
        _required_review_text(
            requested_review_status,
            "reviewSubmission.requestedReviewStatus",
        )
        .upper()
        .strip()
    )
    safe_reason_code = _required_review_text(reason_code, "reason_code").upper()
    safe_correlation_id = _required_review_text(correlation_id, "correlation_id")
    safe_idempotency_hash = _required_review_text(
        idempotency_key_hash,
        "idempotency_key_hash",
    )
    safe_payload_hash = _required_review_text(
        command_payload_hash,
        "command_payload_hash",
    )
    if safe_requested_status != "READY_FOR_REVIEW":
        raise CampaignReviewValidationError(
            "reviewSubmission.requestedReviewStatus must be READY_FOR_REVIEW."
        )

    async with db_connection() as conn:
        existing_audit = await conn.fetchrow(
            """
            SELECT
                account_audit_event_id,
                event_status,
                evidence_summary
            FROM platform_account_audit_events
            WHERE account_id = $1
              AND event_type = $2
              AND idempotency_key_hash = $3
            ORDER BY created_at DESC
            LIMIT 1
            """,
            safe_account_id,
            CAMPAIGN_REVIEW_SUBMIT_EVENT,
            safe_idempotency_hash,
        )
        if existing_audit:
            evidence = existing_audit.get("evidence_summary") or {}
            if isinstance(evidence, str):
                evidence = json.loads(evidence)
            if _optional_text(evidence.get("command_payload_hash")) != safe_payload_hash:
                raise CampaignReviewIdempotencyConflict(
                    "Idempotency key was reused with different campaign review submission."
                )
            return ReferralSaasCampaignReviewResult(
                command_status="CAMPAIGN_REVIEW_SUBMISSION_REPLAYED",
                account_id=safe_account_id,
                campaign_code=_optional_text(evidence.get("campaign_code"))
                or safe_campaign_code,
                review_status=_optional_text(evidence.get("review_status"))
                or "READY_FOR_REVIEW",
                setup_status=_optional_text(evidence.get("setup_status"))
                or "POLICY_SETTINGS_RECORDED",
                readiness_status=_optional_text(evidence.get("readiness_status"))
                or "NEEDS_REVIEW",
                activation_eligibility="NOT_ELIGIBLE_UNTIL_REVIEW_APPROVED",
                activation_status="NOT_ACTIVATED",
                reviewer_action="Record approval or block decision",
                idempotency_status=CAMPAIGN_REVIEW_REPLAYED,
                audit_event_id=_optional_text(
                    existing_audit.get("account_audit_event_id")
                )
                or None,
            )

        campaign = await conn.fetchrow(
            """
            SELECT campaign_code, is_active, attributes
            FROM marketing_campaigns
            WHERE UPPER(tenant_code) = UPPER($1)
              AND UPPER(campaign_code) = UPPER($2)
            LIMIT 1
            """,
            safe_tenant_code,
            safe_campaign_code,
        )
        if not campaign:
            raise CampaignReviewCampaignNotFound(
                "Campaign was not found for the selected customer."
            )
        if bool(campaign.get("is_active")):
            raise CampaignReviewInvalidState(
                "Active campaigns cannot be submitted through the setup review wrapper."
            )

        policy = await conn.fetchrow(
            """
            SELECT
                COUNT(*) AS active_policy_count,
                MAX(updated_at) AS latest_policy_updated_at
            FROM marketing_campaign_policies
            WHERE UPPER(tenant_code) = UPPER($1)
              AND UPPER(campaign_code) = UPPER($2)
              AND is_active = TRUE
            """,
            safe_tenant_code,
            safe_campaign_code,
        )
        if int(policy.get("active_policy_count") or 0) < 1:
            raise CampaignReviewNotReady(
                "Campaign policy/settings evidence must exist before review submission."
            )
        latest_policy_updated_at = _as_iso(policy.get("latest_policy_updated_at"))
        submitted_at = _iso_now()
        submitted_by_ref = (
            _optional_text(command_actor_ref) or "REFERRAL_SAAS_ACCOUNT_OPERATOR"
        )
        submitted_by_role = (_optional_text(command_actor_role) or "UNKNOWN").upper()

        attributes = campaign.get("attributes") or {}
        if isinstance(attributes, str):
            attributes = json.loads(attributes)
        if not isinstance(attributes, dict):
            attributes = {}
        previous_review_state = _campaign_review_state(attributes)
        previous_status = _optional_text(
            previous_review_state.get("review_status")
        ) or "NEEDS_REVIEW_SUBMISSION"
        if previous_status in {"REVIEW_APPROVED", "READY_TO_ACTIVATE", "ACTIVE"}:
            raise CampaignReviewInvalidState(
                "Approved campaigns cannot be resubmitted through this setup review wrapper."
            )

        review_state = {
            "review_status": "READY_FOR_REVIEW",
            "setup_status": "POLICY_SETTINGS_RECORDED",
            "readiness_status": "NEEDS_REVIEW",
            "setup_summary": safe_summary,
            "operator_notes_present": bool(_optional_text(operator_notes)),
            "activation_status": "NOT_ACTIVATED",
            "source": "TASK-262",
            "command_payload_hash": safe_payload_hash,
            "review_submission_payload_hash": safe_payload_hash,
            "submitted_by_ref": submitted_by_ref,
            "submitted_by_role": submitted_by_role,
            "submitted_at": submitted_at,
            "sod_status": CAMPAIGN_REVIEW_SOD_PENDING,
            "policy_evidence_status": CAMPAIGN_POLICY_EVIDENCE_CURRENT,
            "policy_evidence_updated_at": latest_policy_updated_at,
            "no_campaign_activation_confirmed": True,
            "no_link_generation_confirmed": True,
            "no_validation_track_created_confirmed": True,
            "no_webhook_delivery_confirmed": True,
            "no_money_movement_confirmed": True,
        }
        attributes["referral_saas_review"] = review_state

        async with conn.transaction():
            updated_campaign = await conn.fetchrow(
                """
                UPDATE marketing_campaigns
                SET attributes = $3::jsonb,
                    updated_at = NOW()
                WHERE UPPER(tenant_code) = UPPER($1)
                  AND UPPER(campaign_code) = UPPER($2)
                RETURNING campaign_code, is_active, attributes
                """,
                safe_tenant_code,
                safe_campaign_code,
                _jsonb(attributes),
            )
            audit_evidence = {
                "campaign_code": str(updated_campaign["campaign_code"]),
                "previous_review_status": previous_status,
                "review_status": "READY_FOR_REVIEW",
                "setup_status": "POLICY_SETTINGS_RECORDED",
                "readiness_status": "NEEDS_REVIEW",
                "command_payload_hash": safe_payload_hash,
                "submitted_by_ref_present": bool(submitted_by_ref),
                "submitted_by_role": submitted_by_role,
                "submitted_at": submitted_at,
                "sod_status": CAMPAIGN_REVIEW_SOD_PENDING,
                "policy_evidence_status": CAMPAIGN_POLICY_EVIDENCE_CURRENT,
                "policy_evidence_updated_at": latest_policy_updated_at,
                "campaign_is_active": bool(updated_campaign.get("is_active")),
                "no_tenant_code_exposure_confirmed": True,
                "no_campaign_activation_confirmed": True,
                "no_link_generation_confirmed": True,
                "no_validation_track_created_confirmed": True,
                "no_webhook_delivery_confirmed": True,
                "no_invite_or_seat_change_confirmed": True,
                "no_money_movement_confirmed": True,
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
                    $1, $2, $3, $4, $5, $6, $7, $8,
                    $9, 'READY_FOR_REVIEW', $10, $11, $12, $13::jsonb, $14::jsonb
                )
                RETURNING account_audit_event_id
                """,
                safe_account_id,
                _optional_text(account_tenant_id) or None,
                _optional_text(external_ref_id) or None,
                safe_tenant_code,
                CAMPAIGN_REVIEW_SUBMIT_EVENT,
                CAMPAIGN_REVIEW_SUBMITTED,
                submitted_by_ref,
                submitted_by_role,
                previous_status,
                safe_reason_code,
                safe_correlation_id,
                safe_idempotency_hash,
                _jsonb(audit_evidence),
                _jsonb(CAMPAIGN_REVIEW_REDACTIONS),
            )

    return ReferralSaasCampaignReviewResult(
        command_status="CAMPAIGN_REVIEW_SUBMITTED",
        account_id=safe_account_id,
        campaign_code=str(updated_campaign["campaign_code"]),
        review_status="READY_FOR_REVIEW",
        setup_status="POLICY_SETTINGS_RECORDED",
        readiness_status="NEEDS_REVIEW",
        activation_eligibility="NOT_ELIGIBLE_UNTIL_REVIEW_APPROVED",
        activation_status="NOT_ACTIVATED",
        reviewer_action="Record approval or block decision",
        idempotency_status=CAMPAIGN_REVIEW_SUBMITTED,
        audit_event_id=(
            str(audit_event["account_audit_event_id"]) if audit_event else None
        ),
    )


async def record_referral_saas_account_campaign_review_decision(
    *,
    account_id: str,
    tenant_code: str,
    account_tenant_id: str | None,
    external_ref_id: str | None,
    campaign_code: str,
    decision: str,
    reason: str,
    reviewer_ref: str,
    reason_code: str = "CUSTOMER_PROFILE_CAMPAIGN_REVIEW_DECISION",
    correlation_id: str = "",
    idempotency_key_hash: str = "",
    command_payload_hash: str = "",
    command_actor_ref: str | None = None,
    command_actor_role: str | None = None,
) -> ReferralSaasCampaignReviewResult:
    safe_account_id = _required_review_text(account_id, "account_id")
    safe_tenant_code = _required_review_text(tenant_code, "tenant_code")
    safe_campaign_code = _required_review_text(campaign_code, "campaign_code")
    safe_decision = _required_review_text(
        decision,
        "reviewDecision.decision",
    ).upper()
    safe_reason = _required_review_text(reason, "reviewDecision.reason")
    safe_reviewer_ref = _required_review_text(
        reviewer_ref,
        "reviewDecision.reviewerRef",
    )
    safe_reason_code = _required_review_text(reason_code, "reason_code").upper()
    safe_correlation_id = _required_review_text(correlation_id, "correlation_id")
    safe_idempotency_hash = _required_review_text(
        idempotency_key_hash,
        "idempotency_key_hash",
    )
    safe_payload_hash = _required_review_text(
        command_payload_hash,
        "command_payload_hash",
    )
    if safe_decision not in {"APPROVED", "BLOCKED"}:
        raise CampaignReviewValidationError(
            "reviewDecision.decision must be APPROVED or BLOCKED."
        )

    async with db_connection() as conn:
        existing_audit = await conn.fetchrow(
            """
            SELECT
                account_audit_event_id,
                event_status,
                evidence_summary
            FROM platform_account_audit_events
            WHERE account_id = $1
              AND event_type = $2
              AND idempotency_key_hash = $3
            ORDER BY created_at DESC
            LIMIT 1
            """,
            safe_account_id,
            CAMPAIGN_REVIEW_DECISION_EVENT,
            safe_idempotency_hash,
        )
        if existing_audit:
            evidence = existing_audit.get("evidence_summary") or {}
            if isinstance(evidence, str):
                evidence = json.loads(evidence)
            if _optional_text(evidence.get("command_payload_hash")) != safe_payload_hash:
                raise CampaignReviewIdempotencyConflict(
                    "Idempotency key was reused with different campaign review decision."
                )
            review_status = _optional_text(evidence.get("review_status")) or (
                "REVIEW_APPROVED" if safe_decision == "APPROVED" else "REVIEW_BLOCKED"
            )
            pre_activation_decision = {
                "sodStatus": _optional_text(evidence.get("sod_status")) or None,
                "policyEvidenceStatus": _optional_text(
                    evidence.get("policy_evidence_status")
                )
                or None,
                "reviewDecisionFresh": bool(evidence.get("review_decision_fresh")),
                "activationRequiresFreshReview": True,
            }
            return ReferralSaasCampaignReviewResult(
                command_status="CAMPAIGN_REVIEW_DECISION_REPLAYED",
                account_id=safe_account_id,
                campaign_code=_optional_text(evidence.get("campaign_code"))
                or safe_campaign_code,
                review_status=review_status,
                setup_status=_optional_text(evidence.get("setup_status"))
                or "POLICY_SETTINGS_RECORDED",
                readiness_status=_optional_text(evidence.get("readiness_status"))
                or "REVIEWED",
                activation_eligibility=_optional_text(
                    evidence.get("activation_eligibility")
                )
                or (
                    "ELIGIBLE_FOR_FUTURE_ACTIVATION"
                    if review_status == "REVIEW_APPROVED"
                    else "NOT_ELIGIBLE_REVIEW_BLOCKED"
                ),
                activation_status="NOT_ACTIVATED",
                reviewer_action=_optional_text(evidence.get("reviewer_action"))
                or "Open activation checklist",
                idempotency_status=CAMPAIGN_REVIEW_REPLAYED,
                audit_event_id=_optional_text(
                    existing_audit.get("account_audit_event_id")
                )
                or None,
                pre_activation_decision=pre_activation_decision,
            )

        campaign = await conn.fetchrow(
            """
            SELECT campaign_code, is_active, attributes
            FROM marketing_campaigns
            WHERE UPPER(tenant_code) = UPPER($1)
              AND UPPER(campaign_code) = UPPER($2)
            LIMIT 1
            """,
            safe_tenant_code,
            safe_campaign_code,
        )
        if not campaign:
            raise CampaignReviewCampaignNotFound(
                "Campaign was not found for the selected customer."
            )
        if bool(campaign.get("is_active")):
            raise CampaignReviewInvalidState(
                "Active campaigns cannot be changed through the setup review wrapper."
            )

        attributes = campaign.get("attributes") or {}
        if isinstance(attributes, str):
            attributes = json.loads(attributes)
        if not isinstance(attributes, dict):
            attributes = {}
        review_state = _campaign_review_state(attributes)
        previous_status = _optional_text(review_state.get("review_status"))
        if previous_status != "READY_FOR_REVIEW":
            raise CampaignReviewInvalidState(
                "Campaign review decision requires a READY_FOR_REVIEW submission."
            )
        submitted_by_ref = _optional_text(review_state.get("submitted_by_ref"))
        decision_by_ref = _optional_text(command_actor_ref) or safe_reviewer_ref
        decision_by_role = (_optional_text(command_actor_role) or "UNKNOWN").upper()
        if safe_decision == "APPROVED":
            if not submitted_by_ref:
                raise CampaignReviewInvalidState(
                    "Campaign approval requires recorded review submission ownership."
                )
            if submitted_by_ref == decision_by_ref:
                raise CampaignReviewInvalidState(
                    "Campaign approval requires separation of duties from the review submitter."
                )
        programme_binding = _campaign_programme_binding(attributes)
        if not programme_binding:
            raise CampaignActivationNotReady(
                "Campaign must be bound to a published programme version before activation."
            )
        programme_version_id = _optional_text(
            programme_binding.get("programmeVersionId")
        )
        if not programme_version_id:
            raise CampaignActivationNotReady(
                "Campaign programme binding is missing the published programme version."
            )
        programme_version = await _fetch_published_programme_version_for_binding(
            conn,
            account_id=safe_account_id,
            programme_version_id=programme_version_id,
            error_cls=CampaignActivationNotReady,
        )

        policy = await conn.fetchrow(
            """
            SELECT
                COUNT(*) AS active_policy_count,
                MAX(updated_at) AS latest_policy_updated_at
            FROM marketing_campaign_policies
            WHERE UPPER(tenant_code) = UPPER($1)
              AND UPPER(campaign_code) = UPPER($2)
              AND is_active = TRUE
            """,
            safe_tenant_code,
            safe_campaign_code,
        )
        if int(policy.get("active_policy_count") or 0) < 1:
            raise CampaignReviewNotReady(
                "Campaign policy/settings evidence must exist before review decision."
            )
        latest_policy_updated_at = _as_iso(policy.get("latest_policy_updated_at"))
        decision_at = _iso_now()

        next_status = "REVIEW_APPROVED" if safe_decision == "APPROVED" else "REVIEW_BLOCKED"
        activation_eligibility = (
            "ELIGIBLE_FOR_FUTURE_ACTIVATION"
            if safe_decision == "APPROVED"
            else "NOT_ELIGIBLE_REVIEW_BLOCKED"
        )
        reviewer_action = (
            "Open activation checklist"
            if safe_decision == "APPROVED"
            else "Return to campaign setup or policy settings"
        )
        review_state.update(
            {
                "review_status": next_status,
                "review_decision": safe_decision,
                "review_reason_present": bool(safe_reason),
                "reviewer_ref": safe_reviewer_ref,
                "decision_by_ref": decision_by_ref,
                "decision_by_role": decision_by_role,
                "decision_at": decision_at,
                "readiness_status": "REVIEWED",
                "activation_eligibility": activation_eligibility,
                "activation_status": "NOT_ACTIVATED",
                "reviewer_action": reviewer_action,
                "decision_payload_hash": safe_payload_hash,
                "review_decision_payload_hash": safe_payload_hash,
                "sod_status": (
                    CAMPAIGN_REVIEW_SOD_CONFIRMED
                    if safe_decision == "APPROVED"
                    else CAMPAIGN_REVIEW_SOD_BLOCKED
                ),
                "policy_evidence_status": CAMPAIGN_POLICY_EVIDENCE_CURRENT,
                "policy_evidence_updated_at": latest_policy_updated_at,
                "no_campaign_activation_confirmed": True,
                "no_link_generation_confirmed": True,
                "no_validation_track_created_confirmed": True,
                "no_webhook_delivery_confirmed": True,
                "no_money_movement_confirmed": True,
            }
        )
        attributes["referral_saas_review"] = review_state

        async with conn.transaction():
            updated_campaign = await conn.fetchrow(
                """
                UPDATE marketing_campaigns
                SET attributes = $3::jsonb,
                    updated_at = NOW()
                WHERE UPPER(tenant_code) = UPPER($1)
                  AND UPPER(campaign_code) = UPPER($2)
                RETURNING campaign_code, is_active, attributes
                """,
                safe_tenant_code,
                safe_campaign_code,
                _jsonb(attributes),
            )
            audit_evidence = {
                "campaign_code": str(updated_campaign["campaign_code"]),
                "previous_review_status": previous_status,
                "review_status": next_status,
                "setup_status": "POLICY_SETTINGS_RECORDED",
                "readiness_status": "REVIEWED",
                "activation_eligibility": activation_eligibility,
                "activation_status": "NOT_ACTIVATED",
                "reviewer_action": reviewer_action,
                "command_payload_hash": safe_payload_hash,
                "submitted_by_ref_present": bool(submitted_by_ref),
                "decision_by_ref_present": bool(decision_by_ref),
                "decision_by_role": decision_by_role,
                "decision_at": decision_at,
                "sod_status": review_state["sod_status"],
                "policy_evidence_status": CAMPAIGN_POLICY_EVIDENCE_CURRENT,
                "policy_evidence_updated_at": latest_policy_updated_at,
                "review_decision_fresh": True,
                "campaign_is_active": bool(updated_campaign.get("is_active")),
                "no_tenant_code_exposure_confirmed": True,
                "no_campaign_activation_confirmed": True,
                "no_link_generation_confirmed": True,
                "no_validation_track_created_confirmed": True,
                "no_webhook_delivery_confirmed": True,
                "no_invite_or_seat_change_confirmed": True,
                "no_money_movement_confirmed": True,
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
                    $1, $2, $3, $4, $5, $6, $7, $8,
                    $9, $10, $11, $12, $13, $14::jsonb, $15::jsonb
                )
                RETURNING account_audit_event_id
                """,
                safe_account_id,
                _optional_text(account_tenant_id) or None,
                _optional_text(external_ref_id) or None,
                safe_tenant_code,
                CAMPAIGN_REVIEW_DECISION_EVENT,
                CAMPAIGN_REVIEW_SUBMITTED,
                decision_by_ref,
                decision_by_role,
                previous_status,
                next_status,
                safe_reason_code,
                safe_correlation_id,
                safe_idempotency_hash,
                _jsonb(audit_evidence),
                _jsonb(CAMPAIGN_REVIEW_REDACTIONS),
            )

    return ReferralSaasCampaignReviewResult(
        command_status=(
            "CAMPAIGN_REVIEW_APPROVED"
            if safe_decision == "APPROVED"
            else "CAMPAIGN_REVIEW_BLOCKED"
        ),
        account_id=safe_account_id,
        campaign_code=str(updated_campaign["campaign_code"]),
        review_status=next_status,
        setup_status="POLICY_SETTINGS_RECORDED",
        readiness_status="REVIEWED",
        activation_eligibility=activation_eligibility,
        activation_status="NOT_ACTIVATED",
        reviewer_action=reviewer_action,
        idempotency_status=CAMPAIGN_REVIEW_SUBMITTED,
        audit_event_id=(
            str(audit_event["account_audit_event_id"]) if audit_event else None
        ),
        pre_activation_decision={
            "sodStatus": review_state["sod_status"],
            "policyEvidenceStatus": CAMPAIGN_POLICY_EVIDENCE_CURRENT,
            "reviewDecisionFresh": True,
            "activationRequiresFreshReview": True,
        },
    )


async def request_referral_saas_account_campaign_activation(
    *,
    account_id: str,
    tenant_code: str,
    account_tenant_id: str | None,
    external_ref_id: str | None,
    campaign_code: str,
    requested_lifecycle_status: str = "ACTIVE",
    review_status: str = "REVIEW_APPROVED",
    go_live_reason: str = "",
    operator_notes: str | None = None,
    activation_starts_at: datetime | None = None,
    activation_ends_at: datetime | None = None,
    reason_code: str = "CUSTOMER_PROFILE_CAMPAIGN_ACTIVATION",
    correlation_id: str = "",
    idempotency_key_hash: str = "",
    command_payload_hash: str = "",
    command_actor_ref: str | None = None,
    command_actor_role: str | None = None,
    production_activation_decision: dict[str, Any] | None = None,
) -> ReferralSaasCampaignActivationResult:
    safe_account_id = _required_activation_text(account_id, "account_id")
    safe_tenant_code = _required_activation_text(tenant_code, "tenant_code")
    safe_campaign_code = _required_activation_text(campaign_code, "campaign_code")
    safe_requested_lifecycle = _required_activation_text(
        requested_lifecycle_status,
        "activationRequest.requestedLifecycleStatus",
    ).upper()
    safe_review_status = _required_activation_text(
        review_status,
        "activationRequest.reviewStatus",
    ).upper()
    safe_go_live_reason = _required_activation_text(
        go_live_reason,
        "activationRequest.goLiveReason",
    )
    safe_reason_code = _required_activation_text(reason_code, "reason_code").upper()
    safe_correlation_id = _required_activation_text(correlation_id, "correlation_id")
    safe_idempotency_hash = _required_activation_text(
        idempotency_key_hash,
        "idempotency_key_hash",
    )
    safe_payload_hash = _required_activation_text(
        command_payload_hash,
        "command_payload_hash",
    )
    if safe_requested_lifecycle != "ACTIVE":
        raise CampaignActivationValidationError(
            "activationRequest.requestedLifecycleStatus must be ACTIVE."
        )
    if safe_review_status != "REVIEW_APPROVED":
        raise CampaignActivationValidationError(
            "activationRequest.reviewStatus must be REVIEW_APPROVED."
        )
    if (
        activation_starts_at
        and activation_ends_at
        and activation_ends_at < activation_starts_at
    ):
        raise CampaignActivationValidationError(
            "activationRequest.activationWindow.endsAt must be after startsAt."
        )
    if not production_activation_decision:
        raise CampaignActivationNotReady(
            "Production activation decision evidence is required before campaign activation."
        )
    if production_activation_decision.get("launchAllowed") is not True:
        blocked_gates = production_activation_decision.get("disabledReasons") or []
        readable_gates = ", ".join(str(gate) for gate in blocked_gates) or "UNKNOWN"
        raise CampaignActivationNotReady(
            "Production activation is blocked by backend readiness gates: "
            f"{readable_gates}."
        )

    async with db_connection() as conn:
        existing_audit = await conn.fetchrow(
            """
            SELECT
                account_audit_event_id,
                event_status,
                evidence_summary
            FROM platform_account_audit_events
            WHERE account_id = $1
              AND event_type = $2
              AND idempotency_key_hash = $3
            ORDER BY created_at DESC
            LIMIT 1
            """,
            safe_account_id,
            CAMPAIGN_ACTIVATION_EVENT,
            safe_idempotency_hash,
        )
        if existing_audit:
            evidence = existing_audit.get("evidence_summary") or {}
            if isinstance(evidence, str):
                evidence = json.loads(evidence)
            if _optional_text(evidence.get("command_payload_hash")) != safe_payload_hash:
                raise CampaignActivationIdempotencyConflict(
                    "Idempotency key was reused with different campaign activation content."
                )
            return ReferralSaasCampaignActivationResult(
                command_status="CAMPAIGN_ACTIVATION_REPLAYED",
                account_id=safe_account_id,
                campaign_code=_optional_text(evidence.get("campaign_code"))
                or safe_campaign_code,
                previous_lifecycle=_optional_text(evidence.get("previous_lifecycle"))
                or "READY_TO_ACTIVATE",
                lifecycle=_optional_text(evidence.get("lifecycle")) or "ACTIVE",
                review_status=_optional_text(evidence.get("review_status"))
                or "REVIEW_APPROVED",
                activation_eligibility=_optional_text(
                    evidence.get("activation_eligibility")
                )
                or "ELIGIBLE_FOR_FUTURE_ACTIVATION",
                activation_status=_optional_text(evidence.get("activation_status"))
                or "ACTIVATION_REQUEST_ACCEPTED",
                readiness_status=_optional_text(evidence.get("readiness_status"))
                or "READY_TO_ACTIVATE",
                idempotency_status=CAMPAIGN_ACTIVATION_REPLAYED,
                audit_event_id=_optional_text(
                    existing_audit.get("account_audit_event_id")
                )
                or None,
                pre_activation_decision=evidence.get("pre_activation_decision"),
            )

        campaign = await conn.fetchrow(
            """
            SELECT campaign_code, is_active, starts_at, ends_at, attributes
            FROM marketing_campaigns
            WHERE UPPER(tenant_code) = UPPER($1)
              AND UPPER(campaign_code) = UPPER($2)
            LIMIT 1
            """,
            safe_tenant_code,
            safe_campaign_code,
        )
        if not campaign:
            raise CampaignActivationCampaignNotFound(
                "Campaign was not found for the selected customer."
            )
        if bool(campaign.get("is_active")):
            raise CampaignActivationAlreadyActive(
                "Campaign is already active for the selected customer."
            )

        policy = await conn.fetchrow(
            """
            SELECT
                COUNT(*) AS active_policy_count,
                MAX(updated_at) AS latest_policy_updated_at
            FROM marketing_campaign_policies
            WHERE UPPER(tenant_code) = UPPER($1)
              AND UPPER(campaign_code) = UPPER($2)
              AND is_active = TRUE
            """,
            safe_tenant_code,
            safe_campaign_code,
        )
        if int(policy.get("active_policy_count") or 0) < 1:
            raise CampaignActivationNotReady(
                "Campaign policy/settings evidence must exist before activation."
            )
        latest_policy_updated_at = _as_aware_utc(policy.get("latest_policy_updated_at"))

        attributes = campaign.get("attributes") or {}
        if isinstance(attributes, str):
            attributes = json.loads(attributes)
        if not isinstance(attributes, dict):
            attributes = {}
        review_state = _campaign_review_state(attributes)
        previous_review_status = _optional_text(review_state.get("review_status"))
        activation_eligibility = _optional_text(
            review_state.get("activation_eligibility")
        )
        if previous_review_status != "REVIEW_APPROVED":
            raise CampaignActivationNotReady(
                "Campaign review must be approved before activation."
            )
        if activation_eligibility != "ELIGIBLE_FOR_FUTURE_ACTIVATION":
            raise CampaignActivationNotReady(
                "Campaign is not eligible for activation yet."
            )
        sod_status = _optional_text(review_state.get("sod_status"))
        submitted_by_ref = _optional_text(review_state.get("submitted_by_ref"))
        decision_by_ref = _optional_text(review_state.get("decision_by_ref"))
        decision_at = _parse_iso_datetime(review_state.get("decision_at"))
        decision_payload_hash = _optional_text(
            review_state.get("review_decision_payload_hash")
        ) or _optional_text(review_state.get("decision_payload_hash"))
        if sod_status != CAMPAIGN_REVIEW_SOD_CONFIRMED:
            raise CampaignActivationNotReady(
                "Campaign approval must include separation-of-duties proof before activation."
            )
        if not submitted_by_ref or not decision_by_ref or not decision_at:
            raise CampaignActivationNotReady(
                "Campaign approval evidence is incomplete; re-review is required before activation."
            )
        if submitted_by_ref == decision_by_ref:
            raise CampaignActivationNotReady(
                "Campaign activation requires approval by a different actor from the review submitter."
            )
        if not decision_payload_hash:
            raise CampaignActivationNotReady(
                "Campaign approval payload proof is missing; re-review is required before activation."
            )
        if latest_policy_updated_at and latest_policy_updated_at > decision_at:
            review_state.update(
                {
                    "policy_evidence_status": CAMPAIGN_POLICY_EVIDENCE_STALE,
                    "activation_eligibility": "NOT_ELIGIBLE_STALE_REVIEW",
                    "reviewer_action": "Re-review campaign policy settings",
                }
            )
            raise CampaignActivationNotReady(
                "Campaign policy/settings changed after review approval; re-review is required before activation."
            )
        programme_binding = _campaign_programme_binding(attributes)
        if not programme_binding:
            raise CampaignActivationNotReady(
                "Campaign must be bound to a published programme version before activation."
            )
        programme_version_id = _optional_text(
            programme_binding.get("programmeVersionId")
        )
        if not programme_version_id:
            raise CampaignActivationNotReady(
                "Campaign programme binding is missing the published programme version."
            )
        programme_version = await _fetch_published_programme_version_for_binding(
            conn,
            account_id=safe_account_id,
            programme_version_id=programme_version_id,
            error_cls=CampaignActivationNotReady,
        )

        previous_lifecycle = "READY_TO_ACTIVATE"
        pre_activation_decision = {
            "sodStatus": sod_status,
            "submittedByRefPresent": True,
            "approvedByRefPresent": True,
            "reviewDecisionFresh": True,
            "policyEvidenceFresh": True,
            "publishedProgrammeVersionBindingConfirmed": True,
            "programmeVersionId": str(programme_version["programme_version_id"]),
            "programmeCode": str(programme_version["programme_code"]),
            "programmeVersionNumber": int(programme_version.get("version_number") or 1),
            "derivedJourneyContextSource": "PUBLISHED_PROGRAMME_VERSION",
            "customerJourneyVersionId": str(
                programme_version["customer_journey_version_id"]
            ),
            "legacyJourneyBindingAuthoritative": False,
            "serverSideActivationDecisionConfirmed": True,
        }
        activation_state = {
            "activation_status": "ACTIVATION_REQUEST_ACCEPTED",
            "lifecycle": "ACTIVE",
            "review_status": previous_review_status,
            "activation_eligibility": activation_eligibility,
            "readiness_status": "READY_TO_ACTIVATE",
            "go_live_reason_present": bool(safe_go_live_reason),
            "operator_notes_present": bool(_optional_text(operator_notes)),
            "activation_window": {
                "starts_at": _as_iso(activation_starts_at),
                "ends_at": _as_iso(activation_ends_at),
            },
            "source": "TASK-265",
            "command_payload_hash": safe_payload_hash,
            "pre_activation_decision": pre_activation_decision,
            "no_link_generation_confirmed": True,
            "no_validation_track_created_confirmed": True,
            "no_webhook_delivery_confirmed": True,
            "no_credential_creation_confirmed": True,
            "no_money_movement_confirmed": True,
        }
        attributes["referral_saas_activation"] = activation_state
        attributes["referral_saas_lifecycle"] = {
            "lifecycle": "ACTIVE",
            "action": "ACTIVATE",
            "previous_lifecycle": previous_lifecycle,
            "changed_at": _iso_now(),
            "changed_by_ref": _optional_text(command_actor_ref)
            or "REFERRAL_SAAS_ACCOUNT_OPERATOR",
            "reason_code": safe_reason_code,
            "source": "TASK-371",
            "command_payload_hash": safe_payload_hash,
            "no_link_generation_confirmed": True,
            "no_validation_track_created_confirmed": True,
            "no_webhook_delivery_confirmed": True,
            "no_invite_or_seat_change_confirmed": True,
            "no_credential_creation_confirmed": True,
            "no_billing_or_money_movement_confirmed": True,
        }
        review_state.update(
            {
                "activation_status": "ACTIVATION_REQUEST_ACCEPTED",
                "readiness_status": "READY_TO_ACTIVATE",
                "policy_evidence_status": CAMPAIGN_POLICY_EVIDENCE_CURRENT,
            }
        )
        attributes["referral_saas_review"] = review_state

        async with conn.transaction():
            updated_campaign = await conn.fetchrow(
                """
                UPDATE marketing_campaigns
                SET is_active = TRUE,
                    starts_at = COALESCE($3, starts_at),
                    ends_at = COALESCE($4, ends_at),
                    attributes = $5::jsonb,
                    updated_at = NOW()
                WHERE UPPER(tenant_code) = UPPER($1)
                  AND UPPER(campaign_code) = UPPER($2)
                RETURNING campaign_code, is_active, starts_at, ends_at, attributes
                """,
                safe_tenant_code,
                safe_campaign_code,
                activation_starts_at,
                activation_ends_at,
                _jsonb(attributes),
            )
            audit_evidence = {
                "campaign_code": str(updated_campaign["campaign_code"]),
                "previous_lifecycle": previous_lifecycle,
                "lifecycle": "ACTIVE",
                "review_status": previous_review_status,
                "activation_eligibility": activation_eligibility,
                "activation_status": "ACTIVATION_REQUEST_ACCEPTED",
                "readiness_status": "READY_TO_ACTIVATE",
                "campaign_is_active": bool(updated_campaign.get("is_active")),
                "command_payload_hash": safe_payload_hash,
                "pre_activation_decision": pre_activation_decision,
                "no_tenant_code_exposure_confirmed": True,
                "no_link_generation_confirmed": True,
                "no_validation_track_created_confirmed": True,
                "no_webhook_delivery_confirmed": True,
                "no_invite_or_seat_change_confirmed": True,
                "no_credential_creation_confirmed": True,
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
                    $1, $2, $3, $4, $5, $6, $7, $8,
                    $9, 'ACTIVE', $10, $11, $12, $13::jsonb, $14::jsonb
                )
                RETURNING account_audit_event_id
                """,
                safe_account_id,
                _optional_text(account_tenant_id) or None,
                _optional_text(external_ref_id) or None,
                safe_tenant_code,
                CAMPAIGN_ACTIVATION_EVENT,
                CAMPAIGN_ACTIVATION_RECORDED,
                _optional_text(command_actor_ref)
                or "REFERRAL_SAAS_ACCOUNT_OPERATOR",
                _optional_text(command_actor_role) or "UNKNOWN",
                previous_lifecycle,
                safe_reason_code,
                safe_correlation_id,
                safe_idempotency_hash,
                _jsonb(audit_evidence),
                _jsonb(CAMPAIGN_ACTIVATION_REDACTIONS),
            )

    return ReferralSaasCampaignActivationResult(
        command_status="CAMPAIGN_ACTIVATION_ACCEPTED",
        account_id=safe_account_id,
        campaign_code=str(updated_campaign["campaign_code"]),
        previous_lifecycle=previous_lifecycle,
        lifecycle="ACTIVE",
        review_status=previous_review_status,
        activation_eligibility=activation_eligibility,
        activation_status="ACTIVATION_REQUEST_ACCEPTED",
        readiness_status="READY_TO_ACTIVATE",
        idempotency_status=CAMPAIGN_ACTIVATION_RECORDED,
        audit_event_id=(
            str(audit_event["account_audit_event_id"]) if audit_event else None
        ),
        pre_activation_decision=pre_activation_decision,
    )


async def get_referral_saas_account_campaign_lifecycle(
    *,
    account_id: str,
    tenant_code: str,
    campaign_code: str,
) -> ReferralSaasCampaignLifecycleResult | None:
    campaign = await get_referral_saas_account_campaign(
        tenant_code=tenant_code,
        campaign_code=campaign_code,
    )
    if campaign is None:
        return None
    lifecycle = campaign.lifecycle
    return ReferralSaasCampaignLifecycleResult(
        command_status="CAMPAIGN_LIFECYCLE_READ",
        account_id=account_id,
        campaign_code=campaign.campaign_code,
        action=None,
        previous_lifecycle=None,
        lifecycle=lifecycle,
        is_active=lifecycle in {"ACTIVE", "SCHEDULED"},
        allowed_actions=_campaign_allowed_lifecycle_actions(lifecycle),
        plain_language=_campaign_lifecycle_plain_language(None, lifecycle),
    )


async def record_referral_saas_account_campaign_lifecycle_command(
    *,
    account_id: str,
    tenant_code: str,
    account_tenant_id: str | None,
    external_ref_id: str | None,
    campaign_code: str,
    action: str,
    reason: str,
    operator_notes: str | None = None,
    reason_code: str = "CUSTOMER_PROFILE_CAMPAIGN_LIFECYCLE",
    correlation_id: str = "",
    idempotency_key_hash: str = "",
    command_payload_hash: str = "",
    command_actor_ref: str | None = None,
    command_actor_role: str | None = None,
) -> ReferralSaasCampaignLifecycleResult:
    safe_account_id = _required_lifecycle_text(account_id, "account_id")
    safe_tenant_code = _required_lifecycle_text(tenant_code, "tenant_code")
    safe_campaign_code = _required_lifecycle_text(campaign_code, "campaign_code")
    safe_action = _required_lifecycle_text(action, "lifecycleCommand.action").upper()
    safe_reason = _required_lifecycle_text(reason, "lifecycleCommand.reason")
    safe_reason_code = _required_lifecycle_text(reason_code, "reason_code").upper()
    safe_correlation_id = _required_lifecycle_text(correlation_id, "correlation_id")
    safe_idempotency_hash = _required_lifecycle_text(
        idempotency_key_hash,
        "idempotency_key_hash",
    )
    safe_payload_hash = _required_lifecycle_text(
        command_payload_hash,
        "command_payload_hash",
    )
    if safe_action not in CAMPAIGN_LIFECYCLE_ACTIONS:
        raise CampaignLifecycleValidationError(
            "lifecycleCommand.action must be one of PAUSE, RESUME, END, or ARCHIVE."
        )

    async with db_connection() as conn:
        existing_audit = await conn.fetchrow(
            """
            SELECT account_audit_event_id, event_status, evidence_summary
            FROM platform_account_audit_events
            WHERE account_id = $1
              AND event_type = $2
              AND idempotency_key_hash = $3
            ORDER BY created_at DESC
            LIMIT 1
            """,
            safe_account_id,
            CAMPAIGN_LIFECYCLE_EVENT,
            safe_idempotency_hash,
        )
        if existing_audit:
            evidence = existing_audit.get("evidence_summary") or {}
            evidence = _campaign_attributes(evidence)
            if _optional_text(evidence.get("command_payload_hash")) != safe_payload_hash:
                raise CampaignLifecycleIdempotencyConflict(
                    "Idempotency key was reused with different campaign lifecycle content."
                )
            lifecycle = _optional_text(evidence.get("lifecycle")) or "UNKNOWN"
            return ReferralSaasCampaignLifecycleResult(
                command_status="CAMPAIGN_LIFECYCLE_REPLAYED",
                account_id=safe_account_id,
                campaign_code=_optional_text(evidence.get("campaign_code"))
                or safe_campaign_code,
                action=_optional_text(evidence.get("action")) or safe_action,
                previous_lifecycle=_optional_text(evidence.get("previous_lifecycle"))
                or None,
                lifecycle=lifecycle,
                is_active=bool(evidence.get("campaign_is_active")),
                allowed_actions=_campaign_allowed_lifecycle_actions(lifecycle),
                plain_language=_optional_text(evidence.get("plain_language"))
                or _campaign_lifecycle_plain_language(safe_action, lifecycle),
                idempotency_status=CAMPAIGN_LIFECYCLE_REPLAYED,
                audit_event_id=_optional_text(
                    existing_audit.get("account_audit_event_id")
                )
                or None,
            )

        campaign = await conn.fetchrow(
            """
            SELECT campaign_code, is_active, starts_at, ends_at, attributes
            FROM marketing_campaigns
            WHERE UPPER(tenant_code) = UPPER($1)
              AND UPPER(campaign_code) = UPPER($2)
            LIMIT 1
            """,
            safe_tenant_code,
            safe_campaign_code,
        )
        if not campaign:
            raise CampaignLifecycleCampaignNotFound(
                "Campaign was not found for the selected customer."
            )

        attributes = _campaign_attributes(campaign.get("attributes"))
        previous_lifecycle = _campaign_effective_lifecycle(
            is_active=bool(campaign.get("is_active")),
            starts_at=campaign.get("starts_at"),
            ends_at=campaign.get("ends_at"),
            attributes=attributes,
        )
        allowed_actions = _campaign_allowed_lifecycle_actions(previous_lifecycle)
        if safe_action not in allowed_actions:
            raise CampaignLifecycleInvalidTransition(
                f"Cannot {safe_action.lower()} a campaign while lifecycle is {previous_lifecycle}."
            )

        next_lifecycle = {
            "PAUSE": "PAUSED",
            "RESUME": "ACTIVE",
            "END": "ENDED",
            "ARCHIVE": "ARCHIVED",
        }[safe_action]
        next_is_active = next_lifecycle == "ACTIVE"
        lifecycle_state = {
            "lifecycle": next_lifecycle,
            "action": safe_action,
            "previous_lifecycle": previous_lifecycle,
            "changed_at": _iso_now(),
            "changed_by_ref": _optional_text(command_actor_ref)
            or "REFERRAL_SAAS_ACCOUNT_OPERATOR",
            "reason_present": bool(safe_reason),
            "operator_notes_present": bool(_optional_text(operator_notes)),
            "reason_code": safe_reason_code,
            "source": "TASK-371",
            "command_payload_hash": safe_payload_hash,
            "no_link_generation_confirmed": True,
            "no_validation_track_created_confirmed": True,
            "no_webhook_delivery_confirmed": True,
            "no_invite_or_seat_change_confirmed": True,
            "no_credential_creation_confirmed": True,
            "no_billing_or_money_movement_confirmed": True,
        }
        attributes["referral_saas_lifecycle"] = lifecycle_state
        plain_language = _campaign_lifecycle_plain_language(
            safe_action,
            next_lifecycle,
        )

        async with conn.transaction():
            updated_campaign = await conn.fetchrow(
                """
                UPDATE marketing_campaigns
                SET is_active = $3,
                    attributes = $4::jsonb,
                    updated_at = NOW()
                WHERE UPPER(tenant_code) = UPPER($1)
                  AND UPPER(campaign_code) = UPPER($2)
                RETURNING campaign_code, is_active
                """,
                safe_tenant_code,
                safe_campaign_code,
                next_is_active,
                _jsonb(attributes),
            )
            audit_evidence = {
                "campaign_code": str(updated_campaign["campaign_code"]),
                "action": safe_action,
                "previous_lifecycle": previous_lifecycle,
                "lifecycle": next_lifecycle,
                "plain_language": plain_language,
                "campaign_is_active": bool(updated_campaign.get("is_active")),
                "reason_present": True,
                "operator_notes_present": bool(_optional_text(operator_notes)),
                "command_payload_hash": safe_payload_hash,
                "no_tenant_code_exposure_confirmed": True,
                "no_link_generation_confirmed": True,
                "no_validation_track_created_confirmed": True,
                "no_webhook_delivery_confirmed": True,
                "no_invite_or_seat_change_confirmed": True,
                "no_credential_creation_confirmed": True,
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
                    $1, $2, $3, $4, $5, $6, $7, $8,
                    $9, $10, $11, $12, $13, $14::jsonb, $15::jsonb
                )
                RETURNING account_audit_event_id
                """,
                safe_account_id,
                _optional_text(account_tenant_id) or None,
                _optional_text(external_ref_id) or None,
                safe_tenant_code,
                CAMPAIGN_LIFECYCLE_EVENT,
                CAMPAIGN_LIFECYCLE_RECORDED,
                _optional_text(command_actor_ref)
                or "REFERRAL_SAAS_ACCOUNT_OPERATOR",
                _optional_text(command_actor_role) or "UNKNOWN",
                previous_lifecycle,
                next_lifecycle,
                safe_reason_code,
                safe_correlation_id,
                safe_idempotency_hash,
                _jsonb(audit_evidence),
                _jsonb(CAMPAIGN_LIFECYCLE_REDACTIONS),
            )

    return ReferralSaasCampaignLifecycleResult(
        command_status="CAMPAIGN_LIFECYCLE_RECORDED",
        account_id=safe_account_id,
        campaign_code=str(updated_campaign["campaign_code"]),
        action=safe_action,
        previous_lifecycle=previous_lifecycle,
        lifecycle=next_lifecycle,
        is_active=next_is_active,
        allowed_actions=_campaign_allowed_lifecycle_actions(next_lifecycle),
        plain_language=plain_language,
        idempotency_status=CAMPAIGN_LIFECYCLE_RECORDED,
        audit_event_id=str(audit_event["account_audit_event_id"])
        if audit_event
        else None,
    )


async def list_referral_saas_account_campaigns(
    *,
    tenant_code: str,
    limit: int = 50,
) -> list[ReferralSaasCampaignSummary]:
    safe_tenant_code = str(tenant_code or "").strip()
    if not safe_tenant_code:
        return []
    safe_limit = max(1, min(int(limit or 50), MAX_CAMPAIGN_LIST_LIMIT))
    async with db_connection() as conn:
        rows = await conn.fetch(
            """
            SELECT
                campaign.campaign_code,
                campaign.name,
                campaign.segment,
                campaign.is_active,
                campaign.starts_at,
                campaign.ends_at,
                campaign.max_uses,
                campaign.uses_count,
                campaign.attributes,
                campaign.created_at,
                campaign.updated_at,
                COUNT(policy.campaign_code) FILTER (WHERE policy.is_active = TRUE)
                    AS active_policy_count
            FROM marketing_campaigns campaign
            LEFT JOIN marketing_campaign_policies policy
                ON UPPER(policy.campaign_code) = UPPER(campaign.campaign_code)
               AND (
                    policy.tenant_code IS NULL
                    OR UPPER(policy.tenant_code) = UPPER($1)
               )
            WHERE UPPER(campaign.tenant_code) = UPPER($1)
            GROUP BY
                campaign.campaign_code,
                campaign.name,
                campaign.segment,
                campaign.is_active,
                campaign.starts_at,
                campaign.ends_at,
                campaign.max_uses,
                campaign.uses_count,
                campaign.attributes,
                campaign.created_at,
                campaign.updated_at
            ORDER BY campaign.updated_at DESC, campaign.created_at DESC, campaign.campaign_code ASC
            LIMIT $2
            """,
            safe_tenant_code,
            safe_limit,
        )
    return [_to_campaign_summary(dict(row)) for row in rows]


async def get_referral_saas_account_campaign(
    *,
    tenant_code: str,
    campaign_code: str,
) -> ReferralSaasCampaignSummary | None:
    safe_tenant_code = str(tenant_code or "").strip()
    safe_campaign_code = str(campaign_code or "").strip()
    if not safe_tenant_code or not safe_campaign_code:
        return None
    async with db_connection() as conn:
        row = await conn.fetchrow(
            """
            SELECT
                campaign.campaign_code,
                campaign.name,
                campaign.segment,
                campaign.is_active,
                campaign.starts_at,
                campaign.ends_at,
                campaign.max_uses,
                campaign.uses_count,
                campaign.attributes,
                campaign.created_at,
                campaign.updated_at,
                COUNT(policy.campaign_code) FILTER (WHERE policy.is_active = TRUE)
                    AS active_policy_count
            FROM marketing_campaigns campaign
            LEFT JOIN marketing_campaign_policies policy
                ON UPPER(policy.campaign_code) = UPPER(campaign.campaign_code)
               AND (
                    policy.tenant_code IS NULL
                    OR UPPER(policy.tenant_code) = UPPER($1)
               )
            WHERE UPPER(campaign.tenant_code) = UPPER($1)
              AND UPPER(campaign.campaign_code) = UPPER($2)
            GROUP BY
                campaign.campaign_code,
                campaign.name,
                campaign.segment,
                campaign.is_active,
                campaign.starts_at,
                campaign.ends_at,
                campaign.max_uses,
                campaign.uses_count,
                campaign.attributes,
                campaign.created_at,
                campaign.updated_at
            LIMIT 1
            """,
            safe_tenant_code,
            safe_campaign_code,
        )
    return _to_campaign_summary(dict(row)) if row else None


async def build_referral_saas_account_campaign_attribution_projection(
    *,
    tenant_code: str,
    limit: int = 50,
) -> ReferralSaasCampaignAttributionSummary:
    safe_tenant_code = str(tenant_code or "").strip()
    if not safe_tenant_code:
        return ReferralSaasCampaignAttributionSummary(
            status="NO_CUSTOMER_SCOPE",
            campaign_count=0,
            source_count=0,
            total_interactions=0,
            high_confidence_count=0,
            missing_evidence_count=0,
            conflict_count=0,
            plain_language=(
                "Select a customer before reviewing campaign attribution."
            ),
            projections=[],
        )

    safe_limit = max(1, min(int(limit or 50), MAX_CAMPAIGN_LIST_LIMIT))
    async with db_connection() as conn:
        rows = await conn.fetch(
            """
            WITH attribution_base AS (
                SELECT
                    campaign.campaign_code,
                    campaign.name AS campaign_name,
                    campaign.segment,
                    CASE
                        WHEN campaign.is_active THEN 'ACTIVE'
                        ELSE 'DRAFT'
                    END AS campaign_status,
                    COALESCE(
                        NULLIF(attribution.source_channel, ''),
                        'Unknown source'
                    ) AS source_channel,
                    attribution.campaign_track_id,
                    attribution.status,
                    attribution.scanned_at,
                    attribution.validated_at,
                    attribution.attributed_at,
                    attribution.completed_at
                FROM marketing_campaigns campaign
                LEFT JOIN campaign_attributions attribution
                    ON UPPER(attribution.campaign_code) = UPPER(campaign.campaign_code)
                   AND UPPER(attribution.tenant_code) = UPPER($1)
                WHERE UPPER(campaign.tenant_code) = UPPER($1)
            ),
            event_counts AS (
                SELECT
                    attribution.campaign_code,
                    COALESCE(
                        NULLIF(attribution.source_channel, ''),
                        'Unknown source'
                    ) AS source_channel,
                    COUNT(event.id)::int AS event_count
                FROM campaign_attributions attribution
                JOIN campaign_track_events event
                    ON event.campaign_track_id = attribution.campaign_track_id
                WHERE UPPER(attribution.tenant_code) = UPPER($1)
                GROUP BY attribution.campaign_code, source_channel
            ),
            link_counts AS (
                SELECT
                    attribution.campaign_code,
                    COALESCE(
                        NULLIF(attribution.source_channel, ''),
                        'Unknown source'
                    ) AS source_channel,
                    COUNT(DISTINCT link.referral_track_id)::int AS linked_referral_count
                FROM campaign_attributions attribution
                JOIN campaign_referral_links link
                    ON link.campaign_track_id = attribution.campaign_track_id
                WHERE UPPER(attribution.tenant_code) = UPPER($1)
                GROUP BY attribution.campaign_code, source_channel
            )
            SELECT
                base.campaign_code,
                base.campaign_name,
                base.segment,
                base.campaign_status,
                base.source_channel,
                COUNT(base.campaign_track_id)::int AS interaction_count,
                COUNT(base.campaign_track_id)
                    FILTER (WHERE base.status = 'VALIDATED')::int AS validated_count,
                COUNT(base.campaign_track_id)
                    FILTER (WHERE base.status = 'ATTRIBUTED')::int AS attributed_count,
                COUNT(base.campaign_track_id)
                    FILTER (WHERE base.status = 'COMPLETED')::int AS completed_count,
                COUNT(base.campaign_track_id)
                    FILTER (WHERE base.status IN ('BLOCKED', 'INVALID'))::int
                    AS conflict_count,
                COALESCE(link_counts.linked_referral_count, 0)::int
                    AS linked_referral_count,
                COALESCE(event_counts.event_count, 0)::int AS event_count,
                MIN(base.scanned_at) AS first_seen_at,
                MAX(
                    COALESCE(
                        base.completed_at,
                        base.attributed_at,
                        base.validated_at,
                        base.scanned_at
                    )
                ) AS last_seen_at,
                ARRAY_REMOVE(ARRAY_AGG(DISTINCT base.status), NULL) AS status_values
            FROM attribution_base base
            LEFT JOIN event_counts
                ON UPPER(event_counts.campaign_code) = UPPER(base.campaign_code)
               AND event_counts.source_channel = base.source_channel
            LEFT JOIN link_counts
                ON UPPER(link_counts.campaign_code) = UPPER(base.campaign_code)
               AND link_counts.source_channel = base.source_channel
            GROUP BY
                base.campaign_code,
                base.campaign_name,
                base.segment,
                base.campaign_status,
                base.source_channel,
                link_counts.linked_referral_count,
                event_counts.event_count
            ORDER BY
                interaction_count DESC,
                last_seen_at DESC NULLS LAST,
                base.campaign_code ASC,
                base.source_channel ASC
            LIMIT $2
            """,
            safe_tenant_code,
            safe_limit,
        )

    projections = [
        _to_campaign_attribution_projection(dict(row))
        for row in rows
    ]
    total_interactions = sum(
        projection.interaction_count for projection in projections
    )
    high_confidence_count = sum(
        1 for projection in projections if projection.confidence == "HIGH"
    )
    missing_evidence_count = sum(
        1
        for projection in projections
        if projection.confidence in {"MISSING", "LOW"}
    )
    conflict_count = sum(
        1 for projection in projections if projection.confidence == "CONFLICT"
    )
    status = "READY"
    if not projections:
        status = "NO_CAMPAIGNS"
    elif conflict_count:
        status = "REVIEW_REQUIRED"
    elif total_interactions == 0:
        status = "NO_ATTRIBUTION_EVIDENCE"
    elif missing_evidence_count:
        status = "PARTIAL_EVIDENCE"

    return ReferralSaasCampaignAttributionSummary(
        status=status,
        campaign_count=len({projection.campaign_code for projection in projections}),
        source_count=len(projections),
        total_interactions=total_interactions,
        high_confidence_count=high_confidence_count,
        missing_evidence_count=missing_evidence_count,
        conflict_count=conflict_count,
        plain_language=_campaign_attribution_plain_language(
            total_interactions=total_interactions,
            high_confidence_count=high_confidence_count,
            missing_evidence_count=missing_evidence_count,
            conflict_count=conflict_count,
        ),
        projections=projections,
    )
