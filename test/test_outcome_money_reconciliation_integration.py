from __future__ import annotations

import uuid
from decimal import Decimal

import pytest
import pytest_asyncio

from services.outcome_money_reconciliation_service import (
    create_outcome_invoice_evidence,
    get_outcome_money_map,
    resolve_outcome_settlement_exceptions,
)
from utils.db import async_db_cursor


pytestmark = [pytest.mark.asyncio]


@pytest_asyncio.fixture
async def completed_money_trail():
    tenant_code = "FNB"
    sponsor_code = f"SPONSOR-{uuid.uuid4().hex[:8].upper()}"
    campaign_code = f"CAMP-{uuid.uuid4().hex[:8].upper()}"
    distributor_code = f"DIST-{uuid.uuid4().hex[:8].upper()}"
    referral_track_id = uuid.uuid4()
    referrer_code_id = uuid.uuid4()
    distributor_id = uuid.uuid4()
    opportunity_id = uuid.uuid4()
    route_id = uuid.uuid4()
    wallet_id = uuid.uuid4()
    reward_id = uuid.uuid4()
    commission_event_id = uuid.uuid4()
    wallet_ledger_id = uuid.uuid4()
    invoice_id = uuid.uuid4()
    invoice_line_id = uuid.uuid4()
    settlement_id = uuid.uuid4()

    async with async_db_cursor() as cur:
        await cur.execute(
            """
            INSERT INTO referrer_codes (
                referrer_code_id,
                referrer_ucn,
                referrer_ucn_hash,
                referral_code,
                gaming_handle,
                sticker,
                tenant_code,
                segment
            )
            VALUES ($1, $2, $3, $4, $5, 'TEST', $6, 'TEST_SEGMENT')
            """,
            referrer_code_id,
            distributor_code,
            f"hash-{distributor_code}",
            f"REF-{uuid.uuid4().hex[:8].upper()}",
            f"tester_{uuid.uuid4().hex[:8]}",
            tenant_code,
        )
        await cur.execute(
            """
            INSERT INTO referral_instances (
                referral_track_id,
                referrer_code_id,
                referral_code,
                referrer_ucn,
                referee_ucn,
                tenant_code,
                status,
                product,
                sub_product,
                journey_code,
                journey_version,
                accepted_terms,
                is_complete,
                completed_at
            )
            VALUES (
                $1, $2, 'TEST-CODE', $3, 'CUSTOMER-001', $4,
                'COMPLETED', 'Transactional', 'DDA13',
                'BANKING_TRANSACTIONAL', 'v1', TRUE, TRUE, NOW()
            )
            """,
            referral_track_id,
            referrer_code_id,
            distributor_code,
            tenant_code,
        )
        await cur.execute(
            """
            INSERT INTO distribution_distributors (
                distributor_id,
                tenant_code,
                distributor_code,
                distributor_name,
                distributor_type,
                status
            )
            VALUES ($1, $2, $3, 'Integration Distributor', 'AFFILIATE', 'ACTIVE')
            """,
            distributor_id,
            tenant_code,
            distributor_code,
        )
        await cur.execute(
            """
            INSERT INTO distribution_distributor_wallets (
                wallet_id,
                distributor_id,
                tenant_code,
                distributor_code,
                currency,
                current_balance,
                available_balance,
                status
            )
            VALUES ($1, $2, $3, $4, 'ZAR', 25.00, 25.00, 'ACTIVE')
            """,
            wallet_id,
            distributor_id,
            tenant_code,
            distributor_code,
        )
        await cur.execute(
            """
            INSERT INTO distribution_opportunities (
                opportunity_id,
                tenant_code,
                sponsor_code,
                campaign_code,
                opportunity_code,
                title,
                opportunity_status,
                estimated_reward_amount,
                estimated_commission_amount,
                total_budget,
                remaining_budget
            )
            VALUES (
                $1, $2, $3, $4, $5, 'Integration supply launch',
                'PUBLISHED', 100.00, 25.00, 1000.00, 900.00
            )
            """,
            opportunity_id,
            tenant_code,
            sponsor_code,
            campaign_code,
            f"OPP-{uuid.uuid4().hex[:8].upper()}",
        )
        await cur.execute(
            """
            INSERT INTO distribution_offer_routes (
                route_id,
                tenant_code,
                opportunity_id,
                distributor_id,
                route_status,
                route_score
            )
            VALUES ($1, $2, $3, $4, 'ACCEPTED', 95.00)
            """,
            route_id,
            tenant_code,
            opportunity_id,
            distributor_id,
        )
        await cur.execute(
            """
            INSERT INTO distribution_route_referral_links (
                route_id,
                referral_track_id,
                tenant_code,
                distributor_id,
                opportunity_id,
                link_status
            )
            VALUES ($1, $2, $3, $4, $5, 'ACTIVE')
            """,
            route_id,
            referral_track_id,
            tenant_code,
            distributor_id,
            opportunity_id,
        )
        await cur.execute(
            """
            INSERT INTO referral_rewards (
                reward_id,
                referral_track_id,
                reward_type,
                product,
                amount,
                tenant_code
            )
            VALUES ($1, $2, 'REFERRER', 'Transactional', 100.00, $3)
            """,
            reward_id,
            referral_track_id,
            tenant_code,
        )
        await cur.execute(
            """
            INSERT INTO distribution_commission_events (
                commission_event_id,
                tenant_code,
                distributor_id,
                distributor_code,
                wallet_id,
                sponsor_code,
                campaign_code,
                source_event_id,
                activity_type,
                sale_amount,
                commission_amount,
                commission_status,
                credited_at,
                correlation_id
            )
            VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8,
                'CUSTOMER_OUTCOME', 100.00, 25.00, 'CREDITED', NOW(), $8
            )
            """,
            commission_event_id,
            tenant_code,
            distributor_id,
            distributor_code,
            wallet_id,
            sponsor_code,
            campaign_code,
            str(referral_track_id),
        )
        await cur.execute(
            """
            INSERT INTO distribution_distributor_wallet_ledger (
                ledger_id,
                wallet_id,
                distributor_id,
                tenant_code,
                transaction_type,
                amount,
                balance_before,
                balance_after,
                correlation_id,
                metadata
            )
            VALUES ($1, $2, $3, $4, 'CREDIT', 25.00, 0.00, 25.00, $5, $6::jsonb)
            """,
            wallet_ledger_id,
            wallet_id,
            distributor_id,
            tenant_code,
            str(referral_track_id),
            '{"source_event_id": "' + str(referral_track_id) + '"}',
        )
        await cur.execute(
            """
            INSERT INTO sponsor_invoices (
                invoice_id,
                tenant_code,
                sponsor_code,
                sponsor_name,
                invoice_number,
                currency,
                subtotal_amount,
                vat_amount,
                total_amount,
                outstanding_amount,
                status,
                issued_at
            )
            VALUES (
                $1, $2, $3, 'Integration Producer', $4,
                'ZAR', 100.00, 0.00, 100.00, 100.00, 'ISSUED', NOW()
            )
            """,
            invoice_id,
            tenant_code,
            sponsor_code,
            f"INV-{uuid.uuid4().hex[:12].upper()}",
        )
        await cur.execute(
            """
            INSERT INTO sponsor_invoice_lines (
                line_id,
                invoice_id,
                line_type,
                description,
                quantity,
                unit_amount,
                line_amount,
                reward_id
            )
            VALUES ($1, $2, 'UTILISATION', 'Completed customer outcome', 1, 100.00, 100.00, $3)
            """,
            invoice_line_id,
            invoice_id,
            reward_id,
        )
        await cur.execute(
            """
            INSERT INTO fulfilment_settlement_ledger (
                settlement_id,
                tenant_code,
                reward_id,
                audit_id,
                provider_key,
                provider_reference,
                amount,
                currency,
                status,
                settlement_date,
                settled_at
            )
            VALUES ($1, $2, $3, $4, 'TEST_PROVIDER', $5, 100.00, 'ZAR', 'SETTLED', NOW(), NOW())
            """,
            settlement_id,
            tenant_code,
            reward_id,
            uuid.uuid4(),
            f"SETTLED-{uuid.uuid4().hex[:8].upper()}",
        )

    try:
        yield {
            "tenant_code": tenant_code,
            "sponsor_code": sponsor_code,
            "campaign_code": campaign_code,
            "distributor_code": distributor_code,
            "referral_track_id": str(referral_track_id),
            "invoice_id": invoice_id,
            "invoice_line_id": invoice_line_id,
            "settlement_id": settlement_id,
            "wallet_ledger_id": wallet_ledger_id,
        }
    finally:
        async with async_db_cursor() as cur:
            await cur.execute(
                """
                DELETE FROM sponsor_invoice_lines
                WHERE metadata->>'referral_track_id' = $1
                """,
                str(referral_track_id),
            )
            await cur.execute(
                """
                DELETE FROM sponsor_invoices
                WHERE metadata->>'referral_track_id' = $1
                """,
                str(referral_track_id),
            )
            await cur.execute("DELETE FROM settlement_exceptions WHERE settlement_id = $1", settlement_id)
            await cur.execute("DELETE FROM fulfilment_settlement_ledger WHERE settlement_id = $1", settlement_id)
            await cur.execute("DELETE FROM sponsor_invoice_lines WHERE line_id = $1", invoice_line_id)
            await cur.execute("DELETE FROM sponsor_invoices WHERE invoice_id = $1", invoice_id)
            await cur.execute(
                "DELETE FROM distribution_distributor_wallet_ledger WHERE ledger_id = $1",
                wallet_ledger_id,
            )
            await cur.execute(
                "DELETE FROM distribution_commission_events WHERE commission_event_id = $1",
                commission_event_id,
            )
            await cur.execute("DELETE FROM referral_rewards WHERE reward_id = $1", reward_id)
            await cur.execute(
                "DELETE FROM distribution_route_referral_links WHERE referral_track_id = $1",
                referral_track_id,
            )
            await cur.execute("DELETE FROM distribution_offer_routes WHERE route_id = $1", route_id)
            await cur.execute("DELETE FROM distribution_opportunities WHERE opportunity_id = $1", opportunity_id)
            await cur.execute("DELETE FROM distribution_distributor_wallets WHERE wallet_id = $1", wallet_id)
            await cur.execute("DELETE FROM distribution_distributors WHERE distributor_id = $1", distributor_id)
            await cur.execute("DELETE FROM referral_instances WHERE referral_track_id = $1", referral_track_id)
            await cur.execute("DELETE FROM referrer_codes WHERE referrer_code_id = $1", referrer_code_id)


