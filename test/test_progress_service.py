from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager, contextmanager
from datetime import datetime, timezone
from types import SimpleNamespace

import os

os.environ.setdefault(
    "REFERRAL_CODE_SECRET",
    "test-referral-secret-123456789"
)

import services.progress_service as ps
from apps.api.schemas.progress import ProgressEventType
from utils.crypto import (
    account_lookup_key,
    mask_account,
    ucn_lookup_key,
)


_loop = asyncio.new_event_loop()
asyncio.set_event_loop(_loop)


def _run(coro):
    global _loop
    if _loop.is_closed():
        _loop = asyncio.new_event_loop()
        asyncio.set_event_loop(_loop)
    return _loop.run_until_complete(coro)


class FakeCursor:
    def __init__(self, *, fetchall_rows=None):
        self.fetchall_rows = fetchall_rows or []
        self._fetchone_values = []
        self.executed = []

    def execute(self, sql, params=None):
        self.executed.append((sql, params))

    def fetchone(self):
        return self._fetchone_values.pop(0) if self._fetchone_values else None

    def fetchall(self):
        return self.fetchall_rows


class FakeAsyncConn:
    def __init__(
        self,
        *,
        fetchall_rows=None,
        instance_exists=True,
        inserted=True,
        existing_product="Transactional",
        existing_sub_product="DDA13",
        existing_referrer_ucn="5555555555",
        existing_referee_ucn="1234567890",
        existing_referee_ucn_hash=None,
        existing_journey_code="BANKING_TRANSACTIONAL",
        existing_journey_version="v1",
    ):
        self.fetchall_rows = fetchall_rows or []
        self.instance_exists = instance_exists
        self.inserted = inserted
        self.existing_product = existing_product
        self.existing_sub_product = existing_sub_product
        self.existing_referrer_ucn = existing_referrer_ucn
        self.existing_referee_ucn = existing_referee_ucn
        self.existing_referee_ucn_hash = existing_referee_ucn_hash
        self.existing_journey_code = existing_journey_code
        self.existing_journey_version = existing_journey_version
        self.executed = []

    async def fetch(self, sql, *params):
        self.executed.append((sql, params))
        return self.fetchall_rows

    async def fetchrow(self, sql, *params):
        self.executed.append((sql, params))

        if "SELECT" in sql and "FROM referral_instances" in sql:
            if not self.instance_exists:
                return None

            return {
                "referrer_ucn": self.existing_referrer_ucn,
                "product": self.existing_product,
                "sub_product": self.existing_sub_product,
                "referee_ucn": self.existing_referee_ucn,
                "referee_ucn_hash": self.existing_referee_ucn_hash,
                "journey_code": self.existing_journey_code,
                "journey_version": self.existing_journey_version,
            }

        if "INSERT INTO referral_progress_events" in sql:
            return {"id": 123} if self.inserted else None

        return None

    async def execute(self, sql, *params):
        self.executed.append((sql, params))
        return "UPDATE 1"


def _patch_db(monkeypatch, cursor):
    @contextmanager
    def fake_db_cursor(dict_cursor=False, commit=False):
        yield cursor

    monkeypatch.setattr(
        ps,
        "db_cursor",
        lambda dict_cursor=False, commit=False: fake_db_cursor(
            dict_cursor=dict_cursor,
            commit=commit,
        ),
    )


def _patch_async_db(monkeypatch, conn):
    @asynccontextmanager
    async def fake_db_connection():
        yield conn

    monkeypatch.setattr(ps, "db_connection", fake_db_connection)


def make_request(
    *,
    event_type=ProgressEventType.ACCOUNT_OPENED,
    source_system="HOGAN",
    source_event_id="evt-1",
    referee_ucn="1234567890",
    account_number="123456789012",
    product="Transactional",
    sub_product="DDA13",
    journey_code=None,
    journey_version=None,
    meta=None,
):
    return SimpleNamespace(
        referralTrackId="track-1",
        product=product,
        subProduct=sub_product,
        eventType=event_type,
        journeyCode=journey_code,
        journeyVersion=journey_version,
        sourceSystem=source_system,
        sourceEventId=source_event_id,
        refereeUCN=referee_ucn,
        accountNumber=account_number,
        meta={"channel": "api"} if meta is None else meta,
    )


