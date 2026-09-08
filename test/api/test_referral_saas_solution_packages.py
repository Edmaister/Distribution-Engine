from contextlib import asynccontextmanager
from datetime import date
import json
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from services import referral_saas_solution_packages as packages
from services import referral_saas_account_foundation_service as svc
from apps.api.main import app  # Initializes the API test configuration.
from apps.api.routers.referral_saas_accounts import _assert_account_path_scope


def evidence(code=packages.COMBINED, **changes):
    value = dict(plan_code=code, contract_source="SIGNED_ORDER_FORM", entitlement_reference="ORDER-464",
                 responsible_owner="owner-464", effective_from="2020-01-01", effective_until=None)
    return {**value, **changes}


@pytest.mark.parametrize("code,referrals,attribution", [
    (packages.REFERRAL_MANAGEMENT, True, False), (packages.CAMPAIGN_ATTRIBUTION, False, True),
    (packages.COMBINED, True, True),
])
def test_packages_compose_without_cross_granting(code, referrals, attribution):
    value = evidence(code)
    assert packages.solution_access_allowed(value, packages.REFERRAL_MANAGEMENT) is referrals
    assert packages.solution_access_allowed(value, packages.CAMPAIGN_ATTRIBUTION) is attribution
    account = SimpleNamespace(account_id="a", account_code="A", commercial_owner_active=True, account_metadata={"referral_saas_commercial_entitlement": value})
    for solution, allowed in [(packages.REFERRAL_MANAGEMENT, referrals), (packages.CAMPAIGN_ATTRIBUTION, attribution)]:
        if allowed:
            assert _assert_account_path_scope("a", account, solution) == "a"
        else:
            with pytest.raises(HTTPException) as rejected:
                _assert_account_path_scope("a", account, solution)
            assert rejected.value.status_code == 403


@pytest.mark.parametrize("changes", [
    {"plan_code": "REFERRAL_SAAS_H1_STANDARD"}, {"plan_code": "UNKNOWN"},
    {"effective_from": "2099-01-01"}, {"effective_until": "2020-01-02"},
    {"effective_from": "bad"}, {"effective_until": "bad"},
    {"responsible_owner": ""}, {"entitlement_reference": ""}, {"contract_source": "OTHER"},
])
def test_invalid_or_delayed_evidence_fails_closed(changes):
    assert not packages.evidence_is_current(evidence(**changes), date(2026, 9, 8))


def test_effective_window_is_inclusive():
    value = evidence(effective_from="2026-09-08", effective_until="2026-09-08")
    assert packages.evidence_is_current(value, date(2026, 9, 8))
    assert not packages.evidence_is_current(value, date(2026, 9, 9))


class Connection:
    def __init__(self, owner=True):
        self.owner = owner
        self.saved = None
        self.writes = 0
        self.queries = []
    @asynccontextmanager
    async def transaction(self):
        yield
    async def fetchrow(self, sql, *args):
        self.queries.append(sql)
        if "FROM platform_accounts" in sql:
            return {"account_id": "a", "status": "ACTIVE", "metadata": {}}
        if "FROM platform_account_audit_events" in sql:
            return {"account_audit_event_id": "audit", "evidence_summary": self.saved} if self.saved else None
        if "FROM platform_memberships" in sql:
            return {"membership_id": "owner"} if self.owner else None
        if "INSERT INTO platform_account_audit_events" in sql:
            self.saved = json.loads(args[-2])
            return {"account_audit_event_id": "audit"}
        raise AssertionError(sql)
    async def execute(self, sql, *args):
        self.writes += 1


def patch_connection(monkeypatch, conn):
    @asynccontextmanager
    async def db():
        yield conn
    monkeypatch.setattr(svc, "db_connection", db)


def command(**changes):
    return dict(account_ref="a", plan_code=packages.COMBINED, plan_name="Caller cannot rename catalogue",
                contract_source="SIGNED_ORDER_FORM", entitlement_reference="ORDER-464", effective_from="2020-01-01",
                effective_until=None, responsible_owner="owner", actor_ref="admin", actor_role="ADMIN",
                correlation_id="corr", idempotency_key_hash="key", command_payload_hash="payload", **changes)


@pytest.mark.asyncio
async def test_save_replay_and_conflict_are_atomic_and_redacted(monkeypatch):
    conn = Connection()
    patch_connection(monkeypatch, conn)
    saved = await svc.record_referral_saas_commercial_entitlement(**command())
    replay = await svc.record_referral_saas_commercial_entitlement(**command())
    assert saved["auditEventId"] == replay["auditEventId"]
    assert replay["idempotencyStatus"] == "REPLAYED"
    assert conn.writes == 1
    assert "FOR UPDATE" in conn.queries[0]
    assert saved["evidence"]["plan_name"] == packages.SOLUTION_PACKAGES[packages.COMBINED]["name"]
    assert "command_payload_hash" not in replay["evidence"]
    changed = command(); changed["command_payload_hash"] = "different"
    with pytest.raises(svc.CommercialEntitlementIdempotencyConflict):
        await svc.record_referral_saas_commercial_entitlement(**changed)
    assert conn.writes == 1


@pytest.mark.asyncio
async def test_owner_must_be_active_and_scoped_before_write(monkeypatch):
    conn = Connection(owner=False)
    patch_connection(monkeypatch, conn)
    with pytest.raises(svc.CommercialEntitlementValidationError):
        await svc.record_referral_saas_commercial_entitlement(**command())
    assert conn.writes == 0
    owner_query = next(q for q in conn.queries if "FROM platform_memberships" in q)
    assert "account_id = $1" in owner_query and "status = 'ACTIVE'" in owner_query


@pytest.mark.asyncio
async def test_partner_cannot_record_evidence(monkeypatch):
    conn = Connection(); patch_connection(monkeypatch, conn)
    args = command(); args["actor_role"] = "PARTNER"
    with pytest.raises(svc.CommercialEntitlementPermissionDenied):
        await svc.record_referral_saas_commercial_entitlement(**args)
    assert not conn.queries


@pytest.mark.asyncio
@pytest.mark.parametrize("code,path", [
    (packages.REFERRAL_MANAGEMENT, "campaign-attribution"),
    (packages.CAMPAIGN_ATTRIBUTION, "campaigns"),
    (packages.CAMPAIGN_ATTRIBUTION, "referrals"),
])
async def test_customer_api_rejects_other_package(monkeypatch, code, path):
    from httpx import AsyncClient
    from apps.api.routers import referral_saas_accounts as api
    account = SimpleNamespace(account_id="a", account_code="A", account_metadata={"referral_saas_commercial_entitlement": evidence(code)}, commercial_owner_active=True)
    async def resolve(**kwargs):
        return "setup", account
    monkeypatch.setattr(api, "_resolve_referral_saas_account_context", resolve)
    async with AsyncClient(app=app, base_url="http://test", headers={"x-api-key": "test-admin-key"}) as client:
        result = await client.get(f"/v1/referral-saas/accounts/a/{path}", params={"ref_type": "external_tenant_ref", "external_ref": "customer"})
    assert result.status_code == 403
    assert result.json()["detail"]["code"] == "SOLUTION_PACKAGE_NOT_ENTITLED"
