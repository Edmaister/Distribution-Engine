from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from services import link_code_service as svc


class FakeConn:
    def __init__(self, rows=None, fail: bool = False):
        self.rows = list(rows or [])
        self.fail = fail
        self.calls = []

    async def fetchrow(self, query, *params):
        self.calls.append(("fetchrow", query, params))
        if self.fail:
            raise RuntimeError("source unavailable")
        if not self.rows:
            return None
        return self.rows.pop(0)


def patch_db(monkeypatch, conn):
    @asynccontextmanager
    async def fake_db_connection():
        yield conn

    monkeypatch.setattr(svc, "db_connection", fake_db_connection)


def _now():
    return datetime.now(timezone.utc)


@pytest.mark.asyncio
async def test_inspect_referral_code_returns_safe_canonical_shape(monkeypatch):
    conn = FakeConn(
        rows=[
            {
                "referrer_code_id": uuid4(),
                "referral_code": "REF123",
                "gaming_handle": "SafeHandle",
                "sticker": "GOLD",
                "tenant_code": "FNB",
                "segment": "PREMIER",
                "created_at": _now(),
                "updated_at": _now(),
                "referrer_ucn": "900001",
                "referrer_ucn_hash": "hash-900001",
            }
        ]
    )
    patch_db(monkeypatch, conn)

    result = await svc.inspect_link_code(
        tenant_code="fnb",
        source_type="referral_code",
        code_or_ref="REF123",
    )

    assert result["source_type"] == "REFERRAL_CODE"
    assert result["source"] == "referrer_codes"
    assert result["tenant_code"] == "FNB"
    assert result["status"] == "ISSUED"
    assert result["code"] == "REF123"
    assert result["participant"] == {
        "participant_type": "REFERRER",
        "participant_ref": "SafeHandle",
        "source": "referrer_codes",
    }
    assert result["evidence"]["referrer_ucn"] == "[REDACTED]"
    assert result["evidence"]["referrer_ucn_hash"] == "[REDACTED]"
    assert "900001" not in str(result)


@pytest.mark.asyncio
async def test_inspect_campaign_code_maps_active_definition_to_issued(monkeypatch):
    conn = FakeConn(
        rows=[
            {
                "campaign_code": "CAMP001",
                "campaign_id": uuid4(),
                "name": "Core Campaign",
                "segment": "PERSONAL",
                "tenant_code": "FNB",
                "is_active": True,
                "starts_at": _now() - timedelta(days=1),
                "ends_at": _now() + timedelta(days=1),
                "max_uses": 10,
                "uses_count": 1,
                "attributes": {"channel": "QR"},
                "created_at": _now(),
                "updated_at": _now(),
            }
        ]
    )
    patch_db(monkeypatch, conn)

    result = await svc.inspect_link_code(
        tenant_code="FNB",
        source_type="CAMPAIGN_CODE",
        code_or_ref="CAMP001",
    )

    assert result["status"] == "ISSUED"
    assert result["campaign"]["campaign_code"] == "CAMP001"
    assert result["metadata"]["segment"] == "PERSONAL"
    assert result["evidence"]["campaign_code"] == "CAMP001"


@pytest.mark.asyncio
async def test_inspect_campaign_code_maps_expired_definition(monkeypatch):
    conn = FakeConn(
        rows=[
            {
                "campaign_code": "CAMP001",
                "campaign_id": uuid4(),
                "name": "Core Campaign",
                "segment": "PERSONAL",
                "tenant_code": "FNB",
                "is_active": True,
                "starts_at": _now() - timedelta(days=10),
                "ends_at": _now() - timedelta(days=1),
                "max_uses": None,
                "uses_count": 1,
                "attributes": {},
                "created_at": _now(),
                "updated_at": _now(),
            }
        ]
    )
    patch_db(monkeypatch, conn)

    result = await svc.inspect_link_code(
        tenant_code="FNB",
        source_type="CAMPAIGN_CODE",
        code_or_ref="CAMP001",
    )

    assert result["status"] == "EXPIRED"


