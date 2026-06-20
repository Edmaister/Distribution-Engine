from __future__ import annotations

import datetime
import json
from contextlib import asynccontextmanager

import pytest

import services.mission_service as svc


class FakeTx:
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False


class FakeConn:
    def __init__(self, row=None, rows=None):
        self.row = row
        self.rows = rows or []
        self.calls = []

    async def fetchrow(self, query, *params):
        self.calls.append(("fetchrow", query, params))
        return self.row

    async def fetch(self, query, *params):
        self.calls.append(("fetch", query, params))
        return self.rows

    async def execute(self, query, *params):
        self.calls.append(("execute", query, params))
        return "OK"

    def transaction(self):
        return FakeTx()


def patch_db(monkeypatch, conn):
    @asynccontextmanager
    async def fake_db_connection():
        yield conn

    monkeypatch.setattr(svc, "db_connection", fake_db_connection)


def referral(referrer_ucn="u"):
    return {
        "referral_track_id": "track-1",
        "product": "TRANSACTIONAL",
        "sub_product": "GOLD",
        "referrer_ucn": referrer_ucn,
        "referee_ucn": "referee",
    }


def definition(code="M1", event_type="EVENT", goal_count=1, amount=0, category="CORE"):
    return {
        "mission_code": code,
        "mission_name": code,
        "mission_description": "desc",
        "event_type": event_type,
        "goal_count": goal_count,
        "bonus_reward_amount": amount,
        "currency": "ZAR",
        "is_credit_related": False,
        "regulatory_tags": ["TCF"],
        "display_priority": 1,
        "mission_category": category,
    }


def progress_row(progress=0, goal=1, complete=False, bonus=False):
    return {
        "id": 1,
        "referral_track_id": "track-1",
        "mission_code": "M1",
        "beneficiary_type": "REFERRER",
        "beneficiary_ref": "u",
        "progress_count": progress,
        "goal_count": goal,
        "is_complete": complete,
        "completed_at": "done" if complete else None,
        "bonus_reward_applied": bonus,
    }


def test_utcnow_is_timezone_aware():
    now = svc._utcnow()
    assert isinstance(now, datetime.datetime)
    assert now.tzinfo is not None


def test_normalize_mission_category_defaults_and_valid_values():
    assert svc._normalize_mission_category(None) == "CORE"
    assert svc._normalize_mission_category("") == "CORE"
    assert svc._normalize_mission_category("bad") == "CORE"
    assert svc._normalize_mission_category("core") == "CORE"
    assert svc._normalize_mission_category("boost") == "BOOST"
    assert svc._normalize_mission_category("milestone") == "MILESTONE"


def test_derive_mission_status_all_branches():
    assert svc._derive_mission_status(0, 1, False) == "AVAILABLE"
    assert svc._derive_mission_status(1, 2, False) == "IN_PROGRESS"
    assert svc._derive_mission_status(2, 2, False) == "COMPLETED"
    assert svc._derive_mission_status(0, 1, True) == "COMPLETED"


def test_group_sort_key_and_grouping_orders_incomplete_first():
    items = [
        {"missionCode": "B", "category": "CORE", "isComplete": True, "displayOrder": 1},
        {"missionCode": "C", "category": "bad", "isComplete": False, "displayOrder": 3},
        {"missionCode": "A", "category": "CORE", "isComplete": False, "displayOrder": 2},
        {"missionCode": "D", "category": "BOOST", "isComplete": False, "displayOrder": 1},
        {"missionCode": "E", "category": "MILESTONE", "isComplete": False, "displayOrder": 1},
    ]

    grouped = svc._group_mission_items(items)

    assert list(grouped.keys()) == ["core", "boost", "milestone"]
    assert [x["missionCode"] for x in grouped["core"]] == ["A", "C", "B"]
    assert grouped["boost"][0]["missionCode"] == "D"
    assert grouped["milestone"][0]["missionCode"] == "E"


