from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import sys
import time
import urllib.parse
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts import referral_saas_account_setup_ui_physical_check as setup_check
from scripts import referral_saas_selected_customer_e2e_physical_check as read_check


DEFAULT_BASE_URL = setup_check.DEFAULT_BASE_URL
DEFAULT_ADMIN_KEY = setup_check.DEFAULT_ADMIN_KEY
SUCCESSFUL_PROVISIONING_STATUSES = {
    "PROVISIONING_REQUEST_RECORDED",
    "PROVISIONING_REPLAYED",
}
CONTROLLED_BLOCK_STATUSES = {
    "PROVISIONING_REJECTED_ACCOUNT_NOT_ACTIVE",
    "PROVISIONING_REJECTED_TENANT_LINK_NOT_ACTIVE",
    "PROVISIONING_REJECTED_EXTERNAL_REFERENCE_NOT_ACTIVE",
    "PROVISIONING_REJECTED_MEMBERSHIP_NOT_ACTIVE",
    "PROVISIONING_REJECTED_SEAT_UNAVAILABLE",
}
FORBIDDEN_PAYLOAD_TERMS = (
    "tenant_code",
    "tenantcode",
    "api_key",
    "client_secret",
    "private_key",
    "password",
    "wallet",
    "settlement",
    "campaign_activation",
    "campaignactivation",
    "go_live",
    "golive",
    "credential",
    "raw_auth",
    "auth_claims",
    "money",
    "billing",
)


def _quote_path(value: str) -> str:
    return urllib.parse.quote(value, safe="")


def _scope_query(external_tenant_ref: str) -> dict[str, str]:
    return {
        "ref_type": "external_tenant_ref",
        "external_ref": external_tenant_ref,
        "context": "setup",
    }


def _scope_payload(external_tenant_ref: str, *, context: str = "setup") -> dict[str, str]:
    return {
        "refType": "external_tenant_ref",
        "externalRef": external_tenant_ref,
        "context": context,
    }


def _stable_hash(value: str) -> str:
    return hashlib.sha256(value.strip().lower().encode("utf-8")).hexdigest()


def _find_forbidden_payload_key(value: Any, *, path: str = "") -> str | None:
    if isinstance(value, dict):
        for key, item in value.items():
            normalized = str(key).strip().lower().replace("-", "_")
            dotted = f"{path}.{normalized}" if path else normalized
            if any(forbidden in normalized for forbidden in FORBIDDEN_PAYLOAD_TERMS):
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


def _assert_safe_command_payload(payload: dict[str, Any]) -> None:
    unsafe_key = _find_forbidden_payload_key(payload)
    if unsafe_key:
        raise RuntimeError(f"People and Access proof payload contains {unsafe_key}.")


def _require_flag(payload: dict[str, Any], key: str, step: str) -> None:
    if payload.get(key) is not True:
        raise RuntimeError(f"{step} did not confirm {key}.")


def _require_no_adjacent_actions(payload: dict[str, Any], step: str) -> None:
    read_check.assert_no_internal_scope_leak(payload)
    for key in (
        "no_invite_delivery_confirmed",
        "no_auth_claim_change_confirmed",
        "no_credential_creation_confirmed",
        "no_campaign_activation_confirmed",
        "no_go_live_change_confirmed",
        "no_go_live_action_confirmed",
        "no_money_movement_confirmed",
        "no_billing_or_money_movement_confirmed",
    ):
        if key in payload:
            _require_flag(payload, key, step)


def _load_selected_customer(args: argparse.Namespace) -> tuple[dict[str, Any], str, str, str]:
    registry_result = setup_check.get_json(
        base_url=args.base_url,
        path="/v1/referral-saas/accounts",
        admin_key=args.admin_key,
        query={"limit": str(args.registry_limit)},
    )
    setup_check.require_success("load selected-customer registry", registry_result)
    selected_account = read_check._select_customer(
        registry_result.payload,
        external_tenant_ref=args.external_tenant_ref,
        organisation_ref=args.organisation_ref,
    )
    account_ref = read_check._require_account_ref(selected_account)
    external_tenant_ref = read_check._get_external_ref(
        selected_account,
        "external_tenant_ref",
    )
    organisation_ref = read_check._get_external_ref(
        selected_account,
        "organisation_ref",
    )
    return selected_account, account_ref, external_tenant_ref, organisation_ref