@pytest.mark.asyncio
async def test_inspect_campaign_referral_link_maps_to_linked(monkeypatch):
    campaign_track_id = uuid4()
    referral_track_id = uuid4()
    conn = FakeConn(
        rows=[
            {
                "campaign_track_id": campaign_track_id,
                "referral_track_id": referral_track_id,
                "created_at": _now(),
                "campaign_code": "CAMP001",
                "tenant_code": "FNB",
                "campaign_track_status": "VALIDATED",
                "referral_code": "REF123",
                "referral_status": "VALIDATED",
            }
        ]
    )
    patch_db(monkeypatch, conn)

    result = await svc.inspect_link_code(
        tenant_code="FNB",
        source_type="CAMPAIGN_REFERRAL_LINK",
        link_code_id=str(referral_track_id),
    )

    assert result["status"] == "LINKED"
    assert result["campaign"]["campaign_code"] == "CAMP001"
    assert result["campaign"]["campaign_track_id"] == str(campaign_track_id)
    assert result["attribution"]["referral_track_id"] == str(referral_track_id)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("source_status", "expected"),
    [("ACTIVE", "ACTIVE"), ("VOIDED", "VOIDED")],
)
async def test_inspect_route_referral_link_maps_source_status(
    monkeypatch, source_status, expected
):
    route_id = uuid4()
    referral_track_id = uuid4()
    opportunity_id = uuid4()
    distributor_id = uuid4()
    conn = FakeConn(
        rows=[
            {
                "route_id": route_id,
                "referral_track_id": referral_track_id,
                "tenant_code": "FNB",
                "distributor_id": distributor_id,
                "opportunity_id": opportunity_id,
                "link_status": source_status,
                "metadata": {"source": "portal"},
                "created_at": _now(),
                "updated_at": _now(),
            }
        ]
    )
    patch_db(monkeypatch, conn)

    result = await svc.inspect_link_code(
        tenant_code="FNB",
        source_type="ROUTE_REFERRAL_LINK",
        link_code_id=str(route_id),
    )

    assert result["status"] == expected
    assert result["participant"]["participant_type"] == "DISTRIBUTOR"
    assert result["attribution"]["route_id"] == str(route_id)
    assert result["attribution"]["opportunity_id"] == str(opportunity_id)


@pytest.mark.asyncio
async def test_inspect_composite_code_reports_compatibility_source(monkeypatch):
    conn = FakeConn()
    patch_db(monkeypatch, conn)

    result = await svc.inspect_link_code(
        tenant_code="FNB",
        source_type="COMPOSITE_CODE",
        code_or_ref="FNB-ABC123",
    )

    assert result["status"] == "UNKNOWN"
    assert result["source"] == "composite_code_service"
    assert result["source_warnings"][0]["code"] == "COMPATIBILITY_SOURCE_ONLY"
    assert conn.calls == []


@pytest.mark.asyncio
async def test_inspect_missing_referral_code_returns_invalid(monkeypatch):
    conn = FakeConn(rows=[None, None])
    patch_db(monkeypatch, conn)

    result = await svc.inspect_link_code(
        tenant_code="FNB",
        source_type="REFERRAL_CODE",
        code_or_ref="MISSING",
    )

    assert result["status"] == "INVALID"
    assert result["missing_evidence"][0]["code"] == "SOURCE_NOT_FOUND"


@pytest.mark.asyncio
async def test_inspect_tenant_mismatch_returns_invalid_without_other_tenant(
    monkeypatch,
):
    conn = FakeConn(rows=[None, {"tenant_code": "PNP"}])
    patch_db(monkeypatch, conn)

    result = await svc.inspect_link_code(
        tenant_code="FNB",
        source_type="REFERRAL_CODE",
        code_or_ref="REF123",
    )

    assert result["status"] == "INVALID"
    assert result["missing_evidence"][0]["code"] == "TENANT_MISMATCH"
    assert "PNP" not in str(result["missing_evidence"])


@pytest.mark.asyncio
async def test_inspect_source_failure_returns_unknown(monkeypatch):
    conn = FakeConn(fail=True)
    patch_db(monkeypatch, conn)

    result = await svc.inspect_link_code(
        tenant_code="FNB",
        source_type="CAMPAIGN_CODE",
        code_or_ref="CAMP001",
    )

    assert result["status"] == "UNKNOWN"
    assert result["source_warnings"][0]["code"] == "SOURCE_UNAVAILABLE"


@pytest.mark.asyncio
async def test_inspect_can_omit_evidence(monkeypatch):
    conn = FakeConn(
        rows=[
            {
                "referrer_code_id": uuid4(),
                "referral_code": "REF123",
                "gaming_handle": "SafeHandle",
                "sticker": "GOLD",
                "tenant_code": "FNB",
                "segment": "PREMIER",
                "created_at": _now(),
                "updated_at": _now(),
                "referrer_ucn": "900001",
                "referrer_ucn_hash": "hash-900001",
            }
        ]
    )
    patch_db(monkeypatch, conn)

    result = await svc.inspect_link_code(
        tenant_code="FNB",
        source_type="REFERRAL_CODE",
        code_or_ref="REF123",
        include_evidence=False,
    )

    assert result["evidence"] is None
    assert result["redactions"] == []


@pytest.mark.asyncio
async def test_inspect_rejects_invalid_inputs():
    with pytest.raises(ValueError, match="Unsupported link/code source_type"):
        await svc.inspect_link_code(
            tenant_code="FNB",
            source_type="BAD_SOURCE",
            code_or_ref="ABC",
        )

    with pytest.raises(ValueError, match="tenant_code is required"):
        await svc.inspect_link_code(
            tenant_code="",
            source_type="REFERRAL_CODE",
            code_or_ref="ABC",
        )

    with pytest.raises(ValueError, match="link_code_id or code_or_ref is required"):
        await svc.inspect_link_code(
            tenant_code="FNB",
            source_type="REFERRAL_CODE",
        )
