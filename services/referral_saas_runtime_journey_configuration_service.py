from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Optional

from services.journey_definitions import (
    DEFAULT_JOURNEY_CODE,
    DEFAULT_JOURNEY_VERSION,
    JourneyDefinition,
    get_journey_definition,
)
from services.progress_definitions import (
    ProgressDefinition,
    ProgressMilestoneDefinition,
    get_progress_definition,
)
from utils.db import db_connection


RUNTIME_JOURNEY_CONFIGURATION_GUARDRAILS = (
    "EXPLICIT_RUNTIME_COMPATIBILITY_FLAG_REQUIRED",
    "ACCOUNT_SCOPED_PUBLISHED_VERSION_REQUIRED",
    "NO_DRAFT_RUNTIME_EXECUTION",
    "NO_ARCHIVED_VERSION_EXECUTION",
    "STATIC_CODE_BASELINE_FALLBACK",
    "NO_PROVIDER_AUTH_BILLING_OR_MONEY_ACTION",
)

RUNTIME_JOURNEY_CONFIGURATION_REDACTIONS = (
    "definition_payload",
    "published_configuration_payload",
    "payload_hash",
    "tenant_code",
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


class RuntimeJourneyConfigurationError(ValueError):
    """Raised when a published journey version cannot be used by runtime reads."""


class RuntimeJourneyConfigurationNotFound(RuntimeJourneyConfigurationError):
    """Raised when the requested published customer journey version is missing."""


@dataclass(frozen=True)
class RuntimeJourneyConfiguration:
    source: str
    journey_definition: JourneyDefinition
    progress_definition: ProgressDefinition
    customer_journey_version_id: str | None = None
    account_id: str | None = None
    customer_journey_code: str | None = None
    version_number: int | None = None
    template_code: str | None = None
    template_version: str | None = None

    def to_safe_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "journeyCode": self.journey_definition.journey_code,
            "journeyVersion": self.journey_definition.journey_version,
            "customerJourneyVersionId": self.customer_journey_version_id,
            "accountId": self.account_id,
            "customerJourneyCode": self.customer_journey_code,
            "versionNumber": self.version_number,
            "templateCode": self.template_code,
            "templateVersion": self.template_version,
            "milestoneCount": len(self.journey_definition.core_sequence),
            "transitionCount": sum(
                len(targets)
                for targets in self.journey_definition.allowed_transitions.values()
            ),
            "progressMilestoneCount": len(self.progress_definition.milestones),
            "guardrails": list(RUNTIME_JOURNEY_CONFIGURATION_GUARDRAILS),
            "redactions": list(RUNTIME_JOURNEY_CONFIGURATION_REDACTIONS),
            "noDraftRuntimeExecutionConfirmed": self.source
            != "PUBLISHED_CUSTOMER_JOURNEY_VERSION"
            or self.customer_journey_version_id is not None,
            "noProviderAuthBillingOrMoneyActionConfirmed": True,
        }


def resolve_code_baseline_runtime_journey(
    journey_code: str | None = None,
    journey_version: str | None = None,
) -> RuntimeJourneyConfiguration:
    code = str(journey_code or DEFAULT_JOURNEY_CODE).strip().upper()
    version = str(journey_version or DEFAULT_JOURNEY_VERSION).strip()
    return RuntimeJourneyConfiguration(
        source="CODE_BASELINE",
        journey_definition=get_journey_definition(code, version),
        progress_definition=get_progress_definition(code, version),
    )


async def resolve_runtime_journey_configuration(
    *,
    account_id: str | None = None,
    customer_journey_version_id: str | None = None,
    journey_code: str | None = None,
    journey_version: str | None = None,
    published_runtime_enabled: bool = False,
) -> RuntimeJourneyConfiguration:
    if not published_runtime_enabled or not customer_journey_version_id:
        return resolve_code_baseline_runtime_journey(journey_code, journey_version)

    if not account_id or not str(account_id).strip():
        raise RuntimeJourneyConfigurationError(
            "account_id is required for published journey runtime reads."
        )

    async with db_connection() as conn:
        row = await conn.fetchrow(
            """
            SELECT
                cv.customer_journey_version_id,
                cv.account_id,
                cv.customer_journey_code,
                cv.version_number,
                cv.version_status,
                cv.published_configuration_payload,
                cv.archived_at,
                tv.template_code,
                tv.template_version,
                tv.status AS template_status,
                tv.milestone_schema,
                tv.transition_rules
            FROM referral_saas_customer_journey_versions cv
            JOIN referral_saas_journey_template_versions tv
              ON tv.journey_template_version_id = cv.journey_template_version_id
            WHERE cv.customer_journey_version_id = $1
              AND cv.account_id = $2
            LIMIT 1
            """,
            str(customer_journey_version_id).strip(),
            str(account_id).strip(),
        )

    if not row:
        raise RuntimeJourneyConfigurationNotFound(
            "Published customer journey version was not found for this account."
        )

    return runtime_journey_configuration_from_row(row)


