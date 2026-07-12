from __future__ import annotations

# ruff: noqa: E402,I001

import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest

os.environ.setdefault("REFERRAL_CODE_SECRET", "test-referral-secret-123456789")

from services import campaign_readiness_service as campaign_readiness
from services import link_code_service
from services import outcome_trace_service
from services import progress_service
from services import referral_code
from utils.crypto import ucn_lookup_key


class FakeTransaction:
    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return None


class FakeAsyncConn:
    def __init__(
        self,
        *,
        fetchrow_values: list[dict | None] | None = None,
        fetch_values: list[list[dict]] | None = None,
        progress_inserted: bool = True,
        progress_instance_row: dict | None = None,
    ):
        self.fetchrow_values = list(fetchrow_values or [])
        self.fetch_values = list(fetch_values or [])
        self.progress_inserted = progress_inserted
        self.progress_instance_row = progress_instance_row
        self.executed: list[tuple[str, tuple]] = []

    def transaction(self):
        return FakeTransaction()

    async def fetchrow(self, sql, *params):
        self.executed.append((sql, params))
        if "FROM referral_instances" in sql and "referrer_ucn" in sql:
            return self.progress_instance_row or {
                "referrer_ucn": "5555555555",
                "product": "Transactional",
                "sub_product": "DDA13",
                "referee_ucn": "1234567890",
                "referee_ucn_hash": ucn_lookup_key("1234567890"),
                "journey_code": "BANKING_TRANSACTIONAL",
                "journey_version": "v1",
            }
        if "INSERT INTO referral_progress_events" in sql:
            return {"id": 123} if self.progress_inserted else None
        if self.fetchrow_values:
            return self.fetchrow_values.pop(0)
        return None

    async def fetch(self, sql, *params):
        self.executed.append((sql, params))
        if self.fetch_values:
            return self.fetch_values.pop(0)
        return []

    async def execute(self, sql, *params):
        self.executed.append((sql, params))
        return "EXECUTE 1"


def _patch_db(monkeypatch, module, conn: FakeAsyncConn) -> None:
    @asynccontextmanager
    async def fake_db_connection():
        yield conn

    monkeypatch.setattr(module, "db_connection", fake_db_connection)


def _campaign_row(**overrides):
    row = {
        "campaign_code": "CAMP001",
        "tenant_code": "FNB",
        "segment": "PERSONAL",
        "name": "Referral SaaS Campaign",
        "is_active": True,
        "starts_at": None,
        "ends_at": None,
        "max_uses": 100,
        "uses_count": 3,
    }
    row.update(overrides)
    return row


def _policy_row(**overrides):
    row = {
        "campaign_code": "CAMP001",
        "tenant_code": "FNB",
        "version": 1,
        "is_active": True,
        "rolling_window_days": 30,
        "updated_at": datetime(2026, 7, 12, tzinfo=timezone.utc),
    }
    row.update(overrides)
    return row


def _progress_request(*, source_event_id="evt-account-opened-1", **overrides):
    request = {
        "referralTrackId": "11111111-1111-4111-8111-111111111111",
        "product": "Transactional",
        "subProduct": "DDA13",
        "eventType": "ACCOUNT_OPENED",
        "journeyCode": "BANKING_TRANSACTIONAL",
        "journeyVersion": "v1",
        "sourceSystem": "CORE_BANKING",
        "sourceEventId": source_event_id,
        "refereeUCN": "1234567890",
        "accountNumber": "123456789012",
        "meta": {"channel": "api"},
    }
    request.update(overrides)
    return SimpleNamespace(**request)


def _outcome_row():
    return {
        "referral_track_id": "11111111-1111-4111-8111-111111111111",
        "tenant_code": "FNB",
        "referral_code": "REF123",
        "status": "ACCOUNT_OPENED",
        "is_complete": False,
        "product": "Transactional",
        "sub_product": "DDA13",
        "journey_code": "BANKING_TRANSACTIONAL",
        "journey_version": "v1",
        "validated_at": datetime(2026, 7, 12, tzinfo=timezone.utc),
        "created_at": datetime(2026, 7, 12, tzinfo=timezone.utc),
        "updated_at": datetime(2026, 7, 12, tzinfo=timezone.utc),
        "completed_at": None,
        "referrer_code_id": str(uuid4()),
        "referrer_display_ref": "SafeHandle",
        "sticker": "QR001",
        "segment": "PERSONAL",
    }