def _load_membership_posture(
    *,
    base_url: str,
    admin_key: str,
    external_tenant_ref: str,
) -> dict[str, Any]:
    result = setup_check.get_json(
        base_url=base_url,
        path="/v1/referral-saas/accounts/membership-posture",
        admin_key=admin_key,
        query=_scope_query(external_tenant_ref),
    )
    setup_check.require_success("load selected-customer people/access posture", result)
    read_check.assert_no_internal_scope_leak(result.payload)
    return result.payload


def _load_activation_readiness(
    *,
    base_url: str,
    admin_key: str,
    account_ref: str,
    external_tenant_ref: str,
) -> dict[str, Any]:
    result = setup_check.get_json(
        base_url=base_url,
        path=(
            f"/v1/referral-saas/accounts/{_quote_path(account_ref)}"
            "/membership-activation-readiness"
        ),
        admin_key=admin_key,
        query=_scope_query(external_tenant_ref),
    )
    setup_check.require_success(
        "load selected-customer membership activation readiness",
        result,
    )
    read_check.assert_no_internal_scope_leak(result.payload)
    return result.payload


def _items(readiness_payload: dict[str, Any]) -> list[dict[str, Any]]:
    readiness = readiness_payload.get("activationReadiness") or {}
    items = readiness.get("items")
    if not isinstance(items, list):
        raise RuntimeError(
            "Membership activation readiness did not return an item list."
        )
    return [item for item in items if isinstance(item, dict)]


def _first_active_unassigned(readiness_payload: dict[str, Any]) -> dict[str, Any] | None:
    for item in _items(readiness_payload):
        if (
            item.get("membershipStatus") == "ACTIVE"
            and item.get("provisioningReadiness") == "READY_TO_PROVISION_SEAT"
        ):
            return item
    return None


def _first_matching_item(
    readiness_payload: dict[str, Any],
    *,
    membership_ref: str,
) -> dict[str, Any] | None:
    for item in _items(readiness_payload):
        if item.get("membershipRef") == membership_ref:
            return item
    return None


def _extract_invited_membership_ref(payload: dict[str, Any]) -> str:
    invitation = payload.get("invitation") if isinstance(payload.get("invitation"), dict) else {}
    membership = invitation.get("membership") if isinstance(invitation.get("membership"), dict) else {}
    membership_ref = membership.get("membershipRef")
    if not membership_ref:
        raise RuntimeError("Membership invitation did not return membershipRef.")
    return str(membership_ref)


def _extract_activation_status(payload: dict[str, Any]) -> str:
    request = (
        payload.get("activationRequest")
        if isinstance(payload.get("activationRequest"), dict)
        else {}
    )
    status = request.get("commandStatus")
    if not status:
        raise RuntimeError("Membership activation response did not include commandStatus.")
    return str(status)


def _extract_provisioning(payload: dict[str, Any]) -> dict[str, Any]:
    provisioning = (
        payload.get("accessProvisioning")
        if isinstance(payload.get("accessProvisioning"), dict)
        else {}
    )
    if not provisioning:
        raise RuntimeError("Access provisioning response did not include accessProvisioning.")
    return provisioning


def _extract_provisioning_status(payload: dict[str, Any]) -> str:
    provisioning = _extract_provisioning(payload)
    status = provisioning.get("commandStatus")
    if not status:
        raise RuntimeError("Access provisioning response did not include commandStatus.")
    return str(status)


def _extract_account_foundation_activation(payload: dict[str, Any]) -> dict[str, Any]:
    activation = (
        payload.get("activation")
        if isinstance(payload.get("activation"), dict)
        else {}
    )
    if not activation:
        raise RuntimeError(
            "Account foundation activation response did not include activation."
        )
    return activation


