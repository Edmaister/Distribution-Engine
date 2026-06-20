from contextlib import asynccontextmanager
from datetime import datetime, timezone

import pytest

import services.replay_service as rs


class FakeTransaction:
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False


class FakeAsyncConn:
    def __init__(self, *, fetchrow=None, fetch=None):
        self._fetchrow = fetchrow
        self._fetch = fetch or []
        self.executed = []

    async def fetchrow(self, sql, *params):
        self.executed.append((sql, params))
        return self._fetchrow

    async def fetch(self, sql, *params):
        self.executed.append((sql, params))
        return self._fetch

    async def execute(self, sql, *params):
        self.executed.append((sql, params))
        return "UPDATE 1"

    def transaction(self):
        return FakeTransaction()


def patch_async_db(monkeypatch, conn):
    @asynccontextmanager
    async def fake_db_connection():
        yield conn

    monkeypatch.setattr(rs, "db_connection", fake_db_connection)


@pytest.mark.asyncio
async def test_load_instance_success():
    conn = FakeAsyncConn(fetchrow={"referral_track_id": "t1"})

    result = await rs._load_instance(conn, "t1")

    assert result["referral_track_id"] == "t1"


@pytest.mark.asyncio
async def test_load_instance_not_found():
    conn = FakeAsyncConn(fetchrow=None)

    with pytest.raises(ValueError, match="Referral instance not found"):
        await rs._load_instance(conn, "t1")


@pytest.mark.asyncio
async def test_load_events():
    now = datetime.now(timezone.utc)
    conn = FakeAsyncConn(
        fetch=[
            {
                "id": 1,
                "event_type": "STEP1",
                "source_system": "SYS",
                "source_event_id": "E1",
                "occurred_at": now,
                "received_at": now,
                "dedupe_key": None,
                "meta": {},
            }
        ]
    )

    result = await rs._load_events(conn, "t1")

    assert len(result) == 1
    assert result[0]["event_type"] == "STEP1"


def test_reset_instance_projection(monkeypatch):
    instance = {"status": "OLD"}

    monkeypatch.setattr(
        rs,
        "_derive_progress_snapshot",
        lambda **kwargs: {
            "progress_percent": 0,
            "progress_band": "START",
            "display_status": "VALIDATED",
            "next_milestone": "UCN_CAPTURED",
        },
    )

    rs._reset_instance_projection(
        instance,
        journey_code="J1",
        journey_version="v1",
    )

    assert instance["status"] == "VALIDATED"
    assert instance["is_complete"] is False
    assert instance["progress_percent"] == 0


@pytest.mark.asyncio
async def test_rebuild_dry_run(monkeypatch):
    now = datetime.now(timezone.utc)
    conn = FakeAsyncConn()
    patch_async_db(monkeypatch, conn)

    async def fake_load_instance(*args):
        return {"referral_track_id": "t1"}

    async def fake_load_events(*args):
        return [{"event_type": "STEP1", "occurred_at": now}]

    monkeypatch.setattr(rs, "_load_instance", fake_load_instance)
    monkeypatch.setattr(rs, "_load_events", fake_load_events)
    monkeypatch.setattr(rs, "get_journey_definition", lambda *a: {})
    monkeypatch.setattr(rs, "_derive_progress_snapshot", lambda **k: {})
    monkeypatch.setattr(rs, "normalize_event", lambda e: {"normalizedEventType": "STEP1"})
    monkeypatch.setattr(rs, "apply_progress_event_to_instance", lambda **k: "valid")
    monkeypatch.setattr(rs, "log_event", lambda **k: None)

    result = await rs.rebuild_referral_instance("t1", dry_run=True)

    assert result["applied"] == 1
    assert result["ignored"] == 0
    assert result["dryRun"] is True


@pytest.mark.asyncio
async def test_rebuild_with_ignored_event(monkeypatch):
    now = datetime.now(timezone.utc)
    conn = FakeAsyncConn()
    patch_async_db(monkeypatch, conn)

    async def fake_load_instance(*args):
        return {"referral_track_id": "t1"}

    async def fake_load_events(*args):
        return [{"event_type": "STEP1", "occurred_at": now}]

    monkeypatch.setattr(rs, "_load_instance", fake_load_instance)
    monkeypatch.setattr(rs, "_load_events", fake_load_events)
    monkeypatch.setattr(rs, "get_journey_definition", lambda *a: {})
    monkeypatch.setattr(rs, "_derive_progress_snapshot", lambda **k: {})
    monkeypatch.setattr(rs, "normalize_event", lambda e: {"normalizedEventType": "STEP1"})
    monkeypatch.setattr(rs, "apply_progress_event_to_instance", lambda **k: "invalid")
    monkeypatch.setattr(rs, "log_event", lambda **k: None)

    result = await rs.rebuild_referral_instance("t1", dry_run=True)

    assert result["ignored"] == 1
