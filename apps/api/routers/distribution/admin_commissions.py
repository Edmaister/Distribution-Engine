from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from apps.api.schemas.distribution.commissions import (
    CalculateCommissionRequest,
    CalculateCommissionResponse,
    CommissionEventResponse,
    CommissionRuleResponse,
    CreateCommissionRuleRequest,
)
from services.admin_audit_service import try_write_admin_audit
from services.distribution.commission_service import (
    CommissionDistributorNotFound,
    CommissionDuplicateEvent,
    CommissionError,
    CommissionRuleNotFound,
    CommissionWalletNotFound,
    calculate_commission,
    create_commission_rule,
    list_commission_events,
    list_commission_rules,
)
from services.distribution.distributor_wallet_service import (
    DistributorWalletError,
    DistributorWalletNotFound,
)
from utils.security import require_distribution_admin_key as require_admin_key


router = APIRouter(
    prefix="/admin/distribution/commissions",
    tags=["Admin Distribution Commissions"],
    dependencies=[Depends(require_admin_key)],
)


def _handle_commission_error(exc: Exception) -> HTTPException:
    if isinstance(
        exc,
        (
            CommissionDistributorNotFound,
            CommissionRuleNotFound,
            CommissionWalletNotFound,
            DistributorWalletNotFound,
        ),
    ):
        return HTTPException(status_code=404, detail=str(exc))

    if isinstance(exc, CommissionDuplicateEvent):
        return HTTPException(status_code=409, detail=str(exc))

    if isinstance(exc, (CommissionError, DistributorWalletError)):
        return HTTPException(status_code=400, detail=str(exc))

    return HTTPException(status_code=500, detail="Unexpected commission error")


@router.post("/rules", response_model=CommissionRuleResponse)
async def create_rule(
    request: CreateCommissionRuleRequest,
    identity: dict = Depends(require_admin_key),
) -> dict:
    try:
        rule = await create_commission_rule(
            tenant_code=request.tenant_code,
            sponsor_code=request.sponsor_code,
            campaign_code=request.campaign_code,
            distributor_type=request.distributor_type,
            commission_type=request.commission_type,
            rate=request.rate,
            fixed_amount=request.fixed_amount,
            min_commission=request.min_commission,
            max_commission=request.max_commission,
            currency=request.currency,
            priority=request.priority,
            description=request.description,
            metadata=request.metadata,
        )
        await try_write_admin_audit(
            action_type="DISTRIBUTION_COMMISSION_RULE_CREATE",
            action_domain="DISTRIBUTION",
            identity=identity,
            tenant_code=request.tenant_code,
            target_type="distribution_commission_rule",
            target_id=rule.get("rule_id"),
            request_payload=request.model_dump(mode="json"),
            result_payload={
                "rule_id": rule.get("rule_id"),
                "commission_type": rule.get("commission_type"),
                "rule_status": rule.get("rule_status"),
            },
        )
        return rule

    except Exception as exc:
        raise _handle_commission_error(exc) from exc


@router.get("/rules", response_model=list[CommissionRuleResponse])
async def list_rules(
    tenant_code: str = Query(...),
    sponsor_code: str | None = Query(default=None),
    campaign_code: str | None = Query(default=None),
    distributor_type: str | None = Query(default=None),
    rule_status: str | None = Query(default="ACTIVE"),
    limit: int = Query(default=100, ge=1, le=500),
) -> list[dict]:
    return await list_commission_rules(
        tenant_code=tenant_code,
        sponsor_code=sponsor_code,
        campaign_code=campaign_code,
        distributor_type=distributor_type,
        rule_status=rule_status,
        limit=limit,
    )


@router.post("/calculate", response_model=CalculateCommissionResponse)
async def calculate(
    request: CalculateCommissionRequest,
    identity: dict = Depends(require_admin_key),
) -> dict:
    try:
        result = await calculate_commission(
            tenant_code=request.tenant_code,
            distributor_id=request.distributor_id,
            sponsor_code=request.sponsor_code,
            campaign_code=request.campaign_code,
            activity_type=request.activity_type,
            sale_amount=request.sale_amount,
            source_event_id=request.source_event_id,
            wallet_id=request.wallet_id,
            credit_wallet=request.credit_wallet,
            correlation_id=request.correlation_id,
            metadata=request.metadata,
        )
        event = result.get("event", result) if isinstance(result, dict) else {}
        await try_write_admin_audit(
            action_type="DISTRIBUTION_COMMISSION_CALCULATE",
            action_domain="DISTRIBUTION",
            identity=identity,
            tenant_code=request.tenant_code,
            target_type="distribution_commission_event",
            target_id=event.get("commission_event_id"),
            correlation_id=request.correlation_id,
            request_payload=request.model_dump(mode="json"),
            result_payload={
                "commission_event_id": event.get("commission_event_id"),
                "commission_amount": event.get("commission_amount"),
                "commission_status": event.get("commission_status"),
                "credited": request.credit_wallet,
            },
        )
        return result

    except Exception as exc:
        raise _handle_commission_error(exc) from exc


@router.get("/events", response_model=list[CommissionEventResponse])
async def list_events(
    tenant_code: str = Query(...),
    distributor_id: str | None = Query(default=None),
    commission_status: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
) -> list[dict]:
    return await list_commission_events(
        tenant_code=tenant_code,
        distributor_id=distributor_id,
        commission_status=commission_status,
        limit=limit,
    )
