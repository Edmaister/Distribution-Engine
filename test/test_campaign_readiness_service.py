from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone

import pytest

from services import campaign_readiness_service as svc


class FakeConn:
    def __init__(self, rows=None, fail_on_call: int | None = None):
        self.rows = list(rows or [])
        self.fail_on_call = fail_on_call
        self.calls = []

    async def fetchrow(self, query, *params):
        self.calls.append(("fetchrow", query, params))
        if self.fail_on_call == len(self.calls):
            raise RuntimeError("source unavailable")
        if not self.rows:
            return None
        return self.rows.pop(0)


def patch_db(monkeypatch, conn):
    @asynccontextmanager
    async def fake_db_connection():
        yield conn

    monkeypatch.setattr(svc, "db_connection", fake_db_connection)


def _campaign(**overrides):
    row = {
        "campaign_code": "CAMP001",
        "tenant_code": "FNB",
        "segment": "PERSONAL",
        "name": "Test Campaign",
        "is_active": True,
        "starts_at": None,
        "ends_at": None,
        "max_uses": 100,
        "uses_count": 10,
    }
    row.update(overrides)
    return row


def _policy(**overrides):
    row = {
        "campaign_code": "CAMP001",
        "tenant_code": "FNB",
        "version": 2,
        "is_active": True,
        "rolling_window_days": 30,
        "updated_at": datetime(2026, 6, 25, tzinfo=timezone.utc),
    }
    row.update(overrides)
    return row


@pytest.mark.asyncio
async def test_campaign_readiness_ready_for_create_track(monkeypatch):
    conn = FakeConn(rows=[_campaign(), _policy()])
    patch_db(monkeypatch, conn)

    result = await svc.get_campaign_readiness(
        tenant_code="fnb",
        campaign_code="camp001",
        operation="create_track",
    )

    assert result["tenant_code"] == "FNB"
    assert result["campaign_code"] == "CAMP001"
    assert result["operation"] == "CREATE_TRACK"
    assert result["canonical_lifecycle"] == "ACTIVE"
    assert result["readiness"] == "READY"
    assert result["can_proceed"] is True
    assert result["blockers"] == []
    assert result["warnings"] == []
    assert result["unknowns"] == []
    assert result["evidence"]["campaign"]["campaign_code"] == "CAMP001"
    assert result["evidence"]["policy"]["version"] == 2
    assert len(conn.calls) == 2


@pytest.mark.asyncio
async def test_campaign_readiness_campaign_not_found(monkeypatch):
    conn = FakeConn(rows=[None])
    patch_db(monkeypatch, conn)

    result = await svc.get_campaign_readiness(
        tenant_code="FNB",
        campaign_code="MISSING",
        operation="CONTROL_PLANE_VIEW",
    )

    assert result["readiness"] == "NOT_READY"
    assert result["can_proceed"] is False
    assert result["canonical_lifecycle"] == "UNKNOWN"
    assert result["blockers"][0]["code"] == "CAMPAIGN_NOT_FOUND"
    assert len(conn.calls) == 1


@pytest.mark.asyncio
async def test_campaign_readiness_tenant_mismatch_blocks(monkeypatch):
    conn = FakeConn(rows=[_campaign(tenant_code="PNP"), _policy(tenant_code="PNP")])
    patch_db(monkeypatch, conn)

    result = await svc.get_campaign_readiness(
        tenant_code="FNB",
        campaign_code="CAMP001",
        operation="CREATE_TRACK",
    )

    assert result["readiness"] == "NOT_READY"
    assert any(item["code"] == "TENANT_MISMATCH" for item in result["blockers"])


@pytest.mark.asyncio
async def test_campaign_readiness_inactive_blocks(monkeypatch):
    conn = FakeConn(rows=[_campaign(is_active=False), _policy()])
    patch_db(monkeypatch, conn)

    result = await svc.get_campaign_readiness(
        tenant_code="FNB",
        campaign_code="CAMP001",
        operation="CREATE_TRACK",
    )

    assert result["canonical_lifecycle"] == "PAUSED"
    assert result["readiness"] == "NOT_READY"
    assert any(item["code"] == "CAMPAIGN_INACTIVE" for item in result["blockers"])


@pytest.mark.asyncio
async def test_campaign_readiness_not_started_blocks(monkeypatch):
    future = datetime.now(timezone.utc) + timedelta(days=1)
    conn = FakeConn(rows=[_campaign(starts_at=future), _policy()])
    patch_db(monkeypatch, conn)

    result = await svc.get_campaign_readiness(
        tenant_code="FNB",
        campaign_code="CAMP001",
        operation="CREATE_TRACK",
    )

    assert result["canonical_lifecycle"] == "SCHEDULED"
    assert any(item["code"] == "CAMPAIGN_NOT_STARTED" for item in result["blockers"])