def _activate_account_foundation(
    *,
    args: argparse.Namespace,
    suffix: str,
    account_ref: str,
    external_tenant_ref: str,
) -> dict[str, Any]:
    seat_types = list(dict.fromkeys(["ADMIN", args.seat_type]))
    payload = {
        "accountScope": _scope_payload(external_tenant_ref, context="setup"),
        "activation": {
            "seatTypes": seat_types,
        },
        "reasonCode": "TASK_291_ACCOUNT_FOUNDATION_ACTIVATION_PROOF",
        "correlationId": f"task-291-account-foundation-activation-{suffix}",
        "idempotencyKey": f"task-291-account-foundation-activation-{suffix}",
    }
    _assert_safe_command_payload(payload)
    result = setup_check.post_json(
        base_url=args.base_url,
        path=f"/v1/referral-saas/accounts/{_quote_path(account_ref)}/activation-requests",
        admin_key=args.admin_key,
        payload=payload,
    )
    setup_check.require_success(
        "activate selected-customer account foundation",
        result,
        allowed={200},
    )
    _require_no_adjacent_actions(result.payload, "account foundation activation")
    activation = _extract_account_foundation_activation(result.payload)
    status = str(activation.get("commandStatus") or "")
    if status not in {"ACCOUNT_FOUNDATION_ACTIVATED", "ACCOUNT_FOUNDATION_REPLAYED"}:
        raise RuntimeError(
            "Account foundation activation returned unexpected status "
            f"{status}: {json.dumps(result.payload, sort_keys=True)}"
        )
    return result.payload


def _assert_provisioning_response(payload: dict[str, Any], *, step: str) -> None:
    _require_no_adjacent_actions(payload, step)
    provisioning = _extract_provisioning(payload)
    status = str(provisioning.get("commandStatus") or "")
    seat = provisioning.get("seat") if isinstance(provisioning.get("seat"), dict) else {}
    auth_claims = (
        provisioning.get("authClaims")
        if isinstance(provisioning.get("authClaims"), dict)
        else {}
    )
    if status in SUCCESSFUL_PROVISIONING_STATUSES:
        if seat.get("seatAssignmentStatus") != "SEAT_ASSIGNED":
            raise RuntimeError(f"{step} did not assign a seat: {json.dumps(payload)}")
    elif status not in CONTROLLED_BLOCK_STATUSES:
        raise RuntimeError(f"{step} returned unexpected status {status}.")
    if auth_claims.get("authClaimStatus") != "AUTH_CLAIMS_NOT_PROPAGATED":
        raise RuntimeError(f"{step} changed auth claims: {json.dumps(payload)}")


def _record_unique_membership(
    *,
    args: argparse.Namespace,
    suffix: str,
    account_ref: str,
    external_tenant_ref: str,
) -> tuple[str, str]:
    role_family = args.role_family
    permission_set = args.permission_set
    subject = args.actor_subject or f"task-287-seat-provisioning-{suffix}"
    display_name = args.display_name or f"Task 287 Provisioning {suffix}"
    email_hash = args.email_hash or _stable_hash(f"{subject}@example.test")
    payload = {
        "accountScope": _scope_payload(external_tenant_ref),
        "actor": {
            "actorType": "USER",
            "subject": subject,
            "emailHash": email_hash,
            "displayName": display_name,
        },
        "membership": {
            "roleFamily": role_family,
            "permissionSet": permission_set,
            "tenantScope": "PRIMARY_ACCOUNT_TENANT",
        },
        "reasonCode": "TASK_287_PEOPLE_ACCESS_PROVISIONING_PROOF",
        "correlationId": f"task-287-membership-intent-{suffix}",
        "idempotencyKey": f"task-287-membership-intent-{suffix}",
    }
    _assert_safe_command_payload(payload)

    result = setup_check.post_json(
        base_url=args.base_url,
        path=(
            f"/v1/referral-saas/accounts/{_quote_path(account_ref)}"
            "/membership-invitations"
        ),
        admin_key=args.admin_key,
        payload=payload,
    )
    setup_check.require_success(
        "record selected-customer access intent",
        result,
    )
    _require_no_adjacent_actions(result.payload, "membership invitation")
    return _extract_invited_membership_ref(result.payload), subject


