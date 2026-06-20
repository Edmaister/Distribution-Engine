from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import datetime, timezone

import pytest

import services.recommendation_compliance_service as svc


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


def _context(**overrides):
    data = {
        "referral_track_id": "track-1",
        "status": "FUNDED",
        "next_milestone": "SALARY_SWITCHED",
        "product": "TRANSACTIONAL",
        "sub_product": "GOLD",
        "progress_percent": 75,
        "is_complete": False,
        "completed_at": None,
        "reward_preview_amount": 200,
        "is_credit_related": False,
    }
    data.update(overrides)
    return svc.RecommendationContext(**data)


def _template(template_code="SALARY_SWITCH_INFO"):
    return {
        "template_code": template_code,
        "category": "NEXT_BEST_ACTION",
        "title_template": "Next step: {next_milestone}",
        "body_template": "Complete {next_milestone} to qualify for R{reward_amount}.",
        "cta_label": "Learn more",
        "cta_action": "OPEN_INFO",
        "is_credit_related": False,
        "requires_disclaimer": True,
        "regulatory_tags": ["TCF", "FAIS"],
        "template_version": "v1",
    }


def test_helpers():
    assert svc._normalise_text(" x ") == "x"
    assert svc._normalise_text(None) == ""
    assert svc._milestone_to_display("SALARY_SWITCHED") == "Salary Switched"
    assert svc._infer_reward_preview_amount("SALARY_SWITCHED") == 200
    assert svc._infer_reward_preview_amount("DEBIT_ORDER_SWITCHED") == 200
    assert svc._infer_reward_preview_amount("FIRST_TRANSACTION_COMPLETED") == 100
    assert svc._infer_reward_preview_amount("FIRST_PREMIUM_PAID") == 250
    assert svc._infer_reward_preview_amount("OTHER") is None
    assert svc._to_json(None) == "{}"


@pytest.mark.asyncio
async def test_fetch_referral_context_found(monkeypatch):
    completed_at = datetime(2026, 1, 1, tzinfo=timezone.utc)
    conn = FakeConn(
        row={
            "referral_track_id": "track-1",
            "status": "FUNDED",
            "next_milestone": "SALARY_SWITCHED",
            "product": "TRANSACTIONAL",
            "sub_product": "GOLD",
            "progress_percent": 75,
            "is_complete": False,
            "completed_at": completed_at,
        }
    )
    patch_db(monkeypatch, conn)

    result = await svc._fetch_referral_context("track-1")

    assert result.referral_track_id == "track-1"
    assert result.reward_preview_amount == 200
    assert result.completed_at == completed_at


@pytest.mark.asyncio
async def test_fetch_referral_context_missing(monkeypatch):
    conn = FakeConn(row=None)
    patch_db(monkeypatch, conn)

    assert await svc._fetch_referral_context("missing") is None


@pytest.mark.asyncio
async def test_get_active_policy_from_db(monkeypatch):
    conn = FakeConn(
        row={
            "policy_code": "P1",
            "policy_version": "v1",
            "banned_phrases": ["x"],
            "advisory_markers": [],
            "pressure_markers": [],
            "blocked_ctas": [],
            "allowed_ctas": ["Learn more"],
        }
    )
    patch_db(monkeypatch, conn)

    result = await svc._get_active_policy("P1")

    assert result["policy_code"] == "P1"
    assert result["policy_version"] == "v1"


@pytest.mark.asyncio
async def test_get_active_policy_default(monkeypatch):
    conn = FakeConn(row=None)
    patch_db(monkeypatch, conn)

    result = await svc._get_active_policy()

    assert result["policy_code"] == svc.DEFAULT_POLICY_CODE
    assert "do this now" in result["banned_phrases"]


@pytest.mark.asyncio
async def test_get_template_found_and_missing(monkeypatch):
    conn = FakeConn(row=_template())
    patch_db(monkeypatch, conn)

    assert (await svc._get_template("SALARY_SWITCH_INFO"))["template_code"] == "SALARY_SWITCH_INFO"

    conn = FakeConn(row=None)
    patch_db(monkeypatch, conn)

    assert await svc._get_template("MISSING") is None


