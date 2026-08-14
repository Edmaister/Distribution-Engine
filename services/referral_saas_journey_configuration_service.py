from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Mapping, Sequence

from utils.db import db_connection


JOURNEY_TEMPLATE_CATALOGUE_GUARDRAILS = (
    "AMPLIFI_GOVERNED_TEMPLATE_CATALOGUE",
    "READ_ONLY_TEMPLATE_CATALOGUE",
    "NO_TENANT_DATA",
    "NO_CUSTOMER_CONFIGURATION_WRITE",
    "NO_RUNTIME_EXECUTION",
    "NO_CAMPAIGN_BINDING",
    "NO_PROVIDER_AUTH_BILLING_OR_MONEY_ACTION",
)

JOURNEY_TEMPLATE_CATALOGUE_REDACTIONS = (
    "definition_payload",
    "transition_rules",
    "evidence_requirements",
    "allowed_configuration_schema",
    "payload_hash",
    "tenant_code",
    "account_id",
    "raw_event_payload",
    "provider_payload",
    "secret",
    "credential",
    "auth_claim",
    "billing",
    "wallet",
    "payout",
    "settlement",
    "invoice",
    "money",
)

TEMPLATE_CATALOGUE_STATUS_ORDER = ("APPROVED", "DRAFT", "DISABLED", "ARCHIVED")
TEMPLATE_CATALOGUE_STATUSES = frozenset(TEMPLATE_CATALOGUE_STATUS_ORDER)
DEFAULT_TEMPLATE_CATALOGUE_STATUSES = ("APPROVED", "DRAFT")
MAX_TEMPLATE_CATALOGUE_LIMIT = 100
MAX_CUSTOMER_JOURNEY_DRAFT_LIMIT = 100

CUSTOMER_JOURNEY_DRAFT_GUARDRAILS = (
    "ACCOUNT_SCOPED_CUSTOMER_JOURNEY_DRAFT",
    "APPROVED_TEMPLATE_VERSION_REQUIRED",
    "IDEMPOTENT_DRAFT_COMMANDS",
    "SAFE_CONFIGURATION_PAYLOAD_ONLY",
    "NO_RUNTIME_JOURNEY_MUTATION",
    "NO_CAMPAIGN_BINDING",
    "NO_CAMPAIGN_ACTIVATION",
    "NO_PROVIDER_DISPATCH",
    "NO_AUTH_BILLING_OR_MONEY_ACTION",
)

CUSTOMER_JOURNEY_DRAFT_REDACTIONS = tuple(
    dict.fromkeys(
        (
            *JOURNEY_TEMPLATE_CATALOGUE_REDACTIONS,
            "customer_journey_version_id",
            "campaign_binding_id",
            "runtime_journey_id",
            "api_key",
            "password",
            "webhook_secret",
            "access_token",
            "refresh_token",
            "ucn",
            "raw_ucn",
        )
    )
)

CUSTOMER_JOURNEY_DRAFT_UNSAFE_KEY_TOKENS = tuple(
    str(token).lower() for token in CUSTOMER_JOURNEY_DRAFT_REDACTIONS
)

REWARD_CONFIGURATION_UNSAFE_KEYS = frozenset(
    {
        "amount",
        "cash_value",
        "cashvalue",
        "currency_amount",
        "currencyamount",
        "funding_account",
        "fundingaccount",
        "ledger",
        "money_movement",
        "moneymovement",
        "payment",
        "payout",
        "settlement",
        "wallet",
    }
)

ATTRIBUTION_CONFIGURATION_UNSAFE_KEYS = frozenset(
    {
        "force_credit",
        "forcecredit",
        "manual_override",
        "manualoverride",
        "override",
        "raw_event_payload",
        "raweventpayload",
    }
)


class JourneyTemplateCatalogueValidationError(ValueError):
    pass


class JourneyTemplateNotFound(Exception):
    pass


class CustomerJourneyDraftValidationError(ValueError):
    pass


class CustomerJourneyDraftUnsafePayload(CustomerJourneyDraftValidationError):
    pass


class CustomerJourneyDraftNotFound(Exception):
    pass


class CustomerJourneyDraftIdempotencyConflict(Exception):
    pass


@dataclass(frozen=True)
class JourneyTemplateVersionSummary:
    journey_template_version_id: str
    template_version: str
    status: str
    milestone_count: int
    transition_rule_count: int
    evidence_requirement_count: int
    allowed_configuration_sections: tuple[str, ...]
    approved_by_ref: str | None
    approved_at: datetime | str | None
    created_by_ref: str
    created_at: datetime | str | None
    updated_at: datetime | str | None
    archived_at: datetime | str | None

    def to_safe_dict(self) -> dict[str, Any]:
        return {
            "journeyTemplateVersionId": self.journey_template_version_id,
            "templateVersion": self.template_version,
            "status": self.status,
            "milestoneCount": self.milestone_count,
            "transitionRuleCount": self.transition_rule_count,
            "evidenceRequirementCount": self.evidence_requirement_count,
            "allowedConfigurationSections": list(self.allowed_configuration_sections),
            "approvedByRef": self.approved_by_ref,
            "approvedAt": _isoformat(self.approved_at),
            "createdByRef": self.created_by_ref,
            "createdAt": _isoformat(self.created_at),
            "updatedAt": _isoformat(self.updated_at),
            "archivedAt": _isoformat(self.archived_at),
        }


@dataclass(frozen=True)
class JourneyTemplateCatalogueItem:
    journey_template_id: str
    template_code: str
    template_name: str
    template_family: str
    owner_scope: str
    status: str
    safe_summary: dict[str, Any]
    governance_metadata: dict[str, Any]
    created_by_ref: str
    updated_by_ref: str | None
    created_at: datetime | str | None
    updated_at: datetime | str | None
    archived_at: datetime | str | None
    versions: tuple[JourneyTemplateVersionSummary, ...]

    def to_safe_dict(self) -> dict[str, Any]:
        return {
            "journeyTemplateId": self.journey_template_id,
            "templateCode": self.template_code,
            "templateName": self.template_name,
            "templateFamily": self.template_family,
            "ownerScope": self.owner_scope,
            "status": self.status,
            "safeSummary": self.safe_summary,
            "governanceMetadata": self.governance_metadata,
            "versionCount": len(self.versions),
            "versions": [version.to_safe_dict() for version in self.versions],
            "createdByRef": self.created_by_ref,
            "updatedByRef": self.updated_by_ref,
            "createdAt": _isoformat(self.created_at),
            "updatedAt": _isoformat(self.updated_at),
            "archivedAt": _isoformat(self.archived_at),
        }


