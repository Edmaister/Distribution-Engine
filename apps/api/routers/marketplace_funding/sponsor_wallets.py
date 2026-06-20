from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from apps.api.schemas.marketplace_funding.sponsor_wallet import (
    SponsorWalletCreate,
    SponsorWalletResponse,
)
from apps.api.schemas.marketplace_funding.sponsor_wallet_ledger import (
    SponsorWalletLedgerEntry,
)
from apps.api.schemas.marketplace_funding.sponsor_wallet_topup import (
    SponsorWalletTopupRequest,
)
from services.marketplace_funding.sponsor_wallet_balance_service import (
    topup_wallet,
)
from services.marketplace_funding.sponsor_wallet_ledger_service import (
    list_sponsor_wallet_transactions,
)
from services.marketplace_funding.sponsor_wallet_service import (
    create_sponsor_wallet,
    get_sponsor_wallet,
    list_sponsor_wallets,
)
from utils.security import require_finance_admin_key as require_admin_key

router = APIRouter(
    prefix="/admin/marketplace-funding/sponsor-wallets",
    tags=["Marketplace Funding - Sponsor Wallets"],
    dependencies=[Depends(require_admin_key)],
)


@router.post("", response_model=SponsorWalletResponse)
async def create_wallet(payload: SponsorWalletCreate):
    return await create_sponsor_wallet(
        tenant_code=payload.tenant_code,
        sponsor_code=payload.sponsor_code,
        sponsor_name=payload.sponsor_name,
        currency=payload.currency,
    )


@router.get("", response_model=list[SponsorWalletResponse])
async def list_wallets(
    tenant_code: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
):
    return await list_sponsor_wallets(
        tenant_code=tenant_code,
        limit=limit,
    )


@router.get("/{wallet_id}", response_model=SponsorWalletResponse)
async def get_wallet(wallet_id: str):
    wallet = await get_sponsor_wallet(wallet_id=wallet_id)

    if not wallet:
        raise HTTPException(status_code=404, detail="Sponsor wallet not found")

    return wallet


@router.post("/{wallet_id}/topup", response_model=SponsorWalletResponse)
async def topup_sponsor_wallet(
    wallet_id: str,
    payload: SponsorWalletTopupRequest,
):
    try:
        return await topup_wallet(
            wallet_id=wallet_id,
            amount=payload.amount,
            correlation_id=payload.correlation_id,
            metadata=payload.metadata,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/{wallet_id}/ledger", response_model=list[SponsorWalletLedgerEntry])
async def get_wallet_ledger(
    wallet_id: str,
    limit: int = Query(default=100, ge=1, le=500),
):
    wallet = await get_sponsor_wallet(wallet_id=wallet_id)

    if not wallet:
        raise HTTPException(status_code=404, detail="Sponsor wallet not found")

    return await list_sponsor_wallet_transactions(
        wallet_id=wallet_id,
        limit=limit,
    )