def _trace_fetches():
    return [
        [
            {
                "source_type": "CAMPAIGN_REFERRAL_LINK",
                "campaign_track_id": str(uuid4()),
                "referral_track_id": "11111111-1111-4111-8111-111111111111",
                "campaign_code": "CAMP001",
                "tenant_code": "FNB",
                "campaign_track_status": "ATTRIBUTED",
                "source_confidence": "MEDIUM",
            }
        ],
        [],
        [
            {
                "source": "REFERRAL_PROGRESS_EVENT",
                "event_id": "progress-event-1",
                "referral_track_id": "11111111-1111-4111-8111-111111111111",
                "event_type": "ACCOUNT_OPENED",
                "source_system": "CORE_BANKING",
                "source_event_id": "evt-account-opened-1",
                "dedupe_key": "dedupe-1",
            }
        ],
        [],
        [],
        [],
        [],
        [],
        [],
        [],
        [],
    ]


@pytest.mark.asyncio
async def test_referral_saas_local_golden_path_uses_shared_primitives(monkeypatch):
    readiness_conn = FakeAsyncConn(fetchrow_values=[_campaign_row(), _policy_row()])
    _patch_db(monkeypatch, campaign_readiness, readiness_conn)

    readiness = await campaign_readiness.get_campaign_readiness(
        tenant_code="fnb",
        campaign_code="camp001",
        operation="create_track",
    )

    assert readiness["readiness"] == "READY"
    assert readiness["can_proceed"] is True
    assert readiness["blockers"] == []

    issue_conn = FakeAsyncConn(fetchrow_values=[None])
    _patch_db(monkeypatch, referral_code, issue_conn)
    monkeypatch.setattr(referral_code, "_identity_lookup_key", lambda value: "ucn-hash")
    monkeypatch.setattr(referral_code, "_generate_referral_code", lambda: "REF123")

    async def pick_handle(_conn, preferred):
        return preferred or "SafeHandle"

    monkeypatch.setattr(referral_code, "_pick_handle", pick_handle)

    issued, issue_status = await referral_code.get_or_create_referrer_code(
        referrer_ucn="5555555555",
        tenant="FNB",
        sticker="QR001",
        segment="PERSONAL",
        preferred_handle="SafeHandle",
        accepted_terms=True,
    )

    assert issue_status == 201
    assert issued["created"] is True
    assert issued["referral_code"] == "REF123"

    validation_conn = FakeAsyncConn(
        fetchrow_values=[
            {
                "referrer_code_id": "code-id-1",
                "referrer_ucn": "5555555555",
            }
        ]
    )
    _patch_db(monkeypatch, referral_code, validation_conn)
    monkeypatch.setattr(referral_code, "_normalize_alias", lambda value: "Alias1")
    monkeypatch.setattr(
        referral_code,
        "_validate_alias",
        lambda value: (True, None, "alias1"),
    )

    validation, validation_status = await referral_code.validate_referral_code(
        tenant_code="FNB",
        referral_code="REF123",
        accepted_terms=True,
        alias="Alias1",
        device_fingerprint="device-1",
        ip_address="127.0.0.1",
        qr_code="QR001",
    )

    assert validation_status == 200
    assert validation["valid"] is True
    assert validation["validation_outcome"] == "VALIDATED"
    assert validation["referral_track_id"]

    progress_conn = FakeAsyncConn(progress_inserted=True)
    enqueued: list[dict] = []
    _patch_db(monkeypatch, progress_service, progress_conn)
    monkeypatch.setattr(
        progress_service,
        "enqueue_event",
        lambda payload: enqueued.append(payload),
    )

    progress, progress_status = await progress_service.handle_progress_event(
        _progress_request(),
        tenant_code="FNB",
    )

    assert progress_status == 201
    assert progress["status"] == "ok"
    assert progress["deduped"] is False
    assert progress["sourceSystem"] == "CORE_BANKING"
    assert enqueued[0]["eventType"] == "REFERRAL_PROGRESS_RECORDED"

    dedupe_conn = FakeAsyncConn(progress_inserted=False)
    enqueued.clear()
    _patch_db(monkeypatch, progress_service, dedupe_conn)

    deduped, dedupe_status = await progress_service.handle_progress_event(
        _progress_request(),
        tenant_code="FNB",
    )

    assert dedupe_status == 200
    assert deduped["deduped"] is True
    assert enqueued == []

    inspect_conn = FakeAsyncConn(
        fetchrow_values=[
            {
                "referrer_code_id": uuid4(),
                "referral_code": "REF123",
                "gaming_handle": "SafeHandle",
                "sticker": "QR001",
                "tenant_code": "FNB",
                "segment": "PERSONAL",
                "created_at": datetime(2026, 7, 12, tzinfo=timezone.utc),
                "updated_at": datetime(2026, 7, 12, tzinfo=timezone.utc),
                "referrer_ucn": "5555555555",
                "referrer_ucn_hash": "ucn-hash",
            }
        ]
    )
    _patch_db(monkeypatch, link_code_service, inspect_conn)

    inspected = await link_code_service.inspect_link_code(
        tenant_code="FNB",
        source_type="REFERRAL_CODE",
        code_or_ref="REF123",
    )

    assert inspected["status"] == "ISSUED"
    assert inspected["participant"]["participant_ref"] == "SafeHandle"
    assert inspected["evidence"]["referrer_ucn"] == "[REDACTED]"
    assert "5555555555" not in str(inspected)

    trace_conn = FakeAsyncConn(
        fetchrow_values=[_outcome_row()],
        fetch_values=_trace_fetches(),
    )
    _patch_db(monkeypatch, outcome_trace_service, trace_conn)

    trace = await outcome_trace_service.get_outcome_trace(
        tenant_code="FNB",
        referral_track_id="11111111-1111-4111-8111-111111111111",
        identity={"role": "ADMIN"},
        include_sections=["attribution", "events"],
    )

    assert trace["trace_type"] == "OUTCOME"
    assert trace["tenant_code"] == "FNB"
    assert trace["sections"]["outcome"]["status"] == "ACCOUNT_OPENED"
    assert trace["sections"]["attribution"]["count"] == 1
    assert trace["sections"]["events"]["count"] == 1
    assert "funding" not in trace["sections"]
    assert "settlement" not in trace["sections"]
    assert "go_live" not in str(trace).lower()


