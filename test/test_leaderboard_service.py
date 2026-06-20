from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import datetime, timezone

import pytest

import services.leaderboard_service as lbs


class FakeTx:
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False


class FakeConn:
    def __init__(self, rows=None, row=None, value=None):
        self.rows = rows or []
        self.row = row
        self.value = value
        self.calls = []

    async def fetch(self, query, *params):
        self.calls.append(("fetch", query, params))
        return self.rows

    async def fetchrow(self, query, *params):
        self.calls.append(("fetchrow", query, params))
        return self.row

    async def fetchval(self, query, *params):
        self.calls.append(("fetchval", query, params))
        return self.value

    async def execute(self, query, *params):
        self.calls.append(("execute", query, params))
        return "OK"

    def transaction(self):
        return FakeTx()


def patch_db(monkeypatch, conn):
    @asynccontextmanager
    async def fake_db_connection():
        yield conn

    if hasattr(lbs, "db_connection"):
        monkeypatch.setattr(lbs, "db_connection", fake_db_connection)

    if hasattr(lbs, "async_db_connection"):
        monkeypatch.setattr(lbs, "async_db_connection", fake_db_connection)


@pytest.fixture(autouse=True)
def disable_cache(monkeypatch):
    monkeypatch.setattr(lbs, "cache_get", lambda key: None)
    monkeypatch.setattr(lbs, "cache_set", lambda key, value, ttl_seconds=60: None)
    monkeypatch.setattr(lbs, "cache_delete_pattern", lambda pattern: None)


def leaderboard(**overrides):
    data = {
        "leaderboard_code": "GLOBAL_OVERALL",
        "tenant_code": "FNB",
        "product": "Transactional",
        "sub_product": "DDA",
        "journey_code": "BANKING_TRANSACTIONAL",
        "journey_version": "v1",
    }
    data.update(overrides)
    return data


def test_leaderboard_cache_key_includes_tenant_code_limit_and_offset():
    key = lbs._leaderboard_cache_key(
        leaderboard_code="global_overall",
        tenant_code="fnb",
        limit=25,
        offset=50,
    )

    assert key == "leaderboard:FNB:GLOBAL_OVERALL:limit:25:offset:50"


def test_get_rank_tier_thresholds():
    assert lbs.get_rank_tier(0) == "Newbie"
    assert lbs.get_rank_tier(1) == "Bronze"
    assert lbs.get_rank_tier(49) == "Bronze"
    assert lbs.get_rank_tier(50) == "Silver"
    assert lbs.get_rank_tier(99) == "Silver"
    assert lbs.get_rank_tier(100) == "Gold"
    assert lbs.get_rank_tier(199) == "Gold"
    assert lbs.get_rank_tier(200) == "Platinum"


@pytest.mark.asyncio
async def test_get_referrer_display_name_priority_gaming_handle(monkeypatch):
    conn = FakeConn(
        row={
            "gaming_handle": "gamer123",
            "sticker": "sticker123",
            "referral_code": "ref123",
        }
    )
    patch_db(monkeypatch, conn)

    result = await lbs.get_referrer_display_name("00001234")

    assert result == "gamer123"


@pytest.mark.asyncio
async def test_get_referrer_display_name_priority_sticker(monkeypatch):
    conn = FakeConn(
        row={
            "gaming_handle": None,
            "sticker": "sticker123",
            "referral_code": "ref123",
        }
    )
    patch_db(monkeypatch, conn)

    result = await lbs.get_referrer_display_name("00001234")

    assert result == "sticker123"


@pytest.mark.asyncio
async def test_get_referrer_display_name_priority_referral_code(monkeypatch):
    conn = FakeConn(
        row={
            "gaming_handle": None,
            "sticker": None,
            "referral_code": "ref123",
        }
    )
    patch_db(monkeypatch, conn)

    result = await lbs.get_referrer_display_name("00001234")

    assert result == "ref123"


@pytest.mark.asyncio
async def test_get_referrer_display_name_fallback(monkeypatch):
    conn = FakeConn(
        row={
            "gaming_handle": None,
            "sticker": None,
            "referral_code": None,
        }
    )
    patch_db(monkeypatch, conn)

    result = await lbs.get_referrer_display_name("00001234")

    assert result == "Player-1234"