def runtime_journey_configuration_from_row(
    row: Mapping[str, Any],
) -> RuntimeJourneyConfiguration:
    version_status = str(_row_value(row, "version_status") or "").strip().upper()
    template_status = str(_row_value(row, "template_status") or "").strip().upper()
    if version_status != "PUBLISHED" or _row_value(row, "archived_at") is not None:
        raise RuntimeJourneyConfigurationError(
            "Runtime can use only published, unarchived customer journey versions."
        )
    if template_status != "APPROVED":
        raise RuntimeJourneyConfigurationError(
            "Runtime can use only versions based on approved journey templates."
        )

    configuration_payload = _as_dict(
        _row_value(row, "published_configuration_payload")
    )
    milestone_items = _configured_items(
        configuration_payload.get("milestones")
        or configuration_payload.get("enabledMilestones")
    ) or _configured_items(_row_value(row, "milestone_schema"))
    transition_items = _configured_items(
        configuration_payload.get("transitions")
        or configuration_payload.get("transitionRules")
    ) or _configured_items(_row_value(row, "transition_rules"))

    milestones = _milestone_codes(milestone_items)
    if not milestones:
        raise RuntimeJourneyConfigurationError(
            "Published customer journey version has no runtime milestone sequence."
        )

    transitions = _transition_pairs(transition_items)
    allowed_transitions = _allowed_transitions(milestones, transitions)
    journey_code = _safe_code(
        _row_value(row, "customer_journey_code") or _row_value(row, "template_code")
    )
    journey_version = f"published-v{int(_row_value(row, 'version_number') or 1)}"

    journey_definition = JourneyDefinition(
        journey_code=journey_code,
        journey_version=journey_version,
        core_sequence=list(milestones),
        allowed_transitions=allowed_transitions,
        event_to_timestamp_field=_event_timestamp_fields(milestone_items, milestones),
        completion_events=_completion_events(configuration_payload, milestones),
        completion_minimum_milestone=milestones[-1] if len(milestones) > 1 else None,
    )
    progress_definition = _progress_definition(
        journey_code=journey_code,
        journey_version=journey_version,
        milestone_items=milestone_items,
        milestones=milestones,
    )

    return RuntimeJourneyConfiguration(
        source="PUBLISHED_CUSTOMER_JOURNEY_VERSION",
        journey_definition=journey_definition,
        progress_definition=progress_definition,
        customer_journey_version_id=str(_row_value(row, "customer_journey_version_id")),
        account_id=str(_row_value(row, "account_id")),
        customer_journey_code=journey_code,
        version_number=int(_row_value(row, "version_number") or 1),
        template_code=_safe_code(_row_value(row, "template_code")),
        template_version=str(_row_value(row, "template_version") or "").strip(),
    )


def _row_value(row: Mapping[str, Any], key: str) -> Any:
    if hasattr(row, "get"):
        return row.get(key)
    return row[key]


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _configured_items(value: Any) -> tuple[Any, ...]:
    if isinstance(value, list):
        return tuple(value)
    if isinstance(value, dict):
        items = value.get("items") or value.get("milestones") or value.get("rules")
        if isinstance(items, list):
            return tuple(items)
    return ()


def _safe_code(value: Any) -> str:
    safe = str(value or "").strip().upper().replace("-", "_").replace(" ", "_")
    return safe or "CUSTOMER_JOURNEY"


def _item_code(item: Any) -> str | None:
    if isinstance(item, str):
        return _safe_code(item)
    if isinstance(item, Mapping):
        for key in ("code", "milestoneCode", "milestone_code", "id"):
            if item.get(key):
                return _safe_code(item.get(key))
    return None


