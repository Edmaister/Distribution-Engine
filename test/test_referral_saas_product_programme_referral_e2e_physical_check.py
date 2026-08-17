from __future__ import annotations

import pytest

from scripts import referral_saas_account_setup_ui_physical_check as setup_check
from scripts import referral_saas_product_programme_referral_e2e_physical_check as script


def _ok(payload: dict | None = None, *, status_code: int = 200) -> setup_check.ApiResult:
    return setup_check.ApiResult(status_code=status_code, payload=payload or {"status": "ok"})


def _registry_payload() -> dict:
    return {
        "status": "ok",
        "accounts": [
            {
                "accountId": "acct-418",
                "accountCode": "ACCT-418",
                "accountName": "Task 418 Customer",
                "primaryExternalTenantRef": "task-418-customer",
                "externalReferences": [
                    {
                        "refType": "external_tenant_ref",
                        "externalRef": "task-418-customer",
                        "referenceStatus": "ACTIVE",
                    },
                    {
                        "refType": "organisation_ref",
                        "externalRef": "org-task-418",
                        "referenceStatus": "ACTIVE",
                    },
                ],
            }
        ],
    }


def _runtime_context_payload() -> dict:
    return {
        "status": "ok",
        "reportingDimensions": {
            "customerProductBinding": {
                "customerProductLineId": "line-418",
                "customerProductOfferingId": "offering-418",
                "externalProductLineRef": "TRANSACTIONAL_BANKING",
                "externalOfferingRef": "EASY_ACCOUNT",
            },
            "programmeVersionId": "programme-version-418",
            "programmeCode": "TASK418",
            "campaignCode": "TASK418-CAMPAIGN",
            "effectiveRuleSnapshot": {
                "programme": {"programmeVersionId": "programme-version-418"},
                "campaign": {"campaignCode": "TASK418-CAMPAIGN"},
            },
        },
    }


