import os
import uuid

import pytest
import pytest_asyncio

os.environ.setdefault(
    "REFERRAL_CODE_SECRET",
    "test-referral-secret-123456789",
)

import services.journey_orchestrator as jo
import services.progress_service as ps
import services.replay_service as rs
from utils.db import async_db_cursor

try:
    from apps.api.schemas.progress import ProgressEventType, ProgressPostRequest
except Exception as exc:  # pragma: no cover
    raise RuntimeError(
        "Could not import ProgressPostRequest / ProgressEventType. "
        "Adjust the import in test/test_replay_service.py to match your project."
    ) from exc


pytestmark = [pytest.mark.e2e, pytest.mark.asyncio]


async def _insert_referrer_code(
    cur,
    referrer_code_id: str,
    referrer_ucn: str,
    referral_code: str,
    gaming_handle: str,
):
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
):
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
            $1, $2, $3, $4, $5,
            'VALIDATED', 'Transactional', 'DDA13', 'BANKING_TRANSACTIONAL', 'v1', TRUE
        )
        """,
        referral_track_id,
        referrer_code_id,
        referral_code,
        referrer_ucn,
        "FNB",
    )


async def _get_instance(cur, referral_track_id: str) -> dict:
    row = await cur.fetchrow(
        """
        SELECT
            referral_track_id,
            status,
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
            completed_at
        FROM referral_instances
        WHERE referral_track_id = $1
        """,
        referral_track_id,
    )
    assert row is not None, "Referral instance not found during test"
    return dict(row)


def _build_request(
    *,
    referral_track_id: str,
    event_type,
    occurred_at: str,
    source_event_id: str,
    referee_ucn: str | None = None,
    account_number: str | None = None,
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
        meta={"test": "replay_service"},
    )


async def _post_and_orchestrate(req):
    response, status = await ps.handle_progress_event(req, tenant_code="FNB")

    if not response["deduped"]:
        event_payload = {
            "eventType": "REFERRAL_PROGRESS_RECORDED",
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

        if getattr(req, "refereeUCN", None):
            event_payload["refereeUCN"] = req.refereeUCN

        if getattr(req, "accountNumber", None):
            event_payload["accountNumber"] = req.accountNumber

        await jo.handle_referral_progress_recorded(
            event_payload,
            tenant_code="FNB",
        )

    return response, status


async def _post_only(req):
    return await ps.handle_progress_event(req, tenant_code="FNB")


async def _seed_happy_path(track_id: str):
    await _post_and_orchestrate(
        _build_request(
            referral_track_id=track_id,
            event_type=ProgressEventType.UCN_CAPTURED,
            occurred_at="2026-04-01T09:55:00Z",
            source_event_id="evt-rp-ucn-1",
            referee_ucn="1234567890",
        )
    )

    await _post_and_orchestrate(
        _build_request(
            referral_track_id=track_id,
            event_type=ProgressEventType.ACCOUNT_OPENED,
            occurred_at="2026-04-01T10:00:00Z",
            source_event_id="evt-rp-open-1",
            referee_ucn="1234567890",
            account_number="123456789012",
        )
    )

    await _post_and_orchestrate(
        _build_request(
            referral_track_id=track_id,
            event_type=ProgressEventType.FUNDED,
            occurred_at="2026-04-01T10:10:00Z",
            source_event_id="evt-rp-funded-1",
            referee_ucn="1234567890",
        )
    )

    await _post_and_orchestrate(
        _build_request(
            referral_track_id=track_id,
            event_type=ProgressEventType.FIRST_TRANSACTION_COMPLETED,
            occurred_at="2026-04-01T10:15:00Z",
            source_event_id="evt-rp-ftc-1",
            referee_ucn="1234567890",
        )
    )


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

    yield {
        "referral_track_id": referral_track_id,
        "referrer_code_id": referrer_code_id,
    }

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


async def test_rebuild_referral_instance_matches_current_state(seeded_referral):
    track_id = seeded_referral["referral_track_id"]

    await _seed_happy_path(track_id)

    async with async_db_cursor() as cur:
        current = await _get_instance(cur, track_id)

    rebuilt = await rs.rebuild_referral_instance(track_id)

    assert rebuilt["referralTrackId"] == track_id
    assert rebuilt["eventsProcessed"] == 4
    assert rebuilt["applied"] == 4
    assert rebuilt["ignored"] == 0
    assert rebuilt["dryRun"] is True

    assert rebuilt["before"]["status"] == current["status"]
    assert bool(rebuilt["before"]["is_complete"]) == bool(current["is_complete"])
    assert rebuilt["before"]["progress_percent"] == current["progress_percent"]
    assert rebuilt["before"]["progress_band"] == current["progress_band"]
    assert rebuilt["before"]["display_status"] == current["display_status"]
    assert rebuilt["before"]["next_milestone"] == current["next_milestone"]

    assert rebuilt["after"]["status"] == current["status"]
    assert bool(rebuilt["after"]["is_complete"]) == bool(current["is_complete"])
    assert rebuilt["after"]["progress_percent"] == current["progress_percent"]
    assert rebuilt["after"]["progress_band"] == current["progress_band"]
    assert rebuilt["after"]["display_status"] == current["display_status"]
    assert rebuilt["after"]["next_milestone"] == current["next_milestone"]
    assert rebuilt["after"]["completed_at"] is not None

    assert rebuilt["ignoredEvents"] == []


async def test_rebuild_referral_instance_reports_ignored_duplicate_events(seeded_referral):
    track_id = seeded_referral["referral_track_id"]

    for event_type, occurred_at, source_event_id, account_number in [
        (ProgressEventType.UCN_CAPTURED, "2026-04-01T09:55:00Z", "evt-rp-dup-ucn-1", None),
        (ProgressEventType.UCN_CAPTURED, "2026-04-01T09:56:00Z", "evt-rp-dup-ucn-2", None),
        (ProgressEventType.ACCOUNT_OPENED, "2026-04-01T10:00:00Z", "evt-rp-dup-open-1", "123456789012"),
        (ProgressEventType.ACCOUNT_OPENED, "2026-04-01T10:01:00Z", "evt-rp-dup-open-2", "123456789012"),
        (ProgressEventType.FUNDED, "2026-04-01T10:10:00Z", "evt-rp-dup-funded-1", None),
        (ProgressEventType.FIRST_TRANSACTION_COMPLETED, "2026-04-01T10:15:00Z", "evt-rp-dup-ftc-1", None),
    ]:
        await _post_only(
            _build_request(
                referral_track_id=track_id,
                event_type=event_type,
                occurred_at=occurred_at,
                source_event_id=source_event_id,
                referee_ucn="1234567890",
                account_number=account_number,
            )
        )

    rebuilt = await rs.rebuild_referral_instance(track_id)

    assert rebuilt["eventsProcessed"] == 6
    assert rebuilt["applied"] == 4
    assert rebuilt["ignored"] == 2
    assert rebuilt["after"]["status"] == "FUNDED"
    assert rebuilt["after"]["is_complete"] is True
    assert len(rebuilt["ignoredEvents"]) == 2
    assert rebuilt["ignoredEvents"][0]["transition"] == "duplicate"
    assert rebuilt["ignoredEvents"][1]["transition"] == "duplicate"


async def test_rebuild_referral_instance_repairs_projection_when_not_dry_run(seeded_referral):
    track_id = seeded_referral["referral_track_id"]

    await _seed_happy_path(track_id)

    async with async_db_cursor() as cur:
        await cur.execute(
            """
            UPDATE referral_instances
            SET
                status = 'VALIDATED',
                ucn_captured_at = NULL,
                account_opened_at = NULL,
                account_activated_at = NULL,
                funded_at = NULL,
                debit_order_switched_at = NULL,
                salary_switched_at = NULL,
                first_transaction_completed_at = NULL,
                progress_percent = 0,
                progress_band = 'BROKEN',
                display_status = 'Broken projection',
                next_milestone = 'UCN_CAPTURED',
                is_complete = FALSE,
                completed_at = NULL,
                updated_at = NOW()
            WHERE referral_track_id = $1
            """,
            track_id,
        )

    async with async_db_cursor() as cur:
        broken = await _get_instance(cur, track_id)

    assert broken["status"] == "VALIDATED"
    assert broken["is_complete"] is False
    assert broken["progress_percent"] == 0
    assert broken["funded_at"] is None
    assert broken["first_transaction_completed_at"] is None

    repaired = await rs.rebuild_referral_instance(track_id, dry_run=False)

    assert repaired["dryRun"] is False
    assert repaired["eventsProcessed"] == 4
    assert repaired["applied"] == 4
    assert repaired["ignored"] == 0
    assert repaired["before"]["status"] == "VALIDATED"
    assert repaired["after"]["status"] == "FUNDED"
    assert repaired["after"]["is_complete"] is True
    assert repaired["after"]["progress_percent"] == 100

    async with async_db_cursor() as cur:
        current = await _get_instance(cur, track_id)

    assert current["status"] == "FUNDED"
    assert current["is_complete"] is True
    assert current["progress_percent"] == 100
    assert current["progress_band"] == repaired["after"]["progress_band"]
    assert current["display_status"] == repaired["after"]["display_status"]
    assert current["next_milestone"] == repaired["after"]["next_milestone"]
    assert current["funded_at"] is not None
    assert current["first_transaction_completed_at"] is not None
    assert current["completed_at"] is not None


async def test_rebuild_referral_instance_missing_instance_raises():
    missing_track_id = str(uuid.uuid4())

    with pytest.raises(ValueError, match="Referral instance not found"):
        await rs.rebuild_referral_instance(missing_track_id)