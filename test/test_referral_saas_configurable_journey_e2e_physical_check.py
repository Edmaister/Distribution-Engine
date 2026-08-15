from __future__ import annotations

import pytest

from scripts import referral_saas_account_setup_ui_physical_check as setup_check
from scripts import referral_saas_configurable_journey_e2e_physical_check as script


def _ok(payload: dict | None = None, *, status_code: int = 200) -> setup_check.ApiResult:
    return setup_check.ApiResult(status_code=status_code, payload=payload or {"status": "ok"})


def _registry_payload() -> dict:
    return {
        "status": "ok",
        "accounts": [
            {
                "accountId": "acct-394",
                "accountCode": "ACCT-394",
                "accountName": "Task 394 Customer",
                "primaryExternalTenantRef": "task-394-customer",
                "externalReferences": [
                    {
                        "refType": "external_tenant_ref",
                        "externalRef": "task-394-customer",
                        "referenceStatus": "ACTIVE",
                    },
                    {
                        "refType": "organisation_ref",
                        "externalRef": "org-task-394",
                        "referenceStatus": "ACTIVE",
                    },
                ],
            }
        ],
    }


def _catalogue_payload() -> dict:
    return {
        "status": "READY",
        "templates": [
            {
                "templateCode": "REFERRAL_STANDARD",
                "versions": [
                    {
                        "templateVersion": "1.0.0",
                        "status": "APPROVED",
                        "milestoneCount": 2,
                    }
                ],
            }
        ],
    }


def test_run_proves_configurable_journey_end_to_end(monkeypatch):
    calls: list[tuple[str, str, dict | None]] = []
    progress_seen = 0

    def fake_get_json(**kwargs):
        calls.append(("GET", kwargs["path"], kwargs.get("query")))
        path = kwargs["path"]
        if path == "/v1/referral-saas/accounts":
            return _ok(_registry_payload())
        if path == "/v1/referral-saas/journey-templates":
            assert kwargs["query"] == {"status": "APPROVED", "limit": "50"}
            return _ok(_catalogue_payload())
        if path.endswith("/journey-binding"):
            return _ok(
                {
                    "status": "ok",
                    "journeyBinding": {
                        "bindingStatus": "ACTIVE",
                        "activationGateSatisfied": True,
                    },
                }
            )
        if path.endswith("/progress-status"):
            return _ok({"status": "ok", "progressStatus": {"safeStatus": {}}})
        if path.endswith("/trace"):
            return _ok({"status": "ok", "attributionTrace": {"traceStatus": "PARTIAL"}})
        if path.endswith("/reports/campaign_performance"):
            assert kwargs["query"]["campaign_code"] == "TASK394"
            return _ok({"status": "ok", "report": {"rows": []}})
        if path.endswith("/journey-analytics"):
            return _ok({"status": "ok", "journeyAnalytics": {"versionCount": 1}})
        raise AssertionError(f"unexpected GET {path}")

    def fake_post_json(**kwargs):
        nonlocal progress_seen
        calls.append(("POST", kwargs["path"], kwargs["payload"]))
        path = kwargs["path"]
        if path.endswith("/journey-drafts/draft-394/validate"):
            return _ok(
                {
                    "status": "ok",
                    "validation": {
                        "validationStatus": "PASSED_WITH_WARNINGS",
                        "customerJourneyDraftId": "draft-394",
                    },
                    "noRuntimeJourneyMutationConfirmed": True,
                    "noCampaignActivationConfirmed": True,
                    "noProviderDispatchConfirmed": True,
                    "noAuthBillingOrMoneyActionConfirmed": True,
                }
            )
        if path.endswith("/journey-drafts/draft-394/publish"):
            return _ok(
                {
                    "status": "ok",
                    "version": {
                        "customerJourneyVersionId": "version-394",
                        "versionStatus": "PUBLISHED",
                    },
                    "noRuntimeJourneyMutationConfirmed": True,
                    "noCampaignActivationConfirmed": True,
                    "noProviderDispatchConfirmed": True,
                    "noAuthBillingOrMoneyActionConfirmed": True,
                }
            )
        if path == "/v1/referral-saas/accounts/acct-394/campaigns":
            assert kwargs["payload"]["accountScope"]["externalRef"] == "task-394-customer"
            return _ok(
                {
                    "status": "created",
                    "campaignSetup": {"campaign": {"campaignCode": "TASK394"}},
                    "no_campaign_activation_confirmed": True,
                    "no_webhook_delivery_confirmed": True,
                    "no_billing_or_money_movement_confirmed": True,
                }
            )
        if path.endswith("/activation-requests"):
            return _ok(
                {
                    "status": "ok",
                    "noCampaignActivationConfirmed": True,
                    "noProviderDispatchConfirmed": True,
                    "noAuthBillingOrMoneyActionConfirmed": True,
                    "no_campaign_activation_confirmed": True,
                    "no_webhook_delivery_confirmed": True,
                    "no_billing_or_money_movement_confirmed": True,
                }
            )
        if path.endswith("/referral-codes"):
            return _ok(
                {
                    "status": "ok",
                    "linkCode": {"referralCode": "REF394"},
                    "no_campaign_activation_confirmed": True,
                    "no_webhook_delivery_confirmed": True,
                    "no_billing_or_money_movement_confirmed": True,
                },
                status_code=201,
            )
        if path.endswith("/referrals/validate"):
            return _ok(
                {
                    "status": "ok",
                    "validation": {
                        "referralTrackId": "11111111-1111-4111-8111-111111111111",
                    },
                    "no_campaign_activation_confirmed": True,
                    "no_webhook_delivery_confirmed": True,
                    "no_billing_or_money_movement_confirmed": True,
                },
                status_code=201,
            )
        if path == "/v1/progress":
            progress_seen += 1
            return _ok(
                {
                    "status": "ok",
                    "referralTrackId": kwargs["payload"]["referralTrackId"],
                    "eventType": kwargs["payload"]["eventType"],
                    "deduped": progress_seen > 1,
                },
                status_code=200 if progress_seen > 1 else 201,
            )
        if path.endswith("/journey-versions/version-394/archive"):
            return _ok(
                {
                    "detail": {
                        "code": "CUSTOMER_JOURNEY_VERSION_ARCHIVE_BLOCKED",
                        "noCampaignBindingMutationConfirmed": True,
                    }
                },
                status_code=409,
            )
        raise AssertionError(f"unexpected POST {path}")

    def fake_request_json(**kwargs):
        calls.append((kwargs["method"], kwargs["path"], kwargs["payload"]))
        if kwargs["method"] == "PUT" and kwargs["path"].endswith("/journey-drafts"):
            assert kwargs["payload"]["templateCode"] == "REFERRAL_STANDARD"
            assert kwargs["payload"]["configurationPayload"] == {}
            return _ok(
                {
                    "status": "ok",
                    "draft": {"customerJourneyDraftId": "draft-394"},
                    "noRuntimeJourneyMutationConfirmed": True,
                    "noCampaignActivationConfirmed": True,
                    "noProviderDispatchConfirmed": True,
                    "noAuthBillingOrMoneyActionConfirmed": True,
                }
            )
        if kwargs["method"] == "PUT" and kwargs["path"].endswith("/journey-binding"):
            assert kwargs["payload"]["customerJourneyVersionId"] == "version-394"
            return _ok(
                {
                    "status": "ok",
                    "binding": {
                        "bindingStatus": "ACTIVE",
                        "activationGateSatisfied": True,
                    },
                    "noRuntimeJourneyMutationConfirmed": True,
                    "noCampaignActivationConfirmed": True,
                    "noProviderDispatchConfirmed": True,
                    "noAuthBillingOrMoneyActionConfirmed": True,
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
                "--progress-key",
                "test-partner-key",
                "--tenant-code",
                "FNB",
                "--external-tenant-ref",
                "task-394-customer",
                "--suffix",
                "394001",
            ]
        )
    )

    assert result["status"] == "passed"
    assert result["task"] == "TASK-394"
    assert result["approved_template"] == {
        "templateCode": "REFERRAL_STANDARD",
        "templateVersion": "1.0.0",
    }
    assert result["customer_journey"]["draftId"] == "draft-394"
    assert result["customer_journey"]["versionId"] == "version-394"
    assert result["customer_journey"]["archivePosture"] == (
        "ARCHIVE_BLOCKED_BY_ACTIVE_BINDING"
    )
    assert result["campaign"]["campaignCode"] == "TASK394"
    assert result["referral"]["referralCode"] == "REF394"
    assert result["progress_tracking_attribution_and_reporting_readback_confirmed"] is True
    assert [call[0] for call in calls].count("PUT") == 2