def test_normalize_optional_identity():
    assert ps._normalize_optional_identity(None) is None
    assert ps._normalize_optional_identity("   ") is None
    assert ps._normalize_optional_identity("string") is None
    assert ps._normalize_optional_identity("NULL") is None
    assert ps._normalize_optional_identity("none") is None
    assert ps._normalize_optional_identity("n/a") is None
    assert ps._normalize_optional_identity("na") is None
    assert ps._normalize_optional_identity("unknown") is None
    assert ps._normalize_optional_identity("test") is None
    assert ps._normalize_optional_identity("  ABC  ") == "ABC"


def test_normalize_source_system_product_and_sub_product():
    assert ps._normalize_source_system(None) == "PROGRESS_API"
    assert ps._normalize_source_system("core banking") == "CORE_BANKING"
    assert ps._normalize_product(None) is None
    assert ps._normalize_product("transactional") == "TRANSACTIONAL"
    assert ps._normalize_product("gold account") == "GOLD_ACCOUNT"
    assert ps._normalize_sub_product(None) is None
    assert ps._normalize_sub_product("dda13") == "DDA13"


def test_ensure_utc_and_isoz():
    naive = datetime(2026, 1, 1, 10, 0)
    aware = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)

    assert ps._ensure_utc(naive).tzinfo == timezone.utc
    assert ps._isoz(aware) == "2026-01-01T12:00:00Z"


def test_canonical_payload_hash_is_stable():
    assert ps._canonical_payload_hash({"b": 2, "a": 1}) == ps._canonical_payload_hash({"a": 1, "b": 2})


def test_build_dedupe_key_with_source_event_id():
    key1 = ps._build_dedupe_key(
        source_system="HOGAN",
        source_event_id="evt-1",
        referral_track_id="track-1",
        event_type="ACCOUNT_OPENED",
        occurred_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )
    key2 = ps._build_dedupe_key(
        source_system="HOGAN",
        source_event_id="evt-1",
        referral_track_id="different",
        event_type="FUNDED",
        occurred_at=datetime(2026, 1, 2, tzinfo=timezone.utc),
    )

    assert key1 == key2


def test_build_dedupe_key_without_source_event_id():
    key1 = ps._build_dedupe_key(
        source_system="HOGAN",
        source_event_id=None,
        referral_track_id="track-1",
        event_type="ACCOUNT_OPENED",
        occurred_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )
    key2 = ps._build_dedupe_key(
        source_system="HOGAN",
        source_event_id=None,
        referral_track_id="track-2",
        event_type="ACCOUNT_OPENED",
        occurred_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )

    assert key1 != key2


def test_build_event_payload_includes_identity_fields():
    req = make_request()
    occurred_at = datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc)

    payload = ps._build_event_payload(
        req=req,
        referral_track_id="track-1",
        product="TRANSACTIONAL",
        sub_product="DDA13",
        deduped=False,
        source_system="HOGAN",
        source_event_id="evt-1",
        occurred_at=occurred_at,
        dedupe_key="dedupe-1",
        tenant_code="FNB",
    )

    assert payload["tenantCode"] == "FNB"
    assert payload["referralTrackId"] == "track-1"
    assert payload["progressEventType"] == "ACCOUNT_OPENED"
    assert payload["occurredAt"] == "2026-01-01T10:00:00Z"
    assert payload["refereeUCNLookupKey"] == ucn_lookup_key("1234567890")
    assert payload["accountNumberLookupKey"] == account_lookup_key("123456789012")
    assert payload["accountNumberMasked"] == mask_account("123456789012")


def test_build_event_payload_without_optional_identity():
    req = make_request(referee_ucn=None, account_number=None, meta={})
    occurred_at = datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc)

    payload = ps._build_event_payload(
        req=req,
        referral_track_id="track-1",
        product=None,
        sub_product=None,
        deduped=True,
        source_system="PROGRESS_API",
        source_event_id=None,
        occurred_at=occurred_at,
        dedupe_key="dedupe-1",
        tenant_code="FNB",
    )

    assert payload["meta"] == {}
    assert "refereeUCN" not in payload
    assert "accountNumber" not in payload


def test_is_self_referral():
    assert ps._is_self_referral("123", "123") is True
    assert ps._is_self_referral("123", "456") is False
    assert ps._is_self_referral(None, "456") is False
    assert ps._is_self_referral("123", None) is False


def test_account_opened_requires_referee_ucn_and_account():
    req = make_request(referee_ucn=None, account_number=None)

    response, status = _run(ps.handle_progress_event(req))

    assert status == 400
    assert response["status"] == "error"
    assert "required for ACCOUNT_OPENED" in response["message"]


