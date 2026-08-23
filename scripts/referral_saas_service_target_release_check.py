from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import asyncpg

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services.referral_saas_operational_service_clock_service import (
    apply_support_case_status_to_service_target_clock,
    change_service_target_pause_state,
    start_support_case_service_target_clock,
)
from services.referral_saas_operational_service_target_service import (
    create_service_target_policy,
    transition_service_target_policy,
)
from services.referral_saas_operations_service import read_referral_saas_operations
from utils import db


RUN_PREFIX = "TASK436_RELEASE_PROOF"
JURISDICTIONS = ("NA", "ZM")


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _evidence_key(run_ref: str, action: str) -> str:
    return _hash(f"{RUN_PREFIX}:{run_ref}:{action}")


def cleanup_statements() -> tuple[str, ...]:
    return (
        "DELETE FROM referral_saas_operational_service_target_audit WHERE correlation_id LIKE $1",
        "DELETE FROM referral_saas_operational_service_target_pause_events WHERE correlation_id LIKE $1",
        "DELETE FROM referral_saas_operational_service_target_clocks WHERE correlation_id LIKE $1",
        "DELETE FROM referral_saas_support_cases WHERE correlation_id LIKE $1",
        "DELETE FROM referral_saas_operational_service_target_policies WHERE correlation_id LIKE $1",
        "DELETE FROM platform_accounts WHERE account_code LIKE $1",
        "DELETE FROM tenants WHERE tenant_code LIKE $1",
    )


async def _cleanup(conn: asyncpg.Connection, run_ref: str) -> None:
    patterns = (
        f"{RUN_PREFIX}:{run_ref}%",
        f"{RUN_PREFIX}:{run_ref}%",
        f"{RUN_PREFIX}:{run_ref}%",
        f"{RUN_PREFIX}:{run_ref}%",
        f"{RUN_PREFIX}:{run_ref}%",
        f"T436_{run_ref}%",
        f"T436_{run_ref}%",
    )
    async with conn.transaction():
        for statement, pattern in zip(cleanup_statements(), patterns, strict=True):
            await conn.execute(statement, pattern)


async def _insert_fixture(
    conn: asyncpg.Connection,
    *,
    run_ref: str,
    jurisdiction: str,
    case_suffix: str,
    category: str,
    priority: str,
    now: datetime,
) -> tuple[str, str]:
    tenant_code = f"T436_{run_ref}_{jurisdiction}"
    account_id = uuid.uuid4()
    support_case_id = uuid.uuid4()
    correlation_id = f"{RUN_PREFIX}:{run_ref}:CASE:{jurisdiction}:{case_suffix}"
    await conn.execute(
        "INSERT INTO tenants (tenant_code, tenant_name, industry) VALUES ($1, $2, 'test') ON CONFLICT DO NOTHING",
        tenant_code,
        f"TASK-436 {jurisdiction}",
    )
    await conn.execute(
        """
        INSERT INTO platform_accounts (
            account_id, account_code, account_name, legal_organisation_name,
            trading_name, registration_number, account_type, status,
            onboarding_status, operating_jurisdiction_code, created_by_ref, updated_by_ref
        ) VALUES ($1, $2, $3, $3, $3, $4, 'ORGANISATION', 'ACTIVE', 'APPROVED', $5, $6, $6)
        """,
        account_id,
        f"T436_{run_ref}_{jurisdiction}_{case_suffix}",
        f"TASK-436 {jurisdiction} {case_suffix}",
        f"T436-{run_ref}-{jurisdiction}-{case_suffix}",
        jurisdiction,
        RUN_PREFIX,
    )
    await conn.execute(
        """
        INSERT INTO referral_saas_support_cases (
            support_case_id, account_id, tenant_code, category, priority, status,
            title, summary, source_surface, correlation_id, idempotency_key_hash,
            request_payload_hash, created_by_ref, created_by_role, updated_by_ref,
            created_at, updated_at
        ) VALUES ($1, $2, $3, $4, $5, 'OPEN', $6, $7, 'TASK_436_RELEASE_PROOF',
                  $8, $9, $10, $11, 'AMPLIFI_ADMIN', $11, $12, $12)
        """,
        support_case_id,
        account_id,
        tenant_code,
        category,
        priority,
        f"TASK-436 {jurisdiction} {case_suffix}",
        "Temporary release-proof evidence; removed after verification.",
        correlation_id,
        _evidence_key(run_ref, f"case:{jurisdiction}:{case_suffix}"),
        _hash(json.dumps({"jurisdiction": jurisdiction, "case": case_suffix}, sort_keys=True)),
        RUN_PREFIX,
        now,
    )
    return str(account_id), str(support_case_id)


