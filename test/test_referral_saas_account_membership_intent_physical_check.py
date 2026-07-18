from __future__ import annotations

import argparse

import pytest

from scripts import referral_saas_account_membership_intent_physical_check as script


def test_build_membership_invitation_payload_is_bounded_to_step_2_intent():
    payload = script.build_membership_invitation_payload(
        external_tenant_ref="task-213-fnb",
        actor_subject="setup-owner-subject",
        display_name="Setup Owner",
        email_hash="hash-only",
        role_family="DISTRIBUTION_ADMIN",
        permission_set="REFERRAL_SAAS_ACCOUNT_ADMIN",
        correlation_id="task-213-proof",
        idempotency_key="task-213-membership-intent",
    )

    assert payload == {
        "accountScope": {
            "refType": "external_tenant_ref",
            "externalRef": "task-213-fnb",
            "context": "setup",
        },
        "actor": {
            "actorType": "USER",
            "subject": "setup-owner-subject",
            "emailHash": "hash-only",
            "displayName": "Setup Owner",
        },
        "membership": {
            "roleFamily": "DISTRIBUTION_ADMIN",
            "permissionSet": "REFERRAL_SAAS_ACCOUNT_ADMIN",
            "tenantScope": "PRIMARY_ACCOUNT_TENANT",
        },
        "reasonCode": "ACCOUNT_SETUP_USER_ROLE",
        "correlationId": "task-213-proof",
        "idempotencyKey": "task-213-membership-intent",
    }
    script.assert_safe_membership_intent_payload(payload)


def test_membership_intent_payload_rejects_unsafe_adjacent_actions():
    with pytest.raises(RuntimeError, match="delivery"):
        script.assert_safe_membership_intent_payload(
            {
                "actor": {"subject": "setup-owner"},
                "delivery": {"send": True},
            }
        )

    with pytest.raises(RuntimeError, match="tenant_code"):
        script.assert_safe_membership_intent_payload(
            {
                "accountScope": {"tenant_code": "FNB"},
                "actor": {"subject": "setup-owner"},
            }
        )

    with pytest.raises(RuntimeError, match="campaign_activation"):
        script.assert_safe_membership_intent_payload(
            {
                "actor": {"subject": "setup-owner"},
                "campaign_activation": True,
            }
        )


def test_membership_intent_response_requires_no_adjacent_live_action_guards():
    script.assert_membership_intent_response(
        {
            "invitation": {
                "commandStatus": "INVITATION_INTENT_RECORDED",
                "membership": {
                    "status": "INVITED",
                    "roleFamily": "DISTRIBUTION_ADMIN",
                    "permissionSet": "REFERRAL_SAAS_ACCOUNT_ADMIN",
                },
                "delivery": {
                    "status": "DELIVERY_NOT_CONFIGURED",
                    "nextAction": "Configure approved invitation delivery provider",
                },
                "noInviteDeliveryConfirmed": True,
                "noAuthClaimChangeConfirmed": True,
                "noSeatAssignmentConfirmed": True,
                "noMoneyMovementConfirmed": True,
            }
        }
    )

    with pytest.raises(RuntimeError, match="no invite delivery"):
        script.assert_membership_intent_response(
            {
                "invitation": {
                    "commandStatus": "INVITATION_INTENT_RECORDED",
                    "membership": {"status": "INVITED"},
                    "delivery": {"status": "DELIVERY_NOT_CONFIGURED"},
                    "noInviteDeliveryConfirmed": False,
                    "noAuthClaimChangeConfirmed": True,
                    "noSeatAssignmentConfirmed": True,
                    "noMoneyMovementConfirmed": True,
                }
            }
        )


def test_membership_posture_response_requires_invited_evidence():
    script.assert_membership_posture_response(
        {
            "membershipPosture": {
                "invitedCount": 1,
                "noInviteDeliveryConfirmed": True,
            }
        }
    )

    with pytest.raises(RuntimeError, match="invited membership evidence"):
        script.assert_membership_posture_response(
            {
                "membershipPosture": {
                    "invitedCount": 0,
                    "noInviteDeliveryConfirmed": True,
                }
            }
        )


def test_run_chains_account_setup_then_invitation_and_posture(monkeypatch):
    calls: list[tuple[str, str]] = []

    def fake_setup_run(args: argparse.Namespace):
        assert args.external_tenant_ref == "task-213-proof"
        assert args.organisation_ref == "org-task-213-proof"
        return {
            "status": "passed",
            "resolved_account": {"accountId": "acc_task_213"},
        }

    def fake_post_json(*, base_url: str, path: str, admin_key: str, payload: dict):
        calls.append(("POST", path))
        assert base_url == "http://127.0.0.1:8000"
        assert admin_key == "test-admin-key"
        script.assert_safe_membership_intent_payload(payload)
        return script.setup_check.ApiResult(
            status_code=200,
            payload={
                "invitation": {
                    "commandStatus": "INVITATION_INTENT_RECORDED",
                    "membership": {
                        "status": "INVITED",
                        "roleFamily": "DISTRIBUTION_ADMIN",
                        "permissionSet": "REFERRAL_SAAS_ACCOUNT_ADMIN",
                    },
                    "delivery": {
                        "status": "DELIVERY_NOT_CONFIGURED",
                        "nextAction": "Configure approved invitation delivery provider",
                    },
                    "noInviteDeliveryConfirmed": True,
                    "noAuthClaimChangeConfirmed": True,
                    "noSeatAssignmentConfirmed": True,
                    "noMoneyMovementConfirmed": True,
                },
                "no_invite_delivery_confirmed": True,
                "no_auth_claim_change_confirmed": True,
                "no_seat_assignment_confirmed": True,
                "no_money_movement_confirmed": True,
            },
        )

    def fake_get_json(*, base_url: str, path: str, admin_key: str, query: dict):
        calls.append(("GET", path))
        assert query == {
            "ref_type": "external_tenant_ref",
            "external_ref": "task-213-proof",
            "context": "setup",
        }
        return script.setup_check.ApiResult(
            status_code=200,
            payload={
                "membershipPosture": {
                    "invitedCount": 1,
                    "noInviteDeliveryConfirmed": True,
                }
            },
        )

    monkeypatch.setattr(script.setup_check, "run", fake_setup_run)
    monkeypatch.setattr(script.setup_check, "post_json", fake_post_json)
    monkeypatch.setattr(script.setup_check, "get_json", fake_get_json)

    result = script.run(
        script.parse_args(
            [
                "--external-tenant-ref",
                "task-213-proof",
                "--organisation-ref",
                "org-task-213-proof",
                "--suffix",
                "proof",
            ]
        )
    )

    assert result["status"] == "passed"
    assert result["task"] == "TASK-213"
    assert result["account_ref"] == "acc_task_213"
    assert result["membership_status"] == "INVITED"
    assert result["delivery_status"] == "DELIVERY_NOT_CONFIGURED"
    assert calls == [
        ("POST", "/v1/referral-saas/accounts/acc_task_213/membership-invitations"),
        ("GET", "/v1/referral-saas/accounts/membership-posture"),
    ]