@pytest.mark.asyncio
async def test_get_disclosures_empty_and_found(monkeypatch):
    assert await svc._get_disclosures([]) == []

    conn = FakeConn(
        rows=[
            {"disclosure_code": "A", "disclosure_text": "Text A"},
            {"disclosure_code": "B", "disclosure_text": "Text B"},
        ]
    )
    patch_db(monkeypatch, conn)

    result = await svc._get_disclosures(["B", "A", "C"])

    assert result == ["Text B", "Text A"]


@pytest.mark.asyncio
async def test_record_display_audit(monkeypatch):
    conn = FakeConn()
    patch_db(monkeypatch, conn)

    await svc._record_display_audit(
        referral_track_id="track-1",
        recommendation={
            "recommendationId": "rec-1",
            "templateCode": "T1",
            "templateVersion": "v1",
            "policyVersion": "p1",
            "category": "INFO",
            "title": "Title",
            "body": "Body",
            "ctaLabel": "Learn more",
            "ctaAction": "OPEN_INFO",
            "rewardPreview": None,
            "compliance": {"ok": True},
            "disclosures": ["A"],
        },
        channel="API",
    )

    assert conn.calls[0][0] == "execute"


def test_build_candidates_all_branches():
    assert svc._build_candidates(_context(is_complete=True))[0]["templateCode"] == "PROGRESS_COMPLETE_INFO"
    assert any(x["templateCode"] == "SALARY_SWITCH_INFO" for x in svc._build_candidates(_context(next_milestone="SALARY_SWITCHED")))
    assert any(x["templateCode"] == "DEBIT_ORDER_SWITCH_INFO" for x in svc._build_candidates(_context(next_milestone="DEBIT_ORDER_SWITCHED")))
    assert any(x["templateCode"] == "FIRST_TRANSACTION_INFO" for x in svc._build_candidates(_context(next_milestone="FIRST_TRANSACTION_COMPLETED")))
    assert any(x["templateCode"] == "PROGRESS_INFO" for x in svc._build_candidates(_context(status="VALIDATED", next_milestone=None)))
    insurance_items = svc._build_candidates(
        _context(
            journey_code="INSURANCE_POLICY",
            status="QUOTE_ACCEPTED",
            next_milestone="POLICY_ISSUED",
            product="INSURANCE",
            sub_product="FUNERAL_PLAN",
        )
    )
    assert any(x["templateCode"] == "INSURANCE_POLICY_ACTIVATION_INFO" for x in insurance_items)
    assert any(x["templateCode"] == "INSURANCE_PROGRESS_INFO" for x in insurance_items)


@pytest.mark.asyncio
async def test_render_candidate_found_and_missing(monkeypatch):
    async def fake_get_template(template_code):
        return _template(template_code)

    monkeypatch.setattr(svc, "_get_template", fake_get_template)

    result = await svc._render_candidate(
        {
            "recommendationId": "salary_switch_info",
            "templateCode": "SALARY_SWITCH_INFO",
            "category": "NEXT_BEST_ACTION",
            "priority": 1,
        },
        _context(),
    )

    assert result["recommendationId"] == "salary_switch_info"
    assert result["rewardPreview"]["amount"] == 200

    async def fake_missing(template_code):
        return None

    monkeypatch.setattr(svc, "_get_template", fake_missing)

    assert await svc._render_candidate({"templateCode": "MISSING"}, _context()) is None


def test_reward_preview_branches():
    assert svc._reward_preview(_context(reward_preview_amount=None)) is None
    assert "salary switch" in svc._reward_preview(_context(next_milestone="SALARY_SWITCHED"))["conditionSummary"]
    assert "debit order" in svc._reward_preview(_context(next_milestone="DEBIT_ORDER_SWITCHED"))["conditionSummary"]
    assert "first qualifying transaction" in svc._reward_preview(_context(next_milestone="FIRST_TRANSACTION_COMPLETED", reward_preview_amount=100))["conditionSummary"]