def test_ucn_captured_requires_referee_ucn():
    req = make_request(
        event_type=ProgressEventType.UCN_CAPTURED,
        product=None,
        sub_product=None,
        referee_ucn=None,
        account_number=None,
    )

    response, status = _run(ps.handle_progress_event(req))

    assert status == 400
    assert response["message"] == "refereeUCN is required for UCN_CAPTURED"


def test_product_required_for_product_events():
    req = make_request(product=None)

    response, status = _run(ps.handle_progress_event(req))

    assert status == 400
    assert response["message"] == "product is required for ACCOUNT_OPENED"


def test_sub_product_required_for_product_events():
    req = make_request(sub_product=None)

    response, status = _run(ps.handle_progress_event(req))

    assert status == 400
    assert response["message"] == "subProduct is required for ACCOUNT_OPENED"


def test_returns_404_if_instance_not_found(monkeypatch):
    conn = FakeAsyncConn(instance_exists=False)
    _patch_async_db(monkeypatch, conn)

    req = make_request()
    response, status = _run(ps.handle_progress_event(req, tenant_code="FNB"))

    assert status == 404
    assert response["message"] == "Referral instance not found"


def test_rejects_self_referral(monkeypatch):
    conn = FakeAsyncConn(
        existing_referrer_ucn="1234567890",
        existing_referee_ucn="1234567890",
        existing_referee_ucn_hash=ucn_lookup_key("1234567890"),
    )
    _patch_async_db(monkeypatch, conn)

    req = make_request()
    response, status = _run(ps.handle_progress_event(req, tenant_code="FNB"))

    assert status == 409
    assert response["errorCode"] == "SELF_REFERRAL_NOT_ALLOWED"


def test_identity_required_rejects_missing_referee_ucn(monkeypatch):
    conn = FakeAsyncConn(existing_referee_ucn=None, existing_referee_ucn_hash=None)
    _patch_async_db(monkeypatch, conn)

    req = make_request(
        event_type=ProgressEventType.FUNDED,
        referee_ucn=None,
        account_number=None,
    )

    response, status = _run(ps.handle_progress_event(req, tenant_code="FNB"))

    assert status == 400
    assert response["message"] == "refereeUCN is required for FUNDED"


def test_rejects_existing_referee_ucn_mismatch(monkeypatch):
    conn = FakeAsyncConn(existing_referee_ucn="9999999999")
    _patch_async_db(monkeypatch, conn)

    req = make_request(referee_ucn="1234567890")
    response, status = _run(ps.handle_progress_event(req, tenant_code="FNB"))

    assert status == 400
    assert response["message"] == "refereeUCN does not match the referral instance"


def test_rejects_existing_referee_hash_mismatch(monkeypatch):
    conn = FakeAsyncConn(
        existing_referee_ucn=None,
        existing_referee_ucn_hash=ucn_lookup_key("9999999999"),
    )
    _patch_async_db(monkeypatch, conn)

    req = make_request(referee_ucn="1234567890")
    response, status = _run(ps.handle_progress_event(req, tenant_code="FNB"))

    assert status == 400
    assert response["message"] == "refereeUCN does not match the referral instance"


def test_accepts_existing_referee_hash_match(monkeypatch):
    conn = FakeAsyncConn(
        existing_referee_ucn=None,
        existing_referee_ucn_hash=ucn_lookup_key("1234567890"),
    )
    enqueued = []

    _patch_async_db(monkeypatch, conn)
    monkeypatch.setattr(ps, "enqueue_event", lambda payload: enqueued.append(payload))

    req = make_request(referee_ucn="1234567890")
    response, status = _run(ps.handle_progress_event(req, tenant_code="FNB"))

    assert status == 201
    assert response["status"] == "ok"
    assert len(enqueued) == 1


def test_rejects_product_mismatch(monkeypatch):
    conn = FakeAsyncConn(existing_product="Savings")
    _patch_async_db(monkeypatch, conn)

    req = make_request()
    response, status = _run(ps.handle_progress_event(req, tenant_code="FNB"))

    assert status == 400
    assert "Product mismatch" in response["message"]


def test_rejects_sub_product_mismatch(monkeypatch):
    conn = FakeAsyncConn(existing_sub_product="DDA99")
    _patch_async_db(monkeypatch, conn)

    req = make_request()
    response, status = _run(ps.handle_progress_event(req, tenant_code="FNB"))

    assert status == 400
    assert "SubProduct mismatch" in response["message"]


