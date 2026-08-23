from __future__ import annotations

import argparse
import asyncio
import json
import os
import time
from typing import Any

from scripts.referral_saas_account_create_physical_check import (
    assert_no_internal_tenant_identifier,
    build_seed_sections,
    get_json,
    post_json,
    require_success,
    seed_ready_for_review_draft_db,
)


async def verify_lifecycle_evidence(
    *, dsn: str, account_id: str, external_tenant_ref: str, organisation_ref: str
) -> dict[str, int]:
    import asyncpg

    conn = await asyncpg.connect(dsn)
    try:
        row = await conn.fetchrow(
            """
            SELECT
                COUNT(DISTINCT account.account_id) AS account_count,
                COUNT(DISTINCT external_ref.external_ref_id) AS external_ref_count,
                COUNT(DISTINCT audit.account_audit_event_id) FILTER (
                    WHERE audit.event_type = 'ACCOUNT_FOUNDATION_CREATED'
                ) AS creation_audit_count
            FROM platform_accounts account
            LEFT JOIN platform_external_tenant_refs external_ref
                ON external_ref.account_id = account.account_id
               AND external_ref.external_ref IN ($2, $3)
            LEFT JOIN platform_account_audit_events audit
                ON audit.account_id = account.account_id
            WHERE account.account_id = $1::uuid
            """,
            account_id,
            external_tenant_ref,
            organisation_ref,
        )
    finally:
        await conn.close()

    evidence = {key: int(value or 0) for key, value in dict(row).items()}
    expected = {"account_count": 1, "external_ref_count": 2, "creation_audit_count": 1}
    if evidence != expected:
        raise RuntimeError(f"Unexpected lifecycle DB evidence: {evidence}")
    return evidence


async def cleanup_fixture(*, dsn: str, account_id: str, draft_ref: str, tenant_code: str) -> None:
    import asyncpg

    conn = await asyncpg.connect(dsn)
    try:
        async with conn.transaction():
            draft_id = await conn.fetchval(
                "SELECT draft_id FROM onboarding_drafts WHERE draft_ref = $1", draft_ref
            )
            await conn.execute(
                "DELETE FROM platform_account_audit_events WHERE account_id = $1::uuid", account_id
            )
            await conn.execute(
                "DELETE FROM platform_external_tenant_refs WHERE account_id = $1::uuid", account_id
            )
            await conn.execute(
                "DELETE FROM platform_account_tenants WHERE account_id = $1::uuid", account_id
            )
            await conn.execute(
                "DELETE FROM platform_organisations WHERE account_id = $1::uuid", account_id
            )
            await conn.execute(
                "DELETE FROM platform_accounts WHERE account_id = $1::uuid", account_id
            )
            if draft_id:
                await conn.execute("DELETE FROM onboarding_draft_audit_links WHERE draft_id = $1", draft_id)
                await conn.execute("DELETE FROM onboarding_draft_idempotency_keys WHERE draft_id = $1", draft_id)
                await conn.execute("DELETE FROM onboarding_draft_validation_results WHERE draft_id = $1", draft_id)
                await conn.execute("DELETE FROM onboarding_draft_sections WHERE draft_id = $1", draft_id)
                await conn.execute("DELETE FROM onboarding_drafts WHERE draft_id = $1", draft_id)
            await conn.execute(
                """
                DELETE FROM tenants
                WHERE tenant_code = $1
                  AND NOT EXISTS (
                      SELECT 1
                      FROM platform_account_tenants
                      WHERE tenant_code = $1
                  )
                """,
                tenant_code,
            )
    finally:
        await conn.close()


def _customers(payload: dict[str, Any]) -> list[dict[str, Any]]:
    customers = (payload.get("portfolio") or {}).get("customers") or []
    if not isinstance(customers, list):
        raise RuntimeError("Customer portfolio returned an invalid customer collection.")
    return customers