@pytest.mark.asyncio
async def test_campaign_readiness_expired_blocks(monkeypatch):
    past = datetime.now(timezone.utc) - timedelta(days=1)
    conn = FakeConn(rows=[_campaign(ends_at=past), _policy()])
    patch_db(monkeypatch, conn)

    result = await svc.get_campaign_readiness(
        tenant_code="FNB",
        campaign_code="CAMP001",
        operation="CREATE_TRACK",
    )

    assert result["canonical_lifecycle"] == "EXPIRED"
    assert any(item["code"] == "CAMPAIGN_EXPIRED" for item in result["blockers"])


@pytest.mark.asyncio
async def test_campaign_readiness_cap_exhausted_blocks(monkeypatch):
    conn = FakeConn(rows=[_campaign(max_uses=10, uses_count=10), _policy()])
    patch_db(monkeypatch, conn)

    result = await svc.get_campaign_readiness(
        tenant_code="FNB",
        campaign_code="CAMP001",
        operation="CREATE_TRACK",
    )

    assert result["readiness"] == "NOT_READY"
    assert any(item["code"] == "CAMPAIGN_CAP_EXHAUSTED" for item in result["blockers"])


@pytest.mark.asyncio
async def test_campaign_readiness_missing_policy_warns_for_create_track(monkeypatch):
    conn = FakeConn(rows=[_campaign(), None])
    patch_db(monkeypatch, conn)

    result = await svc.get_campaign_readiness(
        tenant_code="FNB",
        campaign_code="CAMP001",
        operation="CREATE_TRACK",
    )

    assert result["readiness"] == "READY_WITH_WARNINGS"
    assert result["can_proceed"] is True
    assert result["warnings"][0]["code"] == "NO_ACTIVE_POLICY"


@pytest.mark.asyncio
async def test_campaign_readiness_missing_policy_blocks_publish(monkeypatch):
    conn = FakeConn(rows=[_campaign(), None])
    patch_db(monkeypatch, conn)

    result = await svc.get_campaign_readiness(
        tenant_code="FNB",
        campaign_code="CAMP001",
        operation="PUBLISH_OPPORTUNITY",
        opportunity_id="opp-1",
    )

    assert result["readiness"] == "NOT_READY"
    assert any(item["code"] == "NO_ACTIVE_POLICY" for item in result["blockers"])


@pytest.mark.asyncio
async def test_campaign_readiness_opportunity_scope_returns_safe_unknown(monkeypatch):
    conn = FakeConn(rows=[_campaign(), _policy()])
    patch_db(monkeypatch, conn)

    result = await svc.get_campaign_readiness(
        tenant_code="FNB",
        campaign_code="CAMP001",
        operation="ROUTE_OPPORTUNITY",
    )

    assert result["readiness"] == "UNKNOWN"
    assert result["can_proceed"] is False
    assert result["unknowns"][0]["code"] == "SOURCE_UNAVAILABLE"
    assert result["unknowns"][0]["source"] == "distribution_opportunities"


@pytest.mark.asyncio
async def test_campaign_readiness_policy_source_failure_is_unknown(monkeypatch):
    conn = FakeConn(rows=[_campaign()], fail_on_call=2)
    patch_db(monkeypatch, conn)

    result = await svc.get_campaign_readiness(
        tenant_code="FNB",
        campaign_code="CAMP001",
        operation="CONTROL_PLANE_VIEW",
    )

    assert result["readiness"] == "UNKNOWN"
    assert result["unknowns"][0]["code"] == "POLICY_UNKNOWN"


@pytest.mark.asyncio
async def test_campaign_readiness_campaign_source_failure_is_unknown(monkeypatch):
    conn = FakeConn(fail_on_call=1)
    patch_db(monkeypatch, conn)

    result = await svc.get_campaign_readiness(
        tenant_code="FNB",
        campaign_code="CAMP001",
        operation="CONTROL_PLANE_VIEW",
    )

    assert result["readiness"] == "UNKNOWN"
    assert result["unknowns"][0]["source"] == "marketing_campaigns"


@pytest.mark.asyncio
async def test_campaign_readiness_can_omit_evidence(monkeypatch):
    conn = FakeConn(rows=[_campaign(), _policy()])
    patch_db(monkeypatch, conn)

    result = await svc.get_campaign_readiness(
        tenant_code="FNB",
        campaign_code="CAMP001",
        operation="CONTROL_PLANE_VIEW",
        include_evidence=False,
    )

    assert result["evidence"] == {}


@pytest.mark.asyncio
async def test_campaign_readiness_rejects_invalid_operation():
    with pytest.raises(ValueError, match="Unsupported campaign readiness operation"):
        await svc.get_campaign_readiness(
            tenant_code="FNB",
            campaign_code="CAMP001",
            operation="DELETE_CAMPAIGN",
        )


@pytest.mark.asyncio
async def test_campaign_readiness_requires_tenant_and_campaign():
    with pytest.raises(ValueError, match="tenant_code is required"):
        await svc.get_campaign_readiness(
            tenant_code="",
            campaign_code="CAMP001",
        )

    with pytest.raises(ValueError, match="campaign_code is required"):
        await svc.get_campaign_readiness(
            tenant_code="FNB",
            campaign_code="",
        )