@dataclass(frozen=True)
class JourneyTemplateCatalogue:
    templates: tuple[JourneyTemplateCatalogueItem, ...]
    status_filter: tuple[str, ...]
    include_archived: bool

    def to_safe_dict(self) -> dict[str, Any]:
        return {
            "status": "READY" if self.templates else "EMPTY",
            "templateCount": len(self.templates),
            "statusFilter": list(self.status_filter),
            "includeArchived": self.include_archived,
            "templates": [template.to_safe_dict() for template in self.templates],
            "guardrails": list(JOURNEY_TEMPLATE_CATALOGUE_GUARDRAILS),
            "redactions": list(JOURNEY_TEMPLATE_CATALOGUE_REDACTIONS),
            "noTenantDataConfirmed": True,
            "noCustomerConfigurationWriteConfirmed": True,
            "noRuntimeExecutionConfirmed": True,
            "noCampaignBindingConfirmed": True,
            "noProviderAuthBillingOrMoneyActionConfirmed": True,
        }


@dataclass(frozen=True)
class CustomerJourneyDraft:
    customer_journey_draft_id: str
    account_id: str
    journey_template_version_id: str
    template_code: str
    template_version: str
    draft_name: str
    draft_status: str
    draft_version: int
    configuration_payload: dict[str, Any]
    last_validation_status: str
    payload_hash: str
    created_by_ref: str
    updated_by_ref: str | None
    created_at: datetime | str | None
    updated_at: datetime | str | None
    archived_at: datetime | str | None

    def to_safe_dict(self) -> dict[str, Any]:
        return {
            "customerJourneyDraftId": self.customer_journey_draft_id,
            "accountId": self.account_id,
            "journeyTemplateVersionId": self.journey_template_version_id,
            "templateCode": self.template_code,
            "templateVersion": self.template_version,
            "draftName": self.draft_name,
            "draftStatus": self.draft_status,
            "draftVersion": self.draft_version,
            "configurationPayload": _redact_json(self.configuration_payload),
            "lastValidationStatus": self.last_validation_status,
            "payloadHash": self.payload_hash,
            "createdByRef": self.created_by_ref,
            "updatedByRef": self.updated_by_ref,
            "createdAt": _isoformat(self.created_at),
            "updatedAt": _isoformat(self.updated_at),
            "archivedAt": _isoformat(self.archived_at),
            "guardrails": list(CUSTOMER_JOURNEY_DRAFT_GUARDRAILS),
            "redactions": list(CUSTOMER_JOURNEY_DRAFT_REDACTIONS),
            "noRuntimeJourneyMutationConfirmed": True,
            "noCampaignBindingConfirmed": True,
            "noCampaignActivationConfirmed": True,
            "noProviderDispatchConfirmed": True,
            "noAuthBillingOrMoneyActionConfirmed": True,
        }


@dataclass(frozen=True)
class CustomerJourneyDraftCommandResult:
    command_status: str
    draft: CustomerJourneyDraft
    idempotency_status: str

    def to_safe_dict(self) -> dict[str, Any]:
        return {
            "commandStatus": self.command_status,
            "idempotencyStatus": self.idempotency_status,
            "draft": self.draft.to_safe_dict(),
            "guardrails": list(CUSTOMER_JOURNEY_DRAFT_GUARDRAILS),
            "redactions": list(CUSTOMER_JOURNEY_DRAFT_REDACTIONS),
            "noRuntimeJourneyMutationConfirmed": True,
            "noCampaignBindingConfirmed": True,
            "noCampaignActivationConfirmed": True,
            "noProviderDispatchConfirmed": True,
            "noAuthBillingOrMoneyActionConfirmed": True,
        }


@dataclass(frozen=True)
class CustomerJourneyDraftValidationResult:
    journey_validation_result_id: str
    account_id: str
    customer_journey_draft_id: str
    journey_template_version_id: str
    validation_status: str
    blockers: tuple[dict[str, Any], ...]
    warnings: tuple[dict[str, Any], ...]
    safe_summary: dict[str, Any]
    payload_hash: str
    created_at: datetime | str | None

    def to_safe_dict(self) -> dict[str, Any]:
        return {
            "journeyValidationResultId": self.journey_validation_result_id,
            "accountId": self.account_id,
            "customerJourneyDraftId": self.customer_journey_draft_id,
            "journeyTemplateVersionId": self.journey_template_version_id,
            "validationStatus": self.validation_status,
            "blockers": list(self.blockers),
            "warnings": list(self.warnings),
            "safeSummary": self.safe_summary,
            "payloadHash": self.payload_hash,
            "createdAt": _isoformat(self.created_at),
            "guardrails": list(CUSTOMER_JOURNEY_DRAFT_GUARDRAILS),
            "redactions": list(CUSTOMER_JOURNEY_DRAFT_REDACTIONS),
            "noRuntimeJourneyMutationConfirmed": True,
            "noCampaignBindingConfirmed": True,
            "noCampaignActivationConfirmed": True,
            "noProviderDispatchConfirmed": True,
            "noAuthBillingOrMoneyActionConfirmed": True,
        }


def _isoformat(value: datetime | str | None) -> str | None:
    if isinstance(value, datetime):
        return value.isoformat()
    return value


def _row_value(row: Mapping[str, Any], key: str) -> Any:
    return row[key] if key in row else None


def _json_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return _redact_json(value)
    return {}


def _json_sequence_count(value: Any) -> int:
    if isinstance(value, list):
        return len(value)
    if isinstance(value, dict):
        items = value.get("items") or value.get("milestones") or value.get("rules")
        if isinstance(items, list):
            return len(items)
        return len(value)
    return 0


def _json_sequence(value: Any, *preferred_keys: str) -> tuple[Any, ...]:
    if isinstance(value, list):
        return tuple(value)
    if isinstance(value, dict):
        for key in preferred_keys:
            items = value.get(key)
            if isinstance(items, list):
                return tuple(items)
        return tuple(value.values())
    return ()


def _configuration_sections(value: Any) -> tuple[str, ...]:
    if not isinstance(value, dict):
        return ()
    return tuple(sorted(_redact_json(value).keys()))


def _redact_json(value: dict[str, Any]) -> dict[str, Any]:
    redacted: dict[str, Any] = {}
    forbidden = {key.lower() for key in JOURNEY_TEMPLATE_CATALOGUE_REDACTIONS}
    for key, item in value.items():
        key_text = str(key)
        if key_text.lower() in forbidden or any(
            token in key_text.lower()
            for token in (
                "tenant",
                "account_id",
                "secret",
                "credential",
                "auth_claim",
                "billing",
                "wallet",
                "payout",
                "settlement",
                "invoice",
                "money",
                "provider_payload",
                "raw_event_payload",
            )
        ):
            continue
        if isinstance(item, dict):
            redacted[key_text] = _redact_json(item)
        elif isinstance(item, list):
            redacted[key_text] = [
                _redact_json(child) if isinstance(child, dict) else child
                for child in item
            ]
        else:
            redacted[key_text] = item
    return redacted


