from __future__ import annotations

from decimal import Decimal

import pytest

from services import outcome_money_reconciliation_service as service


class FakeConnection:
    def __init__(self, rows):
        self.rows = rows
        self.calls = []

    async def fetch(self, query, *args):
        self.calls.append((query, args))
        return self.rows

    def transaction(self):
        return FakeTransaction()


class FakeTransaction:
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False


class FakeConnectionContext:
    def __init__(self, conn):
        self.conn = conn

    async def __aenter__(self):
        return self.conn

    async def __aexit__(self, exc_type, exc, tb):
        return False


@pytest.mark.asyncio
async def test_outcome_money_map_summarises_ready_and_attention(monkeypatch):
    conn = FakeConnection(
        [
            {
                "referral_track_id": "11111111-1111-1111-1111-111111111111",
                "tenant_code": "FNB",
                "distributor_code": "DIST-001",
                "sponsor_code": "FNB",
                "campaign_code": "CARD-2026",
                "opportunity_code": "CARD",
                "opportunity_title": "Card activations",
                "product": "CARD",
                "sub_product": "GOLD",
                "journey_code": "BANKING_TRANSACTIONAL",
                "status": "COMPLETED",
                "completed_at": None,
                "reward_count": 1,
                "reward_amount": Decimal("100.00"),
                "commission_count": 1,
                "commission_amount": Decimal("10.00"),
                "wallet_movement_count": 1,
                "wallet_movement_amount": Decimal("10.00"),
                "invoice_count": 1,
                "invoiced_amount": Decimal("100.00"),
                "settlement_count": 1,
                "settled_count": 1,
                "settled_amount": Decimal("100.00"),
                "exception_count": 0,
            },
            {
                "referral_track_id": "22222222-2222-2222-2222-222222222222",
                "tenant_code": "FNB",
                "distributor_code": "DIST-002",
                "sponsor_code": "FNB",
                "campaign_code": "CARD-2026",
                "opportunity_code": "CARD",
                "opportunity_title": "Card activations",
                "product": "CARD",
                "sub_product": "GOLD",
                "journey_code": "BANKING_TRANSACTIONAL",
                "status": "COMPLETED",
                "completed_at": None,
                "reward_count": 1,
                "reward_amount": Decimal("100.00"),
                "commission_count": 1,
                "commission_amount": Decimal("10.00"),
                "wallet_movement_count": 0,
                "wallet_movement_amount": Decimal("0.00"),
                "invoice_count": 0,
                "invoiced_amount": Decimal("0.00"),
                "settlement_count": 0,
                "settled_count": 0,
                "settled_amount": Decimal("0.00"),
                "exception_count": 1,
            },
        ]
    )

    monkeypatch.setattr(service, "db_connection", lambda: FakeConnectionContext(conn))

    result = await service.get_outcome_money_map(
        tenant_code="FNB",
        sponsor_code="FNB",
        distributor_code=None,
        limit=25,
    )

    assert conn.calls[0][1] == ("FNB", "FNB", None, 25)
    assert result["summary"]["completed_outcome_count"] == 2
    assert result["summary"]["ready_count"] == 1
    assert result["summary"]["attention_count"] == 1
    assert result["summary"]["money_completion_rate"] == Decimal("0.5000")
    assert result["summary"]["attention_breakdown"] == [
        {
            "key": "wallet_movement_count",
            "label": "Distributor wallet movement",
            "count": 1,
            "owner": "Distributor - Demand",
            "action": "Check wallet crediting and ledger correlation.",
        },
        {
            "key": "invoice_count",
            "label": "Producer invoice line",
            "count": 1,
            "owner": "Producer - Supply",
            "action": "Check sponsor billing utilisation and invoice generation.",
        },
        {
            "key": "settled_count",
            "label": "Settlement settled",
            "count": 1,
            "owner": "Amplifi Admin",
            "action": "Check settlement batch, provider response, and approval state.",
        },
        {
            "key": "exception_count",
            "label": "Open exception",
            "count": 1,
            "owner": "Amplifi Admin",
            "action": "Review and resolve the settlement exception.",
        },
    ]
    assert result["items"][0]["money_status"] == "READY"
    assert result["items"][1]["money_status"] == "ATTENTION"
    assert "Distributor wallet movement" in result["items"][1]["missing_steps"]
    assert {
        "type": "CREATE_INVOICE_EVIDENCE",
        "label": "Create producer invoice evidence",
        "owner": "Producer - Supply",
        "action": "Check sponsor billing utilisation and invoice generation.",
        "available": True,
    } in result["items"][1]["repair_actions"]
    assert result["items"][1]["repair_actions"][-1] == {
        "type": "RESOLVE_SETTLEMENT_EXCEPTIONS",
        "label": "Resolve settlement exception",
        "owner": "Amplifi Admin",
        "action": "Review and resolve the settlement exception.",
        "available": True,
        "exception_ids": [],
    }
    assert result["journey"][0]["step"] == "Completed outcome"


