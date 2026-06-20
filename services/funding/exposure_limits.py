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


async def validate_exposure(
    *,
    tenant_code: str,
    account_id: UUID | str,
    amount: Decimal,
) -> tuple[bool, str | None]:
    limit = await get_active_funding_limit(
        tenant_code=tenant_code,
        account_id=account_id,
    )

    if limit is None:
        return False, "NO_ACTIVE_LIMIT"

    rows = await list_funding_exposure(
        tenant_code=tenant_code,
        account_id=account_id,
        limit=500,
    )

    today = date.today()
    current_month = today.month
    current_year = today.year

    daily_used = Decimal("0.00")
    monthly_used = Decimal("0.00")
    current_exposure = Decimal("0.00")

    for row in rows:
        exposure_date = row["exposure_date"]

        reserved = _decimal(row.get("reserved_amount"))
        settled = _decimal(row.get("settled_amount"))

        current_exposure += reserved + settled

        if exposure_date == today:
            daily_used += reserved + settled

        if exposure_date.month == current_month and exposure_date.year == current_year:
            monthly_used += reserved + settled

    projected_daily = daily_used + amount
    projected_monthly = monthly_used + amount
    projected_exposure = current_exposure + amount

    if projected_daily > _decimal(limit["daily_limit"]):
        return False, "DAILY_LIMIT_EXCEEDED"

    if projected_monthly > _decimal(limit["monthly_limit"]):
        return False, "MONTHLY_LIMIT_EXCEEDED"

    if projected_exposure > _decimal(limit["exposure_limit"]):
        return False, "EXPOSURE_LIMIT_EXCEEDED"

    return True, None