def test_empty_grouped_response():
    assert svc._empty_grouped_response() == {
        "core": [],
        "boost": [],
        "milestone": [],
    }


@pytest.mark.asyncio
async def test_get_referral_row_executes_expected_query(monkeypatch):
    conn = FakeConn(row={"referral_track_id": "track-1"})
    patch_db(monkeypatch, conn)

    result = await svc._get_referral_row("track-1")

    assert result == {"referral_track_id": "track-1"}
    assert "FROM referral_instances" in conn.calls[0][1]
    assert conn.calls[0][2] == ("track-1",)


@pytest.mark.asyncio
async def test_get_referral_row_none(monkeypatch):
    conn = FakeConn(row=None)
    patch_db(monkeypatch, conn)

    assert await svc._get_referral_row("missing") is None


@pytest.mark.asyncio
async def test_get_referrals_for_referrer_returns_rows(monkeypatch):
    conn = FakeConn(rows=[{"referral_track_id": "a"}])
    patch_db(monkeypatch, conn)

    result = await svc._get_referrals_for_referrer("ucn")

    assert result == [{"referral_track_id": "a"}]
    assert "WHERE ri.referrer_ucn = $1" in conn.calls[0][1]


@pytest.mark.asyncio
async def test_get_mission_definitions_returns_rows(monkeypatch):
    conn = FakeConn(rows=[{"mission_code": "M1"}])
    patch_db(monkeypatch, conn)

    result = await svc._get_mission_definitions("P", "S")

    assert result == [{"mission_code": "M1"}]
    assert conn.calls[0][2] == ("P", "S")


@pytest.mark.asyncio
async def test_get_reward_disclosures_empty_and_ordered(monkeypatch):
    assert await svc._get_reward_disclosures([]) == []

    conn = FakeConn(
        rows=[
            {"disclosure_code": "B", "disclosure_text": "text-b"},
            {"disclosure_code": "A", "disclosure_text": "text-a"},
        ]
    )
    patch_db(monkeypatch, conn)

    result = await svc._get_reward_disclosures(["A", "MISSING", "B"])

    assert result == ["text-a", "text-b"]
    assert conn.calls[0][2] == (["A", "MISSING", "B"],)


@pytest.mark.asyncio
async def test_get_existing_progress_found_and_missing(monkeypatch):
    conn = FakeConn(row={"mission_code": "M1"})
    patch_db(monkeypatch, conn)

    result = await svc._get_existing_progress("t", "M1", "REFERRER", "u")

    assert result == {"mission_code": "M1"}
    assert conn.calls[0][2] == ("t", "M1", "REFERRER", "u")

    conn_none = FakeConn(row=None)
    patch_db(monkeypatch, conn_none)

    assert await svc._get_existing_progress("t", "M1", "REFERRER", "u") is None


@pytest.mark.asyncio
async def test_upsert_progress_row(monkeypatch):
    conn = FakeConn()
    patch_db(monkeypatch, conn)

    await svc._upsert_progress_row("t", "M1", "REFERRER", "u", 2)

    assert "INSERT INTO user_mission_progress" in conn.calls[0][1]
    assert conn.calls[0][2] == ("t", "M1", "REFERRER", "u", 2)


@pytest.mark.asyncio
async def test_record_mission_display_audit_serializes_json(monkeypatch):
    conn = FakeConn()
    patch_db(monkeypatch, conn)

    await svc._record_mission_display_audit(
        referral_track_id="t",
        mission_code="M1",
        title="Title",
        body="Body",
        compliance={"blocked": False},
        disclosures=["d1"],
        channel="API",
    )

    _, query, params = conn.calls[0]
    assert "INSERT INTO mission_display_audit" in query
    assert json.loads(params[4]) == {"blocked": False}
    assert json.loads(params[5]) == ["d1"]