def _milestone_codes(items: tuple[Any, ...]) -> tuple[str, ...]:
    codes: list[str] = []
    for item in items:
        code = _item_code(item)
        if code and code not in codes:
            codes.append(code)
    return tuple(codes)


def _transition_pairs(items: tuple[Any, ...]) -> tuple[tuple[Optional[str], str], ...]:
    pairs: list[tuple[Optional[str], str]] = []
    for item in items:
        if not isinstance(item, Mapping):
            continue
        from_code = _transition_code(
            item, "from", "fromMilestone", "from_milestone", "fromStatus", "from_status"
        )
        to_code = _transition_code(
            item, "to", "toMilestone", "to_milestone", "toStatus", "to_status"
        )
        if to_code and (from_code, to_code) not in pairs:
            pairs.append((from_code, to_code))
    return tuple(pairs)


def _transition_code(item: Mapping[str, Any], *keys: str) -> str | None:
    for key in keys:
        if key in item:
            value = item.get(key)
            if value is None:
                return None
            return _safe_code(value)
    return None


def _allowed_transitions(
    milestones: tuple[str, ...],
    transitions: tuple[tuple[Optional[str], str], ...],
) -> dict[Optional[str], set[str]]:
    if transitions:
        allowed: dict[Optional[str], set[str]] = {}
        for from_code, to_code in transitions:
            allowed.setdefault(from_code, set()).add(to_code)
        allowed.setdefault(None, {milestones[0]})
        return allowed

    allowed = {None: {milestones[0]}}
    for current, next_code in zip(milestones, milestones[1:]):
        allowed[current] = {next_code}
    return allowed


def _event_timestamp_fields(
    milestone_items: tuple[Any, ...],
    milestones: tuple[str, ...],
) -> dict[str, str]:
    fields: dict[str, str] = {}
    for item in milestone_items:
        code = _item_code(item)
        if not code:
            continue
        if isinstance(item, Mapping):
            field = item.get("timestampField") or item.get("timestamp_field")
            if field:
                fields[code] = str(field).strip()
                continue
        fields[code] = f"{code.lower()}_at"
    for code in milestones:
        fields.setdefault(code, f"{code.lower()}_at")
    return fields


def _completion_events(
    configuration_payload: Mapping[str, Any],
    milestones: tuple[str, ...],
) -> set[str]:
    raw = configuration_payload.get("completionEvents") or configuration_payload.get(
        "completion_events"
    )
    configured = {_safe_code(item) for item in raw if item} if isinstance(raw, list) else set()
    return configured or {milestones[-1]}


def _progress_definition(
    *,
    journey_code: str,
    journey_version: str,
    milestone_items: tuple[Any, ...],
    milestones: tuple[str, ...],
) -> ProgressDefinition:
    count = len(milestones)
    milestone_by_code = {
        _item_code(item): item for item in milestone_items if _item_code(item)
    }
    definitions: dict[str, ProgressMilestoneDefinition] = {}
    for index, code in enumerate(milestones):
        item = milestone_by_code.get(code)
        progress_percent = _progress_percent(item, index=index, count=count)
        definitions[code] = ProgressMilestoneDefinition(
            progress_percent=progress_percent,
            progress_band=_progress_band(progress_percent),
            display_status=_display_status(item, code),
            next_milestone=milestones[index + 1] if index + 1 < count else None,
        )

    return ProgressDefinition(
        journey_code=journey_code,
        journey_version=journey_version,
        milestones=definitions,
        complete_band="COMPLETE",
        complete_display_status="Journey complete",
    )


def _progress_percent(item: Any, *, index: int, count: int) -> int:
    if isinstance(item, Mapping):
        for key in ("progressPercent", "progress_percent", "percent"):
            value = item.get(key)
            if value is not None:
                try:
                    return max(0, min(100, int(value)))
                except (TypeError, ValueError):
                    break
    return int(round(((index + 1) / max(count, 1)) * 100))


def _progress_band(progress_percent: int) -> str:
    if progress_percent >= 100:
        return "COMPLETE"
    if progress_percent >= 75:
        return "NEAR_COMPLETE"
    if progress_percent >= 30:
        return "IN_PROGRESS"
    return "STARTED"


def _display_status(item: Any, code: str) -> str:
    if isinstance(item, Mapping):
        for key in ("displayStatus", "display_status", "label", "name"):
            value = item.get(key)
            if value:
                return str(value).strip()
    return code.replace("_", " ").title()
