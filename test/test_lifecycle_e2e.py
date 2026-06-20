from __future__ import annotations

import os
import uuid
from typing import Optional

import pytest
import pytest_asyncio

os.environ.setdefault("REFERRAL_CODE_SECRET", "test-referral-secret-123456789")

import services.journey_orchestrator as jo
import services.progress_service as ps
from utils.db import async_db_cursor

try:
    from apps.api.schemas.progress import ProgressEventType, ProgressPostRequest
except Exception as exc:  # pragma: no cover
    raise RuntimeError(
        "Could not import ProgressPostRequest / ProgressEventType. "
        "Adjust the import in tests/test_lifecycle_e2e.py to match your project."
    ) from exc


pytestmark = [pytest.mark.e2e, pytest.mark.asyncio]


async def _insert_referrer_code(
    cur,
    referrer_code_id: str,
    referrer_ucn: str,
    referral_code: str,
    gaming_handle: str,
) -> None:
    await cur.execute(
        """
        INSERT INTO referrer_codes (
            referrer_code_id,
            referrer_ucn,
            referrer_ucn_hash,
            referral_code,
            gaming_handle,
            sticker,
            tenant_code,
            segment
        )
        VALUES ($1, $2, $3, $4, $5, 'TEST', 'FNB', 'TEST_SEGMENT')
        """,
        referrer_code_id,
        referrer_ucn,
        f"hash-{referrer_ucn}",
        referral_code,
        gaming_handle,
    )


async def _insert_referral_instance(
    cur,
    referral_track_id: str,
    referrer_code_id: str,
    referral_code: str,
    referrer_ucn: str,
) -> None:
    await cur.execute(
        """
        INSERT INTO referral_instances (
            referral_track_id,
            referrer_code_id,
            referral_code,
            referrer_ucn,
            tenant_code,
            status,
            product,
            sub_product,
            journey_code,
            journey_version,
            accepted_terms
        )
        VALUES (
            $1, $2, $3, $4,
            'FNB',
            'VALIDATED', 'Transactional', 'DDA13', 'BANKING_TRANSACTIONAL', 'v1', TRUE
        )
        """,
        referral_track_id,
        referrer_code_id,
        referral_code,
        referrer_ucn,
    )


async def _get_instance(cur, referral_track_id: str) -> dict:
    row = await cur.fetchrow(
        """
        SELECT
            referral_track_id,
            status,
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
        WHERE referral_track_id = $1
        """,
        referral_track_id,
    )
    assert row is not None, "Referral instance not found during test"
    return dict(row)


async def _count_progress_events(cur, referral_track_id: str) -> int:
    return await cur.fetchval(
        """
        SELECT COUNT(*)
        FROM referral_progress_events
        WHERE referral_track_id = $1
        """,
        referral_track_id,
    )


async def _get_audit_rows(cur, referral_track_id: str) -> list[dict]:
    rows = await cur.fetch(
        """
        SELECT
            event_type,
            processing_status,
            reason,
            previous_status,
            new_status
        FROM referral_processing_audit
        WHERE referral_track_id = $1
        ORDER BY processed_at, id
        """,
        referral_track_id,
    )
    return [dict(row) for row in rows]


async def _get_latest_audit(cur, referral_track_id: str) -> dict | None:
    row = await cur.fetchrow(
        """
        SELECT
            event_type,
            processing_status,
            reason,
            previous_status,
            new_status
        FROM referral_processing_audit
        WHERE referral_track_id = $1
        ORDER BY processed_at DESC, id DESC
        LIMIT 1
        """,
        referral_track_id,
    )
    return dict(row) if row else None


def _build_request(
    *,
    referral_track_id: str,
    event_type,
    occurred_at: str,
    source_event_id: str,
    referee_ucn: Optional[str] = None,
    account_number: Optional[str] = None,
):
    return ProgressPostRequest(
        referralTrackId=referral_track_id,
        product="Transactional",
        subProduct="DDA13",
        eventType=event_type,
        occurredAt=occurred_at,
        sourceSystem="E2E_TEST",
        sourceEventId=source_event_id,
        refereeUCN=referee_ucn,
        accountNumber=account_number,
        meta={"test": "lifecycle_e2e"},
    )