def test_run_proves_product_programme_campaign_referral_reporting_path(monkeypatch):
    calls: list[tuple[str, str, dict | None]] = []

    def fake_get_json(**kwargs):
        calls.append(("GET", kwargs["path"], kwargs.get("query")))
        path = kwargs["path"]
        if path == "/v1/referral-saas/accounts":
            return _ok(_registry_payload())
        if path.endswith("/product-catalogue"):
            return _ok(
                {
                    "status": "ok",
                    "productLines": [
                        {
                            "customerProductLineId": "line-418",
                            "externalProductLineRef": "TASK418-0001-LINE",
                            "offerings": [
                                {
                                    "customerProductOfferingId": "offering-418",
                                    "externalOfferingRef": "TASK418-0001-OFFERING",
                                }
                            ],
                        }
                    ],
                    "noProgrammeBindingConfirmed": True,
                    "noCampaignCreationConfirmed": True,
                    "noReferralCreationConfirmed": True,
                    "noIncentiveApplicationConfirmed": True,
                    "noProviderDispatchConfirmed": True,
                    "noCredentialOrAuthMutationConfirmed": True,
                    "noBillingPayoutSettlementOrMoneyMovementConfirmed": True,
                }
            )
        if path.endswith("/progress-status"):
            return _ok({"status": "ok", "progressStatus": {"safeStatus": {}}})
        if path.endswith("/trace"):
            return _ok({"status": "ok", "attributionTrace": {"traceStatus": "PARTIAL"}})
        if path.endswith("/reports/campaign_performance"):
            assert kwargs["query"]["campaign_code"] == "TASK418-CAMPAIGN"
            return _ok(_runtime_context_payload())
        if path.endswith("/programmes/analytics"):
            return _ok(_runtime_context_payload())
        raise AssertionError(f"unexpected GET {path}")

    def fake_post_json(**kwargs):
        calls.append(("POST", kwargs["path"], kwargs["payload"]))
        path = kwargs["path"]
        if path.endswith("/programmes/drafts"):
            assert kwargs["payload"]["customerProductLineId"] == "line-418"
            assert kwargs["payload"]["customerProductOfferingId"] == "offering-418"
            return _ok(
                {
                    "status": "ok",
                    "resource": {"programmeDraftId": "draft-418"},
                    "noCampaignActivationConfirmed": True,
                    "noProviderDispatchConfirmed": True,
                    "noCredentialOrAuthMutationConfirmed": True,
                    "noBillingPayoutSettlementOrMoneyMovementConfirmed": True,
                }
            )
        if path.endswith("/programmes/drafts/draft-418/validate"):
            return _ok(
                {
                    "status": "ok",
                    "validation": {
                        "validationStatus": "READY",
                        "blockers": [],
                        "customerProductBinding": {
                            "customerProductLineId": "line-418",
                            "customerProductOfferingId": "offering-418",
                        },
                    },
                    "noProgrammePublishConfirmed": True,
                    "noCampaignActivationConfirmed": True,
                    "noReferralRuntimeSwitchConfirmed": True,
                    "noProviderDispatchConfirmed": True,
                    "noCredentialOrAuthMutationConfirmed": True,
                    "noBillingPayoutSettlementOrMoneyMovementConfirmed": True,
                }
            )
        if path.endswith("/submit-review"):
            return _ok(
                {
                    "resource": {"programmeDraftId": "draft-418"},
                    "noCampaignActivationConfirmed": True,
                    "noProviderDispatchConfirmed": True,
                    "noCredentialOrAuthMutationConfirmed": True,
                    "noBillingPayoutSettlementOrMoneyMovementConfirmed": True,
                }
            )
        if path.endswith("/review-decision"):
            return _ok(
                {
                    "resource": {"programmeDraftId": "draft-418"},
                    "noCampaignActivationConfirmed": True,
                    "noProviderDispatchConfirmed": True,
                    "noCredentialOrAuthMutationConfirmed": True,
                    "noBillingPayoutSettlementOrMoneyMovementConfirmed": True,
                }
            )
        if path.endswith("/publish"):
            return _ok(
                {
                    "programmeVersion": {
                        "programmeVersionId": "programme-version-418",
                        "customerProductBinding": {
                            "customerProductLineId": "line-418",
                            "customerProductOfferingId": "offering-418",
                        },
                    },
                    "noCampaignActivationConfirmed": True,
                    "noProviderDispatchConfirmed": True,
                    "noCredentialOrAuthMutationConfirmed": True,
                    "noBillingPayoutSettlementOrMoneyMovementConfirmed": True,
                }
            )
        if path.endswith("/incentive-bindings"):
            return _ok(
                {
                    "binding": {
                        "programmeIncentiveBindingId": "binding-418",
                        "bindingType": "INCENTIVE",
                    },
                    "noRewardApplicationConfirmed": True,
                    "noBadgeAwardConfirmed": True,
                    "noMissionProgressMutationConfirmed": True,
                    "noLeaderboardScoringConfirmed": True,
                    "noCampaignActivationConfirmed": True,
                    "noProviderDispatchConfirmed": True,
                    "noCredentialOrAuthMutationConfirmed": True,
                    "noBillingPayoutSettlementOrMoneyMovementConfirmed": True,
                }
            )
        if path == "/v1/referral-saas/accounts/acct-418/campaigns":
            return _ok(
                {
                    "campaignSetup": {
                        "campaign": {"campaignCode": "TASK418-CAMPAIGN"},
                    },
                    "no_campaign_activation_confirmed": True,
                    "no_webhook_delivery_confirmed": True,
                    "no_billing_or_money_movement_confirmed": True,
                }
            )
        if path.endswith("/referral-codes"):
            return _ok(
                {
                    "linkCode": {"referralCode": "REF418"},
                    "no_campaign_activation_confirmed": True,
                    "no_webhook_delivery_confirmed": True,
                    "no_billing_or_money_movement_confirmed": True,
                },
                status_code=201,
            )
        if path.endswith("/referrals/validate"):
            return _ok(
                {
                    "validation": {
                        "referralTrackId": "11111111-1111-4111-8111-000000000418"
                    },
                    "no_campaign_activation_confirmed": True,
                    "no_webhook_delivery_confirmed": True,
                    "no_billing_or_money_movement_confirmed": True,
                },
                status_code=201,
            )
        if path == "/v1/progress":
            assert kwargs["payload"]["metadata"] == {
                "campaignCode": "TASK418-CAMPAIGN",
                "programmeVersionId": "programme-version-418",
                "customerProductLineId": "line-418",
                "customerProductOfferingId": "offering-418",
            }
            return _ok({"status": "ok"}, status_code=201)
        raise AssertionError(f"unexpected POST {path}")

    def fake_request_json(**kwargs):
        calls.append((kwargs["method"], kwargs["path"], kwargs["payload"]))
        if kwargs["method"] == "PUT" and kwargs["path"].endswith("/product-lines/TASK418-0001-LINE"):
            return _ok(
                {
                    "resource": {
                        "customerProductLineId": "line-418",
                        "externalProductLineRef": "TASK418-0001-LINE",
                    },
                    "noProgrammeBindingConfirmed": True,
                    "noCampaignCreationConfirmed": True,
                    "noReferralCreationConfirmed": True,
                    "noIncentiveApplicationConfirmed": True,
                    "noProviderDispatchConfirmed": True,
                    "noCredentialOrAuthMutationConfirmed": True,
                    "noBillingPayoutSettlementOrMoneyMovementConfirmed": True,
                }
            )
        if "/offerings/" in kwargs["path"]:
            return _ok(
                {
                    "resource": {
                        "customerProductOfferingId": "offering-418",
                        "externalOfferingRef": "TASK418-0001-OFFERING",
                    },
                    "noProgrammeBindingConfirmed": True,
                    "noCampaignCreationConfirmed": True,
                    "noReferralCreationConfirmed": True,
                    "noIncentiveApplicationConfirmed": True,
                    "noProviderDispatchConfirmed": True,
                    "noCredentialOrAuthMutationConfirmed": True,
                    "noBillingPayoutSettlementOrMoneyMovementConfirmed": True,
                }
            )
        if kwargs["method"] == "PUT" and kwargs["path"].endswith("/programme-binding"):
            assert kwargs["payload"]["programmeVersionId"] == "programme-version-418"
            return _ok(
                {
                    "binding": {"programmeVersionId": "programme-version-418"},
                    "noCampaignActivationConfirmed": True,
                    "noProviderDispatchConfirmed": True,
                    "noMoneyMovementConfirmed": True,
                }
            )
        raise AssertionError(f"unexpected request {kwargs['method']} {kwargs['path']}")

    monkeypatch.setattr(script.setup_check, "get_json", fake_get_json)
    monkeypatch.setattr(script.setup_check, "post_json", fake_post_json)
    monkeypatch.setattr(script.setup_check, "request_json", fake_request_json)

    result = script.run(
        script.parse_args(
            [
                "--external-tenant-ref",
                "task-418-customer",
                "--suffix",
                "0001",
            ]
        )
    )

    assert result["status"] == "passed"
    assert result["task"] == "TASK-418"
    assert result["product"] == {
        "productLineRef": "TASK418-0001-LINE",
        "productLineId": "line-418",
        "offeringRef": "TASK418-0001-OFFERING",
        "offeringId": "offering-418",
    }
    assert result["programme"]["versionId"] == "programme-version-418"
    assert result["programme"]["incentiveBindingRef"] == "binding-418"
    assert result["campaign"]["campaignCode"] == "TASK418-CAMPAIGN"
    assert result["referral"]["referralCode"] == "REF418"
    assert result["product_programme_campaign_referral_runtime_readback_confirmed"] is True
    assert result["no_source_journey_deployment_required"] is True
    assert ("PUT", "/v1/referral-saas/accounts/acct-418/campaigns/TASK418-CAMPAIGN/programme-binding", {
        "accountScope": {
            "refType": "external_tenant_ref",
            "externalRef": "task-418-customer",
            "context": "setup",
        },
        "programmeVersionId": "programme-version-418",
        "correlationId": "task-418-campaign-programme-bind-0001",
        "idempotencyKey": "task-418-campaign-programme-bind-0001",
    }) in calls