@pytest.mark.asyncio
async def test_producer_outcome_money_review_is_role_scoped(monkeypatch):
    async def fake_get_outcome_money_map(**kwargs):
        assert kwargs == {
            "tenant_code": "FNB",
            "sponsor_code": "BOXER",
            "limit": 25,
        }
        return {
            "tenant_code": "FNB",
            "sponsor_code": "BOXER",
            "distributor_code": None,
            "limit": 25,
            "items": [
                {
                    "referral_track_id": "ref-1",
                    "tenant_code": "FNB",
                    "sponsor_code": "BOXER",
                    "distributor_code": "DIST-001",
                    "opportunity_title": "Policy activation",
                    "money_status": "ATTENTION",
                    "missing_steps": ["Producer invoice line", "Settlement settled"],
                    "repair_actions": [
                        {
                            "type": "CREATE_INVOICE_EVIDENCE",
                            "owner": "Producer - Supply",
                            "available": True,
                        },
                        {
                            "type": "CREATE_SETTLEMENT_EVIDENCE",
                            "owner": "Amplifi Admin",
                            "available": True,
                        },
                    ],
                    "reward_count": 1,
                    "commission_count": 1,
                    "wallet_movement_count": 1,
                    "invoice_count": 0,
                    "settled_count": 0,
                    "exception_count": 0,
                }
            ],
        }

    monkeypatch.setattr(service, "get_outcome_money_map", fake_get_outcome_money_map)

    review = await service.get_producer_outcome_money_review(
        tenant_code="fnb",
        producer_code="boxer",
        limit=25,
    )

    assert review["surface"] == "Producer - Supply"
    assert review["summary"]["attention_count"] == 1
    assert review["items"][0]["missing_owned_steps"] == ["Producer invoice line"]
    assert review["items"][0]["owned_actions"][0]["type"] == "CREATE_INVOICE_EVIDENCE"
    assert (
        review["items"][0]["admin_follow_up"][0]["type"] == "CREATE_SETTLEMENT_EVIDENCE"
    )


@pytest.mark.asyncio
async def test_distributor_outcome_money_review_is_role_scoped(monkeypatch):
    async def fake_get_outcome_money_map(**kwargs):
        assert kwargs == {
            "tenant_code": "FNB",
            "distributor_code": "DIST-001",
            "limit": 25,
        }
        return {
            "tenant_code": "FNB",
            "sponsor_code": None,
            "distributor_code": "DIST-001",
            "limit": 25,
            "items": [
                {
                    "referral_track_id": "ref-1",
                    "tenant_code": "FNB",
                    "sponsor_code": "BOXER",
                    "distributor_code": "DIST-001",
                    "opportunity_title": "Policy activation",
                    "money_status": "ATTENTION",
                    "missing_steps": ["Distributor wallet movement"],
                    "repair_actions": [
                        {
                            "type": "CREATE_WALLET_EVIDENCE",
                            "owner": "Distributor - Demand",
                            "available": True,
                        }
                    ],
                    "reward_count": 1,
                    "commission_count": 1,
                    "wallet_movement_count": 0,
                    "invoice_count": 1,
                    "settled_count": 1,
                    "exception_count": 0,
                }
            ],
        }

    monkeypatch.setattr(service, "get_outcome_money_map", fake_get_outcome_money_map)

    review = await service.get_distributor_outcome_money_review(
        tenant_code="fnb",
        distributor_code="dist-001",
        limit=25,
    )

    assert review["surface"] == "Distributor - Demand"
    assert review["summary"]["attention_count"] == 1
    assert review["items"][0]["missing_owned_steps"] == ["Distributor wallet movement"]
    assert review["items"][0]["owned_actions"][0]["type"] == "CREATE_WALLET_EVIDENCE"


def test_repair_actions_offer_settlement_evidence_after_invoice():
    actions = service._repair_actions(
        {
            "reward_count": 1,
            "invoice_count": 1,
            "exception_count": 0,
        },
        ["Settlement settled"],
    )

    assert actions == [
        {
            "type": "CREATE_SETTLEMENT_EVIDENCE",
            "label": "Create settlement evidence",
            "owner": "Amplifi Admin",
            "action": "Check settlement batch, provider response, and approval state.",
            "available": True,
        }
    ]


@pytest.mark.asyncio
async def test_create_outcome_settlement_evidence(monkeypatch):
    conn = FakeConnection(
        [
            {
                "settlement_id": "33333333-3333-3333-3333-333333333333",
                "reward_id": "44444444-4444-4444-4444-444444444444",
                "audit_id": "55555555-5555-5555-5555-555555555555",
                "amount": Decimal("100.00"),
                "currency": "ZAR",
                "status": "SETTLED",
                "settled_at": None,
            }
        ]
    )

    monkeypatch.setattr(service, "db_connection", lambda: FakeConnectionContext(conn))

    result = await service.create_outcome_settlement_evidence(
        referral_track_id="11111111-1111-1111-1111-111111111111",
        created_by="ops-user",
        tenant_code="FNB",
    )

    assert conn.calls[0][1] == (
        "11111111-1111-1111-1111-111111111111",
        "FNB",
        "ops-user",
    )
    assert result["settlement_count"] == 1
    assert result["settled_amount"] == Decimal("100.00")
    assert result["items"][0]["status"] == "SETTLED"


