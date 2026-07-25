from __future__ import annotations

import pytest

from scripts import referral_saas_account_setup_ui_physical_check as setup_check
from scripts import referral_saas_people_access_provisioning_physical_check as script


def _registry_payload() -> dict:
    return {
        "status": "ok",
        "accounts": [
            {
                "accountId": "acct-287",
                "accountCode": "ACC-287",
                "accountName": "Task 287 Customer",
                "primaryExternalTenantRef": "task-287-customer",
                "externalReferences": [
                    {
                        "refType": "external_tenant_ref",
                        "externalRef": "task-287-customer",
                        "referenceStatus": "ACTIVE",
                    },
                    {
                        "refType": "organisation_ref",
                        "externalRef": "org-task-287",
                        "referenceStatus": "ACTIVE",
                    },
                ],
            }
        ],
    }


def _posture_payload(*, total: int = 0, active: int = 0) -> dict:
    return {
        "status": "ok",
        "membershipPosture": {
            "totalMemberships": total,
            "activeCount": active,
            "invitedCount": max(total - active, 0),
            "memberships": [],
            "roleFamilies": [],
            "noMembershipWriteConfirmed": True,
            "noInviteDeliveryConfirmed": True,
        },
    }


def _readiness_payload(
    *,
    membership_ref: str | None = None,
    membership_status: str = "ACTIVE",
    provisioning_readiness: str = "READY_TO_PROVISION_SEAT",
    seat_assignment_status: str = "SEAT_NOT_ASSIGNED",
    auth_claim_status: str = "AUTH_CLAIMS_NOT_PROPAGATED",
) -> dict:
    items = []
    if membership_ref:
        items.append(
            {
                "membershipRef": membership_ref,
                "subject": "task-287-subject",
                "displayName": "Task 287 Person",
                "roleFamily": "CAMPAIGN_MANAGER",
                "membershipStatus": membership_status,
                "activationReadiness": "ACTIVE",
                "provisioningReadiness": provisioning_readiness,
                "seatAssignmentStatus": seat_assignment_status,
                "authClaimStatus": auth_claim_status,
                "blockers": [],
                "nextAction": "Ready.",
            }
        )
    return {
        "status": "ok",
        "activationReadiness": {
            "activationReadyCount": 1 if items else 0,
            "items": items,
        },
        "no_membership_activation_confirmed": True,
        "no_invite_delivery_confirmed": True,
        "no_seat_assignment_confirmed": True,
        "no_auth_claim_change_confirmed": True,
        "no_money_movement_confirmed": True,
    }


def _ok(payload: dict | None = None, *, status_code: int = 200) -> setup_check.ApiResult:
    return setup_check.ApiResult(status_code=status_code, payload=payload or {"status": "ok"})


def _provisioning_payload(
    *,
    status: str = "PROVISIONING_REQUEST_RECORDED",
    idempotency_status: str = "RECORDED",
) -> dict:
    return {
        "status": "ok",
        "accessProvisioning": {
            "commandStatus": status,
            "membership": {
                "membershipRef": "membership-287",
                "roleFamily": "CAMPAIGN_MANAGER",
                "permissionSet": "REFERRAL_SAAS_CAMPAIGN_MANAGER",
            },
            "seat": {
                "seatType": "OPERATOR",
                "seatAssignmentStatus": (
                    "SEAT_ASSIGNED"
                    if status in {"PROVISIONING_REQUEST_RECORDED", "PROVISIONING_REPLAYED"}
                    else "SEAT_NOT_ASSIGNED"
                ),
                "seatRef": "seat-287",
            },
            "authClaims": {"authClaimStatus": "AUTH_CLAIMS_NOT_PROPAGATED"},
            "provisioning": {"status": status, "nextAction": "Auth claims stay separate."},
            "idempotency": {"status": idempotency_status},
            "auditEventId": "audit-287",
            "noInviteDeliveryConfirmed": True,
            "noAuthClaimChangeConfirmed": True,
            "noCredentialCreationConfirmed": True,
            "noCampaignActivationConfirmed": True,
            "noGoLiveChangeConfirmed": True,
            "noMoneyMovementConfirmed": True,
        },
        "no_invite_delivery_confirmed": True,
        "no_auth_claim_change_confirmed": True,
        "no_credential_creation_confirmed": True,
        "no_campaign_activation_confirmed": True,
        "no_go_live_change_confirmed": True,
        "no_money_movement_confirmed": True,
    }


