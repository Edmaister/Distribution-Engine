from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any
from uuid import UUID

from services.funding.exposure import list_funding_exposure
from services.funding.limits import get_active_funding_limit


def _decimal(value: Any) -> Decimal:
    if value is None:
        return Decimal("0.00")
    return Decimal(str(value))


def _empty_summary() -> dict[str, Decimal]:
    return {
        "daily_limit": Decimal("0.00"),
        "daily_used": Decimal("0.00"),
        "monthly_limit": Decimal("0.00"),
        "monthly_used": Decimal("0.00"),
        "exposure_limit": Decimal("0.00"),
        "current_exposure": Decimal("0.00"),
    }


async def get_account_funding_summary(
    *,
    tenant_code: str,
    account_id: UUID | str,
) -> dict[str, Decimal | str]:
    limit = await get_active_funding_limit(
        tenant_code=tenant_code,
        account_id=account_id,
    )

    summary = _empty_summary()

    if limit is not None:
        summary["daily_limit"] = _decimal(limit.get("daily_limit"))
        summary["monthly_limit"] = _decimal(limit.get("monthly_limit"))
        summary["exposure_limit"] = _decimal(limit.get("exposure_limit"))

    rows = await list_funding_exposure(
        tenant_code=tenant_code,
        account_id=account_id,
        limit=500,
    )

    today = date.today()

    for row in rows:
        exposure_date = row["exposure_date"]
        reserved = _decimal(row.get("reserved_amount"))
        settled = _decimal(row.get("settled_amount"))

        used = reserved + settled
        summary["current_exposure"] += used

        if exposure_date == today:
            summary["daily_used"] += used

        if exposure_date.year == today.year and exposure_date.month == today.month:
            summary["monthly_used"] += used

    return {
        "tenant_code": tenant_code,
        "account_id": str(account_id),
        **summary,
    }


async def get_tenant_funding_summary(
    *,
    tenant_code: str,
) -> dict[str, Any]:
    rows = await list_funding_exposure(
        tenant_code=tenant_code,
        account_id=None,
        limit=500,
    )

    today = date.today()

    daily_used = Decimal("0.00")
    monthly_used = Decimal("0.00")
    current_exposure = Decimal("0.00")

    account_ids: set[str] = set()

    for row in rows:
        exposure_date = row["exposure_date"]
        reserved = _decimal(row.get("reserved_amount"))
        settled = _decimal(row.get("settled_amount"))

        used = reserved + settled
        current_exposure += used
        account_ids.add(str(row["account_id"]))

        if exposure_date == today:
            daily_used += used

        if exposure_date.year == today.year and exposure_date.month == today.month:
            monthly_used += used

    return {
        "tenant_code": tenant_code,
        "account_count": len(account_ids),
        "daily_used": daily_used,
        "monthly_used": monthly_used,
        "current_exposure": current_exposure,
    }


async def get_funding_summary() -> dict[str, Any]:
    rows = await list_funding_exposure(
        tenant_code=None,
        account_id=None,
        limit=1000,
    )

    tenant_codes: set[str] = set()
    account_ids: set[str] = set()

    current_exposure = Decimal("0.00")

    for row in rows:
        tenant_codes.add(row["tenant_code"])
        account_ids.add(str(row["account_id"]))

        reserved = _decimal(row.get("reserved_amount"))
        settled = _decimal(row.get("settled_amount"))

        current_exposure += reserved + settled

    return {
        "tenant_count": len(tenant_codes),
        "account_count": len(account_ids),
        "current_exposure": current_exposure,
    }