def _normalise_statuses(
    statuses: Sequence[str] | None,
    *,
    include_archived: bool,
) -> tuple[str, ...]:
    selected = tuple(
        dict.fromkeys(
            str(status).strip().upper()
            for status in (statuses or DEFAULT_TEMPLATE_CATALOGUE_STATUSES)
            if str(status).strip()
        )
    )
    invalid = [status for status in selected if status not in TEMPLATE_CATALOGUE_STATUSES]
    if invalid:
        raise JourneyTemplateCatalogueValidationError(
            f"Unsupported journey template status: {', '.join(invalid)}"
        )

    status_set = set(selected)
    if include_archived:
        status_set.add("ARCHIVED")
    else:
        status_set.discard("ARCHIVED")
    return tuple(status for status in TEMPLATE_CATALOGUE_STATUS_ORDER if status in status_set)


def _safe_limit(limit: int) -> int:
    return max(1, min(int(limit), MAX_TEMPLATE_CATALOGUE_LIMIT))


def _safe_draft_limit(limit: int) -> int:
    return max(1, min(int(limit), MAX_CUSTOMER_JOURNEY_DRAFT_LIMIT))


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def _payload_hash(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _jsonb(value: Any) -> str:
    return json.dumps(value, sort_keys=True, default=str)


def _required_text(
    value: Any,
    field_name: str,
    *,
    min_length: int = 1,
    max_length: int = 240,
) -> str:
    safe = str(value or "").strip()
    if len(safe) < min_length:
        raise CustomerJourneyDraftValidationError(f"{field_name} is required.")
    if len(safe) > max_length:
        raise CustomerJourneyDraftValidationError(
            f"{field_name} must be {max_length} characters or fewer."
        )
    return safe


def _optional_text(value: Any, *, max_length: int = 240) -> str | None:
    if value is None:
        return None
    safe = str(value).strip()
    if not safe:
        return None
    return safe[:max_length]


def _normalise_configuration_payload(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise CustomerJourneyDraftValidationError(
            "configuration_payload must be an object."
        )
    _reject_unsafe_customer_journey_payload(value)
    return _redact_json(value)


def _reject_unsafe_customer_journey_payload(value: Any) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            key_text = str(key).lower()
            if any(token in key_text for token in CUSTOMER_JOURNEY_DRAFT_UNSAFE_KEY_TOKENS):
                raise CustomerJourneyDraftUnsafePayload(
                    "Journey draft configuration contains a field reserved for "
                    "tenant, runtime, provider, auth, billing, credential, or "
                    "money workflows."
                )
            _reject_unsafe_customer_journey_payload(child)
    elif isinstance(value, list):
        for item in value:
            _reject_unsafe_customer_journey_payload(item)


def _normalise_code(value: Any) -> str | None:
    if value is None:
        return None
    safe = str(value).strip().upper().replace("-", "_").replace(" ", "_")
    return safe or None


def _extract_code(item: Any, *keys: str) -> str | None:
    if isinstance(item, str):
        return _normalise_code(item)
    if isinstance(item, dict):
        for key in keys:
            if key in item:
                return _normalise_code(item.get(key))
    return None


def _extract_milestone_codes(value: Any) -> tuple[str, ...]:
    codes: list[str] = []
    for item in _json_sequence(value, "milestones", "items"):
        code = _extract_code(item, "code", "milestoneCode", "milestone_code", "id")
        if code and code not in codes:
            codes.append(code)
    return tuple(codes)


def _extract_transition_pairs(value: Any) -> tuple[tuple[str, str], ...]:
    pairs: list[tuple[str, str]] = []
    for item in _json_sequence(value, "transitions", "rules", "items"):
        if not isinstance(item, dict):
            continue
        from_code = _extract_code(
            item, "from", "fromMilestone", "from_milestone", "fromStatus", "from_status"
        )
        to_code = _extract_code(
            item, "to", "toMilestone", "to_milestone", "toStatus", "to_status"
        )
        if from_code and to_code and (from_code, to_code) not in pairs:
            pairs.append((from_code, to_code))
    return tuple(pairs)


def _extract_required_evidence_codes(value: Any) -> tuple[str, ...]:
    codes: list[str] = []
    for item in _json_sequence(value, "evidence", "requirements", "items"):
        if isinstance(item, dict) and item.get("required") is False:
            continue
        code = _extract_code(item, "code", "evidenceCode", "evidence_code", "id")
        if code and code not in codes:
            codes.append(code)
    return tuple(codes)


def _configured_milestone_codes(configuration_payload: Mapping[str, Any]) -> tuple[str, ...]:
    configured = configuration_payload.get("milestones")
    if configured is None:
        configured = configuration_payload.get("enabledMilestones")
    return _extract_milestone_codes(configured)


def _configured_transition_pairs(
    configuration_payload: Mapping[str, Any],
) -> tuple[tuple[str, str], ...]:
    configured = configuration_payload.get("transitions")
    if configured is None:
        configured = configuration_payload.get("transitionRules")
    return _extract_transition_pairs(configured)


def _configured_evidence_codes(configuration_payload: Mapping[str, Any]) -> tuple[str, ...]:
    configured = configuration_payload.get("evidence")
    if configured is None:
        configured = configuration_payload.get("evidenceRequirements")
    if configured is None:
        configured = configuration_payload.get("requiredEvidence")
    return _extract_required_evidence_codes(configured)


def _iter_dicts(value: Any) -> tuple[dict[str, Any], ...]:
    if isinstance(value, dict):
        return (value,)
    if isinstance(value, list):
        return tuple(item for item in value if isinstance(item, dict))
    return ()


def _contains_key(value: Any, keys: frozenset[str]) -> bool:
    if isinstance(value, dict):
        for key, child in value.items():
            normalised_key = str(key).strip().lower().replace("-", "_")
            if normalised_key in keys:
                return True
            if _contains_key(child, keys):
                return True
    elif isinstance(value, list):
        return any(_contains_key(item, keys) for item in value)
    return False


def _validate_reward_safety(
    configuration_payload: Mapping[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], str]:
    rewards = configuration_payload.get("rewards")
    if rewards is None:
        return [], [], "NOT_CONFIGURED"
    if not isinstance(rewards, (dict, list)):
        return [
            {
                "code": "INVALID_REWARD_CONFIGURATION",
                "message": "Reward configuration must be an object or list of objects.",
            }
        ], [], "BLOCKED"
    if _contains_key(rewards, REWARD_CONFIGURATION_UNSAFE_KEYS):
        return [
            {
                "code": "UNSAFE_REWARD_SETTING",
                "message": (
                    "Reward configuration may reference approved policy codes only. "
                    "Cash values, payouts, wallets, funding, or settlement settings "
                    "must stay in governed reward and money workflows."
                ),
            }
        ], [], "BLOCKED"
    warnings: list[dict[str, Any]] = []
    if not any(
        any(key in reward for key in ("policyCode", "policy_code", "rewardPolicyRef"))
        for reward in _iter_dicts(rewards)
    ):
        warnings.append(
            {
                "code": "REWARD_POLICY_REFERENCE_NOT_SUPPLIED",
                "message": (
                    "Reward settings do not reference an approved reward policy. "
                    "Template defaults will be used until a policy reference is supplied."
                ),
            }
        )
    return [], warnings, "PASSED_WITH_WARNINGS" if warnings else "PASSED"


def _validate_attribution_safety(
    configuration_payload: Mapping[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], str]:
    attribution = configuration_payload.get("attribution")
    if attribution is None:
        return [], [], "NOT_CONFIGURED"
    if not isinstance(attribution, dict):
        return [
            {
                "code": "INVALID_ATTRIBUTION_CONFIGURATION",
                "message": "Attribution configuration must be an object.",
            }
        ], [], "BLOCKED"

    blockers: list[dict[str, Any]] = []
    if _contains_key(attribution, ATTRIBUTION_CONFIGURATION_UNSAFE_KEYS):
        blockers.append(
            {
                "code": "UNSAFE_ATTRIBUTION_SETTING",
                "message": (
                    "Attribution settings cannot force credit, override attribution, "
                    "or include raw event payloads in the customer journey draft."
                ),
            }
        )

    window = attribution.get("windowDays", attribution.get("lookbackDays"))
    if window is not None:
        try:
            window_days = int(window)
        except (TypeError, ValueError):
            window_days = 0
        if window_days < 1 or window_days > 90:
            blockers.append(
                {
                    "code": "ATTRIBUTION_WINDOW_OUT_OF_RANGE",
                    "message": "Attribution lookback windows must be between 1 and 90 days.",
                }
            )
    return blockers, [], "BLOCKED" if blockers else "PASSED"


def _draft_from_row(row: Mapping[str, Any]) -> CustomerJourneyDraft:
    return CustomerJourneyDraft(
        customer_journey_draft_id=str(_row_value(row, "customer_journey_draft_id")),
        account_id=str(_row_value(row, "account_id")),
        journey_template_version_id=str(_row_value(row, "journey_template_version_id")),
        template_code=str(_row_value(row, "template_code")),
        template_version=str(_row_value(row, "template_version")),
        draft_name=str(_row_value(row, "draft_name")),
        draft_status=str(_row_value(row, "draft_status")),
        draft_version=int(_row_value(row, "draft_version") or 1),
        configuration_payload=_json_dict(_row_value(row, "configuration_payload")),
        last_validation_status=str(_row_value(row, "last_validation_status")),
        payload_hash=str(_row_value(row, "payload_hash")),
        created_by_ref=str(_row_value(row, "created_by_ref")),
        updated_by_ref=_row_value(row, "updated_by_ref"),
        created_at=_row_value(row, "created_at"),
        updated_at=_row_value(row, "updated_at"),
        archived_at=_row_value(row, "archived_at"),
    )


def _validation_result_from_row(
    row: Mapping[str, Any],
) -> CustomerJourneyDraftValidationResult:
    blockers = _row_value(row, "blockers")
    warnings = _row_value(row, "warnings")
    return CustomerJourneyDraftValidationResult(
        journey_validation_result_id=str(_row_value(row, "journey_validation_result_id")),
        account_id=str(_row_value(row, "account_id")),
        customer_journey_draft_id=str(_row_value(row, "customer_journey_draft_id")),
        journey_template_version_id=str(_row_value(row, "journey_template_version_id")),
        validation_status=str(_row_value(row, "validation_status")),
        blockers=tuple(blocker for blocker in blockers if isinstance(blocker, dict))
        if isinstance(blockers, list)
        else (),
        warnings=tuple(warning for warning in warnings if isinstance(warning, dict))
        if isinstance(warnings, list)
        else (),
        safe_summary=_json_dict(_row_value(row, "safe_summary")),
        payload_hash=str(_row_value(row, "payload_hash")),
        created_at=_row_value(row, "created_at"),
    )


async def _find_approved_template_version(
    conn: Any,
    *,
    template_code: str,
    template_version: str | None,
) -> Mapping[str, Any]:
    if template_version:
        row = await conn.fetchrow(
            """
            SELECT *
            FROM referral_saas_journey_template_versions
            WHERE UPPER(template_code) = UPPER($1)
              AND template_version = $2
              AND status = 'APPROVED'
              AND archived_at IS NULL
            LIMIT 1
            """,
            template_code,
            template_version,
        )
    else:
        row = await conn.fetchrow(
            """
            SELECT *
            FROM referral_saas_journey_template_versions
            WHERE UPPER(template_code) = UPPER($1)
              AND status = 'APPROVED'
              AND archived_at IS NULL
            ORDER BY created_at DESC, template_version DESC
            LIMIT 1
            """,
            template_code,
        )
    if not row:
        raise JourneyTemplateNotFound(template_code)
    return row


def _validate_configuration_against_schema(
    configuration_payload: Mapping[str, Any],
    allowed_configuration_schema: Any,
    milestone_schema: Any,
    transition_rules: Any,
    evidence_requirements: Any,
) -> tuple[str, list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    blockers: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    allowed_sections = set(_configuration_sections(allowed_configuration_schema))
    supplied_sections = set(configuration_payload.keys())
    template_milestones = _extract_milestone_codes(milestone_schema)
    template_transitions = _extract_transition_pairs(transition_rules)
    template_required_evidence = _extract_required_evidence_codes(
        evidence_requirements
    )
    configured_milestones = _configured_milestone_codes(configuration_payload)
    configured_transitions = _configured_transition_pairs(configuration_payload)
    configured_evidence = _configured_evidence_codes(configuration_payload)

    if allowed_sections:
        unknown_sections = sorted(supplied_sections.difference(allowed_sections))
        if unknown_sections:
            warnings.append(
                {
                    "code": "UNKNOWN_CONFIGURATION_SECTION",
                    "message": (
                        "Configuration includes sections not defined by the approved "
                        "template schema."
                    ),
                    "sections": unknown_sections,
                }
            )

    if not supplied_sections:
        warnings.append(
            {
                "code": "EMPTY_CONFIGURATION",
                "message": (
                    "No customer-specific journey settings were supplied. Template "
                    "defaults will be used until configuration is added."
                ),
            }
        )

    if not template_milestones:
        blockers.append(
            {
                "code": "TEMPLATE_MILESTONES_MISSING",
                "message": (
                    "The approved template version does not expose milestone codes "
                    "that can be safely simulated."
                ),
            }
        )

    milestone_set = set(template_milestones)
    for from_code, to_code in template_transitions:
        missing = sorted({from_code, to_code}.difference(milestone_set))
        if missing:
            blockers.append(
                {
                    "code": "INVALID_TEMPLATE_TRANSITION",
                    "message": (
                        "The approved template contains transition rules that point "
                        "to milestones not present in the milestone schema."
                    ),
                    "transition": {"from": from_code, "to": to_code},
                    "missingMilestones": missing,
                }
            )

    if len(template_milestones) > 1 and not template_transitions:
        warnings.append(
            {
                "code": "TEMPLATE_TRANSITIONS_NOT_SUPPLIED",
                "message": (
                    "The approved template has more than one milestone but does not "
                    "expose transition rules. Simulation can only show milestone order."
                ),
            }
        )

    unknown_configured_milestones = sorted(
        set(configured_milestones).difference(milestone_set)
    )
    if unknown_configured_milestones:
        blockers.append(
            {
                "code": "UNKNOWN_MILESTONE",
                "message": (
                    "Customer configuration references milestone codes outside the "
                    "approved template version."
                ),
                "milestones": unknown_configured_milestones,
            }
        )

    transition_set = set(template_transitions)
    invalid_configured_transitions = [
        {"from": from_code, "to": to_code}
        for from_code, to_code in configured_transitions
        if (from_code, to_code) not in transition_set
    ]
    if invalid_configured_transitions:
        blockers.append(
            {
                "code": "INVALID_CUSTOMER_TRANSITION",
                "message": (
                    "Customer configuration includes transition rules that are not "
                    "allowed by the approved template version."
                ),
                "transitions": invalid_configured_transitions,
            }
        )

    template_evidence_set = set(template_required_evidence)
    unknown_configured_evidence = sorted(
        set(configured_evidence).difference(template_evidence_set)
    )
    if unknown_configured_evidence:
        blockers.append(
            {
                "code": "UNKNOWN_EVIDENCE_REQUIREMENT",
                "message": (
                    "Customer configuration references evidence requirements outside "
                    "the approved template version."
                ),
                "evidence": unknown_configured_evidence,
            }
        )

    if template_required_evidence and configured_evidence:
        missing_evidence = sorted(template_evidence_set.difference(configured_evidence))
        if missing_evidence:
            blockers.append(
                {
                    "code": "REQUIRED_EVIDENCE_MISSING",
                    "message": (
                        "Customer configuration omits required evidence from the "
                        "approved template version."
                    ),
                    "evidence": missing_evidence,
                }
            )
    elif template_required_evidence:
        warnings.append(
            {
                "code": "REQUIRED_EVIDENCE_USES_TEMPLATE_DEFAULTS",
                "message": (
                    "Required evidence is defined by the approved template. Customer "
                    "configuration does not override it."
                ),
                "evidenceCount": len(template_required_evidence),
            }
        )

    reward_blockers, reward_warnings, reward_status = _validate_reward_safety(
        configuration_payload
    )
    attribution_blockers, attribution_warnings, attribution_status = (
        _validate_attribution_safety(configuration_payload)
    )
    blockers.extend(reward_blockers)
    blockers.extend(attribution_blockers)
    warnings.extend(reward_warnings)
    warnings.extend(attribution_warnings)

    status = "PASSED"
    if blockers:
        status = "BLOCKED"
    elif warnings:
        status = "PASSED_WITH_WARNINGS"

    transition_blocked = any(
        blocker["code"] in {"INVALID_TEMPLATE_TRANSITION", "INVALID_CUSTOMER_TRANSITION"}
        for blocker in blockers
    )
    evidence_warned = any(
        warning["code"] == "REQUIRED_EVIDENCE_USES_TEMPLATE_DEFAULTS"
        for warning in warnings
    )
    evidence_blocked = any(
        blocker["code"] in {"UNKNOWN_EVIDENCE_REQUIREMENT", "REQUIRED_EVIDENCE_MISSING"}
        for blocker in blockers
    )
    simulated_path = list(configured_milestones or template_milestones)
    safe_summary = {
        "configurationSectionCount": len(supplied_sections),
        "configurationSections": sorted(supplied_sections),
        "allowedConfigurationSections": sorted(allowed_sections),
        "templateMilestoneCount": len(template_milestones),
        "templateTransitionCount": len(template_transitions),
        "templateRequiredEvidenceCount": len(template_required_evidence),
        "configuredMilestoneCount": len(configured_milestones),
        "configuredTransitionCount": len(configured_transitions),
        "configuredEvidenceCount": len(configured_evidence),
        "transitionCheckStatus": "BLOCKED" if transition_blocked else "PASSED",
        "evidenceCheckStatus": "BLOCKED"
        if evidence_blocked
        else "PASSED_WITH_WARNINGS"
        if evidence_warned
        else "PASSED",
        "rewardSafetyStatus": reward_status,
        "attributionSafetyStatus": attribution_status,
        "simulation": {
            "status": status,
            "canPublish": status != "BLOCKED",
            "canBindCampaign": False,
            "simulatedMilestonePath": simulated_path,
            "customerReadableSummary": (
                "This journey draft can be reviewed for publish readiness."
                if status != "BLOCKED"
                else "This journey draft needs fixes before it can be published."
            ),
            "nextAction": (
                "Review warnings and continue to governed publish controls."
                if status != "BLOCKED"
                else "Resolve blockers, then validate the journey draft again."
            ),
        },
        "blockerCount": len(blockers),
        "warningCount": len(warnings),
        "noRuntimeJourneyMutationConfirmed": True,
        "noCampaignBindingConfirmed": True,
        "noCampaignActivationConfirmed": True,
        "noProviderDispatchConfirmed": True,
        "noAuthBillingOrMoneyActionConfirmed": True,
    }
    return status, blockers, warnings, safe_summary


def _build_catalogue(
    rows: Sequence[Mapping[str, Any]],
    *,
    status_filter: tuple[str, ...],
    include_archived: bool,
) -> JourneyTemplateCatalogue:
    template_order: list[str] = []
    templates: dict[str, dict[str, Any]] = {}

    for row in rows:
        template_code = str(_row_value(row, "template_code"))
        if template_code not in templates:
            template_order.append(template_code)
            templates[template_code] = {
                "journey_template_id": str(_row_value(row, "journey_template_id")),
                "template_code": template_code,
                "template_name": str(_row_value(row, "template_name")),
                "template_family": str(_row_value(row, "template_family")),
                "owner_scope": str(_row_value(row, "owner_scope")),
                "status": str(_row_value(row, "template_status")),
                "safe_summary": _json_dict(_row_value(row, "safe_summary")),
                "governance_metadata": _json_dict(
                    _row_value(row, "governance_metadata")
                ),
                "created_by_ref": str(_row_value(row, "template_created_by_ref")),
                "updated_by_ref": _row_value(row, "template_updated_by_ref"),
                "created_at": _row_value(row, "template_created_at"),
                "updated_at": _row_value(row, "template_updated_at"),
                "archived_at": _row_value(row, "template_archived_at"),
                "versions": [],
            }

        if _row_value(row, "journey_template_version_id") is not None:
            templates[template_code]["versions"].append(
                JourneyTemplateVersionSummary(
                    journey_template_version_id=str(
                        _row_value(row, "journey_template_version_id")
                    ),
                    template_version=str(_row_value(row, "template_version")),
                    status=str(_row_value(row, "version_status")),
                    milestone_count=_json_sequence_count(
                        _row_value(row, "milestone_schema")
                    ),
                    transition_rule_count=_json_sequence_count(
                        _row_value(row, "transition_rules")
                    ),
                    evidence_requirement_count=_json_sequence_count(
                        _row_value(row, "evidence_requirements")
                    ),
                    allowed_configuration_sections=_configuration_sections(
                        _row_value(row, "allowed_configuration_schema")
                    ),
                    approved_by_ref=_row_value(row, "approved_by_ref"),
                    approved_at=_row_value(row, "approved_at"),
                    created_by_ref=str(_row_value(row, "version_created_by_ref")),
                    created_at=_row_value(row, "version_created_at"),
                    updated_at=_row_value(row, "version_updated_at"),
                    archived_at=_row_value(row, "version_archived_at"),
                )
            )

    return JourneyTemplateCatalogue(
        templates=tuple(
            JourneyTemplateCatalogueItem(
                **{
                    **templates[template_code],
                    "versions": tuple(templates[template_code]["versions"]),
                }
            )
            for template_code in template_order
        ),
        status_filter=status_filter,
        include_archived=include_archived,
    )


async def list_referral_saas_journey_templates(
    *,
    statuses: Sequence[str] | None = None,
    include_archived: bool = False,
    limit: int = 50,
) -> JourneyTemplateCatalogue:
    status_filter = _normalise_statuses(statuses, include_archived=include_archived)
    query = """
        SELECT
            t.journey_template_id,
            t.template_code,
            t.template_name,
            t.template_family,
            t.owner_scope,
            t.status AS template_status,
            t.safe_summary,
            t.governance_metadata,
            t.created_by_ref AS template_created_by_ref,
            t.updated_by_ref AS template_updated_by_ref,
            t.created_at AS template_created_at,
            t.updated_at AS template_updated_at,
            t.archived_at AS template_archived_at,
            v.journey_template_version_id,
            v.template_version,
            v.status AS version_status,
            v.milestone_schema,
            v.transition_rules,
            v.evidence_requirements,
            v.allowed_configuration_schema,
            v.approved_by_ref,
            v.approved_at,
            v.created_by_ref AS version_created_by_ref,
            v.created_at AS version_created_at,
            v.updated_at AS version_updated_at,
            v.archived_at AS version_archived_at
        FROM referral_saas_journey_templates t
        LEFT JOIN referral_saas_journey_template_versions v
            ON v.journey_template_id = t.journey_template_id
            AND v.status = ANY($2::text[])
        WHERE t.status = ANY($1::text[])
        ORDER BY t.updated_at DESC, t.template_code ASC, v.template_version DESC
        LIMIT $3
    """
    async with db_connection() as conn:
        rows = await conn.fetch(
            query,
            list(status_filter),
            list(status_filter),
            _safe_limit(limit),
        )

    return _build_catalogue(
        rows,
        status_filter=status_filter,
        include_archived=include_archived,
    )


async def get_referral_saas_journey_template(
    *,
    template_code: str,
    statuses: Sequence[str] | None = None,
    include_archived: bool = False,
) -> JourneyTemplateCatalogueItem:
    status_filter = _normalise_statuses(statuses, include_archived=include_archived)
    query = """
        SELECT
            t.journey_template_id,
            t.template_code,
            t.template_name,
            t.template_family,
            t.owner_scope,
            t.status AS template_status,
            t.safe_summary,
            t.governance_metadata,
            t.created_by_ref AS template_created_by_ref,
            t.updated_by_ref AS template_updated_by_ref,
            t.created_at AS template_created_at,
            t.updated_at AS template_updated_at,
            t.archived_at AS template_archived_at,
            v.journey_template_version_id,
            v.template_version,
            v.status AS version_status,
            v.milestone_schema,
            v.transition_rules,
            v.evidence_requirements,
            v.allowed_configuration_schema,
            v.approved_by_ref,
            v.approved_at,
            v.created_by_ref AS version_created_by_ref,
            v.created_at AS version_created_at,
            v.updated_at AS version_updated_at,
            v.archived_at AS version_archived_at
        FROM referral_saas_journey_templates t
        LEFT JOIN referral_saas_journey_template_versions v
            ON v.journey_template_id = t.journey_template_id
            AND v.status = ANY($2::text[])
        WHERE t.status = ANY($1::text[])
            AND UPPER(t.template_code) = UPPER($3)
        ORDER BY v.template_version DESC
    """
    async with db_connection() as conn:
        rows = await conn.fetch(
            query,
            list(status_filter),
            list(status_filter),
            template_code,
        )

    catalogue = _build_catalogue(
        rows,
        status_filter=status_filter,
        include_archived=include_archived,
    )
    if not catalogue.templates:
        raise JourneyTemplateNotFound(template_code)
    return catalogue.templates[0]


async def list_referral_saas_customer_journey_drafts(
    *,
    account_id: str,
    include_archived: bool = False,
    limit: int = 50,
) -> tuple[CustomerJourneyDraft, ...]:
    safe_account_id = _required_text(account_id, "account_id", max_length=80)
    archived_clause = "" if include_archived else "AND d.archived_at IS NULL"
    query = f"""
        SELECT
            d.*,
            v.template_code,
            v.template_version
        FROM referral_saas_customer_journey_drafts d
        JOIN referral_saas_journey_template_versions v
            ON v.journey_template_version_id = d.journey_template_version_id
        WHERE d.account_id = $1
        {archived_clause}
        ORDER BY d.updated_at DESC, d.created_at DESC
        LIMIT $2
    """
    async with db_connection() as conn:
        rows = await conn.fetch(query, safe_account_id, _safe_draft_limit(limit))
    return tuple(_draft_from_row(row) for row in rows)


async def save_referral_saas_customer_journey_draft(
    *,
    account_id: str,
    template_code: str,
    template_version: str | None,
    draft_name: str,
    configuration_payload: Mapping[str, Any] | None,
    customer_journey_draft_id: str | None = None,
    idempotency_key_hash: str,
    request_payload_hash: str,
    actor_ref: str,
    actor_role: str | None,
    correlation_id: str | None = None,
) -> CustomerJourneyDraftCommandResult:
    safe_account_id = _required_text(account_id, "account_id", max_length=80)
    safe_template_code = _required_text(
        template_code, "template_code", max_length=120
    )
    safe_template_version = _optional_text(template_version, max_length=80)
    safe_draft_name = _required_text(draft_name, "draft_name", max_length=180)
    safe_payload = _normalise_configuration_payload(configuration_payload)
    safe_idempotency_hash = _required_text(
        idempotency_key_hash, "idempotency_key_hash", max_length=256
    )
    safe_request_hash = _required_text(
        request_payload_hash, "request_payload_hash", max_length=256
    )
    safe_actor_ref = _required_text(actor_ref, "actor_ref", max_length=160)
    safe_actor_role = _optional_text(actor_role, max_length=80)
    safe_correlation_id = _optional_text(correlation_id, max_length=160)
    safe_draft_id = _optional_text(customer_journey_draft_id, max_length=80)
    payload_hash = _payload_hash(safe_payload)

    async with db_connection() as conn:
        existing_idempotency = await conn.fetchrow(
            """
            SELECT *
            FROM referral_saas_journey_configuration_idempotency_keys
            WHERE account_id = $1
              AND operation_type = 'CUSTOMER_JOURNEY_DRAFT_SAVE'
              AND idempotency_key_hash = $2
            LIMIT 1
            """,
            safe_account_id,
            safe_idempotency_hash,
        )
        if existing_idempotency:
            if (
                _row_value(existing_idempotency, "request_payload_hash")
                != safe_request_hash
            ):
                raise CustomerJourneyDraftIdempotencyConflict(
                    "Idempotency key was reused with different journey draft content."
                )
            draft_row = await conn.fetchrow(
                """
                SELECT
                    d.*,
                    v.template_code,
                    v.template_version
                FROM referral_saas_customer_journey_drafts d
                JOIN referral_saas_journey_template_versions v
                    ON v.journey_template_version_id = d.journey_template_version_id
                WHERE d.customer_journey_draft_id = $1
                  AND d.account_id = $2
                LIMIT 1
                """,
                _row_value(existing_idempotency, "resource_id"),
                safe_account_id,
            )
            if not draft_row:
                raise CustomerJourneyDraftNotFound(
                    str(_row_value(existing_idempotency, "resource_id"))
                )
            return CustomerJourneyDraftCommandResult(
                command_status="REPLAY_SAME_PAYLOAD",
                draft=_draft_from_row(draft_row),
                idempotency_status="REPLAY_SAME_PAYLOAD",
            )

        template = await _find_approved_template_version(
            conn,
            template_code=safe_template_code,
            template_version=safe_template_version,
        )

        async with conn.transaction():
            if safe_draft_id:
                row = await conn.fetchrow(
                    """
                    UPDATE referral_saas_customer_journey_drafts
                    SET journey_template_version_id = $3,
                        draft_name = $4,
                        draft_status = 'DRAFT',
                        draft_version = draft_version + 1,
                        configuration_payload = $5::jsonb,
                        payload_hash = $6,
                        last_validation_status = 'NOT_VALIDATED',
                        idempotency_key_hash = $7,
                        correlation_id = $8,
                        updated_by_ref = $9,
                        updated_at = now()
                    WHERE customer_journey_draft_id = $1
                      AND account_id = $2
                      AND archived_at IS NULL
                      AND draft_status <> 'PUBLISHED'
                    RETURNING *
                    """,
                    safe_draft_id,
                    safe_account_id,
                    _row_value(template, "journey_template_version_id"),
                    safe_draft_name,
                    _jsonb(safe_payload),
                    payload_hash,
                    safe_idempotency_hash,
                    safe_correlation_id,
                    safe_actor_ref,
                )
                if not row:
                    raise CustomerJourneyDraftNotFound(safe_draft_id)
                event_type = "CUSTOMER_JOURNEY_DRAFT_UPDATED"
            else:
                row = await conn.fetchrow(
                    """
                    INSERT INTO referral_saas_customer_journey_drafts (
                        account_id,
                        journey_template_version_id,
                        draft_name,
                        draft_status,
                        draft_version,
                        configuration_payload,
                        payload_hash,
                        last_validation_status,
                        idempotency_key_hash,
                        correlation_id,
                        created_by_ref,
                        updated_by_ref
                    )
                    VALUES (
                        $1, $2, $3, 'DRAFT', 1, $4::jsonb, $5,
                        'NOT_VALIDATED', $6, $7, $8, $8
                    )
                    RETURNING *
                    """,
                    safe_account_id,
                    _row_value(template, "journey_template_version_id"),
                    safe_draft_name,
                    _jsonb(safe_payload),
                    payload_hash,
                    safe_idempotency_hash,
                    safe_correlation_id,
                    safe_actor_ref,
                )
                event_type = "CUSTOMER_JOURNEY_DRAFT_CREATED"

            draft_id = str(_row_value(row, "customer_journey_draft_id"))
            await conn.execute(
                """
                INSERT INTO referral_saas_journey_configuration_idempotency_keys (
                    account_id,
                    operation_type,
                    idempotency_key_hash,
                    request_payload_hash,
                    response_payload_hash,
                    resource_type,
                    resource_id,
                    response_status
                )
                VALUES ($1, 'CUSTOMER_JOURNEY_DRAFT_SAVE', $2, $3, $4,
                        'CUSTOMER_JOURNEY_DRAFT', $5, 'SUCCESS')
                """,
                safe_account_id,
                safe_idempotency_hash,
                safe_request_hash,
                _payload_hash({"customerJourneyDraftId": draft_id}),
                draft_id,
            )
            await conn.execute(
                """
                INSERT INTO referral_saas_journey_configuration_audit (
                    account_id,
                    journey_template_version_id,
                    customer_journey_draft_id,
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
                    $1, $2, $3, $4, 'RECORDED', $5, $6, NULL, 'DRAFT',
                    'CUSTOMER_JOURNEY_DRAFT_SAVE', $7, $8, $9::jsonb, $10::jsonb
                )
                """,
                safe_account_id,
                _row_value(template, "journey_template_version_id"),
                draft_id,
                event_type,
                safe_actor_ref,
                safe_actor_role,
                safe_correlation_id,
                safe_idempotency_hash,
                _jsonb(
                    {
                        "templateCode": safe_template_code,
                        "templateVersion": str(_row_value(template, "template_version")),
                        "payloadHash": payload_hash,
                    }
                ),
                _jsonb(CUSTOMER_JOURNEY_DRAFT_REDACTIONS),
            )

        draft_row = await conn.fetchrow(
            """
            SELECT
                d.*,
                v.template_code,
                v.template_version
            FROM referral_saas_customer_journey_drafts d
            JOIN referral_saas_journey_template_versions v
                ON v.journey_template_version_id = d.journey_template_version_id
            WHERE d.customer_journey_draft_id = $1
              AND d.account_id = $2
            LIMIT 1
            """,
            draft_id,
            safe_account_id,
        )

    if not draft_row:
        raise CustomerJourneyDraftNotFound(draft_id)
    return CustomerJourneyDraftCommandResult(
        command_status="DRAFT_SAVED",
        draft=_draft_from_row(draft_row),
        idempotency_status="NEW_REQUEST",
    )


async def validate_referral_saas_customer_journey_draft(
    *,
    account_id: str,
    customer_journey_draft_id: str,
    idempotency_key_hash: str,
    request_payload_hash: str,
    actor_ref: str,
    actor_role: str | None,
    correlation_id: str | None = None,
) -> CustomerJourneyDraftValidationResult:
    safe_account_id = _required_text(account_id, "account_id", max_length=80)
    safe_draft_id = _required_text(
        customer_journey_draft_id, "customer_journey_draft_id", max_length=80
    )
    safe_idempotency_hash = _required_text(
        idempotency_key_hash, "idempotency_key_hash", max_length=256
    )
    safe_request_hash = _required_text(
        request_payload_hash, "request_payload_hash", max_length=256
    )
    safe_actor_ref = _required_text(actor_ref, "actor_ref", max_length=160)
    safe_actor_role = _optional_text(actor_role, max_length=80)
    safe_correlation_id = _optional_text(correlation_id, max_length=160)

    async with db_connection() as conn:
        existing_idempotency = await conn.fetchrow(
            """
            SELECT *
            FROM referral_saas_journey_configuration_idempotency_keys
            WHERE account_id = $1
              AND operation_type = 'CUSTOMER_JOURNEY_DRAFT_VALIDATE'
              AND idempotency_key_hash = $2
            LIMIT 1
            """,
            safe_account_id,
            safe_idempotency_hash,
        )
        if existing_idempotency:
            if (
                _row_value(existing_idempotency, "request_payload_hash")
                != safe_request_hash
            ):
                raise CustomerJourneyDraftIdempotencyConflict(
                    "Idempotency key was reused with different journey validation content."
                )
            validation_row = await conn.fetchrow(
                """
                SELECT *
                FROM referral_saas_journey_validation_results
                WHERE journey_validation_result_id = $1
                  AND account_id = $2
                LIMIT 1
                """,
                _row_value(existing_idempotency, "resource_id"),
                safe_account_id,
            )
            if not validation_row:
                raise CustomerJourneyDraftNotFound(
                    str(_row_value(existing_idempotency, "resource_id"))
                )
            return _validation_result_from_row(validation_row)

        draft_row = await conn.fetchrow(
            """
            SELECT
                d.*,
                v.template_code,
                v.template_version,
                v.status AS version_status,
                v.milestone_schema,
                v.transition_rules,
                v.evidence_requirements,
                v.allowed_configuration_schema
            FROM referral_saas_customer_journey_drafts d
            JOIN referral_saas_journey_template_versions v
                ON v.journey_template_version_id = d.journey_template_version_id
            WHERE d.customer_journey_draft_id = $1
              AND d.account_id = $2
              AND d.archived_at IS NULL
            LIMIT 1
            """,
            safe_draft_id,
            safe_account_id,
        )
        if not draft_row:
            raise CustomerJourneyDraftNotFound(safe_draft_id)
        if _row_value(draft_row, "version_status") != "APPROVED":
            raise CustomerJourneyDraftValidationError(
                "Journey draft must reference an approved template version."
            )

        configuration_payload = _normalise_configuration_payload(
            _row_value(draft_row, "configuration_payload")
        )
        validation_status, blockers, warnings, safe_summary = (
            _validate_configuration_against_schema(
                configuration_payload,
                _row_value(draft_row, "allowed_configuration_schema"),
                _row_value(draft_row, "milestone_schema"),
                _row_value(draft_row, "transition_rules"),
                _row_value(draft_row, "evidence_requirements"),
            )
        )
        next_draft_status = (
            "VALIDATION_FAILED" if validation_status == "BLOCKED" else "VALIDATED"
        )

        async with conn.transaction():
            validation_row = await conn.fetchrow(
                """
                INSERT INTO referral_saas_journey_validation_results (
                    account_id,
                    customer_journey_draft_id,
                    journey_template_version_id,
                    validation_status,
                    blockers,
                    warnings,
                    safe_summary,
                    payload_hash,
                    idempotency_key_hash,
                    correlation_id,
                    validated_by_ref
                )
                VALUES (
                    $1, $2, $3, $4, $5::jsonb, $6::jsonb, $7::jsonb,
                    $8, $9, $10, $11
                )
                RETURNING *
                """,
                safe_account_id,
                safe_draft_id,
                _row_value(draft_row, "journey_template_version_id"),
                validation_status,
                _jsonb(blockers),
                _jsonb(warnings),
                _jsonb(safe_summary),
                _row_value(draft_row, "payload_hash"),
                safe_idempotency_hash,
                safe_correlation_id,
                safe_actor_ref,
            )
            validation_id = str(_row_value(validation_row, "journey_validation_result_id"))
            await conn.execute(
                """
                UPDATE referral_saas_customer_journey_drafts
                SET last_validation_status = $3,
                    draft_status = $4,
                    updated_by_ref = $5,
                    updated_at = now()
                WHERE customer_journey_draft_id = $1
                  AND account_id = $2
                """,
                safe_draft_id,
                safe_account_id,
                validation_status,
                next_draft_status,
                safe_actor_ref,
            )
            await conn.execute(
                """
                INSERT INTO referral_saas_journey_configuration_idempotency_keys (
                    account_id,
                    operation_type,
                    idempotency_key_hash,
                    request_payload_hash,
                    response_payload_hash,
                    resource_type,
                    resource_id,
                    response_status
                )
                VALUES ($1, 'CUSTOMER_JOURNEY_DRAFT_VALIDATE', $2, $3, $4,
                        'CUSTOMER_JOURNEY_VALIDATION_RESULT', $5, 'SUCCESS')
                """,
                safe_account_id,
                safe_idempotency_hash,
                safe_request_hash,
                _payload_hash({"journeyValidationResultId": validation_id}),
                validation_id,
            )
            await conn.execute(
                """
                INSERT INTO referral_saas_journey_configuration_audit (
                    account_id,
                    journey_template_version_id,
                    customer_journey_draft_id,
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
                    $1, $2, $3, 'CUSTOMER_JOURNEY_DRAFT_VALIDATED',
                    'RECORDED', $4, $5, $6, $7,
                    'CUSTOMER_JOURNEY_DRAFT_VALIDATE', $8, $9, $10::jsonb,
                    $11::jsonb
                )
                """,
                safe_account_id,
                _row_value(draft_row, "journey_template_version_id"),
                safe_draft_id,
                safe_actor_ref,
                safe_actor_role,
                _row_value(draft_row, "draft_status"),
                next_draft_status,
                safe_correlation_id,
                safe_idempotency_hash,
                _jsonb(safe_summary),
                _jsonb(CUSTOMER_JOURNEY_DRAFT_REDACTIONS),
            )

    return _validation_result_from_row(validation_row)
