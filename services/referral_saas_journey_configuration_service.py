from __future__ import annotations

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


class JourneyTemplateCatalogueValidationError(ValueError):
    pass


class JourneyTemplateNotFound(Exception):
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
