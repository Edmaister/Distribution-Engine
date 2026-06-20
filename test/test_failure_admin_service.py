from __future__ import annotations

import json

import pytest

import services.failure_admin_service as fas


class FakeAsyncConnection:
    def __init__(self, fetchrow=None, fetch=None, execute_result="UPDATE 1"):
        self.fetchrow_value = fetchrow
        self.fetch_value = fetch or []
        self.execute_result = execute_result
        self.executed = []

    async def fetch(self, sql, *params):
        self.executed.append(("fetch", sql, params))
        return self.fetch_value

    async def fetchrow(self, sql, *params):
        self.executed.append(("fetchrow", sql, params))
        return self.fetchrow_value

    async def execute(self, sql, *params):
        self.executed.append(("execute", sql, params))
        return self.execute_result


class FakeAsyncConnectionContext:
    def __init__(self, conn):
        self.conn = conn

    async def __aenter__(self):
        return self.conn

    async def __aexit__(self, exc_type, exc, tb):
        return False


def patch_async_db(monkeypatch, conn):
    monkeypatch.setattr(
        fas,
        "get_async_connection",
        lambda: FakeAsyncConnectionContext(conn),
    )


@pytest.mark.asyncio
async def test_list_failures_basic(monkeypatch):
    conn = FakeAsyncConnection(fetch=[{"id": 1, "status": "OPEN"}])
    patch_async_db(monkeypatch, conn)

    result = await fas.list_failures()

    assert result == [{"id": 1, "status": "OPEN"}]
    action, sql, params = conn.executed[0]
    assert action == "fetch"
    assert "status = $1" in sql
    assert "LIMIT $2" in sql
    assert params == ("OPEN", 100)


@pytest.mark.asyncio
async def test_list_failures_with_category(monkeypatch):
    conn = FakeAsyncConnection(fetch=[{"id": 2, "failure_category": "SYSTEM_BUG"}])
    patch_async_db(monkeypatch, conn)

    result = await fas.list_failures(
        status="OPEN",
        failure_category="SYSTEM_BUG",
        limit=50,
    )

    assert result[0]["id"] == 2
    action, sql, params = conn.executed[0]
    assert action == "fetch"
    assert "status = $1" in sql
    assert "failure_category = $2" in sql
    assert "LIMIT $3" in sql
    assert params == ("OPEN", "SYSTEM_BUG", 50)


@pytest.mark.asyncio
async def test_list_failures_without_status(monkeypatch):
    conn = FakeAsyncConnection(fetch=[])
    patch_async_db(monkeypatch, conn)

    result = await fas.list_failures(status=None, limit=25)

    assert result == []
    action, sql, params = conn.executed[0]
    assert action == "fetch"
    assert "status =" not in sql
    assert "LIMIT $1" in sql
    assert params == (25,)


@pytest.mark.asyncio
async def test_get_failure_summary(monkeypatch):
    conn = FakeAsyncConnection(
        fetch=[
            {
                "status": "OPEN",
                "failure_category": "SYSTEM",
                "failure_count": 5,
            },
            {
                "status": "RESOLVED",
                "failure_category": "DATA",
                "failure_count": 2,
            },
        ]
    )
    patch_async_db(monkeypatch, conn)

    result = await fas.get_failure_summary()

    assert result == {
        "count": 2,
        "items": [
            {
                "status": "OPEN",
                "failure_category": "SYSTEM",
                "failure_count": 5,
            },
            {
                "status": "RESOLVED",
                "failure_category": "DATA",
                "failure_count": 2,
            },
        ],
    }


@pytest.mark.asyncio
async def test_resolve_failure_success(monkeypatch):
    logs = []
    monkeypatch.setattr(fas, "log_event", lambda **kwargs: logs.append(kwargs))

    conn = FakeAsyncConnection(execute_result="UPDATE 1")
    patch_async_db(monkeypatch, conn)

    result = await fas.resolve_failure(failure_id=1, resolution_note="fixed")

    assert result is True
    assert logs[0]["message"] == "failure_resolved"
    assert logs[0]["extra"]["failure_id"] == 1
    assert logs[0]["extra"]["resolution_note"] == "fixed"


@pytest.mark.asyncio
async def test_resolve_failure_no_update(monkeypatch):
    logs = []
    monkeypatch.setattr(fas, "log_event", lambda **kwargs: logs.append(kwargs))

    conn = FakeAsyncConnection(execute_result="UPDATE 0")
    patch_async_db(monkeypatch, conn)

    result = await fas.resolve_failure(failure_id=1)

    assert result is False
    assert logs == []


@pytest.mark.asyncio
async def test_get_failure_by_id_found(monkeypatch):
    conn = FakeAsyncConnection(fetchrow={"id": 1, "status": "OPEN"})
    patch_async_db(monkeypatch, conn)

    result = await fas.get_failure_by_id(failure_id=1)

    assert result == {"id": 1, "status": "OPEN"}


@pytest.mark.asyncio
async def test_get_failure_by_id_not_found(monkeypatch):
    conn = FakeAsyncConnection(fetchrow=None)
    patch_async_db(monkeypatch, conn)

    result = await fas.get_failure_by_id(failure_id=1)

    assert result is None


@pytest.mark.asyncio
async def test_mark_failure_reprocessed_success(monkeypatch):
    logs = []
    monkeypatch.setattr(fas, "log_event", lambda **kwargs: logs.append(kwargs))

    conn = FakeAsyncConnection(execute_result="UPDATE 1")
    patch_async_db(monkeypatch, conn)

    result = await fas.mark_failure_reprocessed(
        failure_id=1,
        resolution_note="done",
    )

    assert result is True
    assert logs[0]["message"] == "failure_reprocessed"
    assert logs[0]["extra"]["failure_id"] == 1
    assert logs[0]["extra"]["resolution_note"] == "done"


