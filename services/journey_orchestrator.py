from __future__ import annotations

import datetime
from typing import Any, Dict, Optional

from apps.core.logging_utils import log_event
from services.audit_service import write_processing_audit
from services.badge_service import (
    evaluate_badges_for_hve_event,
    evaluate_badges_for_referral_completion,
    evaluate_badges_for_referral_created,
)
from services.journey_definitions import (
    DEFAULT_JOURNEY_CODE,
    DEFAULT_JOURNEY_VERSION,
    get_journey_definition,
)
from services.progress_definitions import get_progress_definition
from services.leaderboard_events import publish_leaderboard_rebuild_requested
from services.mission_service import apply_event_to_missions
from services.reward_policy_service import get_reward_policy
from services.reward_service import build_base_reward_instructions, apply_reward
from utils.db import db_connection


HVE_EVENT_TYPES = {
    "SALARY_SWITCHED",
    "DEBIT_ORDER_SWITCHED",
    "FIRST_TRANSACTION_COMPLETED",
}


async def _publish_leaderboard_rebuild(
    *,
    tenant_code: str,
    referrer_ucn: str,
    correlation_id: str | None = None,
    referral_track_id: str | None = None,
) -> None:
    await publish_leaderboard_rebuild_requested(
        tenant_code=tenant_code,
        referrer_ucn=referrer_ucn,
        correlation_id=correlation_id,
        referral_track_id=referral_track_id,
    )


async def _write_processing_audit_async(**kwargs) -> None:
    await write_processing_audit(**kwargs)


def _isoz(dt: datetime.datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=datetime.timezone.utc)
    return dt.isoformat().replace("+00:00", "Z")


def _ensure_utc(
    dt: Optional[datetime.datetime],
) -> Optional[datetime.datetime]:
    if dt is None:
        return None

    if dt.tzinfo is not None:
        return dt.astimezone(datetime.timezone.utc).replace(tzinfo=None)

    return dt


def _parse_occurred_at(event: Dict[str, Any]) -> datetime.datetime:
    raw = event.get("occurredAt") or event.get("occurred_at")
    if raw:
        return datetime.datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
    return datetime.datetime.now(datetime.timezone.utc)


def _derive_progress_snapshot(
    *,
    status: str,
    journey_code: str,
    journey_version: str,
    is_complete: bool,
) -> dict[str, object]:
    progress_definition = get_progress_definition(journey_code, journey_version)
    milestone = progress_definition.milestones.get(status)

    if milestone is None:
        return {
            "progress_percent": 100 if is_complete else None,
            "progress_band": progress_definition.complete_band if is_complete else None,
            "display_status": progress_definition.complete_display_status if is_complete else None,
            "next_milestone": None,
        }

    if is_complete:
        return {
            "progress_percent": 100,
            "progress_band": progress_definition.complete_band,
            "display_status": progress_definition.complete_display_status,
            "next_milestone": None,
        }

    return {
        "progress_percent": milestone.progress_percent,
        "progress_band": milestone.progress_band,
        "display_status": milestone.display_status,
        "next_milestone": milestone.next_milestone,
    }


def _bind_event_context(instance: Dict[str, Any], event: Dict[str, Any]) -> None:
    referee_ucn = event.get("refereeUCN") or event.get("referee_ucn")
    referee_ucn_hash = event.get("refereeUCNHash") or event.get("referee_ucn_hash")
    account_number = event.get("accountNumber") or event.get("account_number")
    account_hash = event.get("accountNumberHash") or event.get("account_number_hash")
    account_masked = event.get("accountNumberMasked") or event.get("account_number_masked")

    if referee_ucn and not instance.get("referee_ucn"):
        instance["referee_ucn"] = referee_ucn

    if referee_ucn_hash and not instance.get("referee_ucn_hash"):
        instance["referee_ucn_hash"] = referee_ucn_hash

    if account_number and not instance.get("referee_account_number"):
        instance["referee_account_number"] = account_number

    if account_hash and not instance.get("referee_account_hash"):
        instance["referee_account_hash"] = account_hash

    if account_masked and not instance.get("referee_account_masked"):
        instance["referee_account_masked"] = account_masked


def _is_self_referral(instance: Dict[str, Any]) -> bool:
    referrer_ucn = str(instance.get("referrer_ucn") or "").strip()
    referee_ucn = str(instance.get("referee_ucn") or "").strip()
    return bool(referrer_ucn and referee_ucn and referrer_ucn == referee_ucn)