def test_inserts_and_enqueues(monkeypatch):
    conn = FakeAsyncConn(
        instance_exists=True,
        inserted=True,
        existing_referee_ucn_hash=ucn_lookup_key("1234567890"),
    )
    enqueued = []

    _patch_async_db(monkeypatch, conn)
    monkeypatch.setattr(ps, "enqueue_event", lambda payload: enqueued.append(payload))

    req = make_request()
    response, status = _run(ps.handle_progress_event(req, tenant_code="FNB"))

    assert status == 201
    assert response["status"] == "ok"
    assert response["deduped"] is False
    assert response["sourceSystem"] == "HOGAN"
    assert response["sourceEventId"] == "evt-1"
    assert len(enqueued) == 1
    assert enqueued[0]["eventType"] == "REFERRAL_PROGRESS_RECORDED"


def test_dedupes_and_does_not_enqueue(monkeypatch):
    conn = FakeAsyncConn(
        instance_exists=True,
        inserted=False,
        existing_referee_ucn_hash=ucn_lookup_key("1234567890"),
    )
    enqueued = []

    _patch_async_db(monkeypatch, conn)
    monkeypatch.setattr(ps, "enqueue_event", lambda payload: enqueued.append(payload))

    req = make_request()
    response, status = _run(ps.handle_progress_event(req, tenant_code="FNB"))

    assert status == 200
    assert response["deduped"] is True
    assert response["message"] == "Progress already recorded (deduped)"
    assert len(enqueued) == 0


def test_ucn_captured_allows_missing_product_and_subproduct(monkeypatch):
    conn = FakeAsyncConn(
        existing_product=None,
        existing_sub_product=None,
        existing_referee_ucn_hash=ucn_lookup_key("1234567890"),
    )
    enqueued = []

    _patch_async_db(monkeypatch, conn)
    monkeypatch.setattr(ps, "enqueue_event", lambda payload: enqueued.append(payload))

    req = make_request(
        event_type=ProgressEventType.UCN_CAPTURED,
        product=None,
        sub_product=None,
        account_number=None,
    )

    response, status = _run(ps.handle_progress_event(req, tenant_code="FNB"))

    assert status == 201
    assert response["eventType"] == "UCN_CAPTURED"
    assert len(enqueued) == 1


def test_normalizes_source_system_and_source_event_id(monkeypatch):
    conn = FakeAsyncConn(existing_referee_ucn_hash=ucn_lookup_key("1234567890"))
    enqueued = []

    _patch_async_db(monkeypatch, conn)
    monkeypatch.setattr(ps, "enqueue_event", lambda payload: enqueued.append(payload))

    req = make_request(source_system=" core system ", source_event_id=" string ")
    response, status = _run(ps.handle_progress_event(req, tenant_code="FNB"))

    assert status == 201
    assert response["sourceSystem"] == "CORE_SYSTEM"
    assert response["sourceEventId"] is None


def test_accepts_insurance_progress_event_and_binds_journey(monkeypatch):
    conn = FakeAsyncConn(
        existing_product=None,
        existing_sub_product=None,
        existing_referee_ucn=None,
        existing_referee_ucn_hash=None,
        existing_journey_code=None,
        existing_journey_version=None,
    )
    enqueued = []

    _patch_async_db(monkeypatch, conn)
    monkeypatch.setattr(ps, "enqueue_event", lambda payload: enqueued.append(payload))

    req = make_request(
        event_type="FIRST_PREMIUM_PAID",
        product="Insurance",
        sub_product="Life",
        journey_code="INSURANCE_POLICY",
        journey_version="v1",
        referee_ucn=None,
        account_number=None,
        meta={"policyNumber": "POL-123"},
    )

    response, status = _run(ps.handle_progress_event(req, tenant_code="FNB"))

    assert status == 201
    assert response["eventType"] == "FIRST_PREMIUM_PAID"
    assert response["journeyCode"] == "INSURANCE_POLICY"
    assert response["journeyVersion"] == "v1"
    assert enqueued[0]["progressEventType"] == "FIRST_PREMIUM_PAID"
    assert enqueued[0]["journeyCode"] == "INSURANCE_POLICY"
    assert any("journey_code = COALESCE" in sql for sql, _params in conn.executed)


