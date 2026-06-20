from __future__ import annotations

import builtins
import importlib
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from decimal import Decimal

import pytest

import services.reward_service as rs


class FakeTx:
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False


class FakeConn:
    def __init__(self, row=None, rows=None, execute_result="INSERT 0 1", fail_execute=False):
        self.row = row
        self.rows = rows or []
        self.execute_result = execute_result
        self.fail_execute = fail_execute
        self.calls = []

    async def execute(self, query, *params):
        if self.fail_execute:
            raise RuntimeError("db failed")
        self.calls.append(("execute", query, params))
        return self.execute_result

    async def fetchrow(self, query, *params):
        self.calls.append(("fetchrow", query, params))
        return self.row

    async def fetch(self, query, *params):
        self.calls.append(("fetch", query, params))
        return self.rows

    def transaction(self):
        return FakeTx()


def reward_row(
    reward_id=1,
    tenant_code="FNB",
    referral_track_id="track-1",
    beneficiary_type="REFERRER",
    beneficiary_ref="123",
    product="Transactional",
    sub_product="DDA",
    reward_type="CASH",
    amount=Decimal("100.00"),
    status="APPLIED",
    created_at=None,
    reward_source="BASE",
    mission_code=None,
):
    return {
        "id": reward_id,
        "tenant_code": tenant_code,
        "referral_track_id": referral_track_id,
        "beneficiary_type": beneficiary_type,
        "beneficiary_ref": beneficiary_ref,
        "product": product,
        "sub_product": sub_product,
        "reward_type": reward_type,
        "amount": amount,
        "status": status,
        "created_at": created_at or datetime(2026, 1, 1, tzinfo=timezone.utc),
        "reward_source": reward_source,
        "mission_code": mission_code,
    }


def patch_db(monkeypatch, conn):
    @asynccontextmanager
    async def fake_db_connection():
        yield conn

    monkeypatch.setattr(rs, "db_connection", fake_db_connection)


def valid_instruction(**overrides):
    data = {
        "tenant_code": "FNB",
        "referral_track_id": "track-1",
        "beneficiary_type": "REFERRER",
        "beneficiary_ref": "123",
        "product": "Transactional",
        "sub_product": "DDA",
        "reward_type": "CASH",
        "amount": Decimal("100"),
        "reward_source": "BASE",
        "mission_code": None,
        "status": "APPLIED",
    }
    data.update(overrides)
    return rs.RewardInstruction(**data)


def test_import_fallbacks_when_kafka_and_metrics_unavailable(monkeypatch):
    original_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name in {"utils.kafka", "utils.metrics"}:
            raise Exception("forced import failure")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    module = importlib.reload(rs)

    assert module.publish_event is None
    assert module.rewards_applied_inc is None

    monkeypatch.setattr(builtins, "__import__", original_import)
    importlib.reload(rs)


def test_quantize_amount_rounds_half_up():
    assert rs._quantize_amount(Decimal("10.126")) == Decimal("10.13")


@pytest.mark.parametrize(
    "field,value,error",
    [
        ("tenant_code", "", "tenant_code is required"),
        ("referral_track_id", "", "referral_track_id is required"),
        ("beneficiary_type", "BAD", "Invalid beneficiary_type"),
        ("beneficiary_ref", "", "beneficiary_ref is required"),
        ("product", "", "product is required"),
        ("reward_type", "", "reward_type is required"),
        ("reward_source", "BAD", "Invalid reward_source"),
        ("status", "BAD", "Invalid status"),
        ("amount", Decimal("0"), "amount must be > 0"),
    ],
)
def test_validate_instruction_all_invalid_paths(field, value, error):
    with pytest.raises(ValueError, match=error):
        rs._validate_instruction(valid_instruction(**{field: value}))


def test_validate_instruction_valid():
    rs._validate_instruction(valid_instruction())