def _became_reward_eligible(referral_before: dict, referral_after: dict) -> bool:
    was_complete = bool((referral_before or {}).get("is_complete", False))
    is_complete = bool((referral_after or {}).get("is_complete", False))
    return (not was_complete) and is_complete


async def _issue_base_rewards_if_eligible(referral_before: dict,referral_after: dict,) -> None:
    referral_track_id = referral_after.get("referral_track_id")

    if not _became_reward_eligible(referral_before, referral_after):
        log_event(
            level="INFO",
            component="journey_orchestrator",
            message="reward_issuance_skipped_not_newly_complete",
            referral_track_id=referral_track_id,
            extra={
                "was_complete": bool((referral_before or {}).get("is_complete", False)),
                "is_complete": bool((referral_after or {}).get("is_complete", False)),
            },
        )
        return

    product = referral_after.get("product")
    sub_product = referral_after.get("sub_product")

    if not product:
        log_event(
            level="WARNING",
            component="journey_orchestrator",
            message="reward_issuance_skipped_missing_product",
            referral_track_id=referral_track_id,
        )
        return

    policy = await get_reward_policy(product=product, sub_product=sub_product)

    if not policy:
        log_event(
            level="INFO",
            component="journey_orchestrator",
            message="reward_policy_not_found",
            referral_track_id=referral_track_id,
            extra={"product": product, "sub_product": sub_product},
        )
        return

    instructions = build_base_reward_instructions(referral_after, policy)

    for instruction in instructions:
        result = await apply_reward(instruction)

        log_event(
            level="INFO",
            component="journey_orchestrator",
            message="reward_applied",
            referral_track_id=referral_track_id,
            extra={
                "tenant_code": referral_after.get("tenant_code"),
                "reward_id": result.get("id"),
                "beneficiary_type": result.get("beneficiary_type"),
                "beneficiary_ref": result.get("beneficiary_ref"),
                "reward_source": result.get("reward_source"),
                "reward_type": result.get("reward_type"),
                "amount": result.get("amount"),
                "inserted": result.get("inserted"),
            },
        )


async def _issue_base_rewards_if_eligible_async(
    referral_before: dict,
    referral_after: dict,
) -> None:
    await _issue_base_rewards_if_eligible(
        referral_before,
        referral_after,
    )


async def _issue_badges(
    *,
    referral_before: dict,
    referral_after: dict,
    incoming_event: str,
    correlation_id: str,
    referral_track_id: str,
    source_system: str,
    dedupe_key: Optional[str],
) -> None:
    awarded_badges = []

    if incoming_event == "UCN_CAPTURED":
        awarded_badges.extend(
            await evaluate_badges_for_referral_created(referral_track_id)
        )

    if _became_reward_eligible(referral_before, referral_after):
        awarded_badges.extend(
            await evaluate_badges_for_referral_completion(referral_track_id)
        )

    if incoming_event in HVE_EVENT_TYPES:
        awarded_badges.extend(
            await evaluate_badges_for_hve_event(
                referral_track_id=referral_track_id,
                event_type=incoming_event,
            )
        )

    log_event(
        level="INFO",
        component="journey_orchestrator",
        message="badge_evaluation_completed",
        correlation_id=correlation_id,
        referral_track_id=referral_track_id,
        source_system=source_system,
        event_type=incoming_event,
        extra={
            "tenant_code": referral_after.get("tenant_code"),
            "awarded_badge_count": len(awarded_badges),
            "awarded_badges": awarded_badges,
            "dedupe_key": dedupe_key,
        },
    )


async def _issue_badges_async(
    *,
    referral_before: dict,
    referral_after: dict,
    incoming_event: str,
    correlation_id: str,
    referral_track_id: str,
    source_system: str,
    dedupe_key: Optional[str],
) -> None:
    await _issue_badges(
        referral_before=referral_before,
        referral_after=referral_after,
        incoming_event=incoming_event,
        correlation_id=correlation_id,
        referral_track_id=referral_track_id,
        source_system=source_system,
        dedupe_key=dedupe_key,
    )