def run(args: argparse.Namespace) -> dict[str, Any]:
    if not args.db_dsn:
        raise RuntimeError("TASK-448 requires --db-dsn for authoritative proof and cleanup.")
    suffix = args.suffix or str(int(time.time()))
    external_ref = f"task-448-{suffix}"
    organisation_ref = f"org-task-448-{suffix}"
    draft_ref = f"draft_task_448_{suffix}".replace("-", "_")
    correlation_id = f"task-448-lifecycle-{suffix}"
    account_id: str | None = None
    tenant_code = args.internal_tenant_code or (
        "T448" + suffix.replace("-", "")
    )[:20].upper()
    sections = build_seed_sections(
        external_tenant_ref=external_ref,
        organisation_ref=organisation_ref,
        producer_ref=f"producer-{suffix}",
        sponsor_ref=f"sponsor-{suffix}",
        distributor_ref=f"distributor-{suffix}",
        campaign_code=f"CMP-{suffix}",
        opportunity_ref=f"opp-{suffix}",
        organisation_name=f"Task 448 Customer {suffix}",
        admin_contact="task-448@example.test",
    )
    try:
        before = get_json(
            base_url=args.base_url,
            path="/v1/referral-saas/operator/customer-portfolio",
            admin_key=args.admin_key,
            query={"search": external_ref},
        )
        require_success("search before create", before)
        if _customers(before.payload):
            raise RuntimeError("Generated customer fixture already exists.")

        asyncio.run(seed_ready_for_review_draft_db(
            dsn=args.db_dsn,
            draft_ref=draft_ref,
            external_tenant_ref=external_ref,
            organisation_ref=organisation_ref,
            sections=sections,
            correlation_id=correlation_id,
        ))
        create_payload = {
            "draft_ref": draft_ref,
            "internal_tenant_code": tenant_code,
            "idempotency_key": f"task-448-create-{suffix}",
            "correlation_id": correlation_id,
        }
        created = post_json(
            base_url=args.base_url,
            path="/v1/referral-saas/accounts/from-draft",
            admin_key=args.admin_key,
            payload=create_payload,
        )
        require_success("create account foundation", created)
        assert_no_internal_tenant_identifier(created.payload)
        account_id = str((created.payload.get("account") or {}).get("accountId") or "")
        if not account_id:
            raise RuntimeError("Create response did not include the persisted account id.")

        replay = post_json(
            base_url=args.base_url,
            path="/v1/referral-saas/accounts/from-draft",
            admin_key=args.admin_key,
            payload=create_payload,
        )
        require_success("replay account creation", replay)
        if str((replay.payload.get("account") or {}).get("accountId") or "") != account_id:
            raise RuntimeError("Exact replay did not return the original account.")

        conflict_payload = dict(create_payload)
        conflict_payload["idempotency_key"] = f"task-448-conflict-{suffix}"
        conflict = post_json(
            base_url=args.base_url,
            path="/v1/referral-saas/accounts/from-draft",
            admin_key=args.admin_key,
            payload=conflict_payload,
        )
        if conflict.status_code != 409:
            raise RuntimeError(f"Duplicate create returned HTTP {conflict.status_code}, expected 409.")

        after = get_json(
            base_url=args.base_url,
            path="/v1/referral-saas/operator/customer-portfolio",
            admin_key=args.admin_key,
            query={"search": external_ref},
        )
        require_success("refresh customer portfolio", after)
        customers = _customers(after.payload)
        destination = f"/admin/referral-saas/account-maintenance/{account_id}"
        if len(customers) != 1 or customers[0].get("accountRef") != account_id:
            raise RuntimeError("Created customer was not returned exactly once by discovery.")
        if customers[0].get("destination") != destination:
            raise RuntimeError("Discovery did not return the persisted profile destination.")

        evidence = asyncio.run(verify_lifecycle_evidence(
            dsn=args.db_dsn,
            account_id=account_id,
            external_tenant_ref=external_ref,
            organisation_ref=organisation_ref,
        ))
        return {
            "status": "passed",
            "task": "TASK-448",
            "accountRef": account_id,
            "destination": destination,
            "idempotentReplayConfirmed": True,
            "duplicateConflictConfirmed": True,
            "permissionScopedPortfolioConfirmed": bool(
                after.payload.get("noCrossJurisdictionAccessConfirmed")
            ),
            "databaseEvidence": evidence,
            "fixtureCleanup": "completed",
        }
    finally:
        if account_id:
            asyncio.run(cleanup_fixture(
                dsn=args.db_dsn, account_id=account_id, draft_ref=draft_ref, tenant_code=tenant_code
            ))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run TASK-448 Customer Accounts lifecycle proof.")
    parser.add_argument("--base-url", default=os.environ.get("API_BASE_URL", "http://127.0.0.1:8000"))
    parser.add_argument("--admin-key", default=os.environ.get("LOCAL_API_KEY", "test-admin-key"))
    parser.add_argument("--db-dsn", default=os.environ.get("APP_DB_DSN"))
    parser.add_argument("--internal-tenant-code")
    parser.add_argument("--suffix")
    return parser.parse_args()


if __name__ == "__main__":
    print(json.dumps(run(parse_args()), indent=2, sort_keys=True))