@pytest.mark.asyncio
async def test_count_completed_referrals_for_referrer_list_string_and_empty(monkeypatch):
    conn_list = FakeConn(row={"completed_count": 2, "referral_track_ids": ["a", "b"]})
    patch_db(monkeypatch, conn_list)

    result = await svc._count_completed_referrals_for_referrer(
        "u",
        product="P",
        sub_product="S",
    )

    assert result == {"completed_count": 2, "referral_track_ids": ["a", "b"]}
    assert "UPPER(TRIM(product))" in conn_list.calls[0][1]
    assert "UPPER(TRIM(sub_product))" in conn_list.calls[0][1]
    assert conn_list.calls[0][2] == ("u", "P", "S")

    conn_string = FakeConn(row={"completed_count": 2, "referral_track_ids": "{a,b}"})
    patch_db(monkeypatch, conn_string)

    assert await svc._count_completed_referrals_for_referrer("u") == {
        "completed_count": 2,
        "referral_track_ids": ["a", "b"],
    }

    conn_empty = FakeConn(row={})
    patch_db(monkeypatch, conn_empty)

    assert await svc._count_completed_referrals_for_referrer("u") == {
        "completed_count": 0,
        "referral_track_ids": [],
    }

    conn_none = FakeConn(row=None)
    patch_db(monkeypatch, conn_none)

    assert await svc._count_completed_referrals_for_referrer("u") == {
        "completed_count": 0,
        "referral_track_ids": [],
    }


@pytest.mark.asyncio
async def test_build_mission_response_item_non_credit(monkeypatch):
    async def fake_disclosures(codes):
        return [f"DISC::{c}" for c in codes]

    monkeypatch.setattr(svc, "_get_reward_disclosures", fake_disclosures)

    item = await svc._build_mission_response_item(
        definition(
            code="FIRST_SALARY_SWITCH",
            amount=200,
            category="BOOST",
        ),
        {
            "beneficiary_type": "REFERRER",
            "beneficiary_ref": "20260408174749",
            "progress_count": 0,
            "goal_count": 1,
            "is_complete": False,
            "completed_at": None,
        },
        associated_referral_track_ids=["t"],
    )

    assert item["missionCode"] == "FIRST_SALARY_SWITCH"
    assert item["category"] == "BOOST"
    assert item["status"] == "AVAILABLE"
    assert item["rewardLabel"] == "+ZAR 200"
    assert item["associatedReferralTrackIds"] == ["t"]
    assert "DISC::GENERAL_INFO_ONLY" in item["disclosures"]
    assert item["compliance"]["isCreditRelated"] is False


@pytest.mark.asyncio
async def test_build_mission_response_item_credit_defaults(monkeypatch):
    async def fake_disclosures(codes):
        return codes

    monkeypatch.setattr(svc, "_get_reward_disclosures", fake_disclosures)

    item = await svc._build_mission_response_item(
        {
            **definition(code="CREDIT_MISSION", amount=50, category="invalid"),
            "is_credit_related": True,
            "currency": None,
            "display_priority": None,
            "regulatory_tags": None,
        },
        {
            "beneficiary_type": "REFERRER",
            "beneficiary_ref": "u",
            "progress_count": 1,
            "goal_count": 1,
            "is_complete": True,
            "completed_at": "done",
        },
    )

    assert item["category"] == "CORE"
    assert item["displayOrder"] == 9999
    assert item["currency"] == "ZAR"
    assert item["completedAt"] == "done"
    assert item["status"] == "COMPLETED"
    assert "CREDIT_DISCLOSURE" in item["compliance"]["disclaimerCodes"]
    assert item["compliance"]["regulatoryTags"] == [
        "TCF",
        "FAIS",
        "MARKET_CONDUCT",
        "BANKING_CODE",
    ]