def test_derive_business_key_is_stable():
    key1 = rs._derive_business_key("track-1", "REFERRER", "123", "Transactional", "CASH", "BASE", None)
    key2 = rs._derive_business_key("track-1", "REFERRER", "123", "Transactional", "CASH", "BASE", None)
    assert key1 == key2


def test_row_to_dict_with_datetime():
    result = rs._row_to_dict(reward_row())
    assert result["id"] == 1
    assert result["tenant_code"] == "FNB"
    assert result["amount"] == 100.0
    assert result["created_at"].startswith("2026-01-01")


def test_row_to_dict_with_string_created_at():
    result = rs._row_to_dict(reward_row(created_at="2026-01-01T00:00:00Z"))
    assert result["created_at"] == "2026-01-01T00:00:00Z"


@pytest.mark.asyncio
async def test_publish_reward_event_skips_when_publisher_missing(monkeypatch):
    monkeypatch.setattr(rs, "publish_event", None)
    await rs._publish_reward_applied_event({"id": 1})


@pytest.mark.asyncio
async def test_publish_reward_event_success(monkeypatch):
    captured = {}

    def fake_publish(topic, payload):
        captured["topic"] = topic
        captured["payload"] = payload

    monkeypatch.setattr(rs, "publish_event", fake_publish)

    await rs._publish_reward_applied_event({"id": 1})

    assert captured["topic"] == "reward.applied"
    assert captured["payload"]["event_type"] == "REWARD_APPLIED"
    assert captured["payload"]["version"] == 2


@pytest.mark.asyncio
async def test_publish_reward_event_failure_is_swallowed(monkeypatch):
    def fake_publish(*args, **kwargs):
        raise RuntimeError("broker down")

    monkeypatch.setattr(rs, "publish_event", fake_publish)
    await rs._publish_reward_applied_event({"id": 1})


@pytest.mark.asyncio
async def test_record_reward_metric_skips_when_missing(monkeypatch):
    monkeypatch.setattr(rs, "rewards_applied_inc", None)
    await rs._record_reward_metric({"product": "Transactional", "reward_type": "CASH"})


@pytest.mark.asyncio
async def test_record_reward_metric_success(monkeypatch):
    captured = {}

    def fake_metric(product, reward_type):
        captured["product"] = product
        captured["reward_type"] = reward_type

    monkeypatch.setattr(rs, "rewards_applied_inc", fake_metric)

    await rs._record_reward_metric({"product": "Transactional", "reward_type": "CASH"})

    assert captured == {"product": "Transactional", "reward_type": "CASH"}


@pytest.mark.asyncio
async def test_record_reward_metric_failure_is_swallowed(monkeypatch):
    def fake_metric(*args, **kwargs):
        raise RuntimeError("metric failed")

    monkeypatch.setattr(rs, "rewards_applied_inc", fake_metric)
    await rs._record_reward_metric({"product": "Transactional", "reward_type": "CASH"})


@pytest.mark.asyncio
async def test_apply_reward_base_success_inserted(monkeypatch):
    conn = FakeConn(row=reward_row(), execute_result="INSERT 0 1")
    patch_db(monkeypatch, conn)
    fulfilment_events = []
    
    async def fake_publish_reward_fulfilment_requested(**kwargs):
        fulfilment_events.append(kwargs)

    monkeypatch.setattr(rs, "publish_event", lambda *a, **k: None)
    monkeypatch.setattr(rs, "rewards_applied_inc", lambda *a, **k: None)
    monkeypatch.setattr(
        rs,
        "publish_reward_fulfilment_requested",
        fake_publish_reward_fulfilment_requested,
    )

    result = await rs.apply_reward(
        valid_instruction(
            journey_code="INSURANCE_POLICY",
            milestone_code="FIRST_PREMIUM_PAID",
        )
    )

    assert result["tenant_code"] == "FNB"
    assert result["referral_track_id"] == "track-1"
    assert result["amount"] == 100.0
    assert result["inserted"] is True
    assert result["business_key"]
    assert fulfilment_events[0]["journey_code"] == "INSURANCE_POLICY"
    assert fulfilment_events[0]["milestone_code"] == "FIRST_PREMIUM_PAID"


