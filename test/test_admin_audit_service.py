from __future__ import annotations

from uuid import UUID

import pytest

import services.admin_audit_service as service


class FakeConnection:
    def __init__(self, *, row=None, rows=None):
        self.row = row or {
            "admin_audit_id": UUID("11111111-1111-1111-1111-111111111111"),
            "action_type": "FX_RATE_UPSERT",
            "action_domain": "FINANCE",
            "action_status": "SUCCESS",
            "actor_role": "FINANCE_ADMIN",
            "actor_tenant_code": "INTERNAL",
            "actor_subject": None,
            "tenant_code": "FNB",
            "target_type": "fx_rate",
            "target_id": "fx-123",
            "correlation_id": None,
            "reason": None,
            "request_payload": '{"base_currency": "USD"}',
            "result_payload": '{"fx_rate_id": "fx-123"}',
            "error_message": None,
        }
        self.rows = rows or [self.row]
        self.fetchrow_calls = []
        self.fetch_calls = []
        self.fetch_call_index = 0

    async def fetchrow(self, query, *params):
        self.fetchrow_calls.append((query, params))
        return self.row

    async def fetch(self, query, *params):
        self.fetch_calls.append((query, params))
        if "SELECT *" in query:
            return self.rows

        if self.fetch_call_index == 0:
            rows = [{"action_domain": "FINANCE", "count": 3}]
        elif self.fetch_call_index == 1:
            rows = [{"action_status": "SUCCESS", "count": 3}]
        elif self.fetch_call_index == 2:
            rows = [{"action_type": "FX_RATE_UPSERT", "count": 3}]
        else:
            rows = self.rows
        self.fetch_call_index += 1
        return rows


class FakeDbConnection:
    def __init__(self, conn):
        self.conn = conn

    async def __aenter__(self):
        return self.conn

    async def __aexit__(self, exc_type, exc, tb):
        return False


@pytest.mark.asyncio
async def test_write_admin_audit_inserts_row(monkeypatch):
    conn = FakeConnection()
    metric_calls = []
    monkeypatch.setattr(service, "db_connection", lambda: FakeDbConnection(conn))
    monkeypatch.setattr(service, "admin_audit_write_inc", lambda **kwargs: metric_calls.append(kwargs))

    result = await service.write_admin_audit(
        action_type="FX_RATE_UPSERT",
        action_domain="FINANCE",
        identity={"role": "FINANCE_ADMIN", "tenant_code": "INTERNAL"},
        tenant_code="FNB",
        target_type="fx_rate",
        target_id="fx-123",
        request_payload={"base_currency": "USD"},
        result_payload={"fx_rate_id": "fx-123"},
    )

    query, params = conn.fetchrow_calls[0]
    assert "INSERT INTO admin_audit_log" in query
    assert params[:9] == (
        "FX_RATE_UPSERT",
        "FINANCE",
        "SUCCESS",
        "FINANCE_ADMIN",
        "INTERNAL",
        None,
        "FNB",
        "fx_rate",
        "fx-123",
    )
    assert result["admin_audit_id"] == "11111111-1111-1111-1111-111111111111"
    assert result["request_payload"] == {"base_currency": "USD"}
    assert metric_calls == [
        {
            "action_domain": "FINANCE",
            "action_type": "FX_RATE_UPSERT",
            "action_status": "SUCCESS",
            "result": "success",
        }
    ]


@pytest.mark.asyncio
async def test_list_admin_audit_filters(monkeypatch):
    conn = FakeConnection()
    monkeypatch.setattr(service, "db_connection", lambda: FakeDbConnection(conn))

    result = await service.list_admin_audit(
        action_domain="FINANCE",
        action_type="FX_RATE_UPSERT",
        tenant_code="FNB",
        target_type="fx_rate",
        target_id="fx-123",
        limit=25,
    )

    query, params = conn.fetch_calls[0]
    assert "FROM admin_audit_log" in query
    assert params == (
        "FINANCE",
        "FX_RATE_UPSERT",
        "FNB",
        "fx_rate",
        "fx-123",
        25,
    )
    assert result[0]["result_payload"] == {"fx_rate_id": "fx-123"}


@pytest.mark.asyncio
async def test_get_admin_audit_summary(monkeypatch):
    conn = FakeConnection()
    monkeypatch.setattr(service, "db_connection", lambda: FakeDbConnection(conn))

    result = await service.get_admin_audit_summary(
        action_domain="FINANCE",
        tenant_code="FNB",
        hours=12,
    )

    assert len(conn.fetch_calls) == 3
    assert conn.fetch_calls[0][1] == (12, "FINANCE", "FNB")
    assert result == {
        "window_hours": 12,
        "action_domain": "FINANCE",
        "tenant_code": "FNB",
        "total": 3,
        "by_domain": [{"action_domain": "FINANCE", "count": 3}],
        "by_status": [{"action_status": "SUCCESS", "count": 3}],
        "top_actions": [{"action_type": "FX_RATE_UPSERT", "count": 3}],
    }


@pytest.mark.asyncio
async def test_try_write_admin_audit_swallows_audit_failures(monkeypatch):
    metric_calls = []

    async def boom(**kwargs):
        raise RuntimeError("database not ready")

    monkeypatch.setattr(service, "write_admin_audit", boom)
    monkeypatch.setattr(service, "admin_audit_write_inc", lambda **kwargs: metric_calls.append(kwargs))

    assert await service.try_write_admin_audit(action_type="X", action_domain="Y") is None
    assert metric_calls == [
        {
            "action_domain": "Y",
            "action_type": "X",
            "action_status": "SUCCESS",
            "result": "failure",
        }
    ]
