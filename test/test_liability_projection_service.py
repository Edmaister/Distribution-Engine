from __future__ import annotations

from decimal import Decimal

import pytest

from services import liability_projection_service as service


def _trace(*, missing_evidence=None):
    return {
        "trace_id": "outcome:referral_track_id:track-1",
        "trace_completeness": "PARTIAL" if missing_evidence else "COMPLETE",
        "tenant_code": "FNB",
        "lookup": {"type": "REFERRAL_TRACK_ID", "value": "track-1"},
        "sections": {
            "reward": {
                "items": [
                    {
                        "source": "rewards",
                        "reward_id": "reward-1",
                        "beneficiary_type": "REFERRER",
                        "beneficiary_ref": "safe-ref",
                        "reward_type": "CASH",
                        "amount": "100.00",
                        "status": "APPLIED",
                    }
                ]
            },
            "commission": {
                "items": [
                    {
                        "commission_event_id": "commission-1",
                        "commission_status": "CREDITED",
                        "commission_amount": "25.00",
                        "source_event_id": "track-1",
                    }
                ]
            },
            "funding": {
                "items": [
                    {
                        "source": "funding_reservations",
                        "funding_id": "funding-1",
                        "reward_id": "reward-1",
                        "amount": "100.00",
                        "status": "RESERVED",
                    }
                ]
            },
            "fulfilment": {
                "items": [
                    {
                        "audit_id": "audit-1",
                        "status": "SUCCESS",
                        "reward_value": "100.00",
                    }
                ]
            },
            "settlement": {
                "items": [
                    {
                        "settlement_id": "settlement-1",
                        "reward_id": "reward-1",
                        "amount": "100.00",
                        "status": "SETTLED",
                        "exception_count": 0,
                    }
                ]
            },
            "audit": {"items": [{"audit_id": "admin-audit-1"}]},
        },
        "missing_evidence": missing_evidence or [],
        "source_warnings": [],
        "support_trace": {
            "trace_id": "outcome:referral_track_id:track-1",
            "audit_references": [{"audit_id": "admin-audit-1"}],
            "audit_reference_count": 1,
            "correlation_references": [
                {
                    "section": "fulfilment",
                    "source": "fulfilment_audit",
                    "reference_type": "correlation_id",
                    "value": "track-1",
                    "related_id": "audit-1",
                }
            ],
            "correlation_reference_count": 1,
            "missing_audit_evidence": [],
        },
        "redactions": [{"field": "referrer_ucn"}],
        "generated_at": "2026-06-22T00:00:00Z",
    }


def test_derive_liability_projection_preserves_categories_and_phase_totals():
    result = service.derive_liability_projection(_trace())

    assert result["projection_type"] == "OUTCOME_LIABILITY"
    assert result["tenant_code"] == "FNB"
    assert result["liability_completeness"] == "COMPLETE"

    assert result["totals"]["obligation_total"] == Decimal("125.00")
    assert result["totals"]["reserved_total"] == Decimal("100.00")
    assert result["totals"]["fulfilled_total"] == Decimal("125.00")
    assert result["totals"]["settled_total"] == Decimal("100.00")
    assert result["support_trace"]["audit_reference_count"] == 1
    assert result["support_trace"]["correlation_reference_count"] == 1

    # Funding, fulfilment, and settlement are phase evidence; they must not
    # inflate the source obligation total.
    assert result["totals"]["obligation_total"] != Decimal("425.00")

    categories = {item["liability_category"] for item in result["items"]}
    assert "REFERRER_REWARD" in categories
    assert "DISTRIBUTOR_COMMISSION" in categories


def test_derive_liability_projection_surfaces_missing_money_evidence_only():
    result = service.derive_liability_projection(
        _trace(
            missing_evidence=[
                {
                    "section": "funding",
                    "code": "JOIN_AMBIGUOUS",
                    "severity": "WARNING",
                    "message": "Funding join is weak.",
                    "source": "funding_reservations",
                },
                {
                    "section": "webhooks",
                    "code": "JOIN_AMBIGUOUS",
                    "severity": "WARNING",
                    "message": "Webhook join is weak.",
                    "source": "partner_webhook_deliveries",
                },
                {
                    "section": "participants",
                    "code": "SECTION_NOT_REQUESTED",
                    "severity": "INFO",
                    "message": "participants evidence was not requested.",
                    "source": "outcome_trace_service",
                },
            ]
        )
    )

    assert result["liability_completeness"] == "PARTIAL"
    assert result["missing_evidence"] == [
        {
            "section": "funding",
            "code": "JOIN_AMBIGUOUS",
            "severity": "WARNING",
            "message": "Funding join is weak.",
            "source": "funding_reservations",
        }
    ]


def test_derive_liability_projection_dedupes_duplicate_reward_evidence():
    trace = _trace()
    trace["sections"]["reward"]["items"].append(
        {
            "source": "referral_rewards",
            "reward_id": "reward-1",
            "beneficiary_type": "REFERRER",
            "beneficiary_ref": "safe-ref",
            "reward_type": "CASH",
            "amount": "100.00",
            "status": "EARNED",
        }
    )

    result = service.derive_liability_projection(trace)

    assert result["totals"]["obligation_total"] == Decimal("125.00")
    assert result["source_warnings"][0]["code"] == "DUPLICATE_SOURCE_EVIDENCE"


@pytest.mark.asyncio
async def test_get_outcome_liability_projection_uses_money_trace_sections(monkeypatch):
    captured = {}

    async def fake_get_outcome_trace(**kwargs):
        captured.update(kwargs)
        return _trace()

    monkeypatch.setattr(service, "get_outcome_trace", fake_get_outcome_trace)

    result = await service.get_outcome_liability_projection(
        tenant_code="FNB",
        referral_track_id="track-1",
        identity={"role": "ADMIN"},
    )

    assert captured["tenant_code"] == "FNB"
    assert captured["referral_track_id"] == "track-1"
    assert captured["include_sections"] == [
        "reward",
        "commission",
        "funding",
        "fulfilment",
        "settlement",
        "audit",
    ]
    assert result["totals"]["obligation_total"] == Decimal("125.00")
