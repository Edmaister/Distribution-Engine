from __future__ import annotations

from typing import Any, Dict, Optional

from utils.db import get_async_connection


async def create_tenant(
    tenant_code: str,
    tenant_name: str,
    industry: str,
) -> None:
    async with get_async_connection() as conn:
        await conn.execute(
            """
            INSERT INTO tenants (tenant_code, tenant_name, industry)
            VALUES ($1, $2, $3)
            ON CONFLICT (tenant_code) DO UPDATE SET
                tenant_name = EXCLUDED.tenant_name,
                industry = EXCLUDED.industry
            """,
            tenant_code,
            tenant_name,
            industry,
        )


async def get_tenant(tenant_code: str) -> Optional[Dict[str, Any]]:
    async with get_async_connection() as conn:
        row = await conn.fetchrow(
            """
            SELECT tenant_code, tenant_name, industry, currency, locale, is_active
            FROM tenants
            WHERE tenant_code = $1
            """,
            tenant_code,
        )

    return dict(row) if row else None