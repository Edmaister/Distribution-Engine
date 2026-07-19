from __future__ import annotations

import argparse

import pytest

from scripts import referral_saas_client_workspace_physical_check as script


def test_registry_assertion_finds_created_client_without_internal_leakage():
    account = script.assert_registry_contains_client(
        {
            "accounts": [
                {
                    "accountId": "acct-task-229",
                    "accountCode": "ACCT_TASK_229",
                    "accountName": "Task 229 Client",
                    "primaryExternalTenantRef": "task-229-client",
                    "externalReferences": [
                        {
                            "refType": "external_tenant_ref",
                            "externalRef": "task-229-client",
                        },
                        {
                            "refType": "organisation_ref",
                            "externalRef": "org-task-229-client",
                        },
                    ],
                }
            ]
        },
        external_tenant_ref="task-229-client",
        organisation_ref="org-task-229-client",
    )

    assert account["accountId"] == "acct-task-229"


def test_registry_assertion_rejects_missing_client_and_internal_fields():
    with pytest.raises(RuntimeError, match="not returned"):
        script.assert_registry_contains_client(
            {"accounts": []},
            external_tenant_ref="task-229-client",
            organisation_ref="org-task-229-client",
        )

    with pytest.raises(RuntimeError, match="tenant_code"):
        script.assert_registry_contains_client(
            {"accounts": [{"tenant_code": "FNB"}]},
            external_tenant_ref="task-229-client",
            organisation_ref="org-task-229-client",
        )


def test_existing_client_selector_requires_complete_external_refs():
    selected = script.select_existing_registry_client(
        {
            "accounts": [
                {
                    "accountId": "incomplete",
                    "externalReferences": [
                        {"refType": "external_tenant_ref", "externalRef": "task-229"}
                    ],
                },
                {
                    "accountId": "complete",
                    "primaryExternalTenantRef": "task-229",
                    "externalReferences": [
                        {"refType": "organisation_ref", "externalRef": "org-task-229"}
                    ],
                },
            ]
        }
    )

    assert selected["accountId"] == "complete"

    with pytest.raises(RuntimeError, match="No existing clients"):
        script.select_existing_registry_client({"accounts": []})


def test_maintenance_state_assertion_requires_selected_client_scope():
    scope = script.assert_maintenance_state_is_client_scoped(
        {
            "onboarding_state": {
                "scope": {
                    "external_tenant_ref": "task-229-client",
                    "organisation_ref": "org-task-229-client",
                }
            },
            "readiness": {"overall_status": "GO_LIVE_DISABLED"},
        },
        external_tenant_ref="task-229-client",
        organisation_ref="org-task-229-client",
    )

    assert scope["external_tenant_ref"] == "task-229-client"

    with pytest.raises(RuntimeError, match="selected client reference"):
        script.assert_maintenance_state_is_client_scoped(
            {
                "onboarding_state": {
                    "scope": {
                        "external_tenant_ref": "other-client",
                        "organisation_ref": "org-task-229-client",
                    }
                },
                "readiness": {},
            },
            external_tenant_ref="task-229-client",
            organisation_ref="org-task-229-client",
        )


def test_client_workspace_routes_stay_inside_referral_saas_boundary():
    script.assert_client_workspace_routes_are_bounded(script.CLIENT_WORKSPACE_ROUTES)

    with pytest.raises(RuntimeError, match="escapes Referral SaaS boundary"):
        script.assert_client_workspace_routes_are_bounded(
            (
                "/admin/referral-saas/account-setup",
                "/admin/funding",
            )
        )


