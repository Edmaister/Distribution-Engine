from __future__ import annotations

from typing import Any

from services.outcome_money_reconciliation_service import get_outcome_money_map


CANONICAL_INSURANCE_PROOF = {
    "tenant_code": "FNB",
    "sponsor_code": "INSURECO",
    "campaign_code": "INS-FUNERAL-2026",
    "distributor_code": "DIST-INSURANCE-ADVOCATE",
    "referral_track_id": "22222222-2222-4222-8222-222222222222",
    "journey_code": "INSURANCE_POLICY",
}


def _step(
    *,
    surface: str,
    label: str,
    ready: bool,
    evidence: str,
    action: str,
) -> dict[str, Any]:
    return {
        "surface": surface,
        "label": label,
        "ready": ready,
        "status": "READY" if ready else "MISSING",
        "evidence": evidence,
        "action": action,
    }


def _missing_proof() -> dict[str, Any]:
    return {
        **CANONICAL_INSURANCE_PROOF,
        "status": "MISSING",
        "ready": False,
        "money_status": "MISSING",
        "proof_summary": "Canonical Insurance journey seed was not found.",
        "steps": [
            _step(
                surface="Producer - Supply",
                label="Insurance offer and invoice evidence",
                ready=False,
                evidence="No canonical Insurance outcome found.",
                action="Seed or complete an Insurance producer supply journey.",
            ),
            _step(
                surface="Distributor - Demand",
                label="Accepted route, commission, and wallet movement",
                ready=False,
                evidence="No linked distributor outcome found.",
                action="Confirm route attribution and distributor wallet evidence.",
            ),
            _step(
                surface="Consumer Journey",
                label="Policy issue, first premium, and reward visibility",
                ready=False,
                evidence="No completed Insurance referral found.",
                action="Run the Insurance progress journey to completion.",
            ),
            _step(
                surface="Amplifi Admin",
                label="Outcome-to-money reconciliation",
                ready=False,
                evidence="No money trail found.",
                action="Review outcome-money reconciliation after the journey completes.",
            ),
        ],
    }


def _scoped_step(proof: dict[str, Any], surface: str) -> dict[str, Any] | None:
    return next(
        (
            step
            for step in proof.get("steps") or []
            if str(step.get("surface") or "") == surface
        ),
        None,
    )


def _scope_unavailable(
    *,
    proof: dict[str, Any],
    scope: str,
    surface: str,
    summary: str,
) -> dict[str, Any]:
    return {
        "status": "NOT_AVAILABLE",
        "ready": False,
        "scope": scope,
        "surface": surface,
        "tenant_code": proof.get("tenant_code"),
        "campaign_code": proof.get("campaign_code"),
        "journey_code": proof.get("journey_code"),
        "referral_track_id": proof.get("referral_track_id"),
        "proof_summary": summary,
        "steps": [
            _step(
                surface=surface,
                label=f"{surface} Insurance proof",
                ready=False,
                evidence="No matching Insurance journey proof is available for this context.",
                action="Load the matching Insurance journey or ask an admin to confirm the proof seed.",
            )
        ],
    }


def _scoped_proof(
    *,
    proof: dict[str, Any],
    scope: str,
    surface: str,
    allowed_fields: set[str],
) -> dict[str, Any]:
    step = _scoped_step(proof, surface)
    scoped = {
        "status": step.get("status") if step else proof.get("status"),
        "ready": bool(step.get("ready")) if step else False,
        "scope": scope,
        "surface": surface,
        "tenant_code": proof.get("tenant_code"),
        "campaign_code": proof.get("campaign_code"),
        "journey_code": proof.get("journey_code"),
        "money_status": proof.get("money_status"),
        "proof_summary": proof.get("proof_summary"),
        "steps": [step] if step else [],
    }
    for field in allowed_fields:
        scoped[field] = proof.get(field)
    return scoped


