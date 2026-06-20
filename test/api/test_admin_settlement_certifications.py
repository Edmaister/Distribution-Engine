from __future__ import annotations

from uuid import uuid4

import pytest
from fastapi import HTTPException

import apps.api.routers.admin_settlement_certifications as mod


def unique_uuid() -> str:
    return str(uuid4())


@pytest.mark.asyncio
async def test_create_certification(monkeypatch):
    async def fake_create_settlement_certification(**kwargs):
        return {
            "certification_id": unique_uuid(),
            "tenant_code": kwargs["tenant_code"],
            "period_id": kwargs["period_id"],
            "expected_amount": kwargs["expected_amount"],
            "actual_amount": kwargs["actual_amount"],
            "variance_amount": -50,
            "status": "PENDING",
        }

    monkeypatch.setattr(
        mod,
        "create_settlement_certification",
        fake_create_settlement_certification,
    )

    result = await mod.create_certification(
        {
            "tenant_code": "FNB",
            "period_id": unique_uuid(),
            "expected_amount": 1000,
            "actual_amount": 950,
        }
    )

    assert result["tenant_code"] == "FNB"
    assert result["status"] == "PENDING"
    assert result["variance_amount"] == -50


@pytest.mark.asyncio
async def test_list_certifications(monkeypatch):
    async def fake_list_settlement_certifications(**kwargs):
        return [
            {
                "certification_id": unique_uuid(),
                "tenant_code": kwargs["tenant_code"],
                "status": "PENDING",
            }
        ]

    monkeypatch.setattr(
        mod,
        "list_settlement_certifications",
        fake_list_settlement_certifications,
    )

    result = await mod.list_certifications(
        tenant_code="FNB",
        limit=10,
    )

    assert len(result) == 1
    assert result[0]["tenant_code"] == "FNB"


@pytest.mark.asyncio
async def test_get_certification_found(monkeypatch):
    certification_id = unique_uuid()

    async def fake_get_settlement_certification(value):
        return {
            "certification_id": value,
            "tenant_code": "FNB",
            "status": "PENDING",
        }

    monkeypatch.setattr(
        mod,
        "get_settlement_certification",
        fake_get_settlement_certification,
    )

    result = await mod.get_certification(certification_id)

    assert result["certification_id"] == certification_id
    assert result["status"] == "PENDING"


@pytest.mark.asyncio
async def test_get_certification_not_found(monkeypatch):
    async def fake_get_settlement_certification(value):
        return None

    monkeypatch.setattr(
        mod,
        "get_settlement_certification",
        fake_get_settlement_certification,
    )

    with pytest.raises(HTTPException) as exc:
        await mod.get_certification(unique_uuid())

    assert exc.value.status_code == 404
    assert exc.value.detail == "Certification not found"


@pytest.mark.asyncio
async def test_certify_found(monkeypatch):
    certification_id = unique_uuid()

    async def fake_certify_settlement_period(**kwargs):
        return {
            "certification_id": kwargs["certification_id"],
            "status": "CERTIFIED",
            "certified_by": kwargs["certified_by"],
            "certification_notes": kwargs["certification_notes"],
        }

    monkeypatch.setattr(
        mod,
        "certify_settlement_period",
        fake_certify_settlement_period,
    )

    result = await mod.certify(
        certification_id,
        {
            "certified_by": "Treasury User",
            "certification_notes": "Certified.",
        },
    )

    assert result["certification_id"] == certification_id
    assert result["status"] == "CERTIFIED"
    assert result["certified_by"] == "Treasury User"


@pytest.mark.asyncio
async def test_certify_found_without_notes(monkeypatch):
    certification_id = unique_uuid()

    async def fake_certify_settlement_period(**kwargs):
        return {
            "certification_id": kwargs["certification_id"],
            "status": "CERTIFIED",
            "certified_by": kwargs["certified_by"],
            "certification_notes": kwargs["certification_notes"],
        }

    monkeypatch.setattr(
        mod,
        "certify_settlement_period",
        fake_certify_settlement_period,
    )

    result = await mod.certify(
        certification_id,
        {
            "certified_by": "Treasury User",
        },
    )

    assert result["status"] == "CERTIFIED"
    assert result["certification_notes"] is None


@pytest.mark.asyncio
async def test_certify_not_found(monkeypatch):
    async def fake_certify_settlement_period(**kwargs):
        return None

    monkeypatch.setattr(
        mod,
        "certify_settlement_period",
        fake_certify_settlement_period,
    )

    with pytest.raises(HTTPException) as exc:
        await mod.certify(
            unique_uuid(),
            {
                "certified_by": "Treasury User",
            },
        )

    assert exc.value.status_code == 404
    assert exc.value.detail == "Certification not found"