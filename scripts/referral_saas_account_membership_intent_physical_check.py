from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.parse
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts import referral_saas_account_setup_ui_physical_check as setup_check


DEFAULT_BASE_URL = setup_check.DEFAULT_BASE_URL
DEFAULT_ADMIN_KEY = setup_check.DEFAULT_ADMIN_KEY
DEFAULT_INTERNAL_TENANT_CODE = setup_check.DEFAULT_INTERNAL_TENANT_CODE
FORBIDDEN_INVITATION_PAYLOAD_TERMS = (
    "tenant_code",
    "tenantcode",
    "api_key",
    "client_secret",
    "private_key",
    "password",
    "wallet",
    "settlement",
    "delivery",
    "send_invite",
    "sendinvite",
    "activate",
    "go_live",
    "golive",
    "campaign_activation",
    "campaignactivation",
    "webhook",
    "reward",
    "funding",
    "fulfilment",
    "fulfillment",
    "payout",
    "invoice",
)


def build_membership_invitation_payload(
    *,
    external_tenant_ref: str,
    actor_subject: str,
    display_name: str,
    email_hash: str,
    role_family: str,
    permission_set: str,
    correlation_id: str,
    idempotency_key: str,
) -> dict[str, Any]:
    return {
        "accountScope": {
            "refType": "external_tenant_ref",
            "externalRef": external_tenant_ref,
            "context": "setup",
        },
        "actor": {
            "actorType": "USER",
            "subject": actor_subject,
            "emailHash": email_hash,
            "displayName": display_name,
        },
        "membership": {
            "roleFamily": role_family,
            "permissionSet": permission_set,
            "tenantScope": "PRIMARY_ACCOUNT_TENANT",
        },
        "reasonCode": "ACCOUNT_SETUP_USER_ROLE",
        "correlationId": correlation_id,
        "idempotencyKey": idempotency_key,
    }


def assert_safe_membership_intent_payload(payload: dict[str, Any]) -> None:
    unsafe_key = _find_forbidden_payload_key(payload)
    if unsafe_key:
        raise RuntimeError(f"Membership intent payload contains {unsafe_key}.")


def assert_membership_intent_response(payload: dict[str, Any]) -> None:
    invitation = payload.get("invitation") or {}
    membership = invitation.get("membership") or {}
    delivery = invitation.get("delivery") or {}
    if invitation.get("commandStatus") not in {
        "INVITATION_INTENT_RECORDED",
        "INVITATION_INTENT_REPLAYED",
    }:
        raise RuntimeError(
            "Unexpected invitation command status: "
            f"{json.dumps(payload, sort_keys=True)}"
        )
    if membership.get("status") != "INVITED":
        raise RuntimeError(
            "Membership intent did not return INVITED status: "
            f"{json.dumps(payload, sort_keys=True)}"
        )
    if delivery.get("status") != "DELIVERY_NOT_CONFIGURED":
        raise RuntimeError(
            "Invitation intent must not configure delivery: "
            f"{json.dumps(payload, sort_keys=True)}"
        )
    if not invitation.get("noInviteDeliveryConfirmed"):
        raise RuntimeError("Invitation response did not confirm no invite delivery.")
    if not invitation.get("noAuthClaimChangeConfirmed"):
        raise RuntimeError("Invitation response did not confirm no auth claim change.")
    if not invitation.get("noSeatAssignmentConfirmed"):
        raise RuntimeError("Invitation response did not confirm no seat assignment.")
    if not invitation.get("noMoneyMovementConfirmed"):
        raise RuntimeError("Invitation response did not confirm no money movement.")
    setup_check.assert_no_forbidden_product_payload(payload)


def assert_membership_posture_response(payload: dict[str, Any]) -> None:
    posture = payload.get("membershipPosture") or {}
    if int(posture.get("invitedCount") or 0) < 1:
        raise RuntimeError(
            "Membership posture did not include invited membership evidence: "
            f"{json.dumps(payload, sort_keys=True)}"
        )
    if not posture.get("noInviteDeliveryConfirmed"):
        raise RuntimeError("Membership posture did not confirm no invite delivery.")
    setup_check.assert_no_forbidden_product_payload(payload)


def _find_forbidden_payload_key(value: Any, *, path: str = "") -> str | None:
    if isinstance(value, dict):
        for key, item in value.items():
            normalized = str(key).strip().lower().replace("-", "_")
            dotted = f"{path}.{normalized}" if path else normalized
            if any(forbidden in normalized for forbidden in FORBIDDEN_INVITATION_PAYLOAD_TERMS):
                return dotted
            nested = _find_forbidden_payload_key(item, path=dotted)
            if nested:
                return nested
    if isinstance(value, list):
        for index, item in enumerate(value):
            nested = _find_forbidden_payload_key(item, path=f"{path}[{index}]")
            if nested:
                return nested
    return None