@pytest.mark.asyncio
async def test_apply_reward_base_success_not_inserted(monkeypatch):
    conn = FakeConn(row=reward_row(), execute_result="INSERT 0 0")
    patch_db(monkeypatch, conn)

    monkeypatch.setattr(rs, "publish_event", lambda *a, **k: None)
    monkeypatch.setattr(rs, "rewards_applied_inc", lambda *a, **k: None)

    result = await rs.apply_reward(valid_instruction())

    assert result["inserted"] is False


@pytest.mark.asyncio
async def test_apply_reward_mission_bonus_success(monkeypatch):
    conn = FakeConn(
        row=reward_row(
            reward_source="MISSION_BONUS",
            mission_code="M1",
            amount=Decimal("25.00"),
        )
    )
    patch_db(monkeypatch, conn)

    monkeypatch.setattr(rs, "publish_event", lambda *a, **k: None)
    monkeypatch.setattr(rs, "rewards_applied_inc", lambda *a, **k: None)

    result = await rs.apply_reward(
        valid_instruction(
            reward_source="MISSION_BONUS",
            mission_code="M1",
            amount=Decimal("25"),
        )
    )

    assert result["reward_source"] == "MISSION_BONUS"
    assert result["mission_code"] == "M1"
    assert result["amount"] == 25.0


@pytest.mark.asyncio
async def test_apply_reward_no_row_raises(monkeypatch):
    conn = FakeConn(row=None)
    patch_db(monkeypatch, conn)

    with pytest.raises(RuntimeError, match="Reward write/read failed"):
        await rs.apply_reward(valid_instruction())


@pytest.mark.asyncio
async def test_apply_reward_db_error_raises(monkeypatch):
    conn = FakeConn(fail_execute=True)
    patch_db(monkeypatch, conn)

    with pytest.raises(RuntimeError, match="db failed"):
        await rs.apply_reward(valid_instruction())


def test_build_base_reward_instructions_referrer_and_referee():
    referral = {
        "tenant_code": "FNB",
        "referral_track_id": "track-1",
        "product": "Transactional",
        "sub_product": "DDA",
        "journey_code": "INSURANCE_POLICY",
        "status": "FIRST_PREMIUM_PAID",
        "referrer_ucn": "111",
        "referee_ucn": "222",
    }

    policy = {
        "reward_type": "CASH",
        "referrer_reward_amount": 100,
        "allow_referee_reward": True,
        "referee_reward_amount": 50,
    }

    result = rs.build_base_reward_instructions(referral, policy)

    assert len(result) == 2
    assert result[0].beneficiary_type == "REFERRER"
    assert result[0].journey_code == "INSURANCE_POLICY"
    assert result[0].milestone_code == "FIRST_PREMIUM_PAID"
    assert result[1].beneficiary_type == "REFEREE"


def test_build_base_reward_instructions_uses_hashes_first():
    referral = {
        "tenant_code": "FNB",
        "referral_track_id": "track-1",
        "product": "Transactional",
        "sub_product": "DDA",
        "referrer_ucn": "111",
        "referee_ucn": "222",
        "referrer_ucn_hash": "hash-referrer",
        "referee_ucn_hash": "hash-referee",
    }

    policy = {
        "reward_type": "CASH",
        "referrer_reward_amount": 100,
        "allow_referee_reward": True,
        "referee_reward_amount": 50,
    }

    result = rs.build_base_reward_instructions(referral, policy)

    assert result[0].beneficiary_ref == "hash-referrer"
    assert result[1].beneficiary_ref == "hash-referee"


