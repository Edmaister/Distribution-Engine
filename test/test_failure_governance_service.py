from __future__ import annotations

import json
import pytest

import services.failure_governance_service as mod


class FakeAsyncConnection:
    def __init__(self):
        self.executed = []

    async def execute(
        self,
        query,
        *params,
    ):
        self.executed.append(
            (
                query,
                params,
            )
        )


class FakeAsyncConnectionContext:
    def __init__(self, conn):
        self.conn = conn

    async def __aenter__(self):
        return self.conn

    async def __aexit__(
        self,
        exc_type,
        exc,
        tb,
    ):
        return False


def patch_async_db(
    monkeypatch,
):
    conn = (
        FakeAsyncConnection()
    )

    monkeypatch.setattr(
        mod,
        "get_async_connection",
        lambda:
        FakeAsyncConnectionContext(
            conn
        ),
    )

    return conn


@pytest.mark.parametrize(
    "exc,expected",
    [
        (
            Exception(
                "timeout"
            ),
            "TRANSIENT",
        ),
        (
            Exception(
                "invalid transition"
            ),
            "BUSINESS_RULE",
        ),
        (
            Exception(
                "missing payload"
            ),
            "DATA_QUALITY",
        ),
        (
            Exception(
                "boom"
            ),
            "SYSTEM_BUG",
        ),
    ],
)
def test_classify_processing_failure(
    exc,
    expected,
):
    assert (
        mod.classify_processing_failure(
            exc
        )
        == expected
    )


@pytest.mark.asyncio
async def test_record_event_failure_source_event_id(
    monkeypatch,
):
    conn = patch_async_db(
        monkeypatch
    )

    event = {
        "referralTrackId":
        "track",
        "eventType":
        "EVENT",
        "sourceEventId":
        "event-1",
    }

    await mod.record_event_failure(
        event=event,
        message_id="msg",
        failure_category=
        "TRANSIENT",
        failure_reason=
        "timeout",
    )

    query, params = (
        conn.executed[0]
    )

    assert (
        "ON CONFLICT "
        "(source_system,"
        " source_event_id)"
        in query
    )

    assert (
        params[0]
        == "track"
    )


@pytest.mark.asyncio
async def test_record_event_failure_dedupe_fallback(
    monkeypatch,
):
    conn = patch_async_db(
        monkeypatch
    )

    event = {
        "dedupeKey":
        "dedupe-1"
    }

    await mod.record_event_failure(
        event=event,
        message_id=None,
        failure_category=
        "SYSTEM_BUG",
        failure_reason=
        "boom",
    )

    assert (
        "ON CONFLICT "
        "(dedupe_key)"
        in conn.executed[
            0
        ][0]
    )


@pytest.mark.asyncio
async def test_record_event_failure_final_fallback(
    monkeypatch,
):
    conn = patch_async_db(
        monkeypatch
    )

    await mod.record_event_failure(
        event=None,
        message_id=None,
        failure_category=
        "SYSTEM_BUG",
        failure_reason=
        "unknown",
    )

    assert (
        "ON CONFLICT"
        not in conn.executed[
            0
        ][0]
    )