def _record_manual_acceptance(
    *,
    args: argparse.Namespace,
    suffix: str,
    account_ref: str,
    external_tenant_ref: str,
    membership_ref: str,
    accepted_subject: str,
) -> dict[str, Any]:
    payload = {
        "accountScope": _scope_payload(external_tenant_ref),
        "activation": {
            "acceptedSubject": accepted_subject,
            "acceptanceEvidenceRef": f"task-287-manual-acceptance-{suffix}",
        },
        "reasonCode": "AMPLIFI_ADMIN_MANUAL_ACCESS_ACCEPTANCE",
        "correlationId": f"task-287-manual-acceptance-{suffix}",
        "idempotencyKey": f"task-287-manual-acceptance-{suffix}",
    }
    _assert_safe_command_payload(payload)
    result = setup_check.post_json(
        base_url=args.base_url,
        path=(
            f"/v1/referral-saas/accounts/{_quote_path(account_ref)}"
            f"/memberships/{_quote_path(membership_ref)}/activation"
        ),
        admin_key=args.admin_key,
        payload=payload,
    )
    setup_check.require_success(
        "record manual accepted access",
        result,
        allowed={200},
    )
    _require_no_adjacent_actions(result.payload, "manual accepted access")
    return result.payload


def _provision_access(
    *,
    args: argparse.Namespace,
    suffix: str,
    account_ref: str,
    external_tenant_ref: str,
    membership_ref: str,
    idempotency_key: str,
) -> dict[str, Any]:
    payload = {
        "accountScope": _scope_payload(external_tenant_ref, context="setup"),
        "provisioning": {
            "seatType": args.seat_type,
            "seatAssignmentEvidenceRef": f"task-287-seat-evidence-{suffix}",
            "operatorNotes": "TASK-287 physical proof; auth claims remain separate.",
        },
        "reasonCode": "TASK_287_PEOPLE_ACCESS_PROVISIONING_PROOF",
        "correlationId": f"task-287-access-provisioning-{suffix}",
        "idempotencyKey": idempotency_key,
    }
    _assert_safe_command_payload(payload)
    result = setup_check.post_json(
        base_url=args.base_url,
        path=(
            f"/v1/referral-saas/accounts/{_quote_path(account_ref)}"
            f"/memberships/{_quote_path(membership_ref)}/access-provisioning"
        ),
        admin_key=args.admin_key,
        payload=payload,
    )
    setup_check.require_success(
        "request selected-customer access provisioning",
        result,
        allowed={200},
    )
    _assert_provisioning_response(result.payload, step="access provisioning")
    return result.payload


async def _verify_database_evidence_async(
    *,
    dsn: str,
    membership_ref: str,
    provisioning_audit_event_id: str | None,
) -> dict[str, Any]:
    import asyncpg  # type: ignore

    conn = await asyncpg.connect(dsn)
    try:
        membership = await conn.fetchrow(
            """
            SELECT
                platform_memberships.membership_id::text AS membership_id,
                platform_memberships.status,
                platform_memberships.seat_id::text AS seat_id,
                platform_memberships.metadata->>'access_provisioning_status'
                    AS access_provisioning_status,
                COALESCE(
                    platform_memberships.metadata->>'auth_claim_status',
                    'AUTH_CLAIMS_NOT_PROPAGATED'
                ) AS auth_claim_status
            FROM platform_memberships
            WHERE platform_memberships.membership_id = $1::uuid
            """,
            membership_ref,
        )
        if not membership:
            raise RuntimeError("DB check did not find the provisioned membership.")

        audit = None
        if provisioning_audit_event_id:
            audit = await conn.fetchrow(
                """
                SELECT
                    account_audit_event_id::text AS audit_event_id,
                    event_type,
                    event_status,
                    membership_id::text AS membership_id,
                    evidence_summary
                FROM platform_account_audit_events
                WHERE account_audit_event_id = $1::uuid
                """,
                provisioning_audit_event_id,
            )
        return {
            "membershipStatus": membership["status"],
            "seatRef": membership["seat_id"],
            "accessProvisioningStatus": membership["access_provisioning_status"],
            "authClaimStatus": membership["auth_claim_status"],
            "auditEventId": audit["audit_event_id"] if audit else None,
            "auditEventType": audit["event_type"] if audit else None,
            "auditEventStatus": audit["event_status"] if audit else None,
        }
    finally:
        await conn.close()