@pytest.mark.asyncio
async def test_mark_failure_reprocessed_no_update(monkeypatch):
    logs = []
    monkeypatch.setattr(fas, "log_event", lambda **kwargs: logs.append(kwargs))

    conn = FakeAsyncConnection(execute_result="UPDATE 0")
    patch_async_db(monkeypatch, conn)

    result = await fas.mark_failure_reprocessed(failure_id=1)

    assert result is False
    assert logs == []


@pytest.mark.asyncio
async def test_reprocess_failure_not_found(monkeypatch):
    async def fake_get_failure_by_id(**kwargs):
        return None

    monkeypatch.setattr(fas, "get_failure_by_id", fake_get_failure_by_id)

    with pytest.raises(ValueError, match="Failure not found"):
        await fas.reprocess_failure(failure_id=1)


@pytest.mark.asyncio
async def test_reprocess_failure_already_resolved(monkeypatch):
    async def fake_get_failure_by_id(**kwargs):
        return {"status": "RESOLVED"}

    monkeypatch.setattr(fas, "get_failure_by_id", fake_get_failure_by_id)

    with pytest.raises(ValueError, match="already closed"):
        await fas.reprocess_failure(failure_id=1)


@pytest.mark.asyncio
async def test_reprocess_failure_already_reprocessed(monkeypatch):
    async def fake_get_failure_by_id(**kwargs):
        return {"status": "REPROCESSED"}

    monkeypatch.setattr(fas, "get_failure_by_id", fake_get_failure_by_id)

    with pytest.raises(ValueError, match="already closed"):
        await fas.reprocess_failure(failure_id=1)


@pytest.mark.asyncio
async def test_reprocess_failure_empty_payload(monkeypatch):
    async def fake_get_failure_by_id(**kwargs):
        return {"status": "OPEN", "payload_json": None}

    monkeypatch.setattr(fas, "get_failure_by_id", fake_get_failure_by_id)

    with pytest.raises(ValueError, match="payload is empty"):
        await fas.reprocess_failure(failure_id=1)


@pytest.mark.asyncio
async def test_reprocess_failure_json_string_payload(monkeypatch):
    handled = []
    marked = []

    async def fake_get_failure_by_id(**kwargs):
        return {
            "status": "OPEN",
            "payload_json": json.dumps({"eventType": "REFERRAL_PROGRESS_RECORDED"}),
        }

    async def fake_handle(payload):
        handled.append(payload)

    async def fake_mark(**kwargs):
        marked.append(kwargs)
        return True

    monkeypatch.setattr(fas, "get_failure_by_id", fake_get_failure_by_id)
    monkeypatch.setattr(fas, "handle_referral_progress_recorded", fake_handle)
    monkeypatch.setattr(fas, "mark_failure_reprocessed", fake_mark)

    result = await fas.reprocess_failure(failure_id=1)

    assert result == {
        "failureId": 1,
        "status": "ok",
        "reprocessed": True,
    }
    assert handled == [{"eventType": "REFERRAL_PROGRESS_RECORDED"}]
    assert marked[0]["failure_id"] == 1


@pytest.mark.asyncio
async def test_reprocess_failure_dict_payload(monkeypatch):
    handled = []

    async def fake_get_failure_by_id(**kwargs):
        return {
            "status": "OPEN",
            "payload_json": {"eventType": "REFERRAL_PROGRESS_RECORDED"},
        }

    async def fake_handle(payload):
        handled.append(payload)

    async def fake_mark(**kwargs):
        return True

    monkeypatch.setattr(fas, "get_failure_by_id", fake_get_failure_by_id)
    monkeypatch.setattr(fas, "handle_referral_progress_recorded", fake_handle)
    monkeypatch.setattr(fas, "mark_failure_reprocessed", fake_mark)

    result = await fas.reprocess_failure(failure_id=2)

    assert result["reprocessed"] is True
    assert handled == [{"eventType": "REFERRAL_PROGRESS_RECORDED"}]


@pytest.mark.asyncio
async def test_reprocess_failure_payload_not_dict(monkeypatch):
    async def fake_get_failure_by_id(**kwargs):
        return {"status": "OPEN", "payload_json": json.dumps(["not", "dict"])}

    monkeypatch.setattr(fas, "get_failure_by_id", fake_get_failure_by_id)

    with pytest.raises(ValueError, match="not valid JSON"):
        await fas.reprocess_failure(failure_id=1)


@pytest.mark.asyncio
async def test_reprocess_failure_wrong_event_type(monkeypatch):
    async def fake_get_failure_by_id(**kwargs):
        return {
            "status": "OPEN",
            "payload_json": json.dumps({"eventType": "OTHER"}),
        }

    monkeypatch.setattr(fas, "get_failure_by_id", fake_get_failure_by_id)

    with pytest.raises(ValueError, match="Unsupported payload eventType"):
        await fas.reprocess_failure(failure_id=1)


@pytest.mark.asyncio
async def test_reprocess_failure_mark_reprocessed_fails(monkeypatch):
    async def fake_get_failure_by_id(**kwargs):
        return {
            "status": "OPEN",
            "payload_json": json.dumps({"eventType": "REFERRAL_PROGRESS_RECORDED"}),
        }

    async def fake_handle(payload):
        return None

    async def fake_mark(**kwargs):
        return False

    monkeypatch.setattr(fas, "get_failure_by_id", fake_get_failure_by_id)
    monkeypatch.setattr(fas, "handle_referral_progress_recorded", fake_handle)
    monkeypatch.setattr(fas, "mark_failure_reprocessed", fake_mark)

    with pytest.raises(ValueError, match="could not be marked"):
        await fas.reprocess_failure(failure_id=1)