@pytest.mark.asyncio
async def test_get_referrer_display_name_no_row(monkeypatch):
    conn = FakeConn(row=None)
    patch_db(monkeypatch, conn)

    result = await lbs.get_referrer_display_name("")

    assert result == "Player-0000"


@pytest.mark.asyncio
async def test_get_active_leaderboard_definitions(monkeypatch):
    conn = FakeConn(rows=[leaderboard()])
    patch_db(monkeypatch, conn)

    rows = await lbs.get_active_leaderboard_definitions(tenant_code="FNB")

    assert len(rows) == 1
    assert rows[0]["leaderboard_code"] == "GLOBAL_OVERALL"
    assert rows[0]["tenant_code"] == "FNB"


@pytest.mark.asyncio
async def test_get_leaderboard_definition_found(monkeypatch):
    conn = FakeConn(row=leaderboard(leaderboard_code="GLOBAL_TRANSACTIONAL"))
    patch_db(monkeypatch, conn)

    row = await lbs.get_leaderboard_definition(
        "GLOBAL_TRANSACTIONAL",
        tenant_code="FNB",
    )

    assert row is not None
    assert row["leaderboard_code"] == "GLOBAL_TRANSACTIONAL"
    assert row["tenant_code"] == "FNB"


@pytest.mark.asyncio
async def test_get_leaderboard_definition_not_found(monkeypatch):
    conn = FakeConn(row=None)
    patch_db(monkeypatch, conn)

    row = await lbs.get_leaderboard_definition("MISSING", tenant_code="FNB")

    assert row is None


@pytest.mark.asyncio
async def test_get_scoring_rules(monkeypatch):
    conn = FakeConn(
        rows=[
            {
                "id": 1,
                "leaderboard_code": "GLOBAL_OVERALL",
                "milestone_code": "VALIDATED",
                "score_type": "MILESTONE",
            },
            {
                "id": 2,
                "leaderboard_code": "GLOBAL_OVERALL",
                "milestone_code": "COMPLETION_BONUS",
                "score_type": "BONUS",
            },
        ]
    )
    patch_db(monkeypatch, conn)

    rows = await lbs.get_scoring_rules("GLOBAL_OVERALL", tenant_code="FNB")

    assert len(rows) == 2
    assert rows[0]["milestone_code"] == "VALIDATED"
    assert rows[1]["score_type"] == "BONUS"


@pytest.mark.asyncio
async def test_get_referrals_for_board_with_all_filters(monkeypatch):
    conn = FakeConn(
        rows=[
            {
                "referral_track_id": "track1",
                "referrer_ucn": "123",
                "product": "Transactional",
                "sub_product": "DDA13",
                "status": "ACCOUNT_OPENED",
                "is_complete": False,
                "journey_code": "BANKING_TRANSACTIONAL",
                "journey_version": "v1",
                "updated_at": None,
            }
        ]
    )
    patch_db(monkeypatch, conn)

    rows = await lbs.get_referrals_for_board(
        leaderboard(
            sub_product="DDA13",
        ),
        referrer_ucn="123",
    )

    assert len(rows) == 1
    assert rows[0]["referral_track_id"] == "track1"

    method, sql, params = conn.calls[0]
    assert method == "fetch"
    assert "referrer_ucn" in sql
    assert "tenant_code" in sql
    assert "UPPER(TRIM(product))" in sql
    assert "UPPER(TRIM(sub_product))" in sql
    assert "UPPER(TRIM(journey_code))" in sql
    assert "UPPER(TRIM(journey_version))" in sql
    assert params == (
        "123",
        "FNB",
        "Transactional",
        "DDA13",
        "BANKING_TRANSACTIONAL",
        "v1",
    )