def _verify_database_evidence(
    *,
    args: argparse.Namespace,
    account_ref: str,
    membership_ref: str,
    provisioning_payload: dict[str, Any],
) -> dict[str, Any] | None:
    dsn = args.db_dsn or os.environ.get("APP_DB_DSN")
    if not args.database:
        return None
    if not dsn:
        raise RuntimeError("--database requires APP_DB_DSN or --db-dsn.")
    audit_event_id = _extract_provisioning(provisioning_payload).get("auditEventId")
    return asyncio.run(
        _verify_database_evidence_async(
            dsn=dsn,
            membership_ref=membership_ref,
            provisioning_audit_event_id=str(audit_event_id) if audit_event_id else None,
        )
    )


def run(args: argparse.Namespace) -> dict[str, Any]:
    suffix = args.suffix or str(int(time.time()))
    selected_account, account_ref, external_tenant_ref, organisation_ref = (
        _load_selected_customer(args)
    )
    account_foundation_activation_payload = None
    if args.activate_account_foundation:
        account_foundation_activation_payload = _activate_account_foundation(
            args=args,
            suffix=suffix,
            account_ref=account_ref,
            external_tenant_ref=external_tenant_ref,
        )
    initial_posture = _load_membership_posture(
        base_url=args.base_url,
        admin_key=args.admin_key,
        external_tenant_ref=external_tenant_ref,
    )
    initial_readiness = _load_activation_readiness(
        base_url=args.base_url,
        admin_key=args.admin_key,
        account_ref=account_ref,
        external_tenant_ref=external_tenant_ref,
    )

    active_candidate = _first_active_unassigned(initial_readiness)
    created_membership = False
    if active_candidate:
        membership_ref = str(active_candidate["membershipRef"])
        accepted_subject = str(active_candidate.get("subject") or membership_ref)
    else:
        membership_ref, accepted_subject = _record_unique_membership(
            args=args,
            suffix=suffix,
            account_ref=account_ref,
            external_tenant_ref=external_tenant_ref,
        )
        activation_payload = _record_manual_acceptance(
            args=args,
            suffix=suffix,
            account_ref=account_ref,
            external_tenant_ref=external_tenant_ref,
            membership_ref=membership_ref,
            accepted_subject=accepted_subject,
        )
        activation_status = _extract_activation_status(activation_payload)
        if activation_status != "MEMBERSHIP_ACTIVATED":
            raise RuntimeError(
                "Manual accepted access did not activate membership lifecycle: "
                f"{activation_status}"
            )
        created_membership = True

    post_acceptance_readiness = _load_activation_readiness(
        base_url=args.base_url,
        admin_key=args.admin_key,
        account_ref=account_ref,
        external_tenant_ref=external_tenant_ref,
    )
    ready_item = _first_matching_item(
        post_acceptance_readiness,
        membership_ref=membership_ref,
    )
    if not ready_item:
        raise RuntimeError("Accepted membership did not appear in readiness read model.")
    if ready_item.get("activationReadiness") != "ACTIVE":
        raise RuntimeError(
            "Accepted membership is not active in readiness read model: "
            f"{json.dumps(ready_item, sort_keys=True)}"
        )

    idempotency_key = f"task-287-access-provisioning-{suffix}"
    provisioning_payload = _provision_access(
        args=args,
        suffix=suffix,
        account_ref=account_ref,
        external_tenant_ref=external_tenant_ref,
        membership_ref=membership_ref,
        idempotency_key=idempotency_key,
    )
    provisioning_status = _extract_provisioning_status(provisioning_payload)

    replay_payload = _provision_access(
        args=args,
        suffix=suffix,
        account_ref=account_ref,
        external_tenant_ref=external_tenant_ref,
        membership_ref=membership_ref,
        idempotency_key=idempotency_key,
    )
    replay_status = _extract_provisioning_status(replay_payload)
    if provisioning_status in SUCCESSFUL_PROVISIONING_STATUSES and replay_status not in {
        "PROVISIONING_REPLAYED",
        "PROVISIONING_REQUEST_RECORDED",
    }:
        raise RuntimeError(f"Provisioning replay returned {replay_status}.")

    refreshed_posture = _load_membership_posture(
        base_url=args.base_url,
        admin_key=args.admin_key,
        external_tenant_ref=external_tenant_ref,
    )
    refreshed_readiness = _load_activation_readiness(
        base_url=args.base_url,
        admin_key=args.admin_key,
        account_ref=account_ref,
        external_tenant_ref=external_tenant_ref,
    )
    refreshed_item = _first_matching_item(
        refreshed_readiness,
        membership_ref=membership_ref,
    )
    if not refreshed_item:
        raise RuntimeError("Provisioned membership disappeared from refreshed readiness.")
    if refreshed_item.get("authClaimStatus") != "AUTH_CLAIMS_NOT_PROPAGATED":
        raise RuntimeError("Provisioning changed auth-claim status unexpectedly.")

    db_evidence = _verify_database_evidence(
        args=args,
        account_ref=account_ref,
        membership_ref=membership_ref,
        provisioning_payload=provisioning_payload,
    )

    return {
        "status": "passed",
        "task": "TASK-291" if args.activate_account_foundation else "TASK-287",
        "base_url": args.base_url,
        "proof_suffix": suffix,
        "selected_customer": {
            "accountRef": account_ref,
            "accountName": selected_account.get("accountName"),
            "externalTenantRef": external_tenant_ref,
            "organisationRef": organisation_ref,
        },
        "account_foundation_activation": (
            _extract_account_foundation_activation(account_foundation_activation_payload)
            if account_foundation_activation_payload
            else None
        ),
        "membership": {
            "membershipRef": membership_ref,
            "acceptedSubject": accepted_subject,
            "createdByProof": created_membership,
        },
        "provisioning": {
            "status": provisioning_status,
            "replayStatus": replay_status,
            "seat": _extract_provisioning(provisioning_payload).get("seat"),
            "authClaims": _extract_provisioning(provisioning_payload).get("authClaims"),
            "auditEventId": _extract_provisioning(provisioning_payload).get(
                "auditEventId"
            ),
        },
        "read_model": {
            "initialMembershipCount": (initial_posture.get("membershipPosture") or {}).get(
                "totalMemberships"
            ),
            "refreshedMembershipCount": (
                refreshed_posture.get("membershipPosture") or {}
            ).get("totalMemberships"),
            "refreshedProvisioningReadiness": refreshed_item.get(
                "provisioningReadiness"
            ),
            "refreshedSeatAssignmentStatus": refreshed_item.get(
                "seatAssignmentStatus"
            ),
            "refreshedAuthClaimStatus": refreshed_item.get("authClaimStatus"),
        },
        "database_evidence": db_evidence,
        "actual_seat_assignment_completed": provisioning_status
        in SUCCESSFUL_PROVISIONING_STATUSES,
        "controlled_provisioning_block": provisioning_status in CONTROLLED_BLOCK_STATUSES,
        "no_invite_delivery": True,
        "no_credential_creation": True,
        "no_auth_claim_change": True,
        "no_campaign_activation": True,
        "no_go_live_change": True,
        "no_billing_or_money_movement": True,
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Physically verify selected-customer People and Access provisioning "
            "from API calls and optional live DB evidence."
        )
    )
    parser.add_argument("--base-url", default=os.environ.get("API_BASE_URL", DEFAULT_BASE_URL))
    parser.add_argument("--admin-key", default=os.environ.get("LOCAL_API_KEY", DEFAULT_ADMIN_KEY))
    parser.add_argument("--external-tenant-ref")
    parser.add_argument("--organisation-ref")
    parser.add_argument("--registry-limit", type=int, default=50)
    parser.add_argument("--actor-subject")
    parser.add_argument("--display-name")
    parser.add_argument("--email-hash")
    parser.add_argument("--role-family", default="CAMPAIGN_MANAGER")
    parser.add_argument("--permission-set", default="REFERRAL_SAAS_CAMPAIGN_MANAGER")
    parser.add_argument("--seat-type", default="OPERATOR")
    parser.add_argument("--suffix", help="Stable suffix for repeatable proof result labelling.")
    parser.add_argument(
        "--activate-account-foundation",
        action="store_true",
        help=(
            "Activate the selected customer account foundation through the guarded "
            "TASK-288 API before attempting People and Access seat provisioning."
        ),
    )
    parser.add_argument(
        "--database",
        action="store_true",
        help="Also verify platform membership/seat/audit state through APP_DB_DSN.",
    )
    parser.add_argument("--db-dsn", default=os.environ.get("APP_DB_DSN"))
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    result = run(args)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
