from __future__ import annotations

import datetime
import inspect
import json
from typing import Any, Dict, List, Optional, Tuple

from apps.api.schemas.progress import (
    ProgressEventType,
    ProgressPostRequest,
    ReferrerReferralProgressResponse,
    ReferralProgressItem,
)
from services.journey_definitions import (
    DEFAULT_JOURNEY_CODE,
    DEFAULT_JOURNEY_VERSION,
    get_journey_definition,
)
from services.vertical_identifier_service import validate_event_identifiers
from utils.crypto import (
    account_lookup_key,
    mask_account,
    sha256_hex,
    ucn_lookup_key,
)
from utils.db import db_connection
from utils.queue import enqueue_event

from services.progress_definitions import get_progress_definition


def _normalize_optional_identity(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    cleaned = value.strip()
    if not cleaned:
        return None
    if cleaned.lower() in {"string", "null", "none", "n/a", "na", "unknown", "test"}:
        return None
    return cleaned


def _normalize_source_system(value: Optional[str]) -> str:
    cleaned = _normalize_optional_identity(value)
    return cleaned.upper().replace(" ", "_") if cleaned else "PROGRESS_API"


def _normalize_product(value: Optional[str]) -> Optional[str]:
    cleaned = _normalize_optional_identity(value)
    if not cleaned:
        return None
    normalized = cleaned.strip().upper().replace(" ", "_")
    return {"TRANSACTIONAL": "TRANSACTIONAL"}.get(normalized, normalized)


def _normalize_sub_product(value: Optional[str]) -> Optional[str]:
    cleaned = _normalize_optional_identity(value)
    return cleaned.strip().upper() if cleaned else None


def _normalize_event_type(value: Any) -> str:
    raw = value.value if isinstance(value, ProgressEventType) else value
    return str(raw or "").strip().upper()


def _normalize_journey_code(value: Optional[str]) -> Optional[str]:
    cleaned = _normalize_optional_identity(value)
    return cleaned.strip().upper() if cleaned else None


def _normalize_journey_version(value: Optional[str]) -> Optional[str]:
    cleaned = _normalize_optional_identity(value)
    return cleaned.strip() if cleaned else None


def _utc_now() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc)


def _ensure_utc(dt: Optional[datetime.datetime]) -> datetime.datetime:
    if dt is None:
        return _utc_now()
    if dt.tzinfo is None:
        return dt.replace(tzinfo=datetime.timezone.utc)
    return dt.astimezone(datetime.timezone.utc)


def _isoz(dt: datetime.datetime) -> str:
    return _ensure_utc(dt).isoformat().replace("+00:00", "Z")


