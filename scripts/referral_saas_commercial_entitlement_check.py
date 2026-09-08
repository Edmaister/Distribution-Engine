"""TASK-464: migrated PostgreSQL evidence proof; all created data rolls back."""
from contextlib import asynccontextmanager
import asyncio
import json
import os
from uuid import uuid4
from urllib.parse import urlparse

import asyncpg
from dotenv import load_dotenv
from services import referral_saas_account_foundation_service as svc
from services.referral_saas_solution_packages import SOLUTION_PACKAGES


async def main():
    load_dotenv()
    dsn = os.environ["APP_DB_DSN"]
    if urlparse(dsn).hostname not in {"localhost", "127.0.0.1", "::1"}:
        raise RuntimeError("This rollback-only local proof requires a localhost database.")
    conn = await asyncpg.connect(dsn)
    transaction = conn.transaction()
    await transaction.start()
    original = svc.db_connection
    @asynccontextmanager
    async def connection():
        yield conn
    svc.db_connection = connection
    account = str(uuid4()); external = "task-464-" + account
    try:
        tenant = await conn.fetchval("SELECT tenant_code FROM tenants ORDER BY tenant_code LIMIT 1")
        assert tenant, "A migrated local tenant is required"
        await conn.execute("""INSERT INTO platform_accounts (account_id, account_code, account_name, account_type, status, operating_jurisdiction_code, legal_organisation_name)
            VALUES ($1::uuid, $2, 'TASK-464 rollback proof', 'ORGANISATION', 'ACTIVE', 'ZA', 'TASK-464 proof organisation')""", account, external)
        link = await conn.fetchval("""INSERT INTO platform_account_tenants (account_id, tenant_code, relationship_type, status)
            VALUES ($1::uuid, $2, 'OPERATOR', 'ACTIVE') RETURNING account_tenant_id""", account, tenant)
        await conn.execute("""INSERT INTO platform_external_tenant_refs (account_id, account_tenant_id, tenant_code, ref_type, external_ref, status)
            VALUES ($1::uuid, $2, $3, 'external_tenant_ref', $4, 'ACTIVE')""", account, link, tenant, external)
        user = await conn.fetchval("INSERT INTO platform_users (subject, display_name, status) VALUES ($1, 'Proof owner', 'ACTIVE') RETURNING user_id", external)
        owner = await conn.fetchval("""INSERT INTO platform_memberships (account_id, user_id, role_family, permission_set, status)
            VALUES ($1::uuid, $2, 'DISTRIBUTION_ADMIN', 'REFERRAL_SAAS_ACCOUNT_ADMIN', 'ACTIVE') RETURNING membership_id""", account, user)
        for code in SOLUTION_PACKAGES:
            args = dict(account_ref=account, plan_code=code, plan_name="Untrusted label", contract_source="SIGNED_ORDER_FORM",
                entitlement_reference="ORDER-464", effective_from="2020-01-01", effective_until=None,
                responsible_owner=str(owner), actor_ref="TASK-464-PROOF", actor_role="ADMIN", correlation_id=external,
                idempotency_key_hash=external + code, command_payload_hash=code)
            first = await svc.record_referral_saas_commercial_entitlement(**args)
            replay = await svc.record_referral_saas_commercial_entitlement(**args)
            assert replay["idempotencyStatus"] == "REPLAYED" and first["auditEventId"] == replay["auditEventId"]
            ctx = await svc.resolve_setup_account_by_external_reference(ref_type="external_tenant_ref", external_ref=external)
            projection = svc.build_referral_saas_commercial_entitlement_projection(account_context=ctx).to_safe_dict()
            assert projection["launchAllowed"] and projection["solutionPackage"]["code"] == code
            assert projection["plan"]["planName"] == SOLUTION_PACKAGES[code]["name"]
        assert await conn.fetchval("SELECT count(*) FROM platform_account_audit_events WHERE account_id = $1::uuid", account) == 3
        await conn.execute("UPDATE platform_memberships SET status = 'SUSPENDED' WHERE membership_id = $1", owner)
        ctx = await svc.resolve_setup_account_by_external_reference(ref_type="external_tenant_ref", external_ref=external)
        assert not svc.build_referral_saas_commercial_entitlement_projection(account_context=ctx).launch_allowed
        print(json.dumps({"packages": 3, "auditEvents": 3, "replay": "passed", "ownerRevocation": "blocked", "rollback": "required"}))
    finally:
        svc.db_connection = original
        await transaction.rollback()
        assert await conn.fetchval("SELECT count(*) FROM platform_accounts WHERE account_id = $1::uuid", account) == 0
        await conn.close()
    print("PASS: PostgreSQL proof rolled back; no retained test accounts or audit records.")


if __name__ == "__main__":
    asyncio.run(main())