@pytest.mark.asyncio
async def test_build_portfolio_milestone_item_incomplete_and_complete(monkeypatch):
    async def fake_disclosures(codes):
        return codes

    monkeypatch.setattr(svc, "_get_reward_disclosures", fake_disclosures)

    base = definition(code="PORTFOLIO_3", amount=100, category="MILESTONE")
    base["goal_count"] = 3
    base["display_priority"] = 2

    incomplete = await svc._build_portfolio_milestone_item(base, "u", 2, ["a", "b"])
    assert incomplete["scope"] == svc.MISSION_SCOPE_PORTFOLIO
    assert incomplete["progressCount"] == 2
    assert incomplete["status"] == "IN_PROGRESS"
    assert incomplete["isComplete"] is False

    complete = await svc._build_portfolio_milestone_item(
        {**base, "currency": None},
        "u",
        9,
        ["a", "b", "c"],
    )
    assert complete["progressCount"] == 3
    assert complete["status"] == "COMPLETED"
    assert complete["isComplete"] is True
    assert complete["rewardLabel"] == "+ZAR 100"


@pytest.mark.asyncio
async def test_get_missions_for_referral_empty_when_missing(monkeypatch):
    async def fake_referral(referral_track_id):
        return None

    monkeypatch.setattr(svc, "_get_referral_row", fake_referral)

    assert await svc.get_missions_for_referral("missing", audit=False) == []
    assert await svc.get_missions_for_referral(
        "missing",
        audit=False,
        grouped=True,
    ) == svc._empty_grouped_response()


@pytest.mark.asyncio
async def test_get_missions_for_referral_empty_when_referrer_missing(monkeypatch):
    async def fake_referral(referral_track_id):
        return {"referrer_ucn": None}

    monkeypatch.setattr(svc, "_get_referral_row", fake_referral)

    assert await svc.get_missions_for_referral("track", audit=False) == []
    assert await svc.get_missions_for_referral(
        "track",
        audit=False,
        grouped=True,
    ) == svc._empty_grouped_response()


@pytest.mark.asyncio
async def test_get_missions_for_referral_skips_milestone_and_missing_progress(monkeypatch):
    async def fake_referral(referral_track_id):
        return referral()

    async def fake_defs(product, sub_product):
        return [
            definition(code="PORT", category="MILESTONE"),
            definition(code="NO_ROW", category="CORE"),
        ]

    async def fake_upsert(**kwargs):
        return None

    async def fake_progress(**kwargs):
        return None

    monkeypatch.setattr(svc, "_get_referral_row", fake_referral)
    monkeypatch.setattr(svc, "_get_mission_definitions", fake_defs)
    monkeypatch.setattr(svc, "_upsert_progress_row", fake_upsert)
    monkeypatch.setattr(svc, "_get_existing_progress", fake_progress)

    assert await svc.get_missions_for_referral("track", audit=False) == []


@pytest.mark.asyncio
async def test_get_missions_for_referral_with_audit_and_grouped(monkeypatch):
    audits = []
    upserts = []

    async def fake_referral(referral_track_id):
        return referral()

    async def fake_defs(product, sub_product):
        return [
            definition(code="B", amount=25, category="BOOST"),
            definition(code="A", amount=10, category="CORE"),
        ]

    async def fake_upsert(**kwargs):
        upserts.append(kwargs)

    async def fake_progress(**kwargs):
        return {
            "beneficiary_type": kwargs["beneficiary_type"],
            "beneficiary_ref": kwargs["beneficiary_ref"],
            "progress_count": 0,
            "goal_count": 1,
            "is_complete": False,
            "completed_at": None,
            "bonus_reward_applied": False,
        }

    async def fake_disclosures(codes):
        return codes

    async def fake_audit(**kwargs):
        audits.append(kwargs)

    monkeypatch.setattr(svc, "_get_referral_row", fake_referral)
    monkeypatch.setattr(svc, "_get_mission_definitions", fake_defs)
    monkeypatch.setattr(svc, "_upsert_progress_row", fake_upsert)
    monkeypatch.setattr(svc, "_get_existing_progress", fake_progress)
    monkeypatch.setattr(svc, "_get_reward_disclosures", fake_disclosures)
    monkeypatch.setattr(svc, "_record_mission_display_audit", fake_audit)

    grouped = await svc.get_missions_for_referral(
        "track-1",
        channel="MOBILE",
        audit=True,
        grouped=True,
    )

    assert [u["mission_code"] for u in upserts] == ["B", "A"]
    assert len(audits) == 2
    assert audits[0]["channel"] == "MOBILE"
    assert grouped["core"][0]["missionCode"] == "A"
    assert grouped["boost"][0]["missionCode"] == "B"


