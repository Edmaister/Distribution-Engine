from __future__ import annotations

import pytest

from scripts import core_role_journey_smoke as smoke


def test_core_role_journey_smoke_checks_workspaces_and_scope_boundaries(monkeypatch):
    calls = []

    def fake_request(method, base_url, path, *, api_key=None, expected_status=200, **kwargs):
        calls.append(
            {
                "method": method,
                "path": path,
                "api_key": api_key,
                "expected_status": expected_status,
                "params": kwargs.get("params"),
            }
        )

        if path == "/auth/session":
            sessions = {
                "consumer-key": ("CONSUMER", "consumer_journey"),
                "producer-key": ("PRODUCER", "producer_supply"),
                "distributor-key": ("DISTRIBUTOR", "distributor_demand"),
                "admin-key": ("ADMIN", "admin"),
            }
            role, workspace = sessions[api_key]
            return {
                "session": {"role": role},
                "recommended_workspace": {"code": workspace},
            }

        if path == "/v1/experience/consumer":
            if expected_status == 403:
                return {"detail": "forbidden"}
            return {
                "status": "ok",
                "tenantCode": "FNB",
                "referrerUcn": "900010",
                "sections": {},
                "unavailableSections": [],
            }

        if path.endswith("/supply/proof/insurance"):
            if expected_status == 403:
                return {"detail": "forbidden"}
            return {
                "status": "READY",
                "scope": "producer",
                "surface": "Producer - Supply",
                "tenant_code": "FNB",
            }

        if path == "/distribution/portal/proof/insurance":
            if expected_status == 403:
                return {"detail": "forbidden"}
            return {
                "status": "READY",
                "scope": "distributor",
                "surface": "Distributor - Demand",
                "tenant_code": "FNB",
            }

        if path == "/admin/audit/summary":
            if expected_status == 401:
                return {"detail": "unauthorized"}
            return {"summary": {"total": 1}}

        raise AssertionError(f"Unexpected request: {method} {path}")

    monkeypatch.setattr(smoke, "_request", fake_request)

    smoke.run_smoke(
        base_url="http://example.test",
        admin_key="admin-key",
        consumer_key="consumer-key",
        producer_key="producer-key",
        distributor_key="distributor-key",
        tenant_code="FNB",
        referrer_ucn="900010",
        producer_code="INSURECO",
        distributor_code="DIST-INSURANCE-ADVOCATE",
    )

    expected_boundaries = [
        ("/v1/experience/consumer", 403),
        ("/v1/tenants/FNB/producers/OTHER/supply/proof/insurance", 403),
        ("/distribution/portal/proof/insurance", 403),
        ("/admin/audit/summary", 401),
    ]
    assert all(
        any(call["path"] == path and call["expected_status"] == status for call in calls)
        for path, status in expected_boundaries
    )


def test_core_role_journey_smoke_fails_on_wrong_recommended_workspace(monkeypatch):
    def fake_request(method, base_url, path, *, api_key=None, expected_status=200, **kwargs):
        return {
            "session": {"role": "CONSUMER"},
            "recommended_workspace": {"code": "admin"},
        }

    monkeypatch.setattr(smoke, "_request", fake_request)

    with pytest.raises(smoke.SmokeFailure, match="recommended workspace"):
        smoke.run_consumer_check(
            base_url="http://example.test",
            consumer_key="consumer-key",
            tenant_code="FNB",
            referrer_ucn="900010",
        )
