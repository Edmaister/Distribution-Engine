from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from apps.api.schemas.distribution.wallets import (
    CreateDistributorWalletRequest,
    DistributorWalletLedgerEntry,
    DistributorWalletMovementRequest,
    DistributorWalletResponse,
)
from services.admin_audit_service import try_write_admin_audit
from services.distribution.distributor_wallet_service import (
    DistributorWalletDistributorNotFound,
    DistributorWalletError,
    DistributorWalletInsufficientBalance,
    DistributorWalletNotFound,
    create_distributor_wallet,
    credit_distributor_wallet,
    get_distributor_wallet,
    hold_distributor_wallet_funds,
    list_distributor_wallet_ledger,
    list_distributor_wallets,
    payout_distributor_wallet,
    release_distributor_wallet_hold,
    reverse_distributor_wallet_earning,
)
from utils.security import require_distribution_admin_key as require_admin_key


router = APIRouter(
    prefix="/admin/distribution/distributor-wallets",
    tags=["Admin Distribution Distributor Wallets"],
    dependencies=[Depends(require_admin_key)],
)


def _handle_wallet_error(exc: Exception) -> HTTPException:
    if isinstance(exc, (DistributorWalletNotFound, DistributorWalletDistributorNotFound)):
        return HTTPException(status_code=404, detail=str(exc))

    if isinstance(exc, DistributorWalletInsufficientBalance):
        return HTTPException(status_code=409, detail=str(exc))

    if isinstance(exc, DistributorWalletError):
        return HTTPException(status_code=400, detail=str(exc))

    return HTTPException(status_code=500, detail="Unexpected distributor wallet error")


@router.post("", response_model=DistributorWalletResponse)
async def create_wallet(
    request: CreateDistributorWalletRequest,
    identity: dict = Depends(require_admin_key),
) -> dict:
    try:
        wallet = await create_distributor_wallet(
            distributor_id=request.distributor_id,
            currency=request.currency,
            metadata=request.metadata,
        )
        await try_write_admin_audit(
            action_type="DISTRIBUTOR_WALLET_CREATE",
            action_domain="DISTRIBUTION",
            identity=identity,
            tenant_code=wallet.get("tenant_code"),
            target_type="distribution_distributor_wallet",
            target_id=wallet.get("wallet_id"),
            request_payload=request.model_dump(mode="json"),
            result_payload={
                "wallet_id": wallet.get("wallet_id"),
                "distributor_id": wallet.get("distributor_id"),
                "status": wallet.get("status"),
            },
        )
        return wallet

    except Exception as exc:
        raise _handle_wallet_error(exc) from exc


@router.get("", response_model=list[DistributorWalletResponse])
async def list_wallets(
    tenant_code: str = Query(...),
    distributor_id: str | None = Query(default=None),
    status: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
) -> list[dict]:
    return await list_distributor_wallets(
        tenant_code=tenant_code,
        distributor_id=distributor_id,
        status=status,
        limit=limit,
    )


@router.get("/{wallet_id}", response_model=DistributorWalletResponse)
async def get_wallet(wallet_id: str) -> dict:
    try:
        return await get_distributor_wallet(wallet_id=wallet_id)

    except Exception as exc:
        raise _handle_wallet_error(exc) from exc


@router.post("/{wallet_id}/credit", response_model=DistributorWalletResponse)
async def credit_wallet(
    wallet_id: str,
    request: DistributorWalletMovementRequest,
    identity: dict = Depends(require_admin_key),
) -> dict:
    try:
        wallet = await credit_distributor_wallet(
            wallet_id=wallet_id,
            amount=request.amount,
            correlation_id=request.correlation_id,
            metadata=request.metadata,
        )
        await _audit_wallet_movement(
            action_type="DISTRIBUTOR_WALLET_CREDIT",
            identity=identity,
            wallet_id=wallet_id,
            request=request,
            wallet=wallet,
        )
        return wallet

    except Exception as exc:
        raise _handle_wallet_error(exc) from exc


