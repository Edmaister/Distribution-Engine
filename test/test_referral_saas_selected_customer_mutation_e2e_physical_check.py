from __future__ import annotations

import pytest

from scripts import referral_saas_account_setup_ui_physical_check as setup_check
from scripts import referral_saas_selected_customer_mutation_e2e_physical_check as script


def _registry_payload() -> dict:
    return {
        "status": "ok",
        "accounts": [
            {
                "accountId": "acct-271",
                "accountCode": "ACC-271",
                "accountName": "Task 271 Customer",
                "primaryExternalTenantRef": "task-271-customer",
                "externalReferences": [
                    {
                        "refType": "external_tenant_ref",
                        "externalRef": "task-271-customer",
                        "referenceStatus": "ACTIVE",
                    },
                    {
                        "refType": "organisation_ref",
                        "externalRef": "org-task-271",
                        "referenceStatus": "ACTIVE",
                    },
                ],
            }
        ],
    }


def _ok(payload: dict | None = None, *, status_code: int = 200) -> setup_check.ApiResult:
    return setup_check.ApiResult(status_code=status_code, payload=payload or {"status": "ok"})


def test_run_verifies_selected_customer_mutation_path(monkeypatch):
    calls: list[tuple[str, str, dict | None]] = []

    def fake_get_json(**kwargs):
        calls.append(("GET", kwargs["path"], kwargs.get("query")))
        if kwargs["path"] == "/v1/referral-saas/accounts":
            return _ok(_registry_payload())
        if kwargs["path"] == "/v1/referral-saas/accounts/acct-271/reports/campaign_performance":
            return _ok({"status": "ok", "report": {"rows": []}})
        raise AssertionError(f"unexpected GET {kwargs['path']}")

    def fake_post_json(**kwargs):
        calls.append(("POST", kwargs["path"], kwargs["payload"]))
        path = kwargs["path"]
        if path == "/v1/referral-saas/accounts/acct-271/campaigns":
            assert "tenantCode" not in str(kwargs["payload"])
            return _ok(
                {
                    "status": "created",
                    "campaignSetup": {
                        "campaign": {"campaignCode": "TASK271"},
                    },
                    "no_campaign_activation_confirmed": True,
                    "no_link_generation_confirmed": True,
                    "no_webhook_delivery_confirmed": True,
                    "no_billing_or_money_movement_confirmed": True,
                }
            )
        if path == "/v1/referral-saas/accounts/acct-271/campaigns/TASK271/review-submissions":
            return _ok(
                {
                    "status": "ok",
                    "no_campaign_activation_confirmed": True,
                    "no_link_generation_confirmed": True,
                    "no_webhook_delivery_confirmed": True,
                    "no_billing_or_money_movement_confirmed": True,
                }
            )
        if path == "/v1/referral-saas/accounts/acct-271/campaigns/TASK271/review-decisions":
            return _ok(
                {
                    "status": "ok",
                    "no_campaign_activation_confirmed": True,
                    "no_webhook_delivery_confirmed": True,
                    "no_billing_or_money_movement_confirmed": True,
                }
            )
        if path == "/v1/referral-saas/accounts/acct-271/campaigns/TASK271/activation-requests":
            return _ok(
                {
                    "status": "ok",
                    "no_link_generation_confirmed": True,
                    "no_validation_track_created_confirmed": True,
                    "no_webhook_delivery_confirmed": True,
                    "no_credential_creation_confirmed": True,
                    "no_billing_or_money_movement_confirmed": True,
                }
            )
        if path == "/v1/referral-saas/accounts/acct-271/campaigns/TASK271/referral-codes":
            return _ok(
                {
                    "status": "ok",
                    "linkCode": {"referralCode": "REF271"},
                    "no_campaign_activation_confirmed": True,
                    "no_webhook_delivery_confirmed": True,
                    "no_billing_or_money_movement_confirmed": True,
                },
                status_code=201,
            )
        if path == "/v1/referral-saas/accounts/acct-271/campaigns/TASK271/referrals/validate":
            return _ok(
                {
                    "status": "ok",
                    "validation": {"validationStatus": "VALIDATED"},
                    "no_campaign_activation_confirmed": True,
                    "no_webhook_delivery_confirmed": True,
                    "no_billing_or_money_movement_confirmed": True,
                }
            )
        if path.startswith(
            "/v1/referral-saas/accounts/acct-271/reports/campaign_performance/exports/preview"
        ):
            return _ok({"status": "ok", "export_preview": {"status": "PREVIEW_READY"}})
        raise AssertionError(f"unexpected POST {path}")

    def fake_request_json(**kwargs):
        calls.append((kwargs["method"], kwargs["path"], kwargs["payload"]))
        if kwargs["method"] == "PUT" and kwargs["path"] == (
            "/v1/referral-saas/accounts/acct-271/campaigns/TASK271/policy-settings"
        ):
            return _ok(
                {
                    "status": "ok",
                    "no_campaign_activation_confirmed": True,
                    "no_link_generation_confirmed": True,
                    "no_webhook_delivery_confirmed": True,
                    "no_billing_or_money_movement_confirmed": True,
                }
            )
        raise AssertionError(f"unexpected request {kwargs['method']} {kwargs['path']}")

    monkeypatch.setattr(script.setup_check, "get_json", fake_get_json)
    monkeypatch.setattr(script.setup_check, "post_json", fake_post_json)
    monkeypatch.setattr(script.setup_check, "request_json", fake_request_json)

    result = script.run(
        script.parse_args(
            [
                "--base-url",
                "http://127.0.0.1:8000",
                "--admin-key",
                "test-admin-key",
                "--external-tenant-ref",
                "task-271-customer",
                "--suffix",
                "271001",
            ]
        )
    )

    assert result["status"] == "passed"
    assert result["task"] == "TASK-271"
    assert result["selected_customer"]["accountRef"] == "acct-271"
    assert result["created_campaign"]["campaignCode"] == "TASK271"
    assert result["issued_referral_code"] == "REF271"
    assert result["campaign_mutation_limited_to_setup_policy_review_activation"] is True
    assert result["link_code_mutation_limited_to_issue_and_validation"] is True
    assert result["no_webhook_delivery"] is True
    assert result["no_billing_or_money_movement"] is True
    assert [call[0] for call in calls].count("PUT") == 1