def test_run_rejects_blocked_journey_validation(monkeypatch):
    def fake_get_json(**kwargs):
        if kwargs["path"] == "/v1/referral-saas/accounts":
            return _ok(_registry_payload())
        return _ok(_catalogue_payload())

    def fake_request_json(**kwargs):
        return _ok(
            {
                "draft": {"customerJourneyDraftId": "draft-394"},
                "noRuntimeJourneyMutationConfirmed": True,
                "noCampaignActivationConfirmed": True,
                "noProviderDispatchConfirmed": True,
                "noAuthBillingOrMoneyActionConfirmed": True,
            }
        )

    def fake_post_json(**kwargs):
        return _ok({"validation": {"validationStatus": "BLOCKED"}})

    monkeypatch.setattr(script.setup_check, "get_json", fake_get_json)
    monkeypatch.setattr(script.setup_check, "request_json", fake_request_json)
    monkeypatch.setattr(script.setup_check, "post_json", fake_post_json)

    with pytest.raises(RuntimeError, match="validation is blocked"):
        script.run(script.parse_args(["--external-tenant-ref", "task-394-customer"]))


def test_run_rejects_internal_scope_leak_from_catalogue(monkeypatch):
    def fake_get_json(**kwargs):
        if kwargs["path"] == "/v1/referral-saas/accounts":
            return _ok(_registry_payload())
        return _ok({"templates": [{"templateCode": "BAD", "tenantCode": "FNB"}]})

    monkeypatch.setattr(script.setup_check, "get_json", fake_get_json)

    with pytest.raises(RuntimeError, match="tenantCode"):
        script.run(script.parse_args(["--external-tenant-ref", "task-394-customer"]))