@router.post("/{wallet_id}/hold", response_model=DistributorWalletResponse)
async def hold_wallet_funds(
    wallet_id: str,
    request: DistributorWalletMovementRequest,
    identity: dict = Depends(require_admin_key),
) -> dict:
    try:
        wallet = await hold_distributor_wallet_funds(
            wallet_id=wallet_id,
            amount=request.amount,
            correlation_id=request.correlation_id,
            metadata=request.metadata,
        )
        await _audit_wallet_movement(
            action_type="DISTRIBUTOR_WALLET_HOLD",
            identity=identity,
            wallet_id=wallet_id,
            request=request,
            wallet=wallet,
        )
        return wallet

    except Exception as exc:
        raise _handle_wallet_error(exc) from exc


@router.post("/{wallet_id}/release-hold", response_model=DistributorWalletResponse)
async def release_wallet_hold(
    wallet_id: str,
    request: DistributorWalletMovementRequest,
    identity: dict = Depends(require_admin_key),
) -> dict:
    try:
        wallet = await release_distributor_wallet_hold(
            wallet_id=wallet_id,
            amount=request.amount,
            correlation_id=request.correlation_id,
            metadata=request.metadata,
        )
        await _audit_wallet_movement(
            action_type="DISTRIBUTOR_WALLET_RELEASE_HOLD",
            identity=identity,
            wallet_id=wallet_id,
            request=request,
            wallet=wallet,
        )
        return wallet

    except Exception as exc:
        raise _handle_wallet_error(exc) from exc


@router.post("/{wallet_id}/payout", response_model=DistributorWalletResponse)
async def payout_wallet(
    wallet_id: str,
    request: DistributorWalletMovementRequest,
    identity: dict = Depends(require_admin_key),
) -> dict:
    try:
        wallet = await payout_distributor_wallet(
            wallet_id=wallet_id,
            amount=request.amount,
            correlation_id=request.correlation_id,
            metadata=request.metadata,
        )
        await _audit_wallet_movement(
            action_type="DISTRIBUTOR_WALLET_PAYOUT",
            identity=identity,
            wallet_id=wallet_id,
            request=request,
            wallet=wallet,
        )
        return wallet

    except Exception as exc:
        raise _handle_wallet_error(exc) from exc


@router.post("/{wallet_id}/reverse", response_model=DistributorWalletResponse)
async def reverse_wallet_earning(
    wallet_id: str,
    request: DistributorWalletMovementRequest,
    identity: dict = Depends(require_admin_key),
) -> dict:
    try:
        wallet = await reverse_distributor_wallet_earning(
            wallet_id=wallet_id,
            amount=request.amount,
            correlation_id=request.correlation_id,
            metadata=request.metadata,
        )
        await _audit_wallet_movement(
            action_type="DISTRIBUTOR_WALLET_REVERSE",
            identity=identity,
            wallet_id=wallet_id,
            request=request,
            wallet=wallet,
        )
        return wallet

    except Exception as exc:
        raise _handle_wallet_error(exc) from exc


async def _audit_wallet_movement(
    *,
    action_type: str,
    identity: dict,
    wallet_id: str,
    request: DistributorWalletMovementRequest,
    wallet: dict,
) -> None:
    await try_write_admin_audit(
        action_type=action_type,
        action_domain="DISTRIBUTION",
        identity=identity,
        tenant_code=wallet.get("tenant_code"),
        target_type="distribution_distributor_wallet",
        target_id=wallet_id,
        correlation_id=request.correlation_id,
        request_payload=request.model_dump(mode="json"),
        result_payload={
            "wallet_id": wallet.get("wallet_id"),
            "current_balance": wallet.get("current_balance"),
            "available_balance": wallet.get("available_balance"),
            "held_balance": wallet.get("held_balance"),
        },
    )


@router.get("/{wallet_id}/ledger", response_model=list[DistributorWalletLedgerEntry])
async def get_wallet_ledger(
    wallet_id: str,
    limit: int = Query(default=100, ge=1, le=500),
) -> list[dict]:
    try:
        await get_distributor_wallet(wallet_id=wallet_id)

        return await list_distributor_wallet_ledger(
            wallet_id=wallet_id,
            limit=limit,
        )

    except Exception as exc:
        raise _handle_wallet_error(exc) from exc