@pytest.mark.asyncio
async def test_get_referrals_for_board_without_optional_filters(monkeypatch):
    conn = FakeConn(rows=[])
    patch_db(monkeypatch, conn)

    rows = await lbs.get_referrals_for_board({}, referrer_ucn=None)

    assert rows == []

    method, sql, params = conn.calls[0]
    assert method == "fetch"
    assert "AND referrer_ucn =" not in sql
    assert "AND tenant_code =" not in sql
    assert "UPPER(TRIM(product))" not in sql
    assert params == ()


@pytest.mark.asyncio
async def test_get_completed_missions_for_referrer(monkeypatch):
    conn = FakeConn(
        rows=[
            {
                "mission_code": "ACCOUNT_OPENED_CORE",
                "referral_track_id": "track1",
                "progress_count": 1,
                "goal_count": 1,
                "is_complete": True,
                "completed_at": None,
                "mission_category": "CORE",
                "product": "Transactional",
                "sub_product": "DDA",
            }
        ]
    )
    patch_db(monkeypatch, conn)

    rows = await lbs.get_completed_missions_for_referrer("123", leaderboard())

    assert len(rows) == 1
    assert rows[0]["mission_code"] == "ACCOUNT_OPENED_CORE"


@pytest.mark.asyncio
async def test_calculate_mission_score_for_referrer(monkeypatch):
    async def fake_get_completed_missions_for_referrer(referrer_ucn, leaderboard=None):
        return [
            {"mission_code": "ACCOUNT_OPENED_CORE", "mission_category": "CORE"},
            {"mission_code": "COMPLETE_1_REFERRAL", "mission_category": "MILESTONE"},
        ]

    monkeypatch.setattr(
        lbs,
        "get_completed_missions_for_referrer",
        fake_get_completed_missions_for_referrer,
    )

    result = await lbs.calculate_mission_score_for_referrer("123")

    assert result["total_score"] == 45
    assert result["referral_score"] == 20
    assert result["milestone_score"] == 25
    assert result["bonus_score"] == 25


@pytest.mark.asyncio
async def test_calculate_mission_score_with_bonus(monkeypatch):
    async def fake_get_completed_missions_for_referrer(referrer_ucn, leaderboard=None):
        return [
            {"mission_code": "ACCOUNT_OPENED_CORE", "mission_category": "CORE"},
            {"mission_code": "ACCOUNT_ACTIVATED_CORE", "mission_category": "CORE"},
            {"mission_code": "ACCOUNT_FUNDED_CORE", "mission_category": "CORE"},
            {"mission_code": "FIRST_DEBIT_ORDER_SWITCH", "mission_category": "BOOST"},
            {"mission_code": "COMPLETE_1_REFERRAL", "mission_category": "MILESTONE"},
        ]

    monkeypatch.setattr(
        lbs,
        "get_completed_missions_for_referrer",
        fake_get_completed_missions_for_referrer,
    )

    result = await lbs.calculate_mission_score_for_referrer("123")

    assert result["total_score"] == 145
    assert result["referral_score"] == 100
    assert result["bonus_score"] == 45
    assert result["milestone_score"] == 25


@pytest.mark.asyncio
async def test_calculate_mission_score_ignores_unknown_mission(monkeypatch):
    async def fake_get_completed_missions_for_referrer(referrer_ucn, leaderboard=None):
        return [
            {"mission_code": "UNKNOWN_MISSION", "mission_category": "CORE"},
        ]

    monkeypatch.setattr(
        lbs,
        "get_completed_missions_for_referrer",
        fake_get_completed_missions_for_referrer,
    )

    result = await lbs.calculate_mission_score_for_referrer("123")

    assert result["total_score"] == 0
    assert result["referral_score"] == 0
    assert result["bonus_score"] == 0
    assert result["milestone_score"] == 0