def _account_foundation_activation_payload() -> dict:
    return {
        "status": "ok",
        "context": "setup",
        "account": {
            "accountId": "acct-287",
            "accountCode": "ACC-287",
            "accountName": "Task 287 Customer",
        },
        "activation": {
            "commandStatus": "ACCOUNT_FOUNDATION_ACTIVATED",
            "accountStatus": "ACTIVE",
            "tenantLinkStatus": "ACTIVE",
            "seatCapacity": {
                "seatTypes": ["ADMIN", "OPERATOR"],
                "createdSeatCount": 2,
            },
            "idempotency": {"status": "RECORDED"},
            "noMembershipWriteConfirmed": True,
            "noSeatAssignmentConfirmed": True,
            "noInviteDeliveryConfirmed": True,
            "noAuthClaimChangeConfirmed": True,
            "noCredentialCreationConfirmed": True,
            "noCampaignActivationConfirmed": True,
            "noGoLiveActionConfirmed": True,
            "noBillingOrMoneyMovementConfirmed": True,
        },
        "no_membership_write_confirmed": True,
        "no_seat_assignment_confirmed": True,
        "no_invite_delivery_confirmed": True,
        "no_auth_claim_change_confirmed": True,
        "no_credential_creation_confirmed": True,
        "no_campaign_activation_confirmed": True,
        "no_go_live_action_confirmed": True,
        "no_billing_or_money_movement_confirmed": True,
    }


def test_run_records_acceptance_provisions_seat_and_replays(monkeypatch):
    calls: list[tuple[str, str, dict | None]] = []
    readiness_calls = 0
    provisioning_calls = 0

    def fake_get_json(**kwargs):
        nonlocal readiness_calls
        calls.append(("GET", kwargs["path"], kwargs.get("query")))
        if kwargs["path"] == "/v1/referral-saas/accounts":
            return _ok(_registry_payload())
        if kwargs["path"] == "/v1/referral-saas/accounts/membership-posture":
            return _ok(_posture_payload(total=1, active=1))
        if kwargs["path"] == "/v1/referral-saas/accounts/acct-287/membership-activation-readiness":
            readiness_calls += 1
            if readiness_calls == 1:
                return _ok(_readiness_payload())
            return _ok(
                _readiness_payload(
                    membership_ref="membership-287",
                    provisioning_readiness=(
                        "SEAT_ASSIGNED" if readiness_calls >= 3 else "READY_TO_PROVISION_SEAT"
                    ),
                    seat_assignment_status=(
                        "SEAT_ASSIGNED" if readiness_calls >= 3 else "SEAT_NOT_ASSIGNED"
                    ),
                )
            )
        raise AssertionError(f"unexpected GET {kwargs['path']}")

    def fake_post_json(**kwargs):
        nonlocal provisioning_calls
        calls.append(("POST", kwargs["path"], kwargs["payload"]))
        path = kwargs["path"]
        if path == "/v1/referral-saas/accounts/acct-287/membership-invitations":
            assert "tenantCode" not in str(kwargs["payload"])
            return _ok(
                {
                    "status": "ok",
                    "invitation": {
                        "commandStatus": "INVITATION_INTENT_RECORDED",
                        "membership": {
                            "membershipRef": "membership-287",
                            "status": "INVITED",
                        },
                        "delivery": {"status": "DELIVERY_NOT_CONFIGURED"},
                        "noInviteDeliveryConfirmed": True,
                        "noAuthClaimChangeConfirmed": True,
                        "noSeatAssignmentConfirmed": True,
                        "noMoneyMovementConfirmed": True,
                    },
                    "no_invite_delivery_confirmed": True,
                    "no_auth_claim_change_confirmed": True,
                    "no_seat_assignment_confirmed": True,
                    "no_money_movement_confirmed": True,
                }
            )
        if path == "/v1/referral-saas/accounts/acct-287/memberships/membership-287/activation":
            return _ok(
                {
                    "status": "ok",
                    "activationRequest": {
                        "commandStatus": "MEMBERSHIP_ACTIVATED",
                        "membership": {
                            "membershipRef": "membership-287",
                            "status": "ACTIVE",
                        },
                    },
                    "no_invite_delivery_confirmed": True,
                    "no_auth_claim_change_confirmed": True,
                    "no_seat_assignment_confirmed": True,
                    "no_money_movement_confirmed": True,
                }
            )
        if path == "/v1/referral-saas/accounts/acct-287/memberships/membership-287/access-provisioning":
            provisioning_calls += 1
            return _ok(
                _provisioning_payload(
                    status=(
                        "PROVISIONING_REPLAYED"
                        if provisioning_calls == 2
                        else "PROVISIONING_REQUEST_RECORDED"
                    ),
                    idempotency_status="REPLAYED" if provisioning_calls == 2 else "RECORDED",
                )
            )
        raise AssertionError(f"unexpected POST {path}")

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
                "task-287-customer",
                "--suffix",
                "287001",
            ]
        )
    )

    assert result["status"] == "passed"
    assert result["task"] == "TASK-287"
    assert result["membership"]["createdByProof"] is True
    assert result["provisioning"]["status"] == "PROVISIONING_REQUEST_RECORDED"
    assert result["provisioning"]["replayStatus"] == "PROVISIONING_REPLAYED"
    assert result["actual_seat_assignment_completed"] is True
    assert result["read_model"]["refreshedSeatAssignmentStatus"] == "SEAT_ASSIGNED"
    assert [call[0] for call in calls].count("POST") == 4