def test_classify_risk_all_branches():
    assert svc._classify_risk(
        {"title": "Do this now", "body": "", "ctaLabel": "Learn more"},
        {"banned_phrases": ["do this now"], "advisory_markers": [], "pressure_markers": [], "blocked_ctas": []},
    )["blockedReason"].startswith("banned_phrase:")

    assert svc._classify_risk(
        {"title": "Best for you", "body": "", "ctaLabel": "Learn more"},
        {"banned_phrases": [], "advisory_markers": ["best for you"], "pressure_markers": [], "blocked_ctas": []},
    )["isAdvice"] is True

    assert svc._classify_risk(
        {"title": "", "body": "", "ctaLabel": "Claim now"},
        {"banned_phrases": [], "advisory_markers": [], "pressure_markers": [], "blocked_ctas": ["Claim now"]},
    )["blockedReason"].startswith("blocked_cta:")

    result = svc._classify_risk(
        {"title": "Available now", "body": "urgent info", "ctaLabel": "Learn more"},
        {"banned_phrases": [], "advisory_markers": [], "pressure_markers": ["now", "urgent"], "blocked_ctas": []},
    )
    assert result["blocked"] is False
    assert result["pressureScore"] == 2


def test_rewrite_to_safe_language():
    rec = {
        "title": "Do this now",
        "body": "Guaranteed reward if you must do this now",
        "ctaLabel": "Claim now",
        "ctaAction": "OPEN_JOURNEY",
    }

    safe = svc._rewrite_to_safe_language(rec)

    assert "Do this now" not in safe["title"]
    assert "Guaranteed reward" not in safe["body"]
    assert safe["ctaLabel"] == "Learn more"
    assert safe["ctaAction"] == "OPEN_INFO"


def test_build_compliance_metadata_with_reward_and_credit():
    context = _context(is_credit_related=True)
    meta = svc._build_compliance_metadata(context, {"isAdvice": True, "pressureScore": 2})

    assert meta["isAdvice"] is True
    assert "GENERAL_INFO_ONLY" in meta["disclaimerCodes"]
    assert "REWARD_CONDITIONAL" in meta["disclaimerCodes"]
    assert "CREDIT_DISCLOSURE" in meta["disclaimerCodes"]
    assert "NCA" in meta["regulatoryTags"]
    assert meta["fairnessScore"] == 80
    assert meta["transparencyScore"] == 95


def test_build_compliance_metadata_for_insurance():
    context = _context(
        journey_code="INSURANCE_POLICY",
        product="INSURANCE",
        sub_product="FUNERAL_PLAN",
        next_milestone="FIRST_PREMIUM_PAID",
        reward_preview_amount=250,
    )

    meta = svc._build_compliance_metadata(context, {"isAdvice": False, "pressureScore": 0})

    assert "INSURANCE_PRODUCT_INFO" in meta["disclaimerCodes"]
    assert "INSURANCE_CONDUCT" in meta["regulatoryTags"]
    assert "BANKING_CODE" not in meta["regulatoryTags"]


@pytest.mark.asyncio
async def test_generate_recommendations_for_insurance_policy(monkeypatch):
    async def fake_context(referral_track_id):
        return _context(
            journey_code="INSURANCE_POLICY",
            status="POLICY_ISSUED",
            next_milestone="FIRST_PREMIUM_PAID",
            product="INSURANCE",
            sub_product="FUNERAL_PLAN",
            reward_preview_amount=250,
        )

    async def fake_policy():
        return svc._default_policy()

    async def fake_template(template_code):
        return _template(template_code)

    async def fake_disclosures(codes):
        return [f"DISCLOSURE::{code}" for code in codes]

    monkeypatch.setattr(svc, "_fetch_referral_context", fake_context)
    monkeypatch.setattr(svc, "_get_active_policy", fake_policy)
    monkeypatch.setattr(svc, "_get_template", fake_template)
    monkeypatch.setattr(svc, "_get_disclosures", fake_disclosures)

    items = await svc.generate_recommendations_for_referral("track-1", audit=False)

    assert items[0]["templateCode"] == "INSURANCE_POLICY_ACTIVATION_INFO"
    assert "INSURANCE_PRODUCT_INFO" in items[0]["compliance"]["disclaimerCodes"]