def _canonical_payload_hash(payload: Dict[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return sha256_hex(canonical)


def _build_dedupe_key(
    *,
    source_system: str,
    source_event_id: Optional[str],
    referral_track_id: str,
    event_type: str,
    occurred_at: datetime.datetime,
) -> str:
    raw = (
        f"{source_system}|{source_event_id}"
        if source_event_id
        else f"{source_system}|{referral_track_id}|{event_type}|{_isoz(occurred_at)}"
    )
    return sha256_hex(raw)


def _build_event_payload(
    req: ProgressPostRequest,
    referral_track_id: str,
    product: Optional[str],
    sub_product: Optional[str],
    deduped: bool,
    source_system: str,
    source_event_id: Optional[str],
    occurred_at: datetime.datetime,
    dedupe_key: str,
    tenant_code: str,
) -> Dict[str, Any]:
    now = _utc_now()

    payload: Dict[str, Any] = {
        "eventType": "REFERRAL_PROGRESS_RECORDED",
        "tenantCode": str(tenant_code).strip(),
        "referralTrackId": referral_track_id,
        "product": product,
        "subProduct": sub_product,
        "progressEventType": _normalize_event_type(req.eventType),
        "journeyCode": _normalize_journey_code(getattr(req, "journeyCode", None)),
        "journeyVersion": _normalize_journey_version(getattr(req, "journeyVersion", None)),
        "occurredAt": _isoz(occurred_at),
        "recordedAt": _isoz(now),
        "deduped": deduped,
        "sourceSystem": source_system,
        "sourceEventId": source_event_id,
        "dedupeKey": dedupe_key,
        "meta": req.meta or {},
    }

    if req.refereeUCN:
        referee_ucn = req.refereeUCN.strip()
        payload["refereeUCN"] = referee_ucn
        payload["refereeUCNLookupKey"] = ucn_lookup_key(referee_ucn)
        payload["refereeUCNHash"] = payload["refereeUCNLookupKey"]

    if req.accountNumber:
        account_number = req.accountNumber.strip()
        payload["accountNumber"] = account_number
        payload["accountNumberLookupKey"] = account_lookup_key(account_number)
        payload["accountNumberMasked"] = mask_account(account_number)
        payload["accountNumberHash"] = payload["accountNumberLookupKey"]

    return payload


def _is_self_referral(
    referrer_ucn: Optional[str],
    incoming_referee_ucn: Optional[str],
) -> bool:
    referrer = str(referrer_ucn or "").strip()
    referee = str(incoming_referee_ucn or "").strip()
    return bool(referrer and referee and referrer == referee)


async def handle_progress_event(
    req: ProgressPostRequest,
    tenant_code: str | None = None,
) -> Tuple[Dict[str, Any], int]:

    referral_track_id = req.referralTrackId.strip()
    product = _normalize_product(req.product)
    sub_product = _normalize_sub_product(req.subProduct)
    event_type = _normalize_event_type(req.eventType)
    requested_journey_code = _normalize_journey_code(getattr(req, "journeyCode", None))
    requested_journey_version = _normalize_journey_version(getattr(req, "journeyVersion", None))

    source_system = _normalize_source_system(getattr(req, "sourceSystem", None))
    source_event_id = _normalize_optional_identity(getattr(req, "sourceEventId", None))

    product_required_events = {
        ProgressEventType.ACCOUNT_OPENED.value,
        ProgressEventType.ACCOUNT_ACTIVATED.value,
        ProgressEventType.FUNDED.value,
        ProgressEventType.DEBIT_ORDER_SWITCHED.value,
        ProgressEventType.SALARY_SWITCHED.value,
        ProgressEventType.FIRST_TRANSACTION_COMPLETED.value,
    }

    identity_required_events = product_required_events

    if event_type == ProgressEventType.UCN_CAPTURED.value and not req.refereeUCN:
        return {
            "status": "error",
            "referralTrackId": referral_track_id,
            "product": product,
            "subProduct": sub_product,
            "eventType": event_type,
            "deduped": False,
            "message": "refereeUCN is required for UCN_CAPTURED",
        }, 400

    if event_type == ProgressEventType.ACCOUNT_OPENED.value:
        if not req.refereeUCN or not req.accountNumber:
            return {
                "status": "error",
                "referralTrackId": referral_track_id,
                "product": product,
                "subProduct": sub_product,
                "eventType": event_type,
                "deduped": False,
                "message": "refereeUCN and accountNumber are required for ACCOUNT_OPENED",
            }, 400

    if event_type in product_required_events and not product:
        return {
            "status": "error",
            "referralTrackId": referral_track_id,
            "product": product,
            "subProduct": sub_product,
            "eventType": event_type,
            "deduped": False,
            "message": f"product is required for {event_type}",
        }, 400

    if event_type in product_required_events and not sub_product:
        return {
            "status": "error",
            "referralTrackId": referral_track_id,
            "product": product,
            "subProduct": sub_product,
            "eventType": event_type,
            "deduped": False,
            "message": f"subProduct is required for {event_type}",
        }, 400

    occurred_at = _utc_now()

    incoming_referee_ucn = req.refereeUCN.strip() if req.refereeUCN else None
    incoming_referee_ucn_lookup_key = (
        ucn_lookup_key(incoming_referee_ucn) if incoming_referee_ucn else None
    )

    payload_for_hash: Dict[str, Any] = {
        "referralTrackId": referral_track_id,
        "product": product,
        "subProduct": sub_product,
        "eventType": event_type,
        "journeyCode": requested_journey_code,
        "journeyVersion": requested_journey_version,
        "occurredAt": _isoz(occurred_at),
        "sourceSystem": source_system,
        "sourceEventId": source_event_id,
        "meta": req.meta or {},
    }

    if req.refereeUCN:
        payload_for_hash["refereeUCNLookupKey"] = ucn_lookup_key(req.refereeUCN.strip())

    if req.accountNumber:
        payload_for_hash["accountNumberLookupKey"] = account_lookup_key(req.accountNumber.strip())

    event_payload_hash = _canonical_payload_hash(payload_for_hash)

    dedupe_key = _build_dedupe_key(
        source_system=source_system,
        source_event_id=source_event_id,
        referral_track_id=referral_track_id,
        event_type=event_type,
        occurred_at=occurred_at,
    )

    deduped = False

    async with db_connection() as conn:
        row = await conn.fetchrow(
            """
            SELECT
                referrer_ucn,
                product,
                sub_product,
                referee_ucn,
                referee_ucn_hash,
                journey_code,
                journey_version
            FROM referral_instances
            WHERE referral_track_id = $1
            AND tenant_code = $2
            """,
            referral_track_id,
            tenant_code,
        )

        if not row:
            return {
                "status": "error",
                "referralTrackId": referral_track_id,
                "product": product,
                "subProduct": sub_product,
                "eventType": event_type,
                "deduped": False,
                "message": "Referral instance not found",
            }, 404

        referrer_ucn = row["referrer_ucn"]
        existing_product = row["product"]
        existing_sub_product = row["sub_product"]
        existing_referee_ucn = row["referee_ucn"]
        existing_referee_ucn_hash = row["referee_ucn_hash"]
        existing_journey_code = _normalize_journey_code(row["journey_code"])
        existing_journey_version = _normalize_journey_version(row["journey_version"])
        journey_code = requested_journey_code or existing_journey_code or DEFAULT_JOURNEY_CODE
        journey_version = requested_journey_version or existing_journey_version or DEFAULT_JOURNEY_VERSION

        if requested_journey_code and existing_journey_code and requested_journey_code != existing_journey_code:
            return {
                "status": "error",
                "referralTrackId": referral_track_id,
                "product": product,
                "subProduct": sub_product,
                "eventType": event_type,
                "journeyCode": journey_code,
                "journeyVersion": journey_version,
                "deduped": False,
                "message": f"Journey mismatch. Referral is already bound to '{existing_journey_code}'",
            }, 400

        if requested_journey_version and existing_journey_version and requested_journey_version != existing_journey_version:
            return {
                "status": "error",
                "referralTrackId": referral_track_id,
                "product": product,
                "subProduct": sub_product,
                "eventType": event_type,
                "journeyCode": journey_code,
                "journeyVersion": journey_version,
                "deduped": False,
                "message": f"Journey version mismatch. Referral is already bound to '{existing_journey_version}'",
            }, 400

        try:
            journey_definition = get_journey_definition(journey_code, journey_version)
        except ValueError:
            return {
                "status": "error",
                "referralTrackId": referral_track_id,
                "product": product,
                "subProduct": sub_product,
                "eventType": event_type,
                "journeyCode": journey_code,
                "journeyVersion": journey_version,
                "deduped": False,
                "message": f"Unsupported journey definition: {journey_code}:{journey_version}",
            }, 400

        supported_events = set(journey_definition.event_to_timestamp_field) | set(journey_definition.core_sequence)
        if event_type not in supported_events:
            return {
                "status": "error",
                "referralTrackId": referral_track_id,
                "product": product,
                "subProduct": sub_product,
                "eventType": event_type,
                "journeyCode": journey_code,
                "journeyVersion": journey_version,
                "deduped": False,
                "message": f"eventType '{event_type}' is not supported for {journey_code}:{journey_version}",
            }, 400

        identifier_payload = {
            "refereeUCN": req.refereeUCN,
            "accountNumber": req.accountNumber,
            "meta": req.meta or {},
        }
        identifiers_ok, identifier_errors = validate_event_identifiers(
            journey_code=journey_code,
            journey_version=journey_version,
            event_type=event_type,
            payload=identifier_payload,
        )
        if not identifiers_ok:
            return {
                "status": "error",
                "referralTrackId": referral_track_id,
                "product": product,
                "subProduct": sub_product,
                "eventType": event_type,
                "journeyCode": journey_code,
                "journeyVersion": journey_version,
                "deduped": False,
                "message": "; ".join(identifier_errors),
            }, 400

        if _is_self_referral(referrer_ucn, incoming_referee_ucn):
            return {
                "status": "error",
                "referralTrackId": referral_track_id,
                "product": product,
                "subProduct": sub_product,
                "eventType": event_type,
                "deduped": False,
                "errorCode": "SELF_REFERRAL_NOT_ALLOWED",
                "message": "Referrer and referee cannot be the same customer.",
            }, 409

        if event_type in identity_required_events:
            if not incoming_referee_ucn:
                return {
                    "status": "error",
                    "referralTrackId": referral_track_id,
                    "product": product,
                    "subProduct": sub_product,
                    "eventType": event_type,
                    "deduped": False,
                    "message": f"refereeUCN is required for {event_type}",
                }, 400

            if existing_referee_ucn:
                if incoming_referee_ucn != str(existing_referee_ucn).strip():
                    return {
                        "status": "error",
                        "referralTrackId": referral_track_id,
                        "product": product,
                        "subProduct": sub_product,
                        "eventType": event_type,
                        "deduped": False,
                        "message": "refereeUCN does not match the referral instance",
                    }, 400
            elif existing_referee_ucn_hash:
                if incoming_referee_ucn_lookup_key != existing_referee_ucn_hash:
                    return {
                        "status": "error",
                        "referralTrackId": referral_track_id,
                        "product": product,
                        "subProduct": sub_product,
                        "eventType": event_type,
                        "deduped": False,
                        "message": "refereeUCN does not match the referral instance",
                    }, 400

        if product is not None and existing_product and _normalize_product(existing_product) != product:
            return {
                "status": "error",
                "referralTrackId": referral_track_id,
                "product": product,
                "subProduct": sub_product,
                "eventType": event_type,
                "deduped": False,
                "message": f"Product mismatch. Referral is already bound to '{existing_product}'",
            }, 400

        if sub_product is not None and existing_sub_product and _normalize_sub_product(existing_sub_product) != sub_product:
            return {
                "status": "error",
                "referralTrackId": referral_track_id,
                "product": product,
                "subProduct": sub_product,
                "eventType": event_type,
                "deduped": False,
                "message": f"SubProduct mismatch. Referral is already bound to '{existing_sub_product}'",
            }, 400

        should_bind_product = (
            product is not None
            and (existing_product is None or not str(existing_product).strip())
        )

        should_bind_sub_product = (
            sub_product is not None
            and (existing_sub_product is None or not str(existing_sub_product).strip())
        )

        should_bind_journey = (
            requested_journey_code is not None
            and (existing_journey_code is None or not str(existing_journey_code).strip())
        )

        should_bind_journey_version = (
            requested_journey_version is not None
            and (existing_journey_version is None or not str(existing_journey_version).strip())
        )

        if should_bind_product or should_bind_sub_product or should_bind_journey or should_bind_journey_version:
            await conn.execute(
                """
                UPDATE referral_instances
                SET product = COALESCE(product, $1),
                    sub_product = COALESCE(sub_product, $2),
                    journey_code = COALESCE(journey_code, $5),
                    journey_version = COALESCE(journey_version, $6),
                    updated_at = NOW()
                WHERE referral_track_id = $3
                AND tenant_code = $4
                """,
                product,
                sub_product,
                referral_track_id,
                tenant_code,
                journey_code,
                journey_version,
            )

        inserted = await conn.fetchrow(
            """
            INSERT INTO referral_progress_events (
                referral_track_id,
                product,
                sub_product,
                event_type,
                source_system,
                source_event_id,
                occurred_at,
                received_at,
                event_payload_hash,
                dedupe_key,
                idempotency_version,
                meta
            )
            VALUES (
                $1, $2, $3, $4, $5, $6, $7, NOW(), $8, $9, 1, $10
            )
            ON CONFLICT (dedupe_key) DO NOTHING
            RETURNING id
            """,
            referral_track_id,
            product,
            sub_product,
            event_type,
            source_system,
            source_event_id,
            occurred_at,
            event_payload_hash,
            dedupe_key,
            json.dumps(req.meta) if req.meta is not None else None,
        )

        if not inserted:
            deduped = True

    if not deduped:
        payload = _build_event_payload(
            req=req,
            referral_track_id=referral_track_id,
            product=product,
            sub_product=sub_product,
            deduped=False,
            source_system=source_system,
            source_event_id=source_event_id,
            occurred_at=occurred_at,
            dedupe_key=dedupe_key,
            tenant_code=tenant_code,
        )
        enqueue_result = enqueue_event(payload)
        if inspect.isawaitable(enqueue_result):
            await enqueue_result

    return {
        "status": "ok",
        "referralTrackId": referral_track_id,
        "product": product,
        "subProduct": sub_product,
        "eventType": event_type,
        "journeyCode": journey_code,
        "journeyVersion": journey_version,
        "deduped": deduped,
        "message": "Progress recorded" if not deduped else "Progress already recorded (deduped)",
        "sourceSystem": source_system,
        "sourceEventId": source_event_id,
        "occurredAt": _isoz(occurred_at),
        "dedupeKey": dedupe_key,
    }, 200 if deduped else 201


def _resolve_next_milestone_for_ui(
    *,
    journey_code: Optional[str],
    journey_version: Optional[str],
    status: Optional[str],
    stored_next_milestone: Optional[str],
) -> Optional[str]:
    if stored_next_milestone is not None:
        sn = str(stored_next_milestone).strip()
        if sn:
            return sn

    if not status:
        return None

    code = (journey_code or "").strip() or DEFAULT_JOURNEY_CODE
    ver = (journey_version or "").strip() or DEFAULT_JOURNEY_VERSION

    try:
        pdef = get_progress_definition(code, ver)
    except ValueError:
        return None

    milestone = pdef.milestones.get(str(status).strip().upper())
    return milestone.next_milestone if milestone else None


async def get_referrals_progress_by_referrer_ucn(
    referrer_ucn: str,
    tenant_code: str,
) -> ReferrerReferralProgressResponse:
    async with db_connection() as conn:
        referral_rows = await conn.fetch(
            """
            SELECT
                referral_track_id,
                referee_alias,
                product,
                sub_product,
                status,
                journey_code,
                journey_version,
                created_at,
                updated_at,
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
                completed_at
            FROM referral_instances
            WHERE referrer_ucn = $1
            AND tenant_code = $2
            ORDER BY created_at DESC
            """,
            referrer_ucn,
            tenant_code,
        )

    if not referral_rows:
        return ReferrerReferralProgressResponse(
            referrerUcn=referrer_ucn,
            totalReferrals=0,
            completedReferralsCount=0,
            inProgressReferralsCount=0,
            hasActiveReferrals=False,
            items=[],
        )

    items: List[ReferralProgressItem] = []
    completed_count = 0
    in_progress_count = 0

    for row in referral_rows:
        referral_track_id = row["referral_track_id"]
        alias = row["referee_alias"]
        product = row["product"]
        sub_product = row["sub_product"]
        status = row["status"]
        journey_code = row["journey_code"]
        journey_version = row["journey_version"]
        created_at = row["created_at"]
        updated_at = row["updated_at"]
        account_opened_at = row["account_opened_at"]
        account_activated_at = row["account_activated_at"]
        funded_at = row["funded_at"]
        debit_order_switched_at = row["debit_order_switched_at"]
        salary_switched_at = row["salary_switched_at"]
        first_transaction_completed_at = row["first_transaction_completed_at"]
        progress_percent = row["progress_percent"]
        display_status = row["display_status"]
        next_milestone = row["next_milestone"]
        is_complete = row["is_complete"]
        completed_at = row["completed_at"]

        resolved_progress_percent = progress_percent if progress_percent is not None else 0

        status_label = None
        if status:
            s = str(status).strip()
            if s:
                status_label = s.replace("_", " ").title()

        resolved_current_milestone = display_status or status_label or "Not started"

        if is_complete:
            completed_count += 1
            resolved_progress_percent = 100
            resolved_current_milestone = display_status or "Completed"
            resolved_next_milestone = None
            resolved_status = "COMPLETED"
        else:
            in_progress_count += 1
            resolved_status = status
            resolved_next_milestone = _resolve_next_milestone_for_ui(
                journey_code=journey_code,
                journey_version=journey_version,
                status=status,
                stored_next_milestone=next_milestone,
            )

        timestamp_candidates = [
            completed_at,
            first_transaction_completed_at,
            salary_switched_at,
            debit_order_switched_at,
            funded_at,
            account_activated_at,
            account_opened_at,
            updated_at,
            created_at,
        ]

        timestamp_candidates = [
            _ensure_utc(ts)
            for ts in timestamp_candidates
            if ts is not None
        ]

        resolved_last_updated_at = max(timestamp_candidates) if timestamp_candidates else None

        items.append(
            ReferralProgressItem(
                referralTrackId=str(referral_track_id),
                alias=alias,
                product=product,
                subProduct=sub_product,
                progressPercent=resolved_progress_percent,
                currentMilestone=resolved_current_milestone,
                nextMilestone=resolved_next_milestone,
                status=resolved_status,
                lastUpdatedAt=resolved_last_updated_at,
            )
        )

    return ReferrerReferralProgressResponse(
        referrerUcn=referrer_ucn,
        totalReferrals=len(items),
        completedReferralsCount=completed_count,
        inProgressReferralsCount=in_progress_count,
        hasActiveReferrals=in_progress_count > 0,
        items=items,
    )