def test_rejects_insurance_event_missing_policy_number(monkeypatch):
    conn = FakeAsyncConn(
        existing_product=None,
        existing_sub_product=None,
        existing_referee_ucn=None,
        existing_referee_ucn_hash=None,
        existing_journey_code=None,
        existing_journey_version=None,
    )
    _patch_async_db(monkeypatch, conn)

    req = make_request(
        event_type="FIRST_PREMIUM_PAID",
        product="Insurance",
        sub_product="Life",
        journey_code="INSURANCE_POLICY",
        journey_version="v1",
        referee_ucn=None,
        account_number=None,
        meta={},
    )

    response, status = _run(ps.handle_progress_event(req, tenant_code="FNB"))

    assert status == 400
    assert response["journeyCode"] == "INSURANCE_POLICY"
    assert response["message"] == "policyNumber is required for FIRST_PREMIUM_PAID"


def test_rejects_event_not_supported_by_requested_journey(monkeypatch):
    conn = FakeAsyncConn(
        existing_journey_code=None,
        existing_journey_version=None,
    )
    _patch_async_db(monkeypatch, conn)

    req = make_request(
        event_type="FIRST_PREMIUM_PAID",
        journey_code="BANKING_TRANSACTIONAL",
        journey_version="v1",
        referee_ucn=None,
        account_number=None,
    )

    response, status = _run(ps.handle_progress_event(req, tenant_code="FNB"))

    assert status == 400
    assert "not supported for BANKING_TRANSACTIONAL:v1" in response["message"]


def test_rejects_journey_mismatch(monkeypatch):
    conn = FakeAsyncConn(
        existing_journey_code="BANKING_TRANSACTIONAL",
        existing_journey_version="v1",
    )
    _patch_async_db(monkeypatch, conn)

    req = make_request(
        event_type="QUOTE_REQUESTED",
        journey_code="INSURANCE_POLICY",
        journey_version="v1",
        referee_ucn=None,
        account_number=None,
    )

    response, status = _run(ps.handle_progress_event(req, tenant_code="FNB"))

    assert status == 400
    assert "Journey mismatch" in response["message"]


def test_resolve_next_milestone_returns_stored_value():
    result = ps._resolve_next_milestone_for_ui(
        journey_code="BAD",
        journey_version="BAD",
        status="ACCOUNT_OPENED",
        stored_next_milestone="Fund account",
    )

    assert result == "Fund account"


def test_resolve_next_milestone_returns_none_without_status():
    result = ps._resolve_next_milestone_for_ui(
        journey_code=None,
        journey_version=None,
        status=None,
        stored_next_milestone=None,
    )

    assert result is None


def test_resolve_next_milestone_handles_bad_definition(monkeypatch):
    monkeypatch.setattr(
        ps,
        "get_progress_definition",
        lambda code, version: (_ for _ in ()).throw(ValueError("bad")),
    )

    result = ps._resolve_next_milestone_for_ui(
        journey_code="BAD",
        journey_version="v0",
        status="ACCOUNT_OPENED",
        stored_next_milestone=None,
    )

    assert result is None


def test_resolve_next_milestone_from_definition(monkeypatch):
    milestone = SimpleNamespace(next_milestone="Fund your account")
    pdef = SimpleNamespace(milestones={"ACCOUNT_OPENED": milestone})

    monkeypatch.setattr(ps, "get_progress_definition", lambda code, version: pdef)

    result = ps._resolve_next_milestone_for_ui(
        journey_code=None,
        journey_version=None,
        status="account_opened",
        stored_next_milestone=None,
    )

    assert result == "Fund your account"


def test_resolve_next_milestone_missing_status_in_definition(monkeypatch):
    pdef = SimpleNamespace(milestones={})
    monkeypatch.setattr(ps, "get_progress_definition", lambda code, version: pdef)

    result = ps._resolve_next_milestone_for_ui(
        journey_code=None,
        journey_version=None,
        status="UNKNOWN_STATUS",
        stored_next_milestone=None,
    )

    assert result is None


def test_get_referrals_progress_empty(monkeypatch):
    conn = FakeAsyncConn(fetchall_rows=[])
    _patch_async_db(monkeypatch, conn)

    result = _run(ps.get_referrals_progress_by_referrer_ucn("555", "FNB"))

    assert result.referrer_ucn == "555"
    assert result.total_referrals == 0
    assert result.completed_referrals_count == 0
    assert result.in_progress_referrals_count == 0
    assert result.has_active_referrals is False
    assert result.items == []