def test_run_fails_when_mutation_response_leaks_internal_scope(monkeypatch):
    def fake_get_json(**kwargs):
        if kwargs["path"] == "/v1/referral-saas/accounts":
            return _ok(_registry_payload())
        return _ok({"status": "ok"})

    def fake_post_json(**kwargs):
        return _ok(
            {
                "status": "created",
                "campaignSetup": {"campaign": {"campaignCode": "TASK271"}},
                "tenant_code": "FNB",
                "no_campaign_activation_confirmed": True,
                "no_link_generation_confirmed": True,
                "no_webhook_delivery_confirmed": True,
                "no_billing_or_money_movement_confirmed": True,
            }
        )

    monkeypatch.setattr(script.setup_check, "get_json", fake_get_json)
    monkeypatch.setattr(script.setup_check, "post_json", fake_post_json)

    with pytest.raises(RuntimeError, match="tenant_code"):
        script.run(
            script.parse_args(
                [
                    "--external-tenant-ref",
                    "task-271-customer",
                    "--suffix",
                    "271002",
                ]
            )
        )


def test_run_requires_no_adjacent_action_confirmations(monkeypatch):
    def fake_get_json(**kwargs):
        if kwargs["path"] == "/v1/referral-saas/accounts":
            return _ok(_registry_payload())
        return _ok({"status": "ok"})

    def fake_post_json(**kwargs):
        return _ok(
            {
                "status": "created",
                "campaignSetup": {"campaign": {"campaignCode": "TASK271"}},
                "no_campaign_activation_confirmed": True,
                "no_link_generation_confirmed": True,
                "no_webhook_delivery_confirmed": False,
                "no_billing_or_money_movement_confirmed": True,
            }
        )

    monkeypatch.setattr(script.setup_check, "get_json", fake_get_json)
    monkeypatch.setattr(script.setup_check, "post_json", fake_post_json)

    with pytest.raises(RuntimeError, match="no_webhook_delivery_confirmed"):
        script.run(
            script.parse_args(
                [
                    "--external-tenant-ref",
                    "task-271-customer",
                    "--suffix",
                    "271003",
                ]
            )
        )