@pytest.mark.asyncio
async def test_calculate_referrer_score_for_board_aggregates(monkeypatch):
    now_1 = datetime(2026, 4, 1, tzinfo=timezone.utc)
    now_2 = datetime(2026, 4, 2, tzinfo=timezone.utc)

    async def fake_get_referrals_for_board(lb, referrer_ucn=None):
        return [
            {"updated_at": now_1, "is_complete": False},
            {"updated_at": now_2, "is_complete": True},
        ]

    async def fake_calculate_mission_score_for_referrer(referrer_ucn, leaderboard=None):
        return {
            "total_score": 65,
            "referral_score": 30,
            "milestone_score": 25,
            "bonus_score": 10,
        }

    monkeypatch.setattr(lbs, "get_referrals_for_board", fake_get_referrals_for_board)
    monkeypatch.setattr(
        lbs,
        "calculate_mission_score_for_referrer",
        fake_calculate_mission_score_for_referrer,
    )
    async def fake_calculate_configured_score_for_referrals(leaderboard, referrals):
        return {"total_score": 0, "milestone_score": 0, "bonus_score": 0}

    monkeypatch.setattr(
        lbs,
        "calculate_configured_score_for_referrals",
        fake_calculate_configured_score_for_referrals,
    )

    result = await lbs.calculate_referrer_score_for_board(
        {"leaderboard_code": "GLOBAL_OVERALL"},
        "123",
    )

    assert result.total_score == 65
    assert result.referral_score == 30
    assert result.milestone_score == 25
    assert result.bonus_score == 10
    assert result.referrals_count == 2
    assert result.completed_referrals_count == 1
    assert result.last_event_at == now_2


@pytest.mark.asyncio
async def test_calculate_configured_score_applies_insurance_milestones(monkeypatch):
    async def fake_get_scoring_rules(leaderboard_code, tenant_code=None):
        return [
            {
                "leaderboard_code": leaderboard_code,
                "journey_code": "INSURANCE_POLICY",
                "journey_version": "v1",
                "product": "INSURANCE",
                "sub_product": None,
                "milestone_code": "QUOTE_ACCEPTED",
                "score_type": "MILESTONE",
                "score_value": 25,
            },
            {
                "leaderboard_code": leaderboard_code,
                "journey_code": "INSURANCE_POLICY",
                "journey_version": "v1",
                "product": "INSURANCE",
                "sub_product": None,
                "milestone_code": "FIRST_PREMIUM_PAID",
                "score_type": "MILESTONE",
                "score_value": 60,
            },
            {
                "leaderboard_code": leaderboard_code,
                "journey_code": "INSURANCE_POLICY",
                "journey_version": "v1",
                "product": "INSURANCE",
                "sub_product": None,
                "milestone_code": "COMPLETION_BONUS",
                "score_type": "BONUS",
                "score_value": 35,
            },
        ]

    monkeypatch.setattr(lbs, "get_scoring_rules", fake_get_scoring_rules)

    score = await lbs.calculate_configured_score_for_referrals(
        {"leaderboard_code": "GLOBAL_INSURANCE", "tenant_code": "FNB"},
        [
            {
                "journey_code": "INSURANCE_POLICY",
                "journey_version": "v1",
                "product": "INSURANCE",
                "sub_product": "FUNERAL_PLAN",
                "status": "FIRST_PREMIUM_PAID",
                "account_opened_at": datetime(2026, 6, 1, tzinfo=timezone.utc),
                "funded_at": datetime(2026, 6, 3, tzinfo=timezone.utc),
                "is_complete": True,
            }
        ],
    )

    assert score == {
        "total_score": 120,
        "milestone_score": 85,
        "bonus_score": 35,
    }


@pytest.mark.asyncio
async def test_calculate_referrer_score_adds_configured_score(monkeypatch):
    async def fake_get_referrals_for_board(lb, referrer_ucn=None):
        return [{"updated_at": None, "is_complete": True}]

    async def fake_calculate_mission_score_for_referrer(referrer_ucn, leaderboard=None):
        return {
            "total_score": 10,
            "referral_score": 10,
            "milestone_score": 0,
            "bonus_score": 0,
        }

    async def fake_calculate_configured_score_for_referrals(leaderboard, referrals):
        return {"total_score": 95, "milestone_score": 60, "bonus_score": 35}

    monkeypatch.setattr(lbs, "get_referrals_for_board", fake_get_referrals_for_board)
    monkeypatch.setattr(lbs, "calculate_mission_score_for_referrer", fake_calculate_mission_score_for_referrer)
    monkeypatch.setattr(lbs, "calculate_configured_score_for_referrals", fake_calculate_configured_score_for_referrals)

    result = await lbs.calculate_referrer_score_for_board(
        {"leaderboard_code": "GLOBAL_INSURANCE"},
        "123",
    )

    assert result.total_score == 105
    assert result.referral_score == 10
    assert result.milestone_score == 60
    assert result.bonus_score == 35