async def _post_and_orchestrate(req):
    response, status = await ps.handle_progress_event(req, tenant_code="FNB")

    if not response["deduped"]:
        event_payload = {
            "eventType": "REFERRAL_PROGRESS_RECORDED",
            "tenantCode": "FNB",
            "referralTrackId": response["referralTrackId"],
            "product": response["product"],
            "subProduct": response["subProduct"],
            "progressEventType": response["eventType"],
            "occurredAt": response["occurredAt"],
            "deduped": response["deduped"],
            "sourceSystem": response["sourceSystem"],
            "sourceEventId": response["sourceEventId"],
            "dedupeKey": response["dedupeKey"],
        }

        await jo.handle_referral_progress_recorded(event_payload, tenant_code="FNB")

    return response, status


@pytest_asyncio.fixture
async def seeded_referral():
    referrer_code_id = str(uuid.uuid4())
    referral_track_id = str(uuid.uuid4())
    referral_code = f"REF-{uuid.uuid4().hex[:8].upper()}"
    referrer_ucn = "9999999999"

    async with async_db_cursor() as cur:
        await _insert_referrer_code(
            cur,
            referrer_code_id=referrer_code_id,
            referrer_ucn=referrer_ucn,
            referral_code=referral_code,
            gaming_handle=f"tester_{uuid.uuid4().hex[:6]}",
        )
        await _insert_referral_instance(
            cur,
            referral_track_id=referral_track_id,
            referrer_code_id=referrer_code_id,
            referral_code=referral_code,
            referrer_ucn=referrer_ucn,
        )

    try:
        yield {
            "referral_track_id": referral_track_id,
            "referrer_code_id": referrer_code_id,
            "referral_code": referral_code,
            "referrer_ucn": referrer_ucn,
        }
    finally:
        async with async_db_cursor() as cur:
            await cur.execute(
                "DELETE FROM referral_processing_audit WHERE referral_track_id = $1",
                referral_track_id,
            )
            await cur.execute(
                "DELETE FROM referral_progress_events WHERE referral_track_id = $1",
                referral_track_id,
            )
            await cur.execute(
                "DELETE FROM referral_instances WHERE referral_track_id = $1",
                referral_track_id,
            )
            await cur.execute(
                "DELETE FROM referrer_codes WHERE referrer_code_id = $1",
                referrer_code_id,
            )