async def _approve_policy(*, run_ref: str, jurisdiction: str, now: datetime) -> str:
    correlation = f"{RUN_PREFIX}:{run_ref}:POLICY:{jurisdiction}"
    policy, create_result = await create_service_target_policy(
        policy_code=f"T436_{run_ref}_{jurisdiction}",
        operating_jurisdiction_code=jurisdiction,
        work_type="SUPPORT_CASE",
        work_category="MANUAL_REVIEW_REQUIRED",
        priority="HIGH",
        business_timezone="UTC",
        target_duration_minutes=60,
        warning_threshold_minutes=15,
        start_event="SUPPORT_CASE_CREATED",
        completion_event="SUPPORT_CASE_RESOLVED",
        effective_from=now - timedelta(days=1),
        effective_to=now + timedelta(days=1),
        approved_pause_reasons=["CUSTOMER_RESPONSE_PENDING"],
        business_calendar_ref=None,
        metadata={"releaseProof": "TASK-436"},
        actor_ref="task-436-author",
        actor_role="AMPLIFI_ADMIN",
        correlation_id=correlation,
        idempotency_key_hash=_evidence_key(run_ref, f"policy-create:{jurisdiction}"),
        request_payload_hash=_evidence_key(run_ref, f"policy-payload:{jurisdiction}"),
    )
    assert create_result == "NEW_REQUEST"
    for action, actor in (("SUBMIT_REVIEW", "task-436-author"), ("APPROVE", "task-436-reviewer")):
        policy, result = await transition_service_target_policy(
            policy_ref=policy.policy_id,
            action=action,
            reason="TASK-436 PostgreSQL release proof",
            actor_ref=actor,
            actor_role="AMPLIFI_ADMIN",
            correlation_id=correlation,
            idempotency_key_hash=_evidence_key(run_ref, f"policy-{action}:{jurisdiction}"),
            request_payload_hash=_evidence_key(run_ref, f"policy-{action}-payload:{jurisdiction}"),
        )
        assert result == "NEW_REQUEST"
    assert policy.lifecycle_status == "APPROVED"
    return policy.policy_id