def test_run_chains_setup_registry_and_maintenance_state(monkeypatch):
    calls: list[tuple[str, str]] = []

    def fake_setup_run(args: argparse.Namespace):
        assert args.external_tenant_ref == "task-229-proof"
        assert args.organisation_ref == "org-task-229-proof"
        return {
            "status": "passed",
            "draft_ref": "draft_task_229",
            "created_account": {"accountId": "acct-task-229"},
            "validation_status": "ok",
            "no_adjacent_live_action_confirmed": True,
        }

    def fake_get_json(*, base_url: str, path: str, admin_key: str, query: dict):
        calls.append(("GET", path))
        assert base_url == "http://127.0.0.1:8000"
        assert admin_key == "test-admin-key"
        if path == "/v1/referral-saas/accounts":
            assert query == {"limit": "50"}
            return script.setup_check.ApiResult(
                status_code=200,
                payload={
                    "accounts": [
                        {
                            "accountId": "acct-task-229",
                            "accountCode": "ACCT_TASK_229",
                            "accountName": "Task 229 Client",
                            "accountStatus": "PENDING_ONBOARDING",
                            "onboardingStatus": "APPROVED_FOR_INTERNAL_REVIEW",
                            "primaryExternalTenantRef": "task-229-proof",
                            "externalReferences": [
                                {
                                    "refType": "external_tenant_ref",
                                    "externalRef": "task-229-proof",
                                },
                                {
                                    "refType": "organisation_ref",
                                    "externalRef": "org-task-229-proof",
                                },
                            ],
                        }
                    ]
                },
            )
        if path == "/admin/onboarding/state":
            assert query == {
                "external_tenant_ref": "task-229-proof",
                "organisation_ref": "org-task-229-proof",
            }
            return script.setup_check.ApiResult(
                status_code=200,
                payload={
                    "onboarding_state": {
                        "scope": {
                            "external_tenant_ref": "task-229-proof",
                            "organisation_ref": "org-task-229-proof",
                        }
                    },
                    "readiness": {
                        "overall_status": "GO_LIVE_DISABLED",
                        "summary": {"ready_count": 1},
                    },
                },
            )
        raise AssertionError(path)

    monkeypatch.setattr(script.setup_check, "run", fake_setup_run)
    monkeypatch.setattr(script.setup_check, "get_json", fake_get_json)

    result = script.run(
        script.parse_args(
            [
                "--external-tenant-ref",
                "task-229-proof",
                "--organisation-ref",
                "org-task-229-proof",
                "--suffix",
                "proof",
            ]
        )
    )

    assert result["status"] == "passed"
    assert result["task"] == "TASK-229"
    assert result["selected_client"]["accountId"] == "acct-task-229"
    assert result["readiness_status"] == "GO_LIVE_DISABLED"
    assert result["account_setup_creation_mode"] == "created_client"
    assert result["no_money_movement"] is True
    assert calls == [
        ("GET", "/v1/referral-saas/accounts"),
        ("GET", "/v1/referral-saas/accounts"),
        ("GET", "/admin/onboarding/state"),
    ]


def test_run_can_reuse_existing_client_when_local_tenant_pool_is_exhausted(monkeypatch):
    calls: list[tuple[str, str]] = []

    def fail_setup_run(args: argparse.Namespace):
        raise AssertionError("setup creation should be skipped")

    def fake_get_json(*, base_url: str, path: str, admin_key: str, query: dict):
        calls.append(("GET", path))
        if path == "/v1/referral-saas/accounts":
            return script.setup_check.ApiResult(
                status_code=200,
                payload={
                    "accounts": [
                        {
                            "accountId": "acct-existing",
                            "accountCode": "ACCT_EXISTING",
                            "accountName": "Existing Client",
                            "accountStatus": "PENDING_ONBOARDING",
                            "onboardingStatus": "READY_FOR_REVIEW",
                            "primaryExternalTenantRef": "existing-client",
                            "externalReferences": [
                                {
                                    "refType": "organisation_ref",
                                    "externalRef": "existing-org",
                                },
                            ],
                        }
                    ]
                },
            )
        if path == "/admin/onboarding/state":
            assert query == {
                "external_tenant_ref": "existing-client",
                "organisation_ref": "existing-org",
            }
            return script.setup_check.ApiResult(
                status_code=200,
                payload={
                    "onboarding_state": {
                        "scope": {
                            "external_tenant_ref": "existing-client",
                            "organisation_ref": "existing-org",
                        }
                    },
                    "readiness": {"overall_status": "GO_LIVE_DISABLED", "summary": {}},
                },
            )
        raise AssertionError(path)

    monkeypatch.setattr(script.setup_check, "run", fail_setup_run)
    monkeypatch.setattr(script.setup_check, "get_json", fake_get_json)

    result = script.run(script.parse_args(["--reuse-existing-client"]))

    assert result["status"] == "passed"
    assert result["account_setup_creation_mode"] == "reused_existing_client"
    assert result["selected_client"]["accountId"] == "acct-existing"
    assert result["setup_result"]["reason"] == "reused_existing_client"
    assert calls == [
        ("GET", "/v1/referral-saas/accounts"),
        ("GET", "/admin/onboarding/state"),
    ]