@pytest.mark.asyncio
async def test_get_missions_for_referrer_empty_grouped_and_flat(monkeypatch):
    async def fake_referrals(referrer_ucn):
        return []

    monkeypatch.setattr(svc, "_get_referrals_for_referrer", fake_referrals)

    assert await svc.get_missions_for_referrer("u", grouped=True) == svc._empty_grouped_response()
    assert await svc.get_missions_for_referrer("u", grouped=False) == []


@pytest.mark.asyncio
async def test_get_missions_for_referrer_includes_referral_and_milestone_items(monkeypatch):
    async def fake_referrals(referrer_ucn):
        return [
            {"referral_track_id": "t1", "product": "P", "sub_product": "S"},
            {"referral_track_id": "t2", "product": "P", "sub_product": "S"},
        ]

    async def fake_get_missions_for_referral(
        referral_track_id,
        tenant_code=None,
        channel="API",
        audit=True,
        grouped=False,
    ):
        return [
            {
                "missionCode": f"CORE_{referral_track_id}",
                "category": "CORE",
                "isComplete": False,
                "displayOrder": 1,
            }
        ]

    async def fake_defs(product, sub_product):
        return [
            definition(code="PORT_2", amount=100, category="MILESTONE"),
            definition(code="NON_MILESTONE", category="CORE"),
        ]

    async def fake_count(**kwargs):
        return {
            "completed_count": 2,
            "referral_track_ids": ["t1", "t2"],
        }

    async def fake_disclosures(codes):
        return codes

    monkeypatch.setattr(svc, "_get_referrals_for_referrer", fake_referrals)
    monkeypatch.setattr(svc, "get_missions_for_referral", fake_get_missions_for_referral)
    monkeypatch.setattr(svc, "_get_mission_definitions", fake_defs)
    monkeypatch.setattr(svc, "_count_completed_referrals_for_referrer", fake_count)
    monkeypatch.setattr(svc, "_get_reward_disclosures", fake_disclosures)

    grouped = await svc.get_missions_for_referrer("u", audit=False, grouped=True)
    assert [x["missionCode"] for x in grouped["core"]] == ["CORE_t1", "CORE_t2"]
    assert grouped["milestone"][0]["missionCode"] == "PORT_2"
    assert grouped["milestone"][0]["isComplete"] is True

    flat = await svc.get_missions_for_referrer("u", grouped=False)
    assert any(x["missionCode"] == "PORT_2" for x in flat)


@pytest.mark.asyncio
async def test_apply_event_to_missions_empty_paths(monkeypatch):
    async def missing_referral(referral_track_id):
        return None

    monkeypatch.setattr(svc, "_get_referral_row", missing_referral)
    assert await svc.apply_event_to_missions("track", "EVENT") == []

    async def no_referrer(referral_track_id):
        return referral(referrer_ucn=None)

    monkeypatch.setattr(svc, "_get_referral_row", no_referrer)
    assert await svc.apply_event_to_missions("track", "EVENT") == []

    async def valid_referral(referral_track_id):
        return referral()

    async def other_defs(product, sub_product):
        return [definition(event_type="OTHER")]

    monkeypatch.setattr(svc, "_get_referral_row", valid_referral)
    monkeypatch.setattr(svc, "_get_mission_definitions", other_defs)
    assert await svc.apply_event_to_missions("track", "EVENT") == []

    async def milestone_defs(product, sub_product):
        return [definition(category="MILESTONE")]

    monkeypatch.setattr(svc, "_get_mission_definitions", milestone_defs)
    assert await svc.apply_event_to_missions("track", "EVENT") == []


