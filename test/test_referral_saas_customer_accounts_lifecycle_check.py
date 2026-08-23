from __future__ import annotations

from argparse import Namespace

from scripts import referral_saas_customer_accounts_lifecycle_check as lifecycle
from scripts.referral_saas_account_create_physical_check import ApiResult


def test_customers_rejects_invalid_collection() -> None:
    try:
        lifecycle._customers({"portfolio": {"customers": "unsafe"}})
    except RuntimeError as exc:
        assert "invalid customer collection" in str(exc)
    else:
        raise AssertionError("Invalid portfolio collection was accepted.")


def test_lifecycle_proves_discovery_replay_conflict_and_cleanup(monkeypatch) -> None:
    account_id = "389eb0e5-7f27-4ed8-812f-d670f3a34cba"
    get_results = iter([
        ApiResult(200, {"portfolio": {"customers": []}}),
        ApiResult(200, {
            "noCrossJurisdictionAccessConfirmed": True,
            "portfolio": {"customers": [{
                "accountRef": account_id,
                "destination": f"/admin/referral-saas/account-maintenance/{account_id}",
            }]},
        }),
    ])
    post_results = iter([
        ApiResult(200, {"account": {"accountId": account_id}}),
        ApiResult(200, {"account": {"accountId": account_id}}),
        ApiResult(409, {"detail": {"code": "DUPLICATE_EXTERNAL_REFERENCE"}}),
    ])
    cleanup_calls: list[tuple[str, str]] = []

    async def seed(**_kwargs):
        return {"draft_ref": "draft"}

    async def verify(**_kwargs):
        return {"account_count": 1, "external_ref_count": 2, "creation_audit_count": 1}

    async def cleanup(*, dsn: str, account_id: str, draft_ref: str, tenant_code: str):
        cleanup_calls.append((account_id, draft_ref))
        assert tenant_code == "FNB"

    monkeypatch.setattr(lifecycle, "get_json", lambda **_kwargs: next(get_results))
    monkeypatch.setattr(lifecycle, "post_json", lambda **_kwargs: next(post_results))
    monkeypatch.setattr(lifecycle, "seed_ready_for_review_draft_db", seed)
    monkeypatch.setattr(lifecycle, "verify_lifecycle_evidence", verify)
    monkeypatch.setattr(lifecycle, "cleanup_fixture", cleanup)

    result = lifecycle.run(Namespace(
        db_dsn="postgresql://local/referrals",
        suffix="proof",
        base_url="http://127.0.0.1:8000",
        admin_key="test-admin-key",
        internal_tenant_code="FNB",
    ))

    assert result["status"] == "passed"
    assert result["idempotentReplayConfirmed"] is True
    assert result["duplicateConflictConfirmed"] is True
    assert result["permissionScopedPortfolioConfirmed"] is True
    assert cleanup_calls == [(account_id, "draft_task_448_proof")]


def test_lifecycle_requires_database_for_authoritative_cleanup() -> None:
    args = Namespace(
        db_dsn=None,
        suffix="proof",
        base_url="http://127.0.0.1:8000",
        admin_key="test-admin-key",
        internal_tenant_code="FNB",
    )
    try:
        lifecycle.run(args)
    except RuntimeError as exc:
        assert "requires --db-dsn" in str(exc)
    else:
        raise AssertionError("Lifecycle proof ran without an authoritative database.")