def test_repair_actions_offer_ledger_repairs_in_order():
    reward_actions = service._repair_actions(
        {"product": "FUNERAL_PLAN"},
        ["Reward recorded"],
    )
    commission_actions = service._repair_actions(
        {
            "reward_count": 1,
            "distributor_code": "DIST-001",
            "sponsor_code": "INSURECO",
        },
        ["Commission calculated"],
    )
    wallet_actions = service._repair_actions(
        {"commission_count": 1},
        ["Distributor wallet movement"],
    )

    assert reward_actions[0]["type"] == "CREATE_REWARD_EVIDENCE"
    assert reward_actions[0]["available"] is True
    assert commission_actions[0]["type"] == "CREATE_COMMISSION_EVIDENCE"
    assert commission_actions[0]["available"] is True
    assert wallet_actions[0]["type"] == "CREATE_WALLET_EVIDENCE"
    assert wallet_actions[0]["available"] is True


@pytest.mark.asyncio
async def test_create_outcome_reward_evidence(monkeypatch):
    conn = FakeConnection(
        [
            {
                "reward_id": "66666666-6666-6666-6666-666666666666",
                "referral_track_id": "11111111-1111-1111-1111-111111111111",
                "reward_type": "CASH",
                "product": "FUNERAL_PLAN",
                "amount": Decimal("100.00"),
                "tenant_code": "FNB",
                "created_at": None,
            }
        ]
    )

    monkeypatch.setattr(service, "db_connection", lambda: FakeConnectionContext(conn))

    result = await service.create_outcome_reward_evidence(
        referral_track_id="11111111-1111-1111-1111-111111111111",
        created_by="ops-user",
        tenant_code="FNB",
    )

    assert conn.calls[0][1] == ("11111111-1111-1111-1111-111111111111", "FNB")
    assert result["reward_count"] == 1
    assert result["reward_amount"] == Decimal("100.00")


@pytest.mark.asyncio
async def test_create_outcome_commission_evidence(monkeypatch):
    conn = FakeConnection(
        [
            {
                "commission_event_id": "77777777-7777-7777-7777-777777777777",
                "tenant_code": "FNB",
                "distributor_id": "88888888-8888-8888-8888-888888888888",
                "distributor_code": "DIST-001",
                "wallet_id": "99999999-9999-9999-9999-999999999999",
                "rule_id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
                "sponsor_code": "INSURECO",
                "campaign_code": "FUNERAL",
                "source_event_id": "11111111-1111-1111-1111-111111111111",
                "activity_type": "COMPLETED_OUTCOME_REPAIR",
                "sale_amount": Decimal("100.00"),
                "commission_amount": Decimal("10.00"),
                "currency": "ZAR",
                "commission_status": "CALCULATED",
                "correlation_id": "11111111-1111-1111-1111-111111111111",
                "metadata": {},
                "created_at": None,
            }
        ]
    )

    monkeypatch.setattr(service, "db_connection", lambda: FakeConnectionContext(conn))

    result = await service.create_outcome_commission_evidence(
        referral_track_id="11111111-1111-1111-1111-111111111111",
        created_by="ops-user",
        tenant_code="FNB",
    )

    assert conn.calls[0][1] == (
        "11111111-1111-1111-1111-111111111111",
        "FNB",
        "ops-user",
    )
    assert result["commission_count"] == 1
    assert result["commission_amount"] == Decimal("10.00")


@pytest.mark.asyncio
async def test_create_outcome_wallet_evidence(monkeypatch):
    conn = FakeConnection(
        [
            {
                "ledger_id": "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
                "wallet_id": "99999999-9999-9999-9999-999999999999",
                "distributor_id": "88888888-8888-8888-8888-888888888888",
                "tenant_code": "FNB",
                "transaction_type": "CREDIT",
                "amount": Decimal("10.00"),
                "balance_before": Decimal("0.00"),
                "balance_after": Decimal("10.00"),
                "correlation_id": "11111111-1111-1111-1111-111111111111",
                "metadata": {},
                "created_at": None,
            }
        ]
    )

    monkeypatch.setattr(service, "db_connection", lambda: FakeConnectionContext(conn))

    result = await service.create_outcome_wallet_evidence(
        referral_track_id="11111111-1111-1111-1111-111111111111",
        created_by="ops-user",
        tenant_code="FNB",
    )

    assert conn.calls[0][1] == (
        "11111111-1111-1111-1111-111111111111",
        "FNB",
        "ops-user",
    )
    assert result["wallet_movement_count"] == 1
    assert result["wallet_movement_amount"] == Decimal("10.00")