@pytest.mark.asyncio
async def test_apply_event_to_missions_skips_when_progress_row_missing(monkeypatch):
    async def fake_referral(referral_track_id):
        return referral()

    async def fake_defs(product, sub_product):
        return [definition()]

    async def fake_upsert(**kwargs):
        return None

    async def fake_progress(**kwargs):
        return None

    monkeypatch.setattr(svc, "_get_referral_row", fake_referral)
    monkeypatch.setattr(svc, "_get_mission_definitions", fake_defs)
    monkeypatch.setattr(svc, "_upsert_progress_row", fake_upsert)
    monkeypatch.setattr(svc, "_get_existing_progress", fake_progress)

    assert await svc.apply_event_to_missions("track", "EVENT") == []


@pytest.mark.asyncio
async def test_apply_event_to_missions_already_complete(monkeypatch):
    async def fake_referral(referral_track_id):
        return referral()

    async def fake_defs(product, sub_product):
        return [definition(amount=100)]

    async def fake_upsert(**kwargs):
        return None

    async def fake_progress(**kwargs):
        return progress_row(progress=1, goal=1, complete=True, bonus=True)

    monkeypatch.setattr(svc, "_get_referral_row", fake_referral)
    monkeypatch.setattr(svc, "_get_mission_definitions", fake_defs)
    monkeypatch.setattr(svc, "_upsert_progress_row", fake_upsert)
    monkeypatch.setattr(svc, "_get_existing_progress", fake_progress)

    result = await svc.apply_event_to_missions("track", "EVENT")

    assert result[0]["missionCode"] == "M1"
    assert result[0]["status"] == "COMPLETED"
    assert result[0]["isComplete"] is True
    assert result[0]["bonusRewardApplied"] is True


@pytest.mark.asyncio
async def test_apply_event_to_missions_updates_progress_without_reward_when_incomplete(monkeypatch):
    state = {
        "row": progress_row(progress=0, goal=2, complete=False, bonus=False),
    }

    async def fake_referral(referral_track_id):
        return referral()

    async def fake_defs(product, sub_product):
        return [definition(goal_count=2, amount=100)]

    async def fake_upsert(**kwargs):
        return None

    async def fake_progress(**kwargs):
        return state["row"]

    class UpdatingConn(FakeConn):
        async def execute(self, query, *params):
            self.calls.append(("execute", query, params))
            if "SET progress_count" in query:
                state["row"] = {
                    **state["row"],
                    "progress_count": 1,
                    "is_complete": False,
                }
            return "OK"

    monkeypatch.setattr(svc, "_get_referral_row", fake_referral)
    monkeypatch.setattr(svc, "_get_mission_definitions", fake_defs)
    monkeypatch.setattr(svc, "_upsert_progress_row", fake_upsert)
    monkeypatch.setattr(svc, "_get_existing_progress", fake_progress)

    patch_db(monkeypatch, UpdatingConn())

    result = await svc.apply_event_to_missions("track", "EVENT")

    assert result[0]["progressCount"] == 1
    assert result[0]["status"] == "IN_PROGRESS"
    assert result[0]["isComplete"] is False
    assert result[0]["bonusRewardApplied"] is False


