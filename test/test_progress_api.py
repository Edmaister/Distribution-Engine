from __future__ import annotations

from fastapi import HTTPException, Response
import pytest
import asyncio

import apps.api.routers.progress as mod
from apps.api.schemas.progress import ProgressPostRequest


def test_post_progress_sets_status_and_returns_body(monkeypatch):
    captured = {}

    async def fake_handle_progress_event(req, tenant_code=None):
        captured["req"] = req
        captured["tenant_code"] = tenant_code
        return (
            {
                "status": "ok",
                "message": "Progress recorded",
                "referralTrackId": "track-1",
                "progressPercent": 50,
                "progressBand": "IN_PROGRESS",
                "displayStatus": "In progress",
                "nextMilestone": "SALARY_SWITCHED",
                "occurredAt": "2026-05-07T00:00:00Z",
                "recordedAt": "2026-05-07T00:00:01Z",
            },
            202,
        )

    monkeypatch.setattr(mod, "handle_progress_event", fake_handle_progress_event)

    req = ProgressPostRequest(
        referralTrackId="track-1",
        eventType="FIRST_TRANSACTION_COMPLETED",
        occurredAt="2026-05-07T00:00:00Z",
    )

    response = Response()

    result = asyncio.run(
        mod.post_progress(
            req=req,
            response=response,
            identity={"tenant_code": "FNB"},
        )
    )

    assert response.status_code == 202
    assert result["status"] == "ok"
    assert result["referralTrackId"] == "track-1"
    assert captured["req"] == req
    assert captured["tenant_code"] == "FNB"


def test_progress_request_accepts_insurance_event_and_journey_fields():
    req = ProgressPostRequest(
        referralTrackId="track-1",
        eventType="FIRST_PREMIUM_PAID",
        journeyCode="INSURANCE_POLICY",
        journeyVersion="v1",
        product="INSURANCE",
        subProduct="LIFE",
    )

    assert req.eventType == "FIRST_PREMIUM_PAID"
    assert req.journeyCode == "INSURANCE_POLICY"
    assert req.journeyVersion == "v1"


def test_get_referrer_referrals_progress_success(monkeypatch):
    captured = {}

    async def fake_get_referrals_progress_by_referrer_ucn(referrer_ucn, tenant_code=None):
        captured["referrer_ucn"] = referrer_ucn
        captured["tenant_code"] = tenant_code
        return {
            "referrerUcn": referrer_ucn,
            "tenantCode": tenant_code,
            "count": 1,
            "referrals": [
                {
                    "referralTrackId": "track-1",
                    "refereeUcn": "referee-1",
                    "product": "TRANSACTIONAL",
                    "subProduct": "GOLD",
                    "progressPercent": 50,
                    "progressBand": "IN_PROGRESS",
                    "displayStatus": "In progress",
                    "nextMilestone": "SALARY_SWITCHED",
                }
            ],
        }

    monkeypatch.setattr(
        mod,
        "get_referrals_progress_by_referrer_ucn",
        fake_get_referrals_progress_by_referrer_ucn,
    )

    result = asyncio.run(
        mod.get_referrer_referrals_progress(
            referrerUcn="referrer-1",
            identity={"tenant_code": "FNB"},
        )
    )

    assert result["referrerUcn"] == "referrer-1"
    assert result["tenantCode"] == "FNB"
    assert result["count"] == 1
    assert captured == {
        "referrer_ucn": "referrer-1",
        "tenant_code": "FNB",
    }


def test_get_referrer_referrals_progress_handles_service_error(monkeypatch):
    async def fake_get_referrals_progress_by_referrer_ucn(referrer_ucn, tenant_code=None):
        raise RuntimeError("boom")

    monkeypatch.setattr(
        mod,
        "get_referrals_progress_by_referrer_ucn",
        fake_get_referrals_progress_by_referrer_ucn,
    )

    with pytest.raises(HTTPException) as exc:
        asyncio.run(
            mod.get_referrer_referrals_progress(
                referrerUcn="referrer-1",
                identity={"tenant_code": "FNB"},
            )
        )

    assert exc.value.status_code == 500
    assert exc.value.detail == "Internal server error"
