from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from services.finance_metrics_service import get_reconciliation_metrics
from services.finance_wallet_overview_service import get_network_wallet_overview
from services.outcome_money_reconciliation_service import (
    create_outcome_commission_evidence,
    create_outcome_invoice_evidence,
    create_outcome_reward_evidence,
    create_outcome_settlement_evidence,
    create_outcome_wallet_evidence,
    get_outcome_money_map,
    resolve_outcome_settlement_exceptions,
)
from utils.security import require_finance_admin_key as require_admin_key


router = APIRouter(
    prefix="/admin/finance",
    tags=["Admin - Finance"],
    dependencies=[Depends(require_admin_key)],
)


class ResolveOutcomeSettlementExceptionsRequest(BaseModel):
    resolved_by: str
    tenant_code: Optional[str] = None


class CreateOutcomeInvoiceEvidenceRequest(BaseModel):
    created_by: str
    tenant_code: Optional[str] = None


class CreateOutcomeRewardEvidenceRequest(BaseModel):
    created_by: str
    tenant_code: Optional[str] = None


class CreateOutcomeCommissionEvidenceRequest(BaseModel):
    created_by: str
    tenant_code: Optional[str] = None


class CreateOutcomeWalletEvidenceRequest(BaseModel):
    created_by: str
    tenant_code: Optional[str] = None


class CreateOutcomeSettlementEvidenceRequest(BaseModel):
    created_by: str
    tenant_code: Optional[str] = None


@router.get("/reconciliation/metrics")
async def get_finance_reconciliation_metrics(
    tenant_code: Optional[str] = Query(default=None),
    provider_key: Optional[str] = Query(default=None),
):
    metrics = await get_reconciliation_metrics(
        tenant_code=tenant_code,
        provider_key=provider_key,
    )

    return {
        "status": "ok",
        "metrics": metrics,
    }


@router.get("/wallets/overview")
async def get_finance_wallet_overview(
    tenant_code: Optional[str] = Query(default=None),
):
    overview = await get_network_wallet_overview(tenant_code=tenant_code)

    return {
        "status": "ok",
        "overview": overview,
    }


@router.get("/outcome-money-map")
async def get_finance_outcome_money_map(
    tenant_code: Optional[str] = Query(default=None),
    sponsor_code: Optional[str] = Query(default=None),
    distributor_code: Optional[str] = Query(default=None),
    limit: int = Query(default=100, ge=1, le=250),
):
    outcome_money = await get_outcome_money_map(
        tenant_code=tenant_code,
        sponsor_code=sponsor_code,
        distributor_code=distributor_code,
        limit=limit,
    )

    return {
        "status": "ok",
        "outcome_money": outcome_money,
    }


@router.post("/outcome-money-map/{referral_track_id}/settlement-exceptions/resolve")
async def resolve_finance_outcome_settlement_exceptions(
    referral_track_id: str,
    request: ResolveOutcomeSettlementExceptionsRequest,
):
    result = await resolve_outcome_settlement_exceptions(
        referral_track_id=referral_track_id,
        resolved_by=request.resolved_by,
        tenant_code=request.tenant_code,
    )

    return {
        "status": "ok",
        "repair": result,
    }


@router.post("/outcome-money-map/{referral_track_id}/reward-evidence")
async def create_finance_outcome_reward_evidence(
    referral_track_id: str,
    request: CreateOutcomeRewardEvidenceRequest,
):
    result = await create_outcome_reward_evidence(
        referral_track_id=referral_track_id,
        created_by=request.created_by,
        tenant_code=request.tenant_code,
    )

    return {
        "status": "ok",
        "repair": result,
    }


@router.post("/outcome-money-map/{referral_track_id}/commission-evidence")
async def create_finance_outcome_commission_evidence(
    referral_track_id: str,
    request: CreateOutcomeCommissionEvidenceRequest,
):
    result = await create_outcome_commission_evidence(
        referral_track_id=referral_track_id,
        created_by=request.created_by,
        tenant_code=request.tenant_code,
    )

    return {
        "status": "ok",
        "repair": result,
    }


@router.post("/outcome-money-map/{referral_track_id}/wallet-evidence")
async def create_finance_outcome_wallet_evidence(
    referral_track_id: str,
    request: CreateOutcomeWalletEvidenceRequest,
):
    result = await create_outcome_wallet_evidence(
        referral_track_id=referral_track_id,
        created_by=request.created_by,
        tenant_code=request.tenant_code,
    )

    return {
        "status": "ok",
        "repair": result,
    }


@router.post("/outcome-money-map/{referral_track_id}/invoice-evidence")
async def create_finance_outcome_invoice_evidence(
    referral_track_id: str,
    request: CreateOutcomeInvoiceEvidenceRequest,
):
    result = await create_outcome_invoice_evidence(
        referral_track_id=referral_track_id,
        created_by=request.created_by,
        tenant_code=request.tenant_code,
    )

    return {
        "status": "ok",
        "repair": result,
    }


@router.post("/outcome-money-map/{referral_track_id}/settlement-evidence")
async def create_finance_outcome_settlement_evidence(
    referral_track_id: str,
    request: CreateOutcomeSettlementEvidenceRequest,
):
    result = await create_outcome_settlement_evidence(
        referral_track_id=referral_track_id,
        created_by=request.created_by,
        tenant_code=request.tenant_code,
    )

    return {
        "status": "ok",
        "repair": result,
    }