@pytest.mark.asyncio
async def test_apply_event_to_missions_completes_without_reward_when_amount_zero(monkeypatch):
    state = {
        "row": progress_row(progress=0, goal=1, complete=False, bonus=False),
    }

    async def fake_referral(referral_track_id):
        return referral()

    async def fake_defs(product, sub_product):
        return [definition(amount=0)]

    async def fake_upsert(**kwargs):
        return None

    async def fake_progress(**kwargs):
        return state["row"]

    class UpdatingConn(FakeConn):
        async def execute(self, query, *params):
            self.calls.append(("execute", query, params))
            if "SET progress_count" in query:
                state["row"] = {
                    **state["row"],
                    "progress_count": 1,
                    "is_complete": True,
                    "completed_at": "done",
                }
            return "OK"

    monkeypatch.setattr(svc, "_get_referral_row", fake_referral)
    monkeypatch.setattr(svc, "_get_mission_definitions", fake_defs)
    monkeypatch.setattr(svc, "_upsert_progress_row", fake_upsert)
    monkeypatch.setattr(svc, "_get_existing_progress", fake_progress)

    patch_db(monkeypatch, UpdatingConn())

    result = await svc.apply_event_to_missions("track", "EVENT")

    assert result[0]["isComplete"] is True
    assert result[0]["bonusRewardApplied"] is False


@pytest.mark.asyncio
async def test_apply_event_to_missions_completes_and_applies_reward(monkeypatch):
    state = {
        "row": progress_row(progress=0, goal=1, complete=False, bonus=False),
    }

    async def fake_referral(referral_track_id):
        return referral()

    async def fake_defs(product, sub_product):
        return [definition(amount=200, category="BOOST")]

    async def fake_upsert(**kwargs):
        return None

    async def fake_progress(**kwargs):
        return state["row"]

    class RewardConn(FakeConn):
        async def execute(self, query, *params):
            self.calls.append(("execute", query, params))
            if "SET progress_count" in query:
                state["row"] = {
                    **state["row"],
                    "progress_count": 1,
                    "is_complete": True,
                    "completed_at": "done",
                }
            elif "bonus_reward_applied = TRUE" in query:
                state["row"] = {
                    **state["row"],
                    "bonus_reward_applied": True,
                }
            return "OK"

        async def fetchrow(self, query, *params):
            self.calls.append(("fetchrow", query, params))
            if "INSERT INTO rewards" in query:
                return {"id": "reward-id"}
            return None

    monkeypatch.setattr(svc, "_get_referral_row", fake_referral)
    monkeypatch.setattr(svc, "_get_mission_definitions", fake_defs)
    monkeypatch.setattr(svc, "_upsert_progress_row", fake_upsert)
    monkeypatch.setattr(svc, "_get_existing_progress", fake_progress)

    patch_db(monkeypatch, RewardConn())

    result = await svc.apply_event_to_missions("track", "EVENT")

    assert result[0]["category"] == "BOOST"
    assert result[0]["isComplete"] is True
    assert result[0]["bonusRewardApplied"] is True


@pytest.mark.asyncio
async def test_apply_event_to_missions_reward_conflict_does_not_mark_applied(monkeypatch):
    state = {
        "row": progress_row(progress=0, goal=1, complete=False, bonus=False),
    }

    async def fake_referral(referral_track_id):
        return referral()

    async def fake_defs(product, sub_product):
        return [definition(amount=200)]

    async def fake_upsert(**kwargs):
        return None

    async def fake_progress(**kwargs):
        return state["row"]

    class ConflictConn(FakeConn):
        async def execute(self, query, *params):
            self.calls.append(("execute", query, params))
            if "SET progress_count" in query:
                state["row"] = {
                    **state["row"],
                    "progress_count": 1,
                    "is_complete": True,
                    "completed_at": "done",
                }
            return "OK"

        async def fetchrow(self, query, *params):
            self.calls.append(("fetchrow", query, params))
            return None

    monkeypatch.setattr(svc, "_get_referral_row", fake_referral)
    monkeypatch.setattr(svc, "_get_mission_definitions", fake_defs)
    monkeypatch.setattr(svc, "_upsert_progress_row", fake_upsert)
    monkeypatch.setattr(svc, "_get_existing_progress", fake_progress)

    patch_db(monkeypatch, ConflictConn())

    result = await svc.apply_event_to_missions("track", "EVENT")

    assert result[0]["isComplete"] is True
    assert result[0]["bonusRewardApplied"] is False