EVENT_TYPE_MAPPING = {
    "UCN_CAPTURED": "UCN_CAPTURED",
    "REFEREE_UCN_CAPTURED": "UCN_CAPTURED",
    "UCN_CREATED": "ACCOUNT_OPENED",
    "ACCOUNT_OPENED": "ACCOUNT_OPENED",
    "ACCOUNT_ACTIVATED": "ACCOUNT_ACTIVATED",
    "ACCOUNT_FUNDED": "FUNDED",
    "FUNDED": "FUNDED",
    "DEBIT_ORDER_SWITCHED": "DEBIT_ORDER_SWITCHED",
    "SALARY_SWITCHED": "SALARY_SWITCHED",
    "FIRST_TRANSACTION_COMPLETED": "FIRST_TRANSACTION_COMPLETED",
}


def normalize_event(event: Dict[str, Any]) -> Dict[str, Any]:
    source_event_type = str(
        event.get("progressEventType") or event.get("eventType") or ""
    ).strip()

    normalized_event_type = EVENT_TYPE_MAPPING.get(source_event_type, source_event_type)

    normalized = dict(event)
    normalized["sourceEventType"] = source_event_type
    normalized["normalizedEventType"] = normalized_event_type
    return normalized


def _status_rank(status: Optional[str], core_sequence: list[str]) -> int:
    if status is None:
        return -1
    try:
        return core_sequence.index(status)
    except ValueError:
        return -1


def _is_valid_transition(
    current_milestone: Optional[str],
    incoming_event: str,
    allowed_transitions: dict[Optional[str], set[str]],
) -> bool:
    return incoming_event in allowed_transitions.get(current_milestone, set())


def _is_duplicate_event(
    instance: Dict[str, Any],
    incoming_event: str,
    event_to_timestamp_field: dict[str, str],
) -> bool:
    ts_field = event_to_timestamp_field.get(incoming_event)
    return bool(ts_field and instance.get(ts_field) is not None)


def _classify_transition(
    instance: Dict[str, Any],
    incoming_event: str,
    journey_definition,
) -> str:
    current_milestone = instance.get("status")
    allowed_transitions = journey_definition.allowed_transitions
    core_sequence = journey_definition.core_sequence
    event_to_timestamp_field = journey_definition.event_to_timestamp_field

    if _is_duplicate_event(instance, incoming_event, event_to_timestamp_field):
        return "duplicate"

    if _is_valid_transition(current_milestone, incoming_event, allowed_transitions):
        return "valid"

    incoming_rank = _status_rank(incoming_event, core_sequence)
    current_rank = _status_rank(current_milestone, core_sequence)

    completion_events = getattr(
        journey_definition,
        "completion_events",
        {
            "DEBIT_ORDER_SWITCHED",
            "SALARY_SWITCHED",
            "FIRST_TRANSACTION_COMPLETED",
        },
    )
    funded_side_events = set(completion_events) - set(core_sequence)
    completion_minimum = getattr(journey_definition, "completion_minimum_milestone", "FUNDED")

    if incoming_event in funded_side_events:
        if current_milestone == completion_minimum:
            return "valid"
        if current_rank >= 0:
            return "out_of_order"
        return "invalid"

    if incoming_rank >= 0 and current_rank >= 0:
        if incoming_rank < current_rank:
            return "backward"
        if incoming_rank > current_rank:
            return "out_of_order"

    if incoming_rank >= 0 and current_rank == -1:
        return "out_of_order"

    return "invalid"


def _apply_event_fields(instance, incoming_event, occurred_at, journey_definition=None):
    event_to_timestamp_field = getattr(journey_definition, "event_to_timestamp_field", {}) if journey_definition else {}
    timestamp_field = event_to_timestamp_field.get(incoming_event)

    if timestamp_field:
        if incoming_event == "FUNDED" and instance.get("account_activated_at") is None:
            instance["account_activated_at"] = occurred_at
        if instance.get(timestamp_field) is None:
            instance[timestamp_field] = occurred_at
        return

    if incoming_event == "UCN_CAPTURED":
        if instance.get("ucn_captured_at") is None:
            instance["ucn_captured_at"] = occurred_at

    elif incoming_event == "ACCOUNT_OPENED":
        if instance.get("account_opened_at") is None:
            instance["account_opened_at"] = occurred_at

    elif incoming_event == "ACCOUNT_ACTIVATED":
        if instance.get("account_activated_at") is None:
            instance["account_activated_at"] = occurred_at

    elif incoming_event == "FUNDED":
        if instance.get("account_activated_at") is None:
            instance["account_activated_at"] = occurred_at
        if instance.get("funded_at") is None:
            instance["funded_at"] = occurred_at

    elif incoming_event == "DEBIT_ORDER_SWITCHED":
        if instance.get("debit_order_switched_at") is None:
            instance["debit_order_switched_at"] = occurred_at

    elif incoming_event == "SALARY_SWITCHED":
        if instance.get("salary_switched_at") is None:
            instance["salary_switched_at"] = occurred_at

    elif incoming_event == "FIRST_TRANSACTION_COMPLETED":
        if instance.get("first_transaction_completed_at") is None:
            instance["first_transaction_completed_at"] = occurred_at


