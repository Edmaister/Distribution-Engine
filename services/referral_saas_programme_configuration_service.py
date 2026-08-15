from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Mapping

from utils.db import db_connection


PROGRAMME_CONFIGURATION_GUARDRAILS = (
    "ACCOUNT_SCOPED_PROGRAMME_CONFIGURATION",
    "PUBLISHED_CUSTOMER_JOURNEY_VERSION_REQUIRED",
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


class ProgrammeConfigurationValidationError(ValueError):
    """Raised when a programme command fails safe validation."""


class ProgrammeConfigurationUnsafePayload(ProgrammeConfigurationValidationError):
    """Raised when a programme payload includes unsafe platform fields."""


class ProgrammeConfigurationNotFound(Exception):
    """Raised when an account-scoped programme resource cannot be found."""


class ProgrammeConfigurationIdempotencyConflict(Exception):
    """Raised when an idempotency key is reused with different content."""


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
    retired_clause = "" if include_retired else "AND version_status <> 'RETIRED'"

    async with db_connection() as conn:
        rows = await conn.fetch(
            f"""
            SELECT *
            FROM referral_saas_programme_versions
            WHERE account_id = $1
              {retired_clause}
            ORDER BY published_at DESC, version_number DESC
            LIMIT $2
            """,
            safe_account_id,
            _safe_limit(limit),
        )
    return tuple(_version_from_row(row) for row in rows)


async def list_referral_saas_programme_drafts(
    *,
    account_id: str,
    include_archived: bool = False,
    limit: int = 50,
) -> tuple[ProgrammeDraft, ...]:
    safe_account_id = _required_text(account_id, "account_id", max_length=80)
    archived_clause = "" if include_archived else "AND archived_at IS NULL"

    async with db_connection() as conn:
        rows = await conn.fetch(
            f"""
            SELECT *
            FROM referral_saas_programme_drafts
            WHERE account_id = $1
              {archived_clause}
            ORDER BY updated_at DESC, created_at DESC
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
            SELECT *
            FROM referral_saas_programme_drafts
            WHERE account_id = $1
              AND programme_draft_id = $2
              AND archived_at IS NULL
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

    return {
        "productCode": "REFERRAL_SAAS",
        "subProductCodes": sorted(PROGRAMME_SUB_PRODUCT_CODES),
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

        async with conn.transaction():
            if safe_programme_draft_id:
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
                        programme_status = 'DRAFT',
                        draft_version = draft_version + 1,
                        campaign_defaults = $10::jsonb,
                        incentive_refs = $11::jsonb,
                        engagement_refs = $12::jsonb,
                        integration_readiness_snapshot = $13::jsonb,
                        commercial_entitlement_snapshot = $14::jsonb,
                        validation_result_id = NULL,
                        last_validation_status = 'NOT_VALIDATED',
                        review_status = 'NOT_SUBMITTED',
                        effective_from = $15,
                        effective_to = $16,
                        configuration_checksum = $17,
                        payload_hash = $17,
                        idempotency_key_hash = $18,
                        correlation_id = $19,
                        updated_by_ref = $20,
                        updated_at = now()
                    WHERE programme_draft_id = $1
                      AND account_id = $2
                      AND archived_at IS NULL
                      AND programme_status NOT IN ('ARCHIVED', 'DISCARDED')
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
                    raise ProgrammeConfigurationNotFound(safe_programme_draft_id)
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
                        $1, $2, $3, $4, $5, $6, $7, $8, 'DRAFT', 1,
                        $9::jsonb, $10::jsonb, $11::jsonb, $12::jsonb,
                        $13::jsonb, 'NOT_VALIDATED', 'NOT_SUBMITTED',
                        $14, $15, $16, $16, $17, $18, $19, $19
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
                    $1, $2, $3, $4, 'RECORDED', $5, $6, NULL, 'DRAFT',
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
                        "configurationChecksum": payload_hash,
                    }
                ),
                _jsonb(PROGRAMME_CONFIGURATION_REDACTIONS),
            )

    return ProgrammeDraftCommandResult(
        command_status="DRAFT_SAVED",
        draft=_draft_from_row(row),
        idempotency_status="NEW_REQUEST",
    )