@pytest.mark.asyncio
async def test_upsert_leaderboard_entry_writes_display_name(monkeypatch):
    conn = FakeConn()
    patch_db(monkeypatch, conn)

    async def fake_get_referrer_display_name(ucn):
        return "Stormers1"

    monkeypatch.setattr(lbs, "get_referrer_display_name", fake_get_referrer_display_name)

    score = lbs.ScoreBreakdown(
        total_score=220,
        referral_score=220,
        milestone_score=195,
        bonus_score=25,
        referrals_count=3,
        completed_referrals_count=1,
        last_event_at=datetime(2026, 4, 6, 17, 41, tzinfo=timezone.utc),
    )

    await lbs.upsert_leaderboard_entry(
        {
            "leaderboard_code": "GLOBAL_OVERALL",
            "tenant_code": "FNB",
            "product": None,
            "sub_product": None,
        },
        "20260406191654",
        score,
    )

    execute_calls = [call for call in conn.calls if call[0] == "execute"]
    assert len(execute_calls) == 1

    _, sql, params = execute_calls[0]
    assert "display_name" in sql
    assert params[3] == "Stormers1"
    assert params[11] == "Platinum"
    assert params[12] == "FNB"


@pytest.mark.asyncio
async def test_delete_leaderboard_entry_if_no_referrals(monkeypatch):
    conn = FakeConn()
    patch_db(monkeypatch, conn)

    await lbs.delete_leaderboard_entry_if_no_referrals(
        "GLOBAL_OVERALL",
        "123",
        tenant_code="FNB",
    )

    _, sql, params = conn.calls[0]
    assert "DELETE FROM leaderboard_entries" in sql
    assert params == ("GLOBAL_OVERALL", "123", "FNB")


@pytest.mark.asyncio
async def test_recalculate_rankings(monkeypatch):
    conn = FakeConn(
        rows=[
            {"referrer_ucn": "u1"},
            {"referrer_ucn": "u2"},
            {"referrer_ucn": "u3"},
        ]
    )
    patch_db(monkeypatch, conn)

    await lbs.recalculate_rankings("GLOBAL_OVERALL", tenant_code="FNB")

    execute_calls = [call for call in conn.calls if call[0] == "execute"]

    assert len(execute_calls) == 3
    assert execute_calls[0][2] == (1, "GLOBAL_OVERALL", "u1", "FNB")
    assert execute_calls[1][2] == (2, "GLOBAL_OVERALL", "u2", "FNB")
    assert execute_calls[2][2] == (3, "GLOBAL_OVERALL", "u3", "FNB")


@pytest.mark.asyncio
async def test_rebuild_leaderboard_for_referrer_with_referrals(monkeypatch):
    leaderboards = [
        {"leaderboard_code": "GLOBAL_OVERALL", "tenant_code": "FNB"},
        {"leaderboard_code": "GLOBAL_TRANSACTIONAL", "tenant_code": "FNB"},
    ]

    async def fake_get_active_leaderboard_definitions(tenant_code=None):
        return leaderboards

    async def fake_get_referrals_for_board(lb, referrer_ucn=None):
        return [{"x": 1}]

    async def fake_calculate_referrer_score_for_board(leaderboard, referrer_ucn):
        return lbs.ScoreBreakdown(10, 10, 10, 0, 1, 0, None)

    upserts = []
    recalcs = []

    async def fake_upsert_leaderboard_entry(leaderboard, referrer_ucn, score):
        upserts.append((leaderboard["leaderboard_code"], referrer_ucn))

    async def fake_recalculate_rankings(leaderboard_code, tenant_code=None):
        recalcs.append((leaderboard_code, tenant_code))

    monkeypatch.setattr(
        lbs,
        "get_active_leaderboard_definitions",
        fake_get_active_leaderboard_definitions,
    )
    monkeypatch.setattr(lbs, "get_referrals_for_board", fake_get_referrals_for_board)
    monkeypatch.setattr(
        lbs,
        "calculate_referrer_score_for_board",
        fake_calculate_referrer_score_for_board,
    )
    monkeypatch.setattr(lbs, "upsert_leaderboard_entry", fake_upsert_leaderboard_entry)
    monkeypatch.setattr(lbs, "recalculate_rankings", fake_recalculate_rankings)

    await lbs.rebuild_leaderboard_for_referrer("123", tenant_code="FNB")

    assert upserts == [("GLOBAL_OVERALL", "123"), ("GLOBAL_TRANSACTIONAL", "123")]
    assert recalcs == [("GLOBAL_OVERALL", "FNB"), ("GLOBAL_TRANSACTIONAL", "FNB")]