def run(args: argparse.Namespace) -> dict[str, Any]:
    suffix = args.suffix or str(int(time.time()))
    external_tenant_ref = args.external_tenant_ref or f"task-213-{suffix}"
    organisation_ref = args.organisation_ref or f"org-task-213-{suffix}"
    organisation_name = args.organisation_name or f"Task 213 Account {suffix}"
    actor_subject = args.actor_subject or f"task-213-setup-owner-{suffix}"
    display_name = args.display_name or "Referral SaaS setup owner"
    email_hash = args.email_hash or f"hash-task-213-{suffix}"
    correlation_id = f"task-213-membership-intent-proof-{suffix}"

    setup_args = argparse.Namespace(
        base_url=args.base_url,
        admin_key=args.admin_key,
        internal_tenant_code=args.internal_tenant_code,
        external_tenant_ref=external_tenant_ref,
        organisation_ref=organisation_ref,
        organisation_name=organisation_name,
        admin_contact=args.admin_contact,
        suffix=suffix,
    )
    setup_result = setup_check.run(setup_args)
    resolved_account = setup_result.get("resolved_account") or {}
    account_ref = str(
        resolved_account.get("accountId")
        or resolved_account.get("accountCode")
        or ""
    )
    if not account_ref:
        raise RuntimeError(
            "Setup proof did not return a safe account reference for membership intent."
        )

    invitation_payload = build_membership_invitation_payload(
        external_tenant_ref=external_tenant_ref,
        actor_subject=actor_subject,
        display_name=display_name,
        email_hash=email_hash,
        role_family=args.role_family,
        permission_set=args.permission_set,
        correlation_id=correlation_id,
        idempotency_key=f"task-213-membership-intent-{suffix}",
    )
    assert_safe_membership_intent_payload(invitation_payload)

    invitation_result = setup_check.post_json(
        base_url=args.base_url,
        path=(
            "/v1/referral-saas/accounts/"
            f"{urllib.parse.quote(account_ref)}/membership-invitations"
        ),
        admin_key=args.admin_key,
        payload=invitation_payload,
    )
    setup_check.require_success(
        "record account setup membership invitation intent",
        invitation_result,
    )
    assert_membership_intent_response(invitation_result.payload)

    posture_result = setup_check.get_json(
        base_url=args.base_url,
        path="/v1/referral-saas/accounts/membership-posture",
        admin_key=args.admin_key,
        query={
            "ref_type": "external_tenant_ref",
            "external_ref": external_tenant_ref,
            "context": "setup",
        },
    )
    setup_check.require_success("read membership posture", posture_result)
    assert_membership_posture_response(posture_result.payload)

    return {
        "status": "passed",
        "task": "TASK-213",
        "base_url": args.base_url,
        "external_tenant_ref": external_tenant_ref,
        "organisation_ref": organisation_ref,
        "account_ref": account_ref,
        "membership_command_status": invitation_result.payload["invitation"].get(
            "commandStatus"
        ),
        "membership_status": invitation_result.payload["invitation"]
        .get("membership", {})
        .get("status"),
        "delivery_status": invitation_result.payload["invitation"]
        .get("delivery", {})
        .get("status"),
        "membership_posture": posture_result.payload.get("membershipPosture"),
        "no_invite_delivery_confirmed": invitation_result.payload.get(
            "no_invite_delivery_confirmed"
        ),
        "no_auth_claim_change_confirmed": invitation_result.payload.get(
            "no_auth_claim_change_confirmed"
        ),
        "no_seat_assignment_confirmed": invitation_result.payload.get(
            "no_seat_assignment_confirmed"
        ),
        "no_money_movement_confirmed": invitation_result.payload.get(
            "no_money_movement_confirmed"
        ),
        "no_campaign_activation": True,
        "no_go_live": True,
        "setup_result": setup_result,
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Physically verify Referral SaaS Account Setup Step 2 membership "
            "invitation intent against a running local/staging API."
        )
    )
    parser.add_argument("--base-url", default=os.environ.get("API_BASE_URL", DEFAULT_BASE_URL))
    parser.add_argument("--admin-key", default=os.environ.get("LOCAL_API_KEY", DEFAULT_ADMIN_KEY))
    parser.add_argument(
        "--internal-tenant-code",
        default=os.environ.get("TASK_213_INTERNAL_TENANT_CODE", DEFAULT_INTERNAL_TENANT_CODE),
        help="Trusted internal tenant code used by the setup account creation proof.",
    )
    parser.add_argument("--external-tenant-ref")
    parser.add_argument("--organisation-ref")
    parser.add_argument("--organisation-name")
    parser.add_argument("--admin-contact", default="referral-saas-setup-proof@example.test")
    parser.add_argument("--actor-subject")
    parser.add_argument("--display-name")
    parser.add_argument("--email-hash")
    parser.add_argument("--role-family", default="DISTRIBUTION_ADMIN")
    parser.add_argument("--permission-set", default="REFERRAL_SAAS_ACCOUNT_ADMIN")
    parser.add_argument("--suffix", help="Stable suffix for repeatable references.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    result = run(args)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