def test_build_base_reward_instructions_no_rewards_when_amounts_zero():
    referral = {
        "tenant_code": "FNB",
        "referral_track_id": "track-1",
        "product": "Transactional",
        "sub_product": "DDA",
        "referrer_ucn": "111",
        "referee_ucn": "222",
    }

    policy = {
        "reward_type": "CASH",
        "referrer_reward_amount": 0,
        "allow_referee_reward": True,
        "referee_reward_amount": 0,
    }

    assert rs.build_base_reward_instructions(referral, policy) == []


def test_build_base_reward_instructions_referee_not_allowed():
    referral = {
        "tenant_code": "FNB",
        "referral_track_id": "track-1",
        "product": "Transactional",
        "sub_product": "DDA",
        "referrer_ucn": "111",
        "referee_ucn": "222",
    }

    policy = {
        "reward_type": "CASH",
        "referrer_reward_amount": 100,
        "allow_referee_reward": False,
        "referee_reward_amount": 50,
    }

    result = rs.build_base_reward_instructions(referral, policy)

    assert len(result) == 1
    assert result[0].beneficiary_type == "REFERRER"


def test_build_base_reward_instructions_same_referrer_and_referee():
    referral = {
        "tenant_code": "FNB",
        "referral_track_id": "track-1",
        "product": "Transactional",
        "sub_product": "DDA",
        "referrer_ucn": "111",
        "referee_ucn": "111",
    }

    policy = {
        "reward_type": "CASH",
        "referrer_reward_amount": 100,
        "allow_referee_reward": True,
        "referee_reward_amount": 50,
    }

    result = rs.build_base_reward_instructions(referral, policy)

    assert len(result) == 1
    assert result[0].beneficiary_type == "REFERRER"


def test_build_mission_reward_instruction_default_status():
    inst = rs.build_mission_reward_instruction(
        tenant_code="FNB",
        referral_track_id="track-1",
        beneficiary_type="REFERRER",
        beneficiary_ref="123",
        product="Transactional",
        sub_product=None,
        reward_type="CASH",
        amount=Decimal("10"),
        mission_code="M1",
    )

    assert inst.reward_source == "MISSION_BONUS"
    assert inst.status == "APPLIED"


def test_build_mission_reward_instruction_custom_status():
    inst = rs.build_mission_reward_instruction(
        tenant_code="FNB",
        referral_track_id="track-1",
        beneficiary_type="REFERRER",
        beneficiary_ref="123",
        product="Transactional",
        sub_product=None,
        reward_type="CASH",
        amount=Decimal("10"),
        mission_code="M1",
        status="PENDING_FULFILMENT",
    )

    assert inst.status == "PENDING_FULFILMENT"


@pytest.mark.asyncio
async def test_get_reward_by_id_found(monkeypatch):
    conn = FakeConn(row=reward_row())
    patch_db(monkeypatch, conn)

    result = await rs.get_reward_by_id(1, "FNB")

    assert result is not None
    assert result["id"] == 1
    assert result["tenant_code"] == "FNB"


@pytest.mark.asyncio
async def test_get_reward_by_id_not_found(monkeypatch):
    conn = FakeConn(row=None)
    patch_db(monkeypatch, conn)

    assert await rs.get_reward_by_id(999, "FNB") is None


@pytest.mark.asyncio
async def test_list_rewards_for_referral(monkeypatch):
    conn = FakeConn(rows=[reward_row(), reward_row(reward_id=2)])
    patch_db(monkeypatch, conn)

    result = await rs.list_rewards_for_referral("track-1", "FNB", limit=10)

    assert len(result) == 2
    assert result[0]["id"] == 1
    assert result[1]["id"] == 2


@pytest.mark.asyncio
async def test_list_rewards_for_beneficiary(monkeypatch):
    conn = FakeConn(rows=[reward_row(), reward_row(reward_id=2)])
    patch_db(monkeypatch, conn)

    result = await rs.list_rewards_for_beneficiary(
        beneficiary_type="REFERRER",
        beneficiary_ref="123",
        tenant_code="FNB",
        limit=10,
    )

    assert len(result) == 2
    assert result[0]["beneficiary_ref"] == "123"