async def test_happy_path_completion_via_salary_switch(seeded_referral):
    track_id = seeded_referral["referral_track_id"]

    await _post_and_orchestrate(
        _build_request(
            referral_track_id=track_id,
            event_type=ProgressEventType.UCN_CAPTURED,
            occurred_at="2026-04-01T09:55:00Z",
            source_event_id="evt-ucn-1",
            referee_ucn="1234567890",
        )
    )

    async with async_db_cursor() as cur:
        row = await _get_instance(cur, track_id)
    assert row["status"] == "UCN_CAPTURED"

    await _post_and_orchestrate(
        _build_request(
            referral_track_id=track_id,
            event_type=ProgressEventType.ACCOUNT_OPENED,
            occurred_at="2026-04-01T10:00:00Z",
            source_event_id="evt-opened-1",
            referee_ucn="1234567890",
            account_number="123456789012",
        )
    )

    async with async_db_cursor() as cur:
        row = await _get_instance(cur, track_id)
    assert row["status"] == "ACCOUNT_OPENED"
    assert row["account_opened_at"] is not None
    assert row["is_complete"] is False

    await _post_and_orchestrate(
        _build_request(
            referral_track_id=track_id,
            event_type=ProgressEventType.ACCOUNT_ACTIVATED,
            occurred_at="2026-04-01T10:05:00Z",
            source_event_id="evt-activated-1",
            referee_ucn="1234567890",
            account_number="123456789012",
        )
    )

    async with async_db_cursor() as cur:
        row = await _get_instance(cur, track_id)
    assert row["status"] == "ACCOUNT_ACTIVATED"
    assert row["account_activated_at"] is not None
    assert row["is_complete"] is False

    await _post_and_orchestrate(
        _build_request(
            referral_track_id=track_id,
            event_type=ProgressEventType.FUNDED,
            occurred_at="2026-04-01T10:10:00Z",
            source_event_id="evt-funded-1",
            referee_ucn="1234567890",
            account_number="123456789012",
        )
    )

    async with async_db_cursor() as cur:
        row = await _get_instance(cur, track_id)
    assert row["status"] == "FUNDED"
    assert row["funded_at"] is not None
    assert row["is_complete"] is False

    await _post_and_orchestrate(
        _build_request(
            referral_track_id=track_id,
            event_type=ProgressEventType.SALARY_SWITCHED,
            occurred_at="2026-04-01T10:15:00Z",
            source_event_id="evt-salary-1",
            referee_ucn="1234567890",
            account_number="123456789012",
        )
    )

    async with async_db_cursor() as cur:
        row = await _get_instance(cur, track_id)
        audits = await _get_audit_rows(cur, track_id)

    assert row["status"] == "FUNDED"
    assert row["salary_switched_at"] is not None
    assert row["is_complete"] is True
    assert row["completed_at"] is not None
    assert row["progress_percent"] == 100

    processed = [a for a in audits if a["processing_status"] == "PROCESSED"]
    assert [a["event_type"] for a in processed] == [
        "UCN_CAPTURED",
        "ACCOUNT_OPENED",
        "ACCOUNT_ACTIVATED",
        "FUNDED",
        "SALARY_SWITCHED",
    ]


async def test_duplicate_event_does_not_create_second_fact_or_mutate_twice(seeded_referral):
    track_id = seeded_referral["referral_track_id"]

    await _post_and_orchestrate(
        _build_request(
            referral_track_id=track_id,
            event_type=ProgressEventType.UCN_CAPTURED,
            occurred_at="2026-04-01T10:55:00Z",
            source_event_id="evt-ucn-dedup-1",
            referee_ucn="1234567890",
        )
    )

    req = _build_request(
        referral_track_id=track_id,
        event_type=ProgressEventType.ACCOUNT_OPENED,
        occurred_at="2026-04-01T11:00:00Z",
        source_event_id="evt-opened-dedup-1",
        referee_ucn="1234567890",
        account_number="123456789012",
    )

    response1, status1 = await _post_and_orchestrate(req)
    assert status1 == 201
    assert response1["deduped"] is False

    response2, status2 = await _post_and_orchestrate(req)
    assert status2 == 200
    assert response2["deduped"] is True

    async with async_db_cursor() as cur:
        count = await _count_progress_events(cur, track_id)
        audits = await _get_audit_rows(cur, track_id)

    assert count == 2
    assert len(audits) == 2
    assert audits[0]["event_type"] == "UCN_CAPTURED"
    assert audits[0]["processing_status"] == "PROCESSED"
    assert audits[1]["event_type"] == "ACCOUNT_OPENED"
    assert audits[1]["processing_status"] == "PROCESSED"


async def test_out_of_order_funded_does_not_advance_state_and_is_audited(seeded_referral):
    track_id = seeded_referral["referral_track_id"]

    response, status = await _post_and_orchestrate(
        _build_request(
            referral_track_id=track_id,
            event_type=ProgressEventType.FUNDED,
            occurred_at="2026-04-01T12:00:00Z",
            source_event_id="evt-funded-ooo-1",
            referee_ucn="1234567890",
        )
    )

    assert status == 201
    assert response["deduped"] is False

    async with async_db_cursor() as cur:
        count = await _count_progress_events(cur, track_id)
        row = await _get_instance(cur, track_id)
        audit = await _get_latest_audit(cur, track_id)

    assert count == 1
    assert row["status"] == "VALIDATED"
    assert row["funded_at"] is None
    assert row["is_complete"] is False

    assert audit is not None
    assert audit["event_type"] == "FUNDED"
    assert audit["processing_status"] == "IGNORED"
    assert audit["reason"] == "out_of_order"
    assert audit["previous_status"] == "VALIDATED"
    assert audit["new_status"] == "VALIDATED"