async def test_completed_outcome_reads_as_ready_money_trail(completed_money_trail):
    result = await get_outcome_money_map(
        tenant_code=completed_money_trail["tenant_code"],
        sponsor_code=completed_money_trail["sponsor_code"],
        distributor_code=completed_money_trail["distributor_code"],
        limit=10,
    )

    assert result["summary"]["completed_outcome_count"] == 1
    assert result["summary"]["ready_count"] == 1
    assert result["summary"]["attention_count"] == 0
    assert result["summary"]["money_completion_rate"] == Decimal("1.0000")

    item = result["items"][0]
    assert item["referral_track_id"] == completed_money_trail["referral_track_id"]
    assert item["sponsor_code"] == completed_money_trail["sponsor_code"]
    assert item["distributor_code"] == completed_money_trail["distributor_code"]
    assert item["money_status"] == "READY"
    assert item["missing_steps"] == []
    assert item["reward_count"] == 1
    assert item["commission_count"] == 1
    assert item["wallet_movement_count"] == 1
    assert item["invoice_count"] == 1
    assert item["settled_count"] == 1
    assert item["exception_count"] == 0


async def test_broken_money_trail_reads_as_actionable_attention(completed_money_trail):
    exception_id = uuid.uuid4()

    async with async_db_cursor() as cur:
        await cur.execute(
            "DELETE FROM distribution_distributor_wallet_ledger WHERE ledger_id = $1",
            completed_money_trail["wallet_ledger_id"],
        )
        await cur.execute(
            "DELETE FROM sponsor_invoice_lines WHERE line_id = $1",
            completed_money_trail["invoice_line_id"],
        )
        await cur.execute(
            """
            UPDATE fulfilment_settlement_ledger
            SET status = 'FAILED',
                failed_at = NOW(),
                failure_reason = 'Provider rejected settlement'
            WHERE settlement_id = $1
            """,
            completed_money_trail["settlement_id"],
        )
        await cur.execute(
            """
            INSERT INTO settlement_exceptions (
                exception_id,
                settlement_id,
                exception_type,
                severity,
                status,
                exception_message
            )
            VALUES (
                $1, $2, 'PROVIDER_REJECTION', 'HIGH', 'OPEN',
                'Provider rejected settlement'
            )
            """,
            exception_id,
            completed_money_trail["settlement_id"],
        )

    result = await get_outcome_money_map(
        tenant_code=completed_money_trail["tenant_code"],
        sponsor_code=completed_money_trail["sponsor_code"],
        distributor_code=completed_money_trail["distributor_code"],
        limit=10,
    )

    assert result["summary"]["completed_outcome_count"] == 1
    assert result["summary"]["ready_count"] == 0
    assert result["summary"]["attention_count"] == 1
    assert result["summary"]["exception_count"] == 1
    assert result["summary"]["money_completion_rate"] == Decimal("0.0000")
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

    item = result["items"][0]
    assert item["money_status"] == "ATTENTION"
    assert item["reward_count"] == 1
    assert item["commission_count"] == 1
    assert item["wallet_movement_count"] == 0
    assert item["invoice_count"] == 0
    assert item["settled_count"] == 0
    assert item["exception_count"] == 1
    assert item["missing_steps"] == [
        "Distributor wallet movement",
        "Producer invoice line",
        "Settlement settled",
    ]

    invoice_repair = await create_outcome_invoice_evidence(
        referral_track_id=completed_money_trail["referral_track_id"],
        created_by="ops-user",
        tenant_code=completed_money_trail["tenant_code"],
    )

    assert invoice_repair["invoice_id"] is not None
    assert invoice_repair["line_count"] == 1
    assert invoice_repair["invoice_amount"] == Decimal("100.00")

    invoiced_result = await get_outcome_money_map(
        tenant_code=completed_money_trail["tenant_code"],
        sponsor_code=completed_money_trail["sponsor_code"],
        distributor_code=completed_money_trail["distributor_code"],
        limit=10,
    )

    assert invoiced_result["items"][0]["invoice_count"] == 1
    assert "Producer invoice line" not in invoiced_result["items"][0]["missing_steps"]

    repair = await resolve_outcome_settlement_exceptions(
        referral_track_id=completed_money_trail["referral_track_id"],
        resolved_by="ops-user",
        tenant_code=completed_money_trail["tenant_code"],
    )

    assert repair["resolved_count"] == 1
    assert repair["items"][0]["status"] == "RESOLVED"
    assert repair["items"][0]["resolved_by"] == "ops-user"

    repaired_result = await get_outcome_money_map(
        tenant_code=completed_money_trail["tenant_code"],
        sponsor_code=completed_money_trail["sponsor_code"],
        distributor_code=completed_money_trail["distributor_code"],
        limit=10,
    )

    assert repaired_result["summary"]["exception_count"] == 0
    assert repaired_result["summary"]["attention_count"] == 1
    assert repaired_result["items"][0]["exception_count"] == 0
    assert repaired_result["items"][0]["money_status"] == "ATTENTION"
