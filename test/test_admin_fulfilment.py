import pytest

import apps.api.routers.admin_fulfilment as router


class FakeAsyncDbCursor:
    def __init__(self, rows=None):
        self.rows = rows or []
        self.executed = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def fetch(self, query, *args):
        self.executed.append((query, args))
        return self.rows

    async def fetchrow(self, query, *args):
        self.executed.append((query, args))
        return self.rows[0] if self.rows else None


def patch_db(monkeypatch, cursor):
    def fake_async_db_cursor():
        return cursor

    monkeypatch.setattr(router, "async_db_cursor", fake_async_db_cursor)


@pytest.mark.asyncio
async def test_get_fulfilment_audit_found(monkeypatch):
    async def fake_get_fulfilment_audit_by_id(*, audit_id):
        assert audit_id == "audit-123"
        return {
            "audit_id": "audit-123",
            "status": "FAILED_FINAL",
        }

    monkeypatch.setattr(
        router,
        "get_fulfilment_audit_by_id",
        fake_get_fulfilment_audit_by_id,
    )

    result = await router.get_fulfilment_audit("audit-123")

    assert result == {
        "status": "ok",
        "audit": {
            "audit_id": "audit-123",
            "status": "FAILED_FINAL",
        },
    }


@pytest.mark.asyncio
async def test_get_fulfilment_audit_not_found(monkeypatch):
    async def fake_get_fulfilment_audit_by_id(*, audit_id):
        return None

    monkeypatch.setattr(
        router,
        "get_fulfilment_audit_by_id",
        fake_get_fulfilment_audit_by_id,
    )

    result = await router.get_fulfilment_audit("missing")

    assert result == {
        "status": "not_found",
        "audit_id": "missing",
    }


@pytest.mark.asyncio
async def test_list_fulfilment_failures_without_tenant(monkeypatch):
    cursor = FakeAsyncDbCursor(
        rows=[
            {
                "audit_id": "audit-123",
                "tenant_code": "FNB",
                "status": "FAILED_FINAL",
            }
        ]
    )
    patch_db(monkeypatch, cursor)

    result = await router.list_fulfilment_failures(
        tenant_code=None,
        limit=50,
    )

    assert result["status"] == "ok"
    assert result["count"] == 1
    assert result["items"][0]["audit_id"] == "audit-123"

    query, args = cursor.executed[0]
    assert "FAILED_RETRYABLE" in query
    assert "FAILED_FINAL" in query
    assert "DLQ" in query
    assert args == (50,)


@pytest.mark.asyncio
async def test_list_fulfilment_failures_with_tenant(monkeypatch):
    cursor = FakeAsyncDbCursor(
        rows=[
            {
                "audit_id": "audit-123",
                "tenant_code": "FNB",
                "status": "FAILED_RETRYABLE",
            }
        ]
    )
    patch_db(monkeypatch, cursor)

    result = await router.list_fulfilment_failures(
        tenant_code="FNB",
        limit=25,
    )

    assert result["status"] == "ok"
    assert result["count"] == 1
    assert result["items"][0]["tenant_code"] == "FNB"

    query, args = cursor.executed[0]
    assert "tenant_code = $1" in query
    assert "LIMIT $2" in query
    assert args == ("FNB", 25)


@pytest.mark.asyncio
async def test_replay_fulfilment(monkeypatch):
    async def fake_replay_failed_fulfilment(*, audit_id):
        assert audit_id == "audit-123"
        return {
            "status": "replay_requested",
            "audit_id": "audit-123",
        }

    monkeypatch.setattr(
        router,
        "replay_failed_fulfilment",
        fake_replay_failed_fulfilment,
    )

    result = await router.replay_fulfilment("audit-123")

    assert result == {
        "status": "replay_requested",
        "audit_id": "audit-123",
    }