def _derive_current_milestone(instance: Dict[str, Any], journey_definition=None) -> str:
    if journey_definition is not None:
        for milestone in reversed(journey_definition.core_sequence):
            timestamp_field = journey_definition.event_to_timestamp_field.get(milestone)
            if timestamp_field and instance.get(timestamp_field) is not None:
                return milestone
        return journey_definition.core_sequence[0]

    if instance.get("funded_at") is not None:
        return "FUNDED"
    if instance.get("account_activated_at") is not None:
        return "ACCOUNT_ACTIVATED"
    if instance.get("account_opened_at") is not None:
        return "ACCOUNT_OPENED"
    if instance.get("ucn_captured_at") is not None:
        return "UCN_CAPTURED"
    return "VALIDATED"


def _derive_completion(
    instance: Dict[str, Any],
    journey_definition=None,
) -> tuple[bool, Optional[datetime.datetime]]:
    if journey_definition is not None:
        completion_events = getattr(journey_definition, "completion_events", set())
        completion_minimum = getattr(journey_definition, "completion_minimum_milestone", None)
        minimum_met = True
        if completion_minimum:
            minimum_field = journey_definition.event_to_timestamp_field.get(completion_minimum)
            minimum_met = bool(minimum_field and instance.get(minimum_field) is not None)

        is_complete = minimum_met and any(
            instance.get(journey_definition.event_to_timestamp_field.get(event)) is not None
            for event in completion_events
            if journey_definition.event_to_timestamp_field.get(event)
        )
    else:
        is_complete = (
            instance.get("funded_at") is not None
            and (
                instance.get("salary_switched_at") is not None
                or instance.get("debit_order_switched_at") is not None
                or instance.get("first_transaction_completed_at") is not None
            )
        )

    completed_at = instance.get("completed_at")
    if is_complete and completed_at is None:
        completed_at = datetime.datetime.now(datetime.timezone.utc)

    return is_complete, completed_at


def _derive_platform_status(instance: Dict[str, Any]) -> str:
    return "COMPLETED" if instance.get("is_complete") else "IN_PROGRESS"


async def _load_referral_instance(
    conn,
    referral_track_id: str,
    tenant_code: str,
) -> Optional[Dict[str, Any]]:
    row = await conn.fetchrow(
        """
        SELECT
            tenant_code,
            referral_track_id,
            referrer_ucn,
            product,
            sub_product,
            status,
            journey_code,
            journey_version,
            referee_ucn,
            referee_ucn_hash,
            referee_account_number,
            referee_account_hash,
            referee_account_masked,
            referee_alias,
            referee_alias_normalized,
            ucn_captured_at,
            account_opened_at,
            account_activated_at,
            funded_at,
            debit_order_switched_at,
            salary_switched_at,
            first_transaction_completed_at,
            progress_percent,
            progress_band,
            display_status,
            next_milestone,
            is_complete,
            completed_at,
            updated_at
        FROM referral_instances
        WHERE referral_track_id = $1
          AND tenant_code = $2
        """,
        referral_track_id,
        tenant_code,
    )

    if not row:
        return None

    return dict(row)


