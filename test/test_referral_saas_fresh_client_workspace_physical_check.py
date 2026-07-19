from __future__ import annotations

import argparse

import pytest

from scripts import referral_saas_fresh_client_workspace_physical_check as script


def test_build_local_tenant_seed_code_is_stable_and_bounded():
    assert script.build_local_tenant_seed_code("local-230") == "TASK230LOCAL230"
    assert script.build_local_tenant_seed_code("TASK230ABC") == "TASK230ABC"
    assert len(script.build_local_tenant_seed_code("x" * 100)) == 48

    with pytest.raises(RuntimeError, match="non-empty suffix"):
        script.build_local_tenant_seed_code("---")


@pytest.mark.asyncio
async def test_ensure_local_unlinked_tenant_seed_inserts_seed(monkeypatch):
    class FakeConnection:
        def __init__(self):
            self.calls = []

        async def fetchrow(self, sql, *params):
            self.calls.append((sql, params))
            if "FROM platform_account_tenants" in sql:
                return None
            return {
                "tenant_code": "TASK230LOCAL",
                "tenant_name": "Task 230 Local",
                "industry": "Referral management and campaign attribution",
                "is_active": True,
            }

        async def close(self):
            self.calls.append(("close", ()))

    conn = FakeConnection()

    class FakeAsyncpg:
        @staticmethod
        async def connect(dsn):
            assert dsn == "postgresql://user:pass@localhost:5432/referrals"
            return conn

    monkeypatch.setitem(__import__("sys").modules, "asyncpg", FakeAsyncpg)

    result = await script.ensure_local_unlinked_tenant_seed(
        dsn="postgresql://user:pass@localhost:5432/referrals",
        tenant_code="TASK230LOCAL",
        tenant_name="Task 230 Local",
        industry="Referral management and campaign attribution",
    )

    assert result == {
        "tenant_code": "TASK230LOCAL",
        "tenant_name": "Task 230 Local",
        "industry": "Referral management and campaign attribution",
        "is_active": True,
        "owner_link_status": "UNLINKED",
    }
    assert any("INSERT INTO tenants" in str(call[0]) for call in conn.calls)


@pytest.mark.asyncio
async def test_ensure_local_unlinked_tenant_seed_rejects_owner_link(monkeypatch):
    class FakeConnection:
        async def fetchrow(self, sql, *params):
            if "FROM platform_account_tenants" in sql:
                return {"account_tenant_id": "linked", "account_id": "acct", "status": "ACTIVE"}
            raise AssertionError("insert should not run")

        async def close(self):
            return None

    class FakeAsyncpg:
        @staticmethod
        async def connect(dsn):
            return FakeConnection()

    monkeypatch.setitem(__import__("sys").modules, "asyncpg", FakeAsyncpg)

    with pytest.raises(RuntimeError, match="already attached"):
        await script.ensure_local_unlinked_tenant_seed(
            dsn="postgresql://user:pass@localhost:5432/referrals",
            tenant_code="TASK230LOCAL",
            tenant_name="Task 230 Local",
            industry="Referral management and campaign attribution",
        )


def test_run_prepares_seed_then_runs_fresh_client_workspace_proof(monkeypatch):
    captured: dict[str, object] = {}

    async def fake_ensure_local_unlinked_tenant_seed(**kwargs):
        captured["seed_kwargs"] = kwargs
        return {
            "tenant_code": kwargs["tenant_code"],
            "tenant_name": kwargs["tenant_name"],
            "industry": kwargs["industry"],
            "is_active": True,
            "owner_link_status": "UNLINKED",
        }

    def fake_workspace_run(args: argparse.Namespace):
        captured["workspace_args"] = args
        return {
            "status": "passed",
            "account_setup_creation_mode": "created_client",
            "created_account": {"accountId": "acct-task-230"},
            "selected_client": {"accountId": "acct-task-230"},
            "readiness_status": "GO_LIVE_DISABLED",
            "readiness_summary": {"blocked_count": 1},
            "client_workspace_routes": script.workspace_check.CLIENT_WORKSPACE_ROUTES,
            "no_profile_update": True,
            "no_invitation_delivery": True,
            "no_campaign_activation": True,
            "no_go_live": True,
            "no_money_movement": True,
        }

    monkeypatch.setattr(script, "ensure_local_unlinked_tenant_seed", fake_ensure_local_unlinked_tenant_seed)
    monkeypatch.setattr(script.workspace_check, "run", fake_workspace_run)

    result = script.run(
        script.parse_args(
            [
                "--db-dsn",
                "postgresql://user:pass@localhost:5432/referrals",
                "--suffix",
                "local-230",
            ]
        )
    )

    assert result["status"] == "passed"
    assert result["task"] == "TASK-230"
    assert result["tenant_seed"]["tenant_code"] == "TASK230LOCAL230"
    workspace_args = captured["workspace_args"]
    assert isinstance(workspace_args, argparse.Namespace)
    assert workspace_args.internal_tenant_code == "TASK230LOCAL230"
    assert workspace_args.reuse_existing_client is False
    assert result["no_money_movement"] is True


def test_run_requires_db_dsn(monkeypatch):
    monkeypatch.delenv("APP_DB_DSN", raising=False)

    with pytest.raises(RuntimeError, match="APP_DB_DSN"):
        script.run(script.parse_args(["--suffix", "local-230"]))