async def get_insurance_journey_proof() -> dict[str, Any]:
    money_map = await get_outcome_money_map(
        tenant_code=CANONICAL_INSURANCE_PROOF["tenant_code"],
        sponsor_code=CANONICAL_INSURANCE_PROOF["sponsor_code"],
        distributor_code=CANONICAL_INSURANCE_PROOF["distributor_code"],
        limit=25,
    )

    items = money_map.get("items") or []
    item = next(
        (
            candidate
            for candidate in items
            if str(candidate.get("referral_track_id"))
            == CANONICAL_INSURANCE_PROOF["referral_track_id"]
        ),
        None,
    )

    if not item:
        return _missing_proof()

    producer_ready = bool(item.get("sponsor_code")) and int(item.get("invoice_count") or 0) > 0
    distributor_ready = (
        bool(item.get("distributor_code"))
        and int(item.get("commission_count") or 0) > 0
        and int(item.get("wallet_movement_count") or 0) > 0
    )
    consumer_ready = (
        item.get("journey_code") == CANONICAL_INSURANCE_PROOF["journey_code"]
        and str(item.get("product") or "").upper() == "INSURANCE"
        and int(item.get("reward_count") or 0) > 0
    )
    admin_ready = item.get("money_status") == "READY" and int(item.get("exception_count") or 0) == 0
    ready = producer_ready and distributor_ready and consumer_ready and admin_ready

    return {
        **CANONICAL_INSURANCE_PROOF,
        "status": "READY" if ready else "ATTENTION",
        "ready": ready,
        "money_status": item.get("money_status"),
        "reward_amount": item.get("reward_amount"),
        "commission_amount": item.get("commission_amount"),
        "wallet_movement_amount": item.get("wallet_movement_amount"),
        "invoiced_amount": item.get("invoiced_amount"),
        "settled_amount": item.get("settled_amount"),
        "proof_summary": (
            "Insurance customer outcome is visible across Producer, Distributor, Consumer, and Admin surfaces."
            if ready
            else "Insurance customer outcome exists, but one or more operating surfaces need evidence."
        ),
        "steps": [
            _step(
                surface="Producer - Supply",
                label="Insurance offer and invoice evidence",
                ready=producer_ready,
                evidence=f"{item.get('opportunity_title') or 'Insurance offer'} / invoices {item.get('invoice_count')}",
                action="Confirm producer offer and billing evidence.",
            ),
            _step(
                surface="Distributor - Demand",
                label="Accepted route, commission, and wallet movement",
                ready=distributor_ready,
                evidence=f"Commission {item.get('commission_count')} / wallet {item.get('wallet_movement_count')}",
                action="Confirm distributor attribution and earnings movement.",
            ),
            _step(
                surface="Consumer Journey",
                label="Policy issue, first premium, and reward visibility",
                ready=consumer_ready,
                evidence=f"{item.get('journey_code')} / rewards {item.get('reward_count')}",
                action="Confirm policy progress and reward visibility.",
            ),
            _step(
                surface="Amplifi Admin",
                label="Outcome-to-money reconciliation",
                ready=admin_ready,
                evidence=f"Money status {item.get('money_status')} / exceptions {item.get('exception_count')}",
                action="Monitor reconciliation and settlement state.",
            ),
        ],
    }


async def get_producer_insurance_journey_proof(
    *,
    tenant_code: str,
    producer_code: str,
) -> dict[str, Any]:
    proof = await get_insurance_journey_proof()
    if (
        str(proof.get("tenant_code") or "").upper() != tenant_code.upper()
        or str(proof.get("sponsor_code") or "").upper() != producer_code.upper()
    ):
        return _scope_unavailable(
            proof=proof,
            scope="producer",
            surface="Producer - Supply",
            summary="No Insurance proof is available for this producer context.",
        )
    return _scoped_proof(
        proof=proof,
        scope="producer",
        surface="Producer - Supply",
        allowed_fields={"sponsor_code", "invoiced_amount"},
    )


async def get_distributor_insurance_journey_proof(
    *,
    tenant_code: str,
    distributor_code: str,
) -> dict[str, Any]:
    proof = await get_insurance_journey_proof()
    if (
        str(proof.get("tenant_code") or "").upper() != tenant_code.upper()
        or str(proof.get("distributor_code") or "").upper() != distributor_code.upper()
    ):
        return _scope_unavailable(
            proof=proof,
            scope="distributor",
            surface="Distributor - Demand",
            summary="No Insurance proof is available for this distributor context.",
        )
    return _scoped_proof(
        proof=proof,
        scope="distributor",
        surface="Distributor - Demand",
        allowed_fields={
            "distributor_code",
            "commission_amount",
            "wallet_movement_amount",
        },
    )


async def get_consumer_insurance_journey_proof(
    *,
    tenant_code: str,
    referral_track_id: str | None = None,
) -> dict[str, Any]:
    proof = await get_insurance_journey_proof()
    if str(proof.get("tenant_code") or "").upper() != tenant_code.upper():
        return _scope_unavailable(
            proof=proof,
            scope="consumer",
            surface="Consumer Journey",
            summary="No Insurance proof is available for this tenant context.",
        )
    if referral_track_id and str(proof.get("referral_track_id")) != referral_track_id:
        return _scope_unavailable(
            proof=proof,
            scope="consumer",
            surface="Consumer Journey",
            summary="No Insurance proof is available for this customer journey.",
        )
    return _scoped_proof(
        proof=proof,
        scope="consumer",
        surface="Consumer Journey",
        allowed_fields={"referral_track_id", "reward_amount"},
    )
