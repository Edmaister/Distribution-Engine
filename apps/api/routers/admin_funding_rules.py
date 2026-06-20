from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from services.funding.account_rules import (
    create_funding_account_rule,
    get_funding_account_rule,
    list_funding_account_rules,
    update_funding_account_rule,
)
from utils.security import require_finance_admin_key as require_admin_key

router = APIRouter(
    prefix="/admin/funding/rules",
    tags=["Funding Rules"],
    dependencies=[Depends(require_admin_key)],
)


@router.get("")
async def get_funding_rules(
    tenant_code: str | None = None,
):
    items = await list_funding_account_rules(
        tenant_code=tenant_code,
        active_only=False,
    )

    return {
        "status": "ok",
        "count": len(items),
        "items": items,
    }


@router.get("/{rule_id}")
async def get_funding_rule(
    rule_id: UUID,
):
    rule = await get_funding_account_rule(
        rule_id=rule_id,
    )

    if not rule:
        raise HTTPException(
            status_code=404,
            detail="Funding rule not found",
        )

    return {
        "status": "ok",
        "item": rule,
    }


@router.post("")
async def create_rule(
    payload: dict,
):
    rule = await create_funding_account_rule(
        tenant_code=payload["tenant_code"],
        account_id=payload["account_id"],
        reward_type=payload.get("reward_type"),
        segment_code=payload.get("segment_code"),
        campaign_code=payload.get("campaign_code"),
        sponsor_code=payload.get("sponsor_code"),
        priority=payload.get("priority", 100),
    )

    return {
        "status": "created",
        "item": rule,
    }


@router.put("/{rule_id}")
async def update_rule(
    rule_id: UUID,
    payload: dict,
):
    rule = await update_funding_account_rule(
        rule_id=rule_id,
        reward_type=payload.get("reward_type"),
        segment_code=payload.get("segment_code"),
        campaign_code=payload.get("campaign_code"),
        sponsor_code=payload.get("sponsor_code"),
        priority=payload.get("priority"),
        is_active=payload.get("is_active"),
    )

    if not rule:
        raise HTTPException(
            status_code=404,
            detail="Funding rule not found",
        )

    return {
        "status": "updated",
        "item": rule,
    }