@pytest.mark.asyncio
async def test_rebuild_leaderboard_for_referrer_without_referrals(monkeypatch):
    leaderboards = [{"leaderboard_code": "GLOBAL_OVERALL", "tenant_code": "FNB"}]

    async def fake_get_active_leaderboard_definitions(tenant_code=None):
        return leaderboards

    async def fake_get_referrals_for_board(lb, referrer_ucn=None):
        return []

    deleted = []
    recalcs = []

    async def fake_delete_leaderboard_entry_if_no_referrals(
        leaderboard_code,
        referrer_ucn,
        tenant_code=None,
    ):
        deleted.append((leaderboard_code, referrer_ucn, tenant_code))

    async def fake_recalculate_rankings(leaderboard_code, tenant_code=None):
        recalcs.append((leaderboard_code, tenant_code))

    monkeypatch.setattr(
        lbs,
        "get_active_leaderboard_definitions",
        fake_get_active_leaderboard_definitions,
    )
    monkeypatch.setattr(lbs, "get_referrals_for_board", fake_get_referrals_for_board)
    monkeypatch.setattr(
        lbs,
        "delete_leaderboard_entry_if_no_referrals",
        fake_delete_leaderboard_entry_if_no_referrals,
    )
    monkeypatch.setattr(lbs, "recalculate_rankings", fake_recalculate_rankings)

    await lbs.rebuild_leaderboard_for_referrer("123", tenant_code="FNB")

    assert deleted == [("GLOBAL_OVERALL", "123", "FNB")]
    assert recalcs == [("GLOBAL_OVERALL", "FNB")]


@pytest.mark.asyncio
async def test_rebuild_leaderboard_for_referrer_invalidates_cache(monkeypatch):
    async def fake_get_active_leaderboard_definitions(tenant_code=None):
        return [{"leaderboard_code": "GLOBAL_OVERALL", "tenant_code": "FNB"}]

    async def fake_get_referrals_for_board(lb, referrer_ucn=None):
        return []

    async def fake_delete(*args, **kwargs):
        return None

    async def fake_recalculate(*args, **kwargs):
        return None

    deleted = []

    monkeypatch.setattr(
        lbs,
        "get_active_leaderboard_definitions",
        fake_get_active_leaderboard_definitions,
    )
    monkeypatch.setattr(lbs, "get_referrals_for_board", fake_get_referrals_for_board)
    monkeypatch.setattr(lbs, "delete_leaderboard_entry_if_no_referrals", fake_delete)
    monkeypatch.setattr(lbs, "recalculate_rankings", fake_recalculate)
    monkeypatch.setattr(lbs, "cache_delete_pattern", lambda pattern: deleted.append(pattern))

    await lbs.rebuild_leaderboard_for_referrer("123", tenant_code="FNB")

    assert deleted == ["leaderboard:FNB:*"]