async def test_backward_event_is_ignored_and_audited(seeded_referral):
    track_id = seeded_referral["referral_track_id"]

    for event_type, occurred_at, source_event_id, account_number in [
        (ProgressEventType.UCN_CAPTURED, "2026-04-01T13:00:00Z", "evt-ucn-back-1", None),
        (ProgressEventType.ACCOUNT_OPENED, "2026-04-01T13:05:00Z", "evt-open-back-1", "123456789012"),
        (ProgressEventType.ACCOUNT_ACTIVATED, "2026-04-01T13:10:00Z", "evt-act-back-1", None),
        (ProgressEventType.FUNDED, "2026-04-01T13:15:00Z", "evt-funded-back-1", "123456789012"),
        (ProgressEventType.ACCOUNT_OPENED, "2026-04-01T13:20:00Z", "evt-open-back-2", "123456789012"),
    ]:
        await _post_and_orchestrate(
            _build_request(
                referral_track_id=track_id,
                event_type=event_type,
                occurred_at=occurred_at,
                source_event_id=source_event_id,
                referee_ucn="1234567890",
                account_number=account_number,
            )
        )

    async with async_db_cursor() as cur:
        row = await _get_instance(cur, track_id)
        audits = await _get_audit_rows(cur, track_id)

    assert row["status"] == "FUNDED"

    matching = [
        a
        for a in audits
        if a["event_type"] == "ACCOUNT_OPENED"
        and a["processing_status"] == "IGNORED"
        and a["reason"] == "duplicate"
        and a["previous_status"] == "FUNDED"
        and a["new_status"] == "FUNDED"
    ]
    assert len(matching) >= 1


async def test_completion_requires_funded_plus_sub_function(seeded_referral):
    track_id = seeded_referral["referral_track_id"]

    for event_type, occurred_at, source_event_id, account_number in [
        (ProgressEventType.UCN_CAPTURED, "2026-04-01T14:00:00Z", "evt-ucn-comp-1", None),
        (ProgressEventType.ACCOUNT_OPENED, "2026-04-01T14:05:00Z", "evt-open-comp-1", "123456789012"),
        (ProgressEventType.FUNDED, "2026-04-01T14:10:00Z", "evt-funded-comp-1", None),
    ]:
        await _post_and_orchestrate(
            _build_request(
                referral_track_id=track_id,
                event_type=event_type,
                occurred_at=occurred_at,
                source_event_id=source_event_id,
                referee_ucn="1234567890",
                account_number=account_number,
            )
        )

    async with async_db_cursor() as cur:
        row = await _get_instance(cur, track_id)

    assert row["status"] == "FUNDED"
    assert row["is_complete"] is False

    await _post_and_orchestrate(
        _build_request(
            referral_track_id=track_id,
            event_type=ProgressEventType.FIRST_TRANSACTION_COMPLETED,
            occurred_at="2026-04-01T14:15:00Z",
            source_event_id="evt-ftc-comp-1",
            referee_ucn="1234567890",
        )
    )

    async with async_db_cursor() as cur:
        row = await _get_instance(cur, track_id)
        audits = await _get_audit_rows(cur, track_id)

    assert row["status"] == "FUNDED"
    assert row["first_transaction_completed_at"] is not None
    assert row["is_complete"] is True
    assert row["completed_at"] is not None

    processed = [
        a
        for a in audits
        if a["event_type"] == "FIRST_TRANSACTION_COMPLETED"
        and a["processing_status"] == "PROCESSED"
        and a["previous_status"] == "FUNDED"
        and a["new_status"] == "FUNDED"
    ]
    assert len(processed) == 1