async def _update_referral_instance(
    conn,
    instance: Dict[str, Any],
    tenant_code: str,
) -> None:
    await conn.execute(
        """
        UPDATE referral_instances
        SET
            status = $1,
            journey_code = $2,
            journey_version = $3,
            referee_ucn = $4,
            referee_ucn_hash = $5,
            referee_account_number = $6,
            referee_account_hash = $7,
            referee_account_masked = $8,
            referee_alias = $9,
            referee_alias_normalized = $10,
            ucn_captured_at = $11,
            account_opened_at = $12,
            account_activated_at = $13,
            funded_at = $14,
            debit_order_switched_at = $15,
            salary_switched_at = $16,
            first_transaction_completed_at = $17,
            progress_percent = $18,
            progress_band = $19,
            display_status = $20,
            next_milestone = $21,
            is_complete = $22,
            completed_at = $23,
            updated_at = NOW()
        WHERE referral_track_id = $24
          AND tenant_code = $25
        """,
        instance["status"],
        instance["journey_code"],
        instance["journey_version"],
        instance.get("referee_ucn"),
        instance.get("referee_ucn_hash"),
        instance.get("referee_account_number"),
        instance.get("referee_account_hash"),
        instance.get("referee_account_masked"),
        instance.get("referee_alias"),
        instance.get("referee_alias_normalized"),
        _ensure_utc(instance.get("ucn_captured_at")),
        _ensure_utc(instance.get("account_opened_at")),
        _ensure_utc(instance.get("account_activated_at")),
        _ensure_utc(instance.get("funded_at")),
        _ensure_utc(instance.get("debit_order_switched_at")),
        _ensure_utc(instance.get("salary_switched_at")),
        _ensure_utc(instance.get("first_transaction_completed_at")),
        instance.get("progress_percent"),
        instance.get("progress_band"),
        instance.get("display_status"),
        instance.get("next_milestone"),
        instance.get("is_complete"),
        _ensure_utc(instance.get("completed_at")),
        instance["referral_track_id"],
        tenant_code,
    )


