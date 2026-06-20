from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager

from services import journey_orchestrator as jo


class FakeTransaction:
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False


class FakeConnection:
    def __init__(self):
        self.rewards = []
        self.instance = {
            "tenant_code": "FNB",
            "referral_track_id": "track-1",
            "referrer_ucn": "111",
            "product": "Transactional",
            "sub_product": "DDA13",
            "status": "VALIDATED",
            "journey_code": "BANKING_TRANSACTIONAL",
            "journey_version": "v1",
            "referee_ucn": None,
            "referee_ucn_hash": None,
            "referee_account_number": None,
            "referee_account_hash": None,
            "referee_account_masked": None,
            "referee_alias": None,
            "referee_alias_normalized": None,
            "ucn_captured_at": None,
            "account_opened_at": None,
            "account_activated_at": None,
            "funded_at": None,
            "debit_order_switched_at": None,
            "salary_switched_at": None,
            "first_transaction_completed_at": None,
            "progress_percent": None,
            "progress_band": None,
            "display_status": None,
            "next_milestone": None,
            "is_complete": False,
            "completed_at": None,
            "updated_at": None,
        }

    def transaction(self):
        return FakeTransaction()

    async def fetchrow(self, sql, *params):
        return dict(self.instance)

    async def execute(self, sql, *params):
        sql_clean = " ".join(sql.split())

        if "UPDATE referral_instances" not in sql_clean:
            return "OK"

        keys = [
            "status",
            "journey_code",
            "journey_version",
            "referee_ucn",
            "referee_ucn_hash",
            "referee_account_number",
            "referee_account_hash",
            "referee_account_masked",
            "referee_alias",
            "referee_alias_normalized",
            "ucn_captured_at",
            "account_opened_at",
            "account_activated_at",
            "funded_at",
            "debit_order_switched_at",
            "salary_switched_at",
            "first_transaction_completed_at",
            "progress_percent",
            "progress_band",
            "display_status",
            "next_milestone",
            "is_complete",
            "completed_at",
        ]

        for index, key in enumerate(keys):
            self.instance[key] = params[index]

        return "UPDATE 1"


def _patch_common(monkeypatch, conn):
    @asynccontextmanager
    async def fake_db_connection():
        yield conn

    monkeypatch.setattr(jo, "db_connection", fake_db_connection)

    async def fake_audit(**kwargs):
        return None

    async def fake_publish(**kwargs):
        return None

    async def fake_badges(**kwargs):
        return None

    async def fake_missions(referral_track_id, tenant_code=None, event_type=None):
        return []

    monkeypatch.setattr(jo, "_write_processing_audit_async", fake_audit)
    monkeypatch.setattr(jo, "_publish_leaderboard_rebuild", fake_publish)
    monkeypatch.setattr(jo, "_issue_badges_async", fake_badges)
    monkeypatch.setattr(jo, "apply_event_to_missions", fake_missions)


def _emit(event_type):
    payload = {
        "eventType": "REFERRAL_PROGRESS_RECORDED",
        "progressEventType": event_type,
        "tenantCode": "FNB",
        "referralTrackId": "track-1",
        "occurredAt": "2026-01-01T00:00:00Z",
        "deduped": False,
        "sourceSystem": "TEST",
    }

    asyncio.run(
        jo.handle_referral_progress_recorded(
            payload,
            tenant_code="FNB",
        )
    )


def test_rewards_trigger_on_completion(monkeypatch):
    conn = FakeConnection()
    _patch_common(monkeypatch, conn)

    def fake_issue(before, after):
        if after.get("is_complete") and not before.get("is_complete"):
            conn.rewards.append(("REFERRER", 100.0))

    monkeypatch.setattr(jo, "_issue_base_rewards_if_eligible", fake_issue)

    _emit("UCN_CAPTURED")
    _emit("ACCOUNT_OPENED")
    _emit("ACCOUNT_ACTIVATED")
    _emit("FUNDED")

    assert len(conn.rewards) == 0

    _emit("FIRST_TRANSACTION_COMPLETED")

    assert len(conn.rewards) >= 1


def test_rewards_are_idempotent(monkeypatch):
    conn = FakeConnection()
    _patch_common(monkeypatch, conn)

    def fake_issue(before, after):
        reward = ("REFERRER", 100.0)
        if (
            after.get("is_complete")
            and not before.get("is_complete")
            and reward not in conn.rewards
        ):
            conn.rewards.append(reward)

    monkeypatch.setattr(jo, "_issue_base_rewards_if_eligible", fake_issue)

    _emit("UCN_CAPTURED")
    _emit("ACCOUNT_OPENED")
    _emit("ACCOUNT_ACTIVATED")
    _emit("FUNDED")
    _emit("FIRST_TRANSACTION_COMPLETED")

    first = len(conn.rewards)

    _emit("FIRST_TRANSACTION_COMPLETED")

    second = len(conn.rewards)

    assert first == second


def test_rewards_only_on_full_completion(monkeypatch):
    conn = FakeConnection()
    _patch_common(monkeypatch, conn)

    def fake_issue(before, after):
        if after.get("is_complete") and not before.get("is_complete"):
            conn.rewards.append(("REFERRER", 100.0))

    monkeypatch.setattr(jo, "_issue_base_rewards_if_eligible", fake_issue)

    _emit("UCN_CAPTURED")
    _emit("ACCOUNT_OPENED")
    _emit("ACCOUNT_ACTIVATED")
    _emit("FUNDED")

    assert len(conn.rewards) == 0

    _emit("FIRST_TRANSACTION_COMPLETED")

    assert len(conn.rewards) >= 1