def test_get_referrals_progress_completed_and_in_progress(monkeypatch):
    created = datetime(2026, 1, 1, 8, 0)
    updated = datetime(2026, 1, 2, 8, 0, tzinfo=timezone.utc)
    completed_at = datetime(2026, 1, 5, 8, 0, tzinfo=timezone.utc)

    rows = [
        {
            "referral_track_id": "track-complete",
            "referee_alias": "John",
            "product": "TRANSACTIONAL",
            "sub_product": "DDA13",
            "status": "FIRST_TRANSACTION_COMPLETED",
            "journey_code": "BANKING_TRANSACTIONAL",
            "journey_version": "v1",
            "created_at": created,
            "updated_at": updated,
            "account_opened_at": None,
            "account_activated_at": None,
            "funded_at": None,
            "debit_order_switched_at": None,
            "salary_switched_at": None,
            "first_transaction_completed_at": None,
            "progress_percent": 80,
            "progress_band": "COMPLETE",
            "display_status": None,
            "next_milestone": "Ignored because complete",
            "is_complete": True,
            "completed_at": completed_at,
        },
        {
            "referral_track_id": "track-progress",
            "referee_alias": "Mary",
            "product": "TRANSACTIONAL",
            "sub_product": "DDA13",
            "status": "ACCOUNT_OPENED",
            "journey_code": "BANKING_TRANSACTIONAL",
            "journey_version": "v1",
            "created_at": created,
            "updated_at": updated,
            "account_opened_at": datetime(2026, 1, 3, 8, 0, tzinfo=timezone.utc),
            "account_activated_at": None,
            "funded_at": None,
            "debit_order_switched_at": None,
            "salary_switched_at": None,
            "first_transaction_completed_at": None,
            "progress_percent": None,
            "progress_band": "IN_PROGRESS",
            "display_status": None,
            "next_milestone": "Fund your account",
            "is_complete": False,
            "completed_at": None,
        },
    ]

    conn = FakeAsyncConn(fetchall_rows=rows)
    _patch_async_db(monkeypatch, conn)

    result = _run(ps.get_referrals_progress_by_referrer_ucn("555", "FNB"))

    assert result.total_referrals == 2
    assert result.completed_referrals_count == 1
    assert result.in_progress_referrals_count == 1
    assert result.has_active_referrals is True

    complete = result.items[0]
    assert complete.referral_track_id == "track-complete"
    assert complete.progress_percent == 100
    assert complete.current_milestone == "Completed"
    assert complete.next_milestone is None
    assert complete.status == "COMPLETED"

    progress = result.items[1]
    assert progress.referral_track_id == "track-progress"
    assert progress.progress_percent == 0
    assert progress.current_milestone == "Account Opened"
    assert progress.next_milestone == "Fund your account"
    assert progress.status == "ACCOUNT_OPENED"
    assert progress.last_updated_at.isoformat().startswith("2026-01-03T08:00:00")


def test_get_referrals_progress_uses_display_status_and_no_timestamps(monkeypatch):
    rows = [
        {
            "referral_track_id": "track-1",
            "referee_alias": None,
            "product": None,
            "sub_product": None,
            "status": None,
            "journey_code": None,
            "journey_version": None,
            "created_at": None,
            "updated_at": None,
            "account_opened_at": None,
            "account_activated_at": None,
            "funded_at": None,
            "debit_order_switched_at": None,
            "salary_switched_at": None,
            "first_transaction_completed_at": None,
            "progress_percent": None,
            "progress_band": None,
            "display_status": "Custom status",
            "next_milestone": None,
            "is_complete": False,
            "completed_at": None,
        }
    ]

    conn = FakeAsyncConn(fetchall_rows=rows)
    _patch_async_db(monkeypatch, conn)

    result = _run(ps.get_referrals_progress_by_referrer_ucn("555", "FNB"))

    assert result.total_referrals == 1
    assert result.items[0].current_milestone == "Custom status"
    assert result.items[0].last_updated_at is None


def test_get_referrals_progress_defaults_not_started(monkeypatch):
    rows = [
        {
            "referral_track_id": "track-1",
            "referee_alias": None,
            "product": None,
            "sub_product": None,
            "status": "",
            "journey_code": None,
            "journey_version": None,
            "created_at": None,
            "updated_at": None,
            "account_opened_at": None,
            "account_activated_at": None,
            "funded_at": None,
            "debit_order_switched_at": None,
            "salary_switched_at": None,
            "first_transaction_completed_at": None,
            "progress_percent": None,
            "progress_band": None,
            "display_status": None,
            "next_milestone": None,
            "is_complete": False,
            "completed_at": None,
        }
    ]

    conn = FakeAsyncConn(fetchall_rows=rows)
    _patch_async_db(monkeypatch, conn)

    result = _run(ps.get_referrals_progress_by_referrer_ucn("555", "FNB"))

    assert result.items[0].current_milestone == "Not started"
