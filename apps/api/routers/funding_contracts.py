from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from services.marketplace_funding.funding_contract_service import (
    FundingContractError,
    FundingContractExceeded,
    FundingContractExpired,
    FundingContractInactive,
    FundingContractNotFound,
    activate_funding_contract,
    cancel_funding_contract,
    commit_funding_contract_budget,
    create_funding_contract,
    get_funding_contract,
    get_funding_contract_ledger,
    list_funding_contracts,
    release_funding_contract_budget,
    resolve_active_funding_contract,
    suspend_funding_contract,
    utilise_funding_contract_budget,
)
from utils.security import require_finance_admin_key as require_admin_key

router = APIRouter(
    prefix="/admin/funding/contracts",
    tags=["funding-contracts"],
    dependencies=[Depends(require_admin_key)],
)


class CreateFundingContractRequest(BaseModel):
    tenant_code: str
    sponsor_code: str
    sponsor_name: str
    contract_name: str
    contract_value: Decimal = Field(gt=0)
    start_date: date
    end_date: date
    currency: str = "ZAR"
    metadata: dict[str, Any] | None = None


class BudgetMovementRequest(BaseModel):
    amount: Decimal = Field(gt=0)
    reward_id: str | None = None
    allocation_id: str | None = None
    correlation_id: str | None = None
    metadata: dict[str, Any] | None = None


def _handle_contract_error(exc: Exception) -> HTTPException:
    if isinstance(exc, FundingContractNotFound):
        return HTTPException(status_code=404, detail=str(exc))

    if isinstance(exc, FundingContractExceeded):
        return HTTPException(status_code=409, detail=str(exc))

    if isinstance(exc, (FundingContractInactive, FundingContractExpired)):
        return HTTPException(status_code=400, detail=str(exc))

    if isinstance(exc, FundingContractError):
        return HTTPException(status_code=400, detail=str(exc))

    return HTTPException(status_code=500, detail="Unexpected funding contract error")


@router.post("")
async def create_contract(request: CreateFundingContractRequest) -> dict[str, Any]:
    try:
        contract = await create_funding_contract(
            tenant_code=request.tenant_code,
            sponsor_code=request.sponsor_code,
            sponsor_name=request.sponsor_name,
            contract_name=request.contract_name,
            contract_value=request.contract_value,
            start_date=request.start_date,
            end_date=request.end_date,
            currency=request.currency,
            metadata=request.metadata,
        )

        return {"status": "ok", "contract": contract}

    except Exception as exc:
        raise _handle_contract_error(exc) from exc


@router.get("")
async def list_contracts(
    tenant_code: str = Query(...),
    sponsor_code: str | None = Query(default=None),
    status: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
) -> dict[str, Any]:
    contracts = await list_funding_contracts(
        tenant_code=tenant_code,
        sponsor_code=sponsor_code,
        status=status,
        limit=limit,
    )

    return {
        "status": "ok",
        "tenant_code": tenant_code,
        "count": len(contracts),
        "items": contracts,
    }


@router.get("/active")
async def get_active_contract(
    tenant_code: str = Query(...),
    sponsor_code: str = Query(...),
    as_of_date: date | None = Query(default=None),
) -> dict[str, Any]:
    try:
        contract = await resolve_active_funding_contract(
            tenant_code=tenant_code,
            sponsor_code=sponsor_code,
            as_of_date=as_of_date,
        )

        return {"status": "ok", "contract": contract}

    except Exception as exc:
        raise _handle_contract_error(exc) from exc


@router.get("/{contract_id}")
async def get_contract(contract_id: str) -> dict[str, Any]:
    try:
        contract = await get_funding_contract(contract_id=contract_id)
        return {"status": "ok", "contract": contract}

    except Exception as exc:
        raise _handle_contract_error(exc) from exc


@router.get("/{contract_id}/ledger")
async def get_contract_ledger(
    contract_id: str,
    limit: int = Query(default=100, ge=1, le=500),
) -> dict[str, Any]:
    try:
        ledger = await get_funding_contract_ledger(
            contract_id=contract_id,
            limit=limit,
        )

        return {
            "status": "ok",
            "contract_id": contract_id,
            "count": len(ledger),
            "items": ledger,
        }

    except Exception as exc:
        raise _handle_contract_error(exc) from exc


@router.post("/{contract_id}/commit")
async def commit_contract_budget(
    contract_id: str,
    request: BudgetMovementRequest,
) -> dict[str, Any]:
    try:
        contract = await commit_funding_contract_budget(
            contract_id=contract_id,
            amount=request.amount,
            reward_id=request.reward_id,
            allocation_id=request.allocation_id,
            correlation_id=request.correlation_id,
            metadata=request.metadata,
        )

        return {"status": "ok", "contract": contract}

    except Exception as exc:
        raise _handle_contract_error(exc) from exc


@router.post("/{contract_id}/release")
async def release_contract_budget(
    contract_id: str,
    request: BudgetMovementRequest,
) -> dict[str, Any]:
    try:
        contract = await release_funding_contract_budget(
            contract_id=contract_id,
            amount=request.amount,
            reward_id=request.reward_id,
            allocation_id=request.allocation_id,
            correlation_id=request.correlation_id,
            metadata=request.metadata,
        )

        return {"status": "ok", "contract": contract}

    except Exception as exc:
        raise _handle_contract_error(exc) from exc


@router.post("/{contract_id}/utilise")
async def utilise_contract_budget(
    contract_id: str,
    request: BudgetMovementRequest,
) -> dict[str, Any]:
    try:
        contract = await utilise_funding_contract_budget(
            contract_id=contract_id,
            amount=request.amount,
            reward_id=request.reward_id,
            allocation_id=request.allocation_id,
            correlation_id=request.correlation_id,
            metadata=request.metadata,
        )

        return {"status": "ok", "contract": contract}

    except Exception as exc:
        raise _handle_contract_error(exc) from exc


@router.post("/{contract_id}/suspend")
async def suspend_contract(contract_id: str) -> dict[str, Any]:
    try:
        contract = await suspend_funding_contract(contract_id=contract_id)
        return {"status": "ok", "contract": contract}

    except Exception as exc:
        raise _handle_contract_error(exc) from exc


@router.post("/{contract_id}/activate")
async def activate_contract(contract_id: str) -> dict[str, Any]:
    try:
        contract = await activate_funding_contract(contract_id=contract_id)
        return {"status": "ok", "contract": contract}

    except Exception as exc:
        raise _handle_contract_error(exc) from exc


@router.post("/{contract_id}/cancel")
async def cancel_contract(contract_id: str) -> dict[str, Any]:
    try:
        contract = await cancel_funding_contract(contract_id=contract_id)
        return {"status": "ok", "contract": contract}

    except Exception as exc:
        raise _handle_contract_error(exc) from exc