@pytest.mark.asyncio
async def test_rebuild_leaderboard_for_board(monkeypatch):
    async def fake_get_leaderboard_definition(leaderboard_code=None, tenant_code=None):
        return {
            "leaderboard_code": leaderboard_code,
            "tenant_code": tenant_code,
        }

    async def fake_get_referrals_for_board(leaderboard):
        return [
            {"referrer_ucn": "u2"},
            {"referrer_ucn": "u1"},
            {"referrer_ucn": "u1"},
        ]

    async def fake_calculate_referrer_score_for_board(leaderboard, referrer_ucn):
        return lbs.ScoreBreakdown(10, 10, 10, 0, 1, 0, None)

    conn = FakeConn()
    patch_db(monkeypatch, conn)

    upserts = []
    recalcs = []

    async def fake_upsert_leaderboard_entry(leaderboard, referrer_ucn, score):
        upserts.append(referrer_ucn)

    async def fake_recalculate_rankings(leaderboard_code, tenant_code=None):
        recalcs.append((leaderboard_code, tenant_code))

    monkeypatch.setattr(lbs, "get_leaderboard_definition", fake_get_leaderboard_definition)
    monkeypatch.setattr(lbs, "get_referrals_for_board", fake_get_referrals_for_board)
    monkeypatch.setattr(
        lbs,
        "calculate_referrer_score_for_board",
        fake_calculate_referrer_score_for_board,
    )
    monkeypatch.setattr(lbs, "upsert_leaderboard_entry", fake_upsert_leaderboard_entry)
    monkeypatch.setattr(lbs, "recalculate_rankings", fake_recalculate_rankings)

    await lbs.rebuild_leaderboard_for_board("GLOBAL_OVERALL", tenant_code="FNB")

    execute_calls = [call for call in conn.calls if call[0] == "execute"]
    assert len(execute_calls) == 1
    assert "DELETE FROM leaderboard_entries" in execute_calls[0][1]
    assert execute_calls[0][2] == ("GLOBAL_OVERALL", "FNB")

    assert upserts == ["u1", "u2"]
    assert recalcs == [("GLOBAL_OVERALL", "FNB")]


@pytest.mark.asyncio
async def test_rebuild_leaderboard_for_board_not_found(monkeypatch):
    async def fake_get_leaderboard_definition(leaderboard_code=None, tenant_code=None):
        return None

    monkeypatch.setattr(lbs, "get_leaderboard_definition", fake_get_leaderboard_definition)

    with pytest.raises(ValueError, match="Active leaderboard not found"):
        await lbs.rebuild_leaderboard_for_board("MISSING", tenant_code="FNB")


@pytest.mark.asyncio
async def test_rebuild_all_leaderboards(monkeypatch):
    async def fake_get_active_leaderboard_definitions(tenant_code=None):
        return [
            {"leaderboard_code": "A", "tenant_code": "FNB"},
            {"leaderboard_code": "B", "tenant_code": "FNB"},
        ]

    called = []

    async def fake_rebuild_leaderboard_for_board(leaderboard_code, tenant_code=None):
        called.append((leaderboard_code, tenant_code))

    monkeypatch.setattr(
        lbs,
        "get_active_leaderboard_definitions",
        fake_get_active_leaderboard_definitions,
    )
    monkeypatch.setattr(
        lbs,
        "rebuild_leaderboard_for_board",
        fake_rebuild_leaderboard_for_board,
    )

    await lbs.rebuild_all_leaderboards(tenant_code="FNB")

    assert called == [("A", "FNB"), ("B", "FNB")]


@pytest.mark.asyncio
async def test_get_leaderboard_cache_hit(monkeypatch):
    monkeypatch.setattr(
        lbs,
        "cache_get",
        lambda key: [{"display_name": "CachedUser", "total_score": 999}],
    )

    rows = await lbs.get_leaderboard(
        "GLOBAL_OVERALL",
        tenant_code="FNB",
        limit=10,
        offset=0,
    )

    assert rows == [{"display_name": "CachedUser", "total_score": 999}]