def test_run_rejects_missing_product_offering_validation(monkeypatch):
    def fake_get_json(**kwargs):
        if kwargs["path"] == "/v1/referral-saas/accounts":
            return _ok(_registry_payload())
        return _ok({"status": "ok"})

    def fake_request_json(**kwargs):
        if kwargs["path"].endswith("/product-lines/TASK418-0002-LINE"):
            return _ok({"resource": {"customerProductLineId": "line-418"}})
        return _ok({"resource": {"customerProductOfferingId": "offering-418"}})

    def fake_post_json(**kwargs):
        if kwargs["path"].endswith("/programmes/drafts"):
            return _ok({"resource": {"programmeDraftId": "draft-418"}})
        return _ok(
            {
                "validation": {
                    "validationStatus": "BLOCKED",
                    "blockers": [
                        {
                            "code": "ACTIVE_CUSTOMER_PRODUCT_OFFERING_REQUIRED",
                            "area": "customer_product_offering",
                        }
                    ],
                },
                "noProgrammePublishConfirmed": True,
                "noCampaignActivationConfirmed": True,
                "noReferralRuntimeSwitchConfirmed": True,
                "noProviderDispatchConfirmed": True,
                "noCredentialOrAuthMutationConfirmed": True,
                "noBillingPayoutSettlementOrMoneyMovementConfirmed": True,
            }
        )

    monkeypatch.setattr(script.setup_check, "get_json", fake_get_json)
    monkeypatch.setattr(script.setup_check, "request_json", fake_request_json)
    monkeypatch.setattr(script.setup_check, "post_json", fake_post_json)

    with pytest.raises(RuntimeError, match="Programme validation is blocked"):
        script.run(
            script.parse_args(
                [
                    "--external-tenant-ref",
                    "task-418-customer",
                    "--suffix",
                    "0002",
                ]
            )
        )


def test_run_rejects_report_without_programme_product_runtime_context() -> None:
    with pytest.raises(RuntimeError, match="programme/product context"):
        script._require_product_runtime_context(
            {
                "status": "ok",
                "reportingDimensions": {
                    "campaignCode": "TASK418-CAMPAIGN",
                },
            }
        )


def test_run_rejects_runtime_reporting_leakage() -> None:
    with pytest.raises(RuntimeError, match="Unsafe runtime/reporting leakage"):
        script._require_product_runtime_context(
            {
                "status": "ok",
                "reportingDimensions": {
                    "customerProductBinding": {},
                    "programmeVersionId": "programme-version-418",
                    "programmeCode": "TASK418",
                    "campaignCode": "TASK418-CAMPAIGN",
                    "effectiveRuleSnapshot": {},
                    "raw_event_payload": {"secret": "unsafe"},
                },
            }
        )