def test_run_can_activate_account_foundation_before_provisioning(monkeypatch):
    calls: list[tuple[str, str, dict | None]] = []
    readiness_calls = 0
    provisioning_calls = 0

    def fake_get_json(**kwargs):
        nonlocal readiness_calls
        calls.append(("GET", kwargs["path"], kwargs.get("query")))
        if kwargs["path"] == "/v1/referral-saas/accounts":
            return _ok(_registry_payload())
        if kwargs["path"] == "/v1/referral-saas/accounts/membership-posture":
            return _ok(_posture_payload(total=1, active=1))
        if kwargs["path"] == "/v1/referral-saas/accounts/acct-287/membership-activation-readiness":
            readiness_calls += 1
            if readiness_calls == 1:
                return _ok(_readiness_payload())
            return _ok(
                _readiness_payload(
                    membership_ref="membership-287",
                    provisioning_readiness=(
                        "SEAT_ASSIGNED" if readiness_calls >= 3 else "READY_TO_PROVISION_SEAT"
                    ),
                    seat_assignment_status=(
                        "SEAT_ASSIGNED" if readiness_calls >= 3 else "SEAT_NOT_ASSIGNED"
                    ),
                )
            )
        raise AssertionError(f"unexpected GET {kwargs['path']}")

    def fake_post_json(**kwargs):
        nonlocal provisioning_calls
        calls.append(("POST", kwargs["path"], kwargs["payload"]))
        path = kwargs["path"]
        if path == "/v1/referral-saas/accounts/acct-287/activation-requests":
            assert kwargs["payload"] == {
                "accountScope": {
                    "refType": "external_tenant_ref",
                    "externalRef": "task-287-customer",
                    "context": "setup",
                },
                "activation": {"seatTypes": ["ADMIN", "OPERATOR"]},
                "reasonCode": "TASK_291_ACCOUNT_FOUNDATION_ACTIVATION_PROOF",
                "correlationId": "task-291-account-foundation-activation-291001",
                "idempotencyKey": "task-291-account-foundation-activation-291001",
            }
            return _ok(_account_foundation_activation_payload())
        if path == "/v1/referral-saas/accounts/acct-287/membership-invitations":
            return _ok(
                {
                    "status": "ok",
                    "invitation": {
                        "commandStatus": "INVITATION_INTENT_RECORDED",
                        "membership": {
                            "membershipRef": "membership-287",
                            "status": "INVITED",
                        },
                        "delivery": {"status": "DELIVERY_NOT_CONFIGURED"},
                        "noInviteDeliveryConfirmed": True,
                        "noAuthClaimChangeConfirmed": True,
                        "noSeatAssignmentConfirmed": True,
                        "noMoneyMovementConfirmed": True,
                    },
                    "no_invite_delivery_confirmed": True,
                    "no_auth_claim_change_confirmed": True,
                    "no_seat_assignment_confirmed": True,
                    "no_money_movement_confirmed": True,
                }
            )
        if path == "/v1/referral-saas/accounts/acct-287/memberships/membership-287/activation":
            return _ok(
                {
                    "status": "ok",
                    "activationRequest": {
                        "commandStatus": "MEMBERSHIP_ACTIVATED",
                        "membership": {
                            "membershipRef": "membership-287",
                            "status": "ACTIVE",
                        },
                    },
                    "no_invite_delivery_confirmed": True,
                    "no_auth_claim_change_confirmed": True,
                    "no_seat_assignment_confirmed": True,
                    "no_money_movement_confirmed": True,
                }
            )
        if path == "/v1/referral-saas/accounts/acct-287/memberships/membership-287/access-provisioning":
            provisioning_calls += 1
            return _ok(
                _provisioning_payload(
                    status=(
                        "PROVISIONING_REPLAYED"
                        if provisioning_calls == 2
                        else "PROVISIONING_REQUEST_RECORDED"
                    ),
                    idempotency_status="REPLAYED" if provisioning_calls == 2 else "RECORDED",
                )
            )
        raise AssertionError(f"unexpected POST {path}")

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
                "task-287-customer",
                "--suffix",
                "291001",
                "--activate-account-foundation",
            ]
        )
    )

    assert result["status"] == "passed"
    assert result["task"] == "TASK-291"
    assert result["account_foundation_activation"]["commandStatus"] == (
        "ACCOUNT_FOUNDATION_ACTIVATED"
    )
    assert result["account_foundation_activation"]["seatCapacity"] == {
        "seatTypes": ["ADMIN", "OPERATOR"],
        "createdSeatCount": 2,
    }
    assert result["actual_seat_assignment_completed"] is True
    assert [call[1] for call in calls if call[0] == "POST"][0] == (
        "/v1/referral-saas/accounts/acct-287/activation-requests"
    )