@pytest.mark.asyncio
async def test_generate_recommendations_for_salary_switch(monkeypatch):
    async def fake_context(referral_track_id):
        return _context()

    async def fake_policy():
        return {
            "policy_version": "2026-04-08",
            "banned_phrases": ["do this now", "earn now"],
            "advisory_markers": ["best for you"],
            "pressure_markers": ["now", "urgent"],
            "blocked_ctas": ["Claim now"],
            "allowed_ctas": ["Learn more"],
        }

    async def fake_template(template_code):
        return _template(template_code)

    async def fake_disclosures(codes):
        return [f"DISCLOSURE::{code}" for code in codes]

    async def fake_audit(**kwargs):
        return None

    monkeypatch.setattr(svc, "_fetch_referral_context", fake_context)
    monkeypatch.setattr(svc, "_get_active_policy", fake_policy)
    monkeypatch.setattr(svc, "_get_template", fake_template)
    monkeypatch.setattr(svc, "_get_disclosures", fake_disclosures)
    monkeypatch.setattr(svc, "_record_display_audit", fake_audit)

    items = await svc.generate_recommendations_for_referral("track-1", audit=True)

    assert len(items) >= 1
    assert items[0]["recommendationId"] == "salary_switch_info"
    assert "GENERAL_INFO_ONLY" in items[0]["compliance"]["disclaimerCodes"]


@pytest.mark.asyncio
async def test_generate_recommendations_returns_empty_when_referral_missing(monkeypatch):
    async def fake_context(referral_track_id):
        return None

    monkeypatch.setattr(svc, "_fetch_referral_context", fake_context)

    assert await svc.generate_recommendations_for_referral("missing-track", audit=False) == []


@pytest.mark.asyncio
async def test_generate_recommendations_skips_missing_template(monkeypatch):
    async def fake_context(referral_track_id):
        return _context()

    async def fake_policy():
        return svc._default_policy()

    async def fake_render(candidate, context):
        return None

    monkeypatch.setattr(svc, "_fetch_referral_context", fake_context)
    monkeypatch.setattr(svc, "_get_active_policy", fake_policy)
    monkeypatch.setattr(svc, "_render_candidate", fake_render)

    assert await svc.generate_recommendations_for_referral("track-1", audit=False) == []


@pytest.mark.asyncio
async def test_generate_recommendations_blocks_after_rewrite(monkeypatch):
    async def fake_context(referral_track_id):
        return _context()

    async def fake_policy():
        return {
            "policy_version": "v1",
            "banned_phrases": ["still blocked"],
            "advisory_markers": [],
            "pressure_markers": [],
            "blocked_ctas": [],
        }

    async def fake_render(candidate, context):
        return {
            "recommendationId": "blocked",
            "category": "INFO",
            "title": "still blocked",
            "body": "still blocked",
            "ctaLabel": "Learn more",
            "ctaAction": "OPEN_INFO",
            "priority": 1,
            "rewardPreview": None,
            "disclosures": [],
            "compliance": {},
            "templateCode": "T",
            "templateVersion": "v1",
            "policyVersion": "v1",
        }

    monkeypatch.setattr(svc, "_fetch_referral_context", fake_context)
    monkeypatch.setattr(svc, "_get_active_policy", fake_policy)
    monkeypatch.setattr(svc, "_render_candidate", fake_render)

    assert await svc.generate_recommendations_for_referral("track-1", audit=False) == []