@pytest.mark.asyncio
async def test_get_leaderboard(monkeypatch):
    conn = FakeConn(
        rows=[
            {
                "leaderboard_code": "GLOBAL_OVERALL",
                "display_name": "Stormers1",
                "total_score": 220,
                "referral_score": 220,
                "milestone_score": 195,
                "bonus_score": 25,
                "referrals_count": 3,
                "completed_referrals_count": 1,
                "last_event_at": None,
                "rank_position": 1,
                "rank_tier": "Platinum",
            }
        ]
    )
    patch_db(monkeypatch, conn)

    rows = await lbs.get_leaderboard(
        "GLOBAL_OVERALL",
        tenant_code="FNB",
        limit=10,
        offset=0,
    )

    assert rows[0]["display_name"] == "Stormers1"
    assert rows[0]["total_score"] == 220
    assert rows[0]["rank_tier"] == "Platinum"


@pytest.mark.asyncio
async def test_get_leaderboard_count(monkeypatch):
    conn = FakeConn(value=8)
    patch_db(monkeypatch, conn)

    count = await lbs.get_leaderboard_count("GLOBAL_OVERALL", tenant_code="FNB")

    assert count == 8


@pytest.mark.asyncio
async def test_get_leaderboard_count_no_value(monkeypatch):
    conn = FakeConn(value=None)
    patch_db(monkeypatch, conn)

    count = await lbs.get_leaderboard_count("GLOBAL_OVERALL", tenant_code="FNB")

    assert count == 0


@pytest.mark.asyncio
async def test_get_referrer_leaderboard_entry(monkeypatch):
    conn = FakeConn(
        row={
            "leaderboard_code": "GLOBAL_OVERALL",
            "display_name": "Lenovo100",
            "total_score": 30,
            "referral_score": 30,
            "milestone_score": 30,
            "bonus_score": 0,
            "referrals_count": 1,
            "completed_referrals_count": 0,
            "last_event_at": None,
            "rank_position": 3,
            "rank_tier": "Bronze",
        }
    )
    patch_db(monkeypatch, conn)

    row = await lbs.get_referrer_leaderboard_entry(
        "GLOBAL_OVERALL",
        "123",
        tenant_code="FNB",
    )

    assert row["display_name"] == "Lenovo100"
    assert row["rank_position"] == 3
    assert row["rank_tier"] == "Bronze"


@pytest.mark.asyncio
async def test_get_referrer_leaderboard_entry_not_found(monkeypatch):
    conn = FakeConn(row=None)
    patch_db(monkeypatch, conn)

    row = await lbs.get_referrer_leaderboard_entry(
        "GLOBAL_OVERALL",
        "123",
        tenant_code="FNB",
    )

    assert row is None


@pytest.mark.asyncio
async def test_get_next_rank_info(monkeypatch):
    class NextRankConn(FakeConn):
        def __init__(self):
            super().__init__()
            self.responses = [
                {"rank_position": 3, "total_score": 30},
                {"rank_position": 2, "total_score": 200},
            ]

        async def fetchrow(self, query, *params):
            self.calls.append(("fetchrow", query, params))
            return self.responses.pop(0)

    conn = NextRankConn()
    patch_db(monkeypatch, conn)

    info = await lbs.get_next_rank_info(
        "GLOBAL_OVERALL",
        "123",
        tenant_code="FNB",
    )

    assert info == {
        "next_rank_position": 2,
        "next_rank_score": 200,
        "points_to_next_rank": 170,
    }


@pytest.mark.asyncio
async def test_get_next_rank_info_not_found(monkeypatch):
    conn = FakeConn(row=None)
    patch_db(monkeypatch, conn)

    info = await lbs.get_next_rank_info(
        "GLOBAL_OVERALL",
        "123",
        tenant_code="FNB",
    )

    assert info is None


@pytest.mark.asyncio
async def test_get_next_rank_info_top_rank(monkeypatch):
    class TopRankConn(FakeConn):
        def __init__(self):
            super().__init__()
            self.responses = [
                {"rank_position": 1, "total_score": 220},
                None,
            ]

        async def fetchrow(self, query, *params):
            self.calls.append(("fetchrow", query, params))
            return self.responses.pop(0)

    conn = TopRankConn()
    patch_db(monkeypatch, conn)

    info = await lbs.get_next_rank_info(
        "GLOBAL_OVERALL",
        "123",
        tenant_code="FNB",
    )

    assert info is None
