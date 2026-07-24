from __future__ import annotations

import pytest

from scripts import referral_saas_account_setup_ui_physical_check as setup_check
from scripts import referral_saas_selected_customer_e2e_physical_check as script


def _registry_payload() -> dict:
    return {
        "status": "ok",
        "accounts": [
            {
                "accountId": "acct-1",
                "accountCode": "ACC-1",
                "accountName": "Task 269 Customer",
                "accountStatus": "ACTIVE",
                "onboardingStatus": "READY",
                "primaryExternalTenantRef": "task-269-customer",
                "externalReferences": [
                    {
                        "refType": "external_tenant_ref",
                        "externalRef": "task-269-customer",
                        "referenceStatus": "ACTIVE",
                    },
                    {
                        "refType": "organisation_ref",
                        "externalRef": "org-task-269",
                        "referenceStatus": "ACTIVE",
                    },
                ],
            }
        ],
    }


def _ok(payload: dict | None = None) -> setup_check.ApiResult:
    return setup_check.ApiResult(status_code=200, payload=payload or {"status": "ok"})


def test_assert_no_internal_scope_leak_allows_confirmation_keys():
    script.assert_no_internal_scope_leak(
        {
            "no_tenant_code_exposure_confirmed": True,
            "account": {"accountId": "acct-1"},
        }
    )

    with pytest.raises(RuntimeError, match="tenant_code"):
        script.assert_no_internal_scope_leak({"account": {"tenant_code": "FNB"}})


def test_select_customer_matches_requested_external_references():
    selected = script._select_customer(
        _registry_payload(),
        external_tenant_ref="task-269-customer",
        organisation_ref="org-task-269",
    )

    assert selected["accountId"] == "acct-1"

    with pytest.raises(RuntimeError, match="No account matched"):
        script._select_customer(
            _registry_payload(),
            external_tenant_ref="missing",
            organisation_ref=None,
        )


def test_run_verifies_selected_customer_read_only_e2e(monkeypatch):
    calls: list[tuple[str, str, dict | None, dict | None]] = []

    def fake_get_json(**kwargs):
        calls.append(("GET", kwargs["path"], kwargs.get("query"), None))
        path = kwargs["path"]
        if path == "/v1/referral-saas/accounts":
            return _ok(_registry_payload())
        if path == "/v1/referral-saas/accounts/resolve":
            return _ok({"status": "ok", "account": {"accountId": "acct-1"}})
        if path == "/v1/referral-saas/accounts/membership-posture":
            return _ok({"status": "ok", "membershipPosture": {"activeCount": 0}})
        if path == "/v1/referral-saas/accounts/acct-1/technical-setup-readiness":
            return _ok({"status": "ok", "technicalSetupReadiness": {"overallStatus": "ACTION_REQUIRED"}})
        if path == "/v1/referral-saas/accounts/acct-1/campaigns":
            return _ok(
                {
                    "status": "ok",
                    "campaigns": [
                        {
                            "campaignCode": "CAMP001",
                            "status": "ACTIVE",
                            "lifecycle": "ACTIVE",
                        }
                    ],
                }
            )
        if path == "/v1/referral-saas/accounts/acct-1/campaigns/CAMP001/readiness":
            return _ok({"status": "ok", "readiness": {"overall_status": "READY"}})
        if path == "/v1/referral-saas/accounts/acct-1/reports/campaign_performance":
            return _ok({"status": "ok", "report": {"rows": []}})
        raise AssertionError(f"unexpected GET {path}")

    def fake_post_json(**kwargs):
        calls.append(("POST", kwargs["path"], None, kwargs["payload"]))
        assert kwargs["payload"] == {
            "format": "json",
            "redaction_profile": "tenant_safe",
            "filters": {"campaign_code": "CAMP001"},
            "row_limit": 25,
        }
        return _ok({"status": "ok", "export_preview": {"status": "PREVIEW_READY"}})

    monkeypatch.setattr(script.setup_check, "get_json", fake_get_json)
    monkeypatch.setattr(script.setup_check, "post_json", fake_post_json)

    result = script.run(
        script.parse_args(
            [
                "--base-url",
                "http://127.0.0.1:8000",
                "--admin-key",
                "test-admin-key",
                "--external-tenant-ref",
                "task-269-customer",
            ]
        )
    )

    assert result["status"] == "passed"
    assert result["task"] == "TASK-269"
    assert result["selected_customer"]["accountRef"] == "acct-1"
    assert result["selected_campaign"]["campaignCode"] == "CAMP001"
    assert result["no_campaign_mutation"] is True
    assert result["no_export_creation"] is True
    assert calls[-1][0] == "POST"
    assert calls[-1][1].startswith(
        "/v1/referral-saas/accounts/acct-1/reports/campaign_performance/exports/preview"
    )


def test_run_requires_campaign_evidence(monkeypatch):
    def fake_get_json(**kwargs):
        if kwargs["path"] == "/v1/referral-saas/accounts":
            return _ok(_registry_payload())
        if kwargs["path"] == "/v1/referral-saas/accounts/acct-1/campaigns":
            return _ok({"status": "ok", "campaigns": []})
        return _ok({"status": "ok", "account": {"accountId": "acct-1"}})

    monkeypatch.setattr(script.setup_check, "get_json", fake_get_json)

    with pytest.raises(RuntimeError, match="no campaigns"):
        script.run(script.parse_args(["--external-tenant-ref", "task-269-customer"]))
