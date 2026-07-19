from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts import referral_saas_client_workspace_physical_check as workspace_check


DEFAULT_BASE_URL = workspace_check.DEFAULT_BASE_URL
DEFAULT_ADMIN_KEY = workspace_check.DEFAULT_ADMIN_KEY
DEFAULT_TENANT_INDUSTRY = "Referral management and campaign attribution"


def build_local_tenant_seed_code(suffix: str) -> str:
    normalized = re.sub(r"[^A-Za-z0-9]", "", suffix).upper()
    if not normalized:
        raise RuntimeError("A non-empty suffix is required for a local tenant seed.")
    if normalized.startswith("TASK230"):
        return normalized[:48]
    return f"TASK230{normalized}"[:48]


async def ensure_local_unlinked_tenant_seed(
    *,
    dsn: str,
    tenant_code: str,
    tenant_name: str,
    industry: str,
) -> dict[str, Any]:
    import asyncpg

    conn = await asyncpg.connect(dsn)
    try:
        owner_link = await conn.fetchrow(
            """
            SELECT account_tenant_id, account_id, status
            FROM platform_account_tenants
            WHERE tenant_code = $1
              AND relationship_type = 'OWNER'
              AND status IN ('PENDING_SETUP', 'ACTIVE', 'SUSPENDED')
            LIMIT 1
            """,
            tenant_code,
        )
        if owner_link:
            raise RuntimeError(
                "Local tenant seed is already attached to an account owner. "
                "Use a different --suffix for a fresh physical proof."
            )

        row = await conn.fetchrow(
            """
            INSERT INTO tenants (tenant_code, tenant_name, industry)
            VALUES ($1, $2, $3)
            ON CONFLICT (tenant_code) DO UPDATE SET
                tenant_name = EXCLUDED.tenant_name,
                industry = EXCLUDED.industry,
                is_active = TRUE
            RETURNING tenant_code, tenant_name, industry, is_active
            """,
            tenant_code,
            tenant_name,
            industry,
        )
    finally:
        await conn.close()

    return {
        "tenant_code": str(row["tenant_code"]),
        "tenant_name": str(row["tenant_name"]),
        "industry": str(row["industry"]),
        "is_active": bool(row["is_active"]),
        "owner_link_status": "UNLINKED",
    }


def run(args: argparse.Namespace) -> dict[str, Any]:
    if not args.db_dsn:
        raise RuntimeError("--db-dsn or APP_DB_DSN is required for local tenant seed setup.")

    suffix = args.suffix or str(int(time.time()))
    tenant_code = args.internal_tenant_code or build_local_tenant_seed_code(suffix)
    tenant_name = args.tenant_name or f"Task 230 Referral SaaS Seed {suffix}"
    external_tenant_ref = args.external_tenant_ref or f"task-230-{suffix}"
    organisation_ref = args.organisation_ref or f"org-task-230-{suffix}"
    organisation_name = args.organisation_name or f"Task 230 Fresh Client {suffix}"

    seed_result = asyncio.run(
        ensure_local_unlinked_tenant_seed(
            dsn=args.db_dsn,
            tenant_code=tenant_code,
            tenant_name=tenant_name,
            industry=args.tenant_industry,
        )
    )

    proof_args = argparse.Namespace(
        base_url=args.base_url,
        admin_key=args.admin_key,
        internal_tenant_code=tenant_code,
        external_tenant_ref=external_tenant_ref,
        organisation_ref=organisation_ref,
        organisation_name=organisation_name,
        admin_contact=args.admin_contact,
        suffix=suffix,
        reuse_existing_client=False,
    )
    proof_result = workspace_check.run(proof_args)
    if proof_result.get("account_setup_creation_mode") != "created_client":
        raise RuntimeError("Fresh-client proof did not create a new client.")

    return {
        "status": "passed",
        "task": "TASK-230",
        "base_url": args.base_url,
        "tenant_seed": seed_result,
        "external_tenant_ref": external_tenant_ref,
        "organisation_ref": organisation_ref,
        "workspace_proof_status": proof_result.get("status"),
        "created_account": proof_result.get("created_account"),
        "selected_client": proof_result.get("selected_client"),
        "readiness_status": proof_result.get("readiness_status"),
        "readiness_summary": proof_result.get("readiness_summary"),
        "client_workspace_routes": proof_result.get("client_workspace_routes"),
        "no_profile_update": proof_result.get("no_profile_update") is True,
        "no_invitation_delivery": proof_result.get("no_invitation_delivery") is True,
        "no_campaign_activation": proof_result.get("no_campaign_activation") is True,
        "no_go_live": proof_result.get("no_go_live") is True,
        "no_money_movement": proof_result.get("no_money_movement") is True,
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Prepare a local unlinked tenant seed, then physically verify fresh "
            "Referral SaaS Account Setup to selected Client Workspace handoff."
        )
    )
    parser.add_argument("--base-url", default=os.environ.get("API_BASE_URL", DEFAULT_BASE_URL))
    parser.add_argument("--admin-key", default=os.environ.get("LOCAL_API_KEY", DEFAULT_ADMIN_KEY))
    parser.add_argument("--db-dsn", default=os.environ.get("APP_DB_DSN"))
    parser.add_argument("--internal-tenant-code")
    parser.add_argument("--tenant-name")
    parser.add_argument("--tenant-industry", default=DEFAULT_TENANT_INDUSTRY)
    parser.add_argument("--external-tenant-ref")
    parser.add_argument("--organisation-ref")
    parser.add_argument("--organisation-name")
    parser.add_argument("--admin-contact", default="referral-saas-fresh-client-proof@example.test")
    parser.add_argument("--suffix", help="Stable suffix for repeatable local proof references.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    result = run(args)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