def test_run_accepts_controlled_provisioning_block(monkeypatch):
    def fake_get_json(**kwargs):
        if kwargs["path"] == "/v1/referral-saas/accounts":
            return _ok(_registry_payload())
        if kwargs["path"] == "/v1/referral-saas/accounts/membership-posture":
            return _ok(_posture_payload(total=1, active=1))
        if kwargs["path"] == "/v1/referral-saas/accounts/acct-287/membership-activation-readiness":
            return _ok(
                _readiness_payload(
                    membership_ref="membership-287",
                    provisioning_readiness="READY_TO_PROVISION_SEAT",
                )
            )
        raise AssertionError(f"unexpected GET {kwargs['path']}")

    def fake_post_json(**kwargs):
        if kwargs["path"].endswith("/access-provisioning"):
            return _ok(
                _provisioning_payload(
                    status="PROVISIONING_REJECTED_ACCOUNT_NOT_ACTIVE",
                )
            )
        raise AssertionError(f"unexpected POST {kwargs['path']}")

    monkeypatch.setattr(script.setup_check, "get_json", fake_get_json)
    monkeypatch.setattr(script.setup_check, "post_json", fake_post_json)

    result = script.run(
        script.parse_args(
            [
                "--external-tenant-ref",
                "task-287-customer",
                "--suffix",
                "287002",
            ]
        )
    )

    assert result["controlled_provisioning_block"] is True
    assert result["actual_seat_assignment_completed"] is False
    assert result["provisioning"]["status"] == "PROVISIONING_REJECTED_ACCOUNT_NOT_ACTIVE"


def test_run_fails_when_provisioning_changes_auth_claims(monkeypatch):
    def fake_get_json(**kwargs):
        if kwargs["path"] == "/v1/referral-saas/accounts":
            return _ok(_registry_payload())
        if kwargs["path"] == "/v1/referral-saas/accounts/membership-posture":
            return _ok(_posture_payload(total=1, active=1))
        if kwargs["path"] == "/v1/referral-saas/accounts/acct-287/membership-activation-readiness":
            return _ok(
                _readiness_payload(
                    membership_ref="membership-287",
                    provisioning_readiness="READY_TO_PROVISION_SEAT",
                )
            )
        raise AssertionError(f"unexpected GET {kwargs['path']}")

    def fake_post_json(**kwargs):
        payload = _provisioning_payload()
        payload["accessProvisioning"]["authClaims"]["authClaimStatus"] = "AUTH_PROPAGATED"
        return _ok(payload)

    monkeypatch.setattr(script.setup_check, "get_json", fake_get_json)
    monkeypatch.setattr(script.setup_check, "post_json", fake_post_json)

    with pytest.raises(RuntimeError, match="auth claims"):
        script.run(
            script.parse_args(
                [
                    "--external-tenant-ref",
                    "task-287-customer",
                    "--suffix",
                    "287003",
                ]
            )
        )