async def handle_referral_progress_recorded(
    event: Dict[str, Any],
    tenant_code: str,
) -> None:
    tenant_code = str(tenant_code or "").strip()

    if not tenant_code:
        raise ValueError("tenant_code is required")

    referral_track_id = str(
        event.get("referralTrackId") or event.get("referral_track_id") or ""
    ).strip()

    correlation_id = str(
        event.get("correlationId") or event.get("correlation_id") or referral_track_id
    ).strip() or referral_track_id

    source_system = str(
        event.get("sourceSystem") or event.get("source_system") or "unknown"
    ).strip()

    log_event(
        level="INFO",
        component="journey_orchestrator",
        message="orchestrator_received_event",
        correlation_id=correlation_id,
        referral_track_id=referral_track_id or None,
        source_system=source_system,
        event_type=str(event.get("eventType") or ""),
        extra={
            "tenant_code": tenant_code,
            "raw_event_type": event.get("eventType"),
            "deduped": event.get("deduped"),
        },
    )

    if event.get("eventType") != "REFERRAL_PROGRESS_RECORDED":
        log_event(
            level="WARNING",
            component="journey_orchestrator",
            message="orchestrator_ignored_non_progress_event",
            correlation_id=correlation_id,
            referral_track_id=referral_track_id or None,
            source_system=source_system,
            event_type=str(event.get("eventType") or ""),
            extra={"tenant_code": tenant_code},
        )
        return

    if event.get("deduped") is True:
        log_event(
            level="INFO",
            component="journey_orchestrator",
            message="orchestrator_ignored_upstream_deduped_event",
            correlation_id=correlation_id,
            referral_track_id=referral_track_id or None,
            source_system=source_system,
            event_type="REFERRAL_PROGRESS_RECORDED",
            extra={"tenant_code": tenant_code},
        )
        return

    normalized = normalize_event(event)

    referral_track_id = str(
        normalized.get("referralTrackId") or normalized.get("referral_track_id") or ""
    ).strip()

    if not referral_track_id:
        log_event(
            level="ERROR",
            component="journey_orchestrator",
            message="orchestrator_missing_referral_track_id",
            correlation_id=correlation_id,
            source_system=source_system,
            event_type="REFERRAL_PROGRESS_RECORDED",
            extra={"tenant_code": tenant_code},
        )
        raise ValueError("Missing referralTrackId in event payload")

    source_event_type = str(normalized["sourceEventType"]).strip()
    incoming_event = str(normalized["normalizedEventType"]).strip()
    occurred_at = _parse_occurred_at(normalized)

    dedupe_key = str(
        normalized.get("dedupeKey") or normalized.get("dedupe_key") or ""
    ).strip() or None

    previous_status = None
    instance = None
    referral_before = {}

    try:
        async with db_connection() as conn:
            async with conn.transaction():
                instance = await _load_referral_instance(
                    conn=conn,
                    referral_track_id=referral_track_id,
                    tenant_code=tenant_code,
                )

                if not instance:
                    log_event(
                        level="WARNING",
                        component="journey_orchestrator",
                        message="referral_instance_not_found",
                        correlation_id=correlation_id,
                        referral_track_id=referral_track_id,
                        source_system=source_system,
                        event_type=incoming_event,
                        extra={"tenant_code": tenant_code},
                    )
                    return

                instance["tenant_code"] = tenant_code

                referral_before = dict(instance)
                previous_status = instance.get("status")

                _bind_event_context(instance, normalized)

                if _is_self_referral(instance):
                    await _write_processing_audit_async(
                        referral_track_id=referral_track_id,
                        event_id=None,
                        event_type=incoming_event,
                        occurred_at=occurred_at,
                        processing_status="IGNORED",
                        reason="SELF_REFERRAL_NOT_ALLOWED",
                        previous_status=previous_status,
                        new_status=previous_status,
                        metadata={
                            "tenant_code": tenant_code,
                            "source_system": source_system,
                            "source_event_type": source_event_type,
                            "dedupe_key": dedupe_key,
                            "referrer_ucn": instance.get("referrer_ucn"),
                            "referee_ucn": instance.get("referee_ucn"),
                        },
                    )
                    return

                event_journey_code = str(
                    event.get("journeyCode") or event.get("journey_code") or ""
                ).strip().upper()
                event_journey_version = str(
                    event.get("journeyVersion") or event.get("journey_version") or ""
                ).strip()

                if event_journey_code and not instance.get("journey_code"):
                    instance["journey_code"] = event_journey_code
                if event_journey_version and not instance.get("journey_version"):
                    instance["journey_version"] = event_journey_version

                instance["journey_code"] = instance.get("journey_code") or DEFAULT_JOURNEY_CODE
                instance["journey_version"] = instance.get("journey_version") or DEFAULT_JOURNEY_VERSION

                journey_definition = get_journey_definition(
                    instance["journey_code"],
                    instance["journey_version"],
                )

                transition_result = _classify_transition(
                    instance=instance,
                    incoming_event=incoming_event,
                    journey_definition=journey_definition,
                )

                if transition_result != "valid":
                    await _write_processing_audit_async(
                        referral_track_id=referral_track_id,
                        event_id=None,
                        event_type=incoming_event,
                        occurred_at=occurred_at,
                        processing_status="IGNORED",
                        reason=transition_result,
                        previous_status=previous_status,
                        new_status=previous_status,
                        metadata={
                            "tenant_code": tenant_code,
                            "source_system": source_system,
                            "source_event_type": source_event_type,
                            "dedupe_key": dedupe_key,
                        },
                    )
                    return

                _apply_event_fields(instance, incoming_event, occurred_at, journey_definition)

                current_milestone = _derive_current_milestone(instance, journey_definition)
                is_complete, completed_at = _derive_completion(instance, journey_definition)

                instance["current_milestone"] = current_milestone
                instance["is_complete"] = is_complete
                instance["completed_at"] = completed_at
                instance["platform_status"] = _derive_platform_status(instance)
                instance["status"] = current_milestone

                progress_snapshot = _derive_progress_snapshot(
                    status=current_milestone,
                    journey_code=instance["journey_code"],
                    journey_version=instance["journey_version"],
                    is_complete=is_complete,
                )
                instance.update(progress_snapshot)

                await _update_referral_instance(
                    conn=conn,
                    instance=instance,
                    tenant_code=tenant_code,
                )

                await _write_processing_audit_async(
                    referral_track_id=referral_track_id,
                    event_id=None,
                    event_type=incoming_event,
                    occurred_at=occurred_at,
                    processing_status="PROCESSED",
                    previous_status=previous_status,
                    new_status=current_milestone,
                    metadata={
                        "tenant_code": tenant_code,
                        "product": instance.get("product"),
                        "sub_product": instance.get("sub_product"),
                        "source_system": source_system,
                        "source_event_type": source_event_type,
                        "dedupe_key": dedupe_key,
                        "progress_percent": instance.get("progress_percent"),
                        "progress_band": instance.get("progress_band"),
                        "display_status": instance.get("display_status"),
                        "next_milestone": instance.get("next_milestone"),
                        "is_complete": instance.get("is_complete"),
                    },
                )

        try:
            await _issue_base_rewards_if_eligible_async(referral_before, instance)
        except Exception as exc:
            log_event(
                level="ERROR",
                component="journey_orchestrator",
                message="reward_issuance_failed",
                correlation_id=correlation_id,
                referral_track_id=referral_track_id,
                source_system=source_system,
                event_type=incoming_event,
                extra={"tenant_code": tenant_code, "error": str(exc)},
            )

        try:
            await _issue_badges_async(
                referral_before=referral_before,
                referral_after=instance,
                incoming_event=incoming_event,
                correlation_id=correlation_id,
                referral_track_id=referral_track_id,
                source_system=source_system,
                dedupe_key=dedupe_key,
            )
        except Exception as exc:
            log_event(
                level="ERROR",
                component="journey_orchestrator",
                message="badge_evaluation_failed",
                correlation_id=correlation_id,
                referral_track_id=referral_track_id,
                source_system=source_system,
                event_type=incoming_event,
                extra={
                    "tenant_code": tenant_code,
                    "error": str(exc),
                    "dedupe_key": dedupe_key,
                },
            )

        try:
            mission_updates = await apply_event_to_missions(
                referral_track_id=referral_track_id,
                tenant_code=tenant_code,
                event_type=incoming_event,
            )

            log_event(
                level="INFO",
                component="journey_orchestrator",
                message="mission_progress_applied",
                correlation_id=correlation_id,
                referral_track_id=referral_track_id,
                source_system=source_system,
                event_type=incoming_event,
                extra={
                    "tenant_code": tenant_code,
                    "mission_update_count": len(mission_updates),
                    "mission_updates": mission_updates,
                    "dedupe_key": dedupe_key,
                },
            )
        except Exception as exc:
            log_event(
                level="ERROR",
                component="journey_orchestrator",
                message="mission_progress_failed",
                correlation_id=correlation_id,
                referral_track_id=referral_track_id,
                source_system=source_system,
                event_type=incoming_event,
                extra={
                    "tenant_code": tenant_code,
                    "error": str(exc),
                    "dedupe_key": dedupe_key,
                },
            )

        try:
            referrer_ucn = instance.get("referrer_ucn")
            if referrer_ucn:
                await _publish_leaderboard_rebuild(
                    referrer_ucn=referrer_ucn,
                    tenant_code=tenant_code,
                    correlation_id=correlation_id,
                    referral_track_id=referral_track_id,
                )
        except Exception as exc:
            log_event(
                level="ERROR",
                component="leaderboard",
                message="leaderboard_rebuild_failed",
                correlation_id=correlation_id,
                referral_track_id=referral_track_id,
                extra={
                    "tenant_code": tenant_code,
                    "referrer_ucn": instance.get("referrer_ucn") if instance else None,
                    "error": str(exc),
                },
            )

    except Exception as exc:
        log_event(
            level="ERROR",
            component="journey_orchestrator",
            message="processing_error",
            correlation_id=correlation_id,
            referral_track_id=referral_track_id or None,
            source_system=source_system,
            event_type=incoming_event,
            status_before=previous_status,
            extra={
                "tenant_code": tenant_code,
                "error": str(exc),
                "dedupe_key": dedupe_key,
            },
        )

        try:
            await _write_processing_audit_async(
                referral_track_id=referral_track_id or None,
                event_id=None,
                event_type=incoming_event,
                occurred_at=occurred_at,
                processing_status="FAILED",
                reason="error",
                previous_status=previous_status,
                new_status=previous_status,
                metadata={
                    "tenant_code": tenant_code,
                    "error": str(exc),
                    "source_system": source_system,
                    "dedupe_key": dedupe_key,
                },
            )
        except Exception:
            pass

        raise


def apply_progress_event_to_instance(
    *,
    instance: Dict[str, Any],
    incoming_event: str,
    occurred_at: datetime.datetime,
    journey_definition,
    journey_code: str,
    journey_version: str,
    replay_mode: bool = False,
) -> str:
    transition_result = _classify_transition(
        instance=instance,
        incoming_event=incoming_event,
        journey_definition=journey_definition,
    )

    if transition_result != "valid":
        return transition_result

    _apply_event_fields(instance, incoming_event, occurred_at, journey_definition)

    current_milestone = _derive_current_milestone(instance, journey_definition)
    is_complete, completed_at = _derive_completion(instance, journey_definition)

    instance["status"] = current_milestone
    instance["current_milestone"] = current_milestone
    instance["is_complete"] = is_complete
    instance["completed_at"] = completed_at
    instance["platform_status"] = _derive_platform_status(instance)

    snapshot = _derive_progress_snapshot(
        status=current_milestone,
        journey_code=journey_code,
        journey_version=journey_version,
        is_complete=is_complete,
    )

    instance.update(snapshot)

    return "valid"