async def run_release_check(dsn: str) -> dict[str, object]:
    run_ref = uuid.uuid4().hex[:10].upper()
    now = datetime.now(timezone.utc).replace(microsecond=0)
    db.APP_DB_DSN = dsn
    fixture_conn = await asyncpg.connect(dsn)
    try:
        await _cleanup(fixture_conn, run_ref)
        na_account, na_case = await _insert_fixture(
            fixture_conn, run_ref=run_ref, jurisdiction="NA", case_suffix="OPEN",
            category="MANUAL_REVIEW_REQUIRED", priority="HIGH", now=now - timedelta(minutes=8),
        )
        na_complete_account, na_complete_case = await _insert_fixture(
            fixture_conn, run_ref=run_ref, jurisdiction="NA", case_suffix="COMPLETE",
            category="MANUAL_REVIEW_REQUIRED", priority="HIGH", now=now - timedelta(minutes=20),
        )
        na_unavailable_account, na_unavailable_case = await _insert_fixture(
            fixture_conn, run_ref=run_ref, jurisdiction="NA", case_suffix="UNAVAILABLE",
            category="INTEGRATION_HEALTH", priority="HIGH", now=now - timedelta(minutes=3),
        )
        zm_account, zm_case = await _insert_fixture(
            fixture_conn, run_ref=run_ref, jurisdiction="ZM", case_suffix="OPEN",
            category="MANUAL_REVIEW_REQUIRED", priority="HIGH", now=now - timedelta(minutes=6),
        )

        await _approve_policy(run_ref=run_ref, jurisdiction="NA", now=now)
        await _approve_policy(run_ref=run_ref, jurisdiction="ZM", now=now)

        async def start(account_id: str, case_id: str, jurisdiction: str, suffix: str, at: datetime):
            return await start_support_case_service_target_clock(
                account_id=account_id, support_case_id=case_id,
                operating_jurisdiction_code=jurisdiction,
                work_category="MANUAL_REVIEW_REQUIRED", priority="HIGH", started_at=at,
                actor_ref=RUN_PREFIX, actor_role="AMPLIFI_ADMIN",
                correlation_id=f"{RUN_PREFIX}:{run_ref}:CLOCK:{suffix}",
                idempotency_key_hash=_evidence_key(run_ref, f"clock:{suffix}"),
                request_payload_hash=_evidence_key(run_ref, f"clock-payload:{suffix}"),
            )

        na_clock, na_started = await start(na_account, na_case, "NA", "NA_OPEN", now - timedelta(minutes=8))
        complete_clock, complete_started = await start(
            na_complete_account, na_complete_case, "NA", "NA_COMPLETE", now - timedelta(minutes=20)
        )
        zm_clock, zm_started = await start(zm_account, zm_case, "ZM", "ZM_OPEN", now - timedelta(minutes=6))
        unavailable_clock, unavailable_result = await start_support_case_service_target_clock(
            account_id=na_unavailable_account, support_case_id=na_unavailable_case,
            operating_jurisdiction_code="NA", work_category="INTEGRATION_HEALTH",
            priority="HIGH", started_at=now - timedelta(minutes=3), actor_ref=RUN_PREFIX,
            actor_role="AMPLIFI_ADMIN", correlation_id=f"{RUN_PREFIX}:{run_ref}:CLOCK:UNAVAILABLE",
            idempotency_key_hash=_evidence_key(run_ref, "clock:unavailable"),
            request_payload_hash=_evidence_key(run_ref, "clock-payload:unavailable"),
        )
        assert (na_started, complete_started, zm_started) == ("CLOCK_STARTED",) * 3
        assert na_clock and complete_clock and zm_clock
        assert unavailable_clock is None and unavailable_result == "POLICY_UNAVAILABLE"

        replay_clock, replay_result = await start(na_account, na_case, "NA", "NA_OPEN", now - timedelta(minutes=8))
        assert replay_clock and replay_clock.clock_id == na_clock.clock_id
        assert replay_result == "CLOCK_REPLAYED"

        paused, pause_result = await change_service_target_pause_state(
            account_id=na_account, support_case_id=na_case, action="PAUSE",
            pause_reason_code="CUSTOMER_RESPONSE_PENDING", event_at=now - timedelta(minutes=6),
            actor_ref=RUN_PREFIX, actor_role="AMPLIFI_ADMIN",
            correlation_id=f"{RUN_PREFIX}:{run_ref}:PAUSE",
            idempotency_key_hash=_evidence_key(run_ref, "pause"),
            request_payload_hash=_evidence_key(run_ref, "pause-payload"),
        )
        resumed, resume_result = await change_service_target_pause_state(
            account_id=na_account, support_case_id=na_case, action="RESUME",
            pause_reason_code="CUSTOMER_RESPONSE_PENDING", event_at=now - timedelta(minutes=5),
            actor_ref=RUN_PREFIX, actor_role="AMPLIFI_ADMIN",
            correlation_id=f"{RUN_PREFIX}:{run_ref}:RESUME",
            idempotency_key_hash=_evidence_key(run_ref, "resume"),
            request_payload_hash=_evidence_key(run_ref, "resume-payload"),
        )
        assert pause_result == "CLOCK_PAUSED" and paused.clock_status == "PAUSED"
        assert resume_result == "CLOCK_RESUMED" and resumed.accumulated_paused_seconds == 60

        completed, completion_result = await apply_support_case_status_to_service_target_clock(
            account_id=na_complete_account, support_case_id=na_complete_case,
            from_status="OPEN", to_status="RESOLVED", changed_at=now,
            actor_ref=RUN_PREFIX, actor_role="AMPLIFI_ADMIN",
            correlation_id=f"{RUN_PREFIX}:{run_ref}:COMPLETE",
            idempotency_key_hash=_evidence_key(run_ref, "complete"),
            request_payload_hash=_evidence_key(run_ref, "complete-payload"),
        )
        assert completed and completed.completion_outcome == "WITHIN_TARGET"
        assert completion_result == "CLOCK_COMPLETED"
        await fixture_conn.execute(
            "UPDATE referral_saas_support_cases SET status='RESOLVED', closed_at=$2, updated_at=$2 WHERE support_case_id=$1",
            uuid.UUID(na_complete_case), now,
        )

        na_operations = (await read_referral_saas_operations(jurisdictions=["NA"], limit=20)).to_safe_dict()
        zm_operations = (await read_referral_saas_operations(jurisdictions=["ZM"], limit=20)).to_safe_dict()
        na_refs = {item["workItemRef"] for item in na_operations["workItems"]}
        zm_refs = {item["workItemRef"] for item in zm_operations["workItems"]}
        assert na_case in na_refs and na_unavailable_case in na_refs and zm_case not in na_refs
        assert zm_case in zm_refs and na_case not in zm_refs
        assert na_operations["metrics"]["withinServiceTargetPercent"] == 100
        assert na_operations["metrics"]["serviceTargetEvidence"]["eligibleCount"] == 1
        unavailable_item = next(item for item in na_operations["workItems"] if item["workItemRef"] == na_unavailable_case)
        assert unavailable_item["serviceTarget"]["status"] == "UNAVAILABLE"

        audit_count = await fixture_conn.fetchval(
            "SELECT COUNT(*) FROM referral_saas_operational_service_target_audit WHERE correlation_id LIKE $1",
            f"{RUN_PREFIX}:{run_ref}%",
        )
        assert audit_count >= 10
        return {
            "status": "PASS",
            "runRef": run_ref,
            "jurisdictions": list(JURISDICTIONS),
            "withinServiceTargetPercent": 100,
            "unsupportedEvidence": "UNAVAILABLE",
            "crossJurisdictionLeakage": False,
            "auditRecords": audit_count,
        }
    finally:
        await db.close_async_pool()
        await _cleanup(fixture_conn, run_ref)
        remaining = await fixture_conn.fetchval(
            "SELECT COUNT(*) FROM platform_accounts WHERE account_code LIKE $1", f"T436_{run_ref}%"
        )
        await fixture_conn.close()
        if remaining:
            raise RuntimeError("TASK-436 temporary account evidence was not removed.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify Referral SaaS service targets against PostgreSQL.")
    parser.add_argument("--db-dsn", default=os.environ.get("APP_DB_DSN"))
    args = parser.parse_args()
    if not args.db_dsn:
        parser.error("--db-dsn or APP_DB_DSN is required")
    result = asyncio.run(run_release_check(args.db_dsn))
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