@pytest.mark.asyncio
async def test_referral_saas_negative_contract_paths_fail_safely(monkeypatch):
    issue, issue_status = await referral_code.get_or_create_referrer_code(
        referrer_ucn="5555555555",
        tenant="FNB",
        sticker="QR001",
        segment="PERSONAL",
        preferred_handle="SafeHandle",
        accepted_terms=False,
    )

    assert issue_status == 400
    assert issue["created"] is False
    assert issue["error_code"] == "ACCEPTED_TERMS_REQUIRED"
    assert "5555555555" not in str(issue)

    inspect_conn = FakeAsyncConn(fetchrow_values=[None, {"tenant_code": "PNP"}])
    _patch_db(monkeypatch, link_code_service, inspect_conn)

    inspected = await link_code_service.inspect_link_code(
        tenant_code="FNB",
        source_type="REFERRAL_CODE",
        code_or_ref="REF123",
    )

    assert inspected["status"] == "INVALID"
    assert inspected["tenant_code"] == "FNB"
    assert inspected["missing_evidence"][0]["code"] == "TENANT_MISMATCH"
    assert inspected["evidence"] == {}
    assert "PNP" not in str(inspected["missing_evidence"])

    progress_conn = FakeAsyncConn(
        progress_instance_row={
            "referrer_ucn": "1234567890",
            "product": "Transactional",
            "sub_product": "DDA13",
            "referee_ucn": "1234567890",
            "referee_ucn_hash": ucn_lookup_key("1234567890"),
            "journey_code": "BANKING_TRANSACTIONAL",
            "journey_version": "v1",
        }
    )
    enqueued: list[dict] = []
    _patch_db(monkeypatch, progress_service, progress_conn)
    monkeypatch.setattr(
        progress_service,
        "enqueue_event",
        lambda payload: enqueued.append(payload),
    )

    self_referral, self_referral_status = await progress_service.handle_progress_event(
        _progress_request(),
        tenant_code="FNB",
    )

    assert self_referral_status == 409
    assert self_referral["status"] == "error"
    assert self_referral["errorCode"] == "SELF_REFERRAL_NOT_ALLOWED"
    assert self_referral["deduped"] is False
    assert enqueued == []

    journey_conn = FakeAsyncConn()
    _patch_db(monkeypatch, progress_service, journey_conn)

    journey_mismatch, journey_status = await progress_service.handle_progress_event(
        _progress_request(
            eventType="QUOTE_REQUESTED",
            journeyCode="INSURANCE_POLICY",
            journeyVersion="v1",
            refereeUCN=None,
            accountNumber=None,
        ),
        tenant_code="FNB",
    )

    assert journey_status == 400
    assert journey_mismatch["status"] == "error"
    assert journey_mismatch["journeyCode"] == "INSURANCE_POLICY"
    assert "Journey mismatch" in journey_mismatch["message"]
    assert enqueued == []

    trace_conn = FakeAsyncConn(fetchrow_values=[None])
    _patch_db(monkeypatch, outcome_trace_service, trace_conn)

    with pytest.raises(outcome_trace_service.OutcomeTraceNotFound) as exc:
        await outcome_trace_service.get_outcome_trace(
            tenant_code="PNP",
            referral_track_id="11111111-1111-4111-8111-111111111111",
            identity={"role": "ADMIN"},
            include_sections=["attribution", "events"],
        )

    assert "tenant PNP" in str(exc.value)