@pytest.mark.asyncio
async def test_get_fulfilment_dashboard_without_tenant(monkeypatch):
    cursor = FakeAsyncDbCursor(
        rows=[
            {
                "total_count": 10,
                "success_count": 8,
                "failed_retryable_count": 1,
                "failed_final_count": 1,
                "dlq_count": 0,
                "duplicate_skipped_count": 2,
                "processing_count": 0,
                "pending_count": 0,
            }
        ]
    )
    patch_db(monkeypatch, cursor)

    result = await router.get_fulfilment_dashboard(
        tenant_code=None,
    )

    assert result == {
        "status": "ok",
        "tenant_code": None,
        "summary": {
            "total_count": 10,
            "success_count": 8,
            "failed_retryable_count": 1,
            "failed_final_count": 1,
            "dlq_count": 0,
            "duplicate_skipped_count": 2,
            "processing_count": 0,
            "pending_count": 0,
            "success_rate": 80.0,
        },
    }

    query, args = cursor.executed[0]
    assert "FROM fulfilment_audit" in query
    assert "WHERE tenant_code" not in query
    assert args == ()


@pytest.mark.asyncio
async def test_get_fulfilment_dashboard_with_tenant(monkeypatch):
    cursor = FakeAsyncDbCursor(
        rows=[
            {
                "total_count": 4,
                "success_count": 3,
                "failed_retryable_count": 0,
                "failed_final_count": 1,
                "dlq_count": 0,
                "duplicate_skipped_count": 0,
                "processing_count": 0,
                "pending_count": 0,
            }
        ]
    )
    patch_db(monkeypatch, cursor)

    result = await router.get_fulfilment_dashboard(
        tenant_code="FNB",
    )

    assert result["status"] == "ok"
    assert result["tenant_code"] == "FNB"
    assert result["summary"]["total_count"] == 4
    assert result["summary"]["success_count"] == 3
    assert result["summary"]["success_rate"] == 75.0

    query, args = cursor.executed[0]
    assert "WHERE tenant_code = $1" in query
    assert args == ("FNB",)


@pytest.mark.asyncio
async def test_get_fulfilment_dashboard_handles_zero_total(monkeypatch):
    cursor = FakeAsyncDbCursor(
        rows=[
            {
                "total_count": 0,
                "success_count": 0,
                "failed_retryable_count": 0,
                "failed_final_count": 0,
                "dlq_count": 0,
                "duplicate_skipped_count": 0,
                "processing_count": 0,
                "pending_count": 0,
            }
        ]
    )
    patch_db(monkeypatch, cursor)

    result = await router.get_fulfilment_dashboard(
        tenant_code=None,
    )

    assert result["summary"]["total_count"] == 0
    assert result["summary"]["success_rate"] == 0.0

@pytest.mark.asyncio
async def test_get_all_provider_health(monkeypatch):
    async def fake_list_provider_health(*, tenant_code=None):
        assert tenant_code == "FNB"

        return [
            {
                "provider_key": "CASH_PROVIDER",
                "success_rate": 99.5,
            },
            {
                "provider_key": "VOUCHER_PROVIDER",
                "success_rate": 98.0,
            },
        ]

    monkeypatch.setattr(
        router,
        "list_provider_health",
        fake_list_provider_health,
    )

    result = await router.get_all_provider_health(
        tenant_code="FNB",
    )

    assert result == {
        "status": "ok",
        "tenant_code": "FNB",
        "count": 2,
        "items": [
            {
                "provider_key": "CASH_PROVIDER",
                "success_rate": 99.5,
            },
            {
                "provider_key": "VOUCHER_PROVIDER",
                "success_rate": 98.0,
            },
        ],
    }


@pytest.mark.asyncio
async def test_get_single_provider_health(monkeypatch):
    async def fake_get_provider_health(
        *,
        provider_key,
        tenant_code=None,
    ):
        assert provider_key == "CASH_PROVIDER"
        assert tenant_code == "FNB"

        return {
            "provider_key": "CASH_PROVIDER",
            "tenant_code": "FNB",
            "success_rate": 99.5,
            "failure_rate": 0.5,
            "circuit": {
                "state": "CLOSED",
            },
        }

    monkeypatch.setattr(
        router,
        "get_provider_health",
        fake_get_provider_health,
    )

    result = await router.get_single_provider_health(
        provider_key="CASH_PROVIDER",
        tenant_code="FNB",
    )

    assert result == {
        "status": "ok",
        "health": {
            "provider_key": "CASH_PROVIDER",
            "tenant_code": "FNB",
            "success_rate": 99.5,
            "failure_rate": 0.5,
            "circuit": {
                "state": "CLOSED",
            },
        },
    }