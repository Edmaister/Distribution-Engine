from __future__ import annotations

import asyncio
from time import perf_counter
from typing import Any, Awaitable, Callable

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from services.admin_audit_service import get_admin_audit_summary
from services.enterprise_event_inbox_service import get_enterprise_event_summary
from services.outcome_money_reconciliation_service import get_outcome_money_map
from services.provider_sla_service import list_provider_sla_metrics
from utils.metrics import bff_aggregate_request_inc, bff_aggregate_section_observe
from utils.security import require_system_admin_key


router = APIRouter(
    prefix="/v1/experience/admin-command-centre",
    tags=["Admin Experience"],
    dependencies=[Depends(require_system_admin_key)],
)

DEFAULT_SECTION_TIMEOUT_SECONDS = 2.0
ROUTE_METRIC = "admin_command_centre"


class AdminExperienceSection(BaseModel):
    status: str
    data: Any | None = None
    error: str | None = None
    degraded: bool = False


class AdminCommandCentreResponse(BaseModel):
    status: str
    tenantCode: str
    sections: dict[str, AdminExperienceSection] = Field(default_factory=dict)
    unavailableSections: list[str] = Field(default_factory=list)
    guardrail: str


async def _runtime_health_payload() -> dict[str, Any]:
    from apps.api import main as api_main

    return await api_main._compose_health(full=True)


async def _section(
    name: str,
    loader: Callable[[], Awaitable[Any]],
    *,
    tenant_code: str,
    timeout_seconds: float = DEFAULT_SECTION_TIMEOUT_SECONDS,
) -> tuple[str, AdminExperienceSection]:
    start = perf_counter()
    status = "unavailable"
    try:
        status = "ok"
        return name, AdminExperienceSection(
            status="ok",
            data=await asyncio.wait_for(loader(), timeout=timeout_seconds),
        )
    except TimeoutError:
        status = "timeout"
        return name, AdminExperienceSection(
            status="timeout",
            error=f"{name} section timed out after {timeout_seconds:g}s",
            degraded=True,
        )
    except HTTPException as exc:
        status = "unavailable"
        return name, AdminExperienceSection(
            status="unavailable",
            error=str(exc.detail),
            degraded=True,
        )
    except Exception as exc:  # pragma: no cover - defensive boundary
        status = "unavailable"
        return name, AdminExperienceSection(
            status="unavailable",
            error=str(exc),
            degraded=True,
        )
    finally:
        bff_aggregate_section_observe(
            route=ROUTE_METRIC,
            tenant=tenant_code,
            section=name,
            status=status,
            latency_seconds=perf_counter() - start,
        )


@router.get("", response_model=AdminCommandCentreResponse)
async def get_admin_command_centre(
    tenant_code: str = Query("FNB", min_length=2),
    outcome_limit: int = Query(default=25, ge=1, le=100),
    section_timeout_seconds: float = Query(
        DEFAULT_SECTION_TIMEOUT_SECONDS,
        ge=0.05,
        le=10,
        include_in_schema=False,
    ),
) -> AdminCommandCentreResponse:
    resolved_tenant = tenant_code.strip().upper()

    loaders: list[tuple[str, Callable[[], Awaitable[Any]]]] = [
        ("runtime", _runtime_health_payload),
        ("events", get_enterprise_event_summary),
        (
            "audit",
            lambda: get_admin_audit_summary(
                tenant_code=resolved_tenant,
                hours=24,
                action_domain=None,
            ),
        ),
        (
            "finance",
            lambda: get_outcome_money_map(
                tenant_code=resolved_tenant,
                limit=outcome_limit,
            ),
        ),
        ("providers", list_provider_sla_metrics),
    ]

    resolved_sections = await asyncio.gather(
        *[
            _section(
                name,
                loader,
                tenant_code=resolved_tenant,
                timeout_seconds=section_timeout_seconds,
            )
            for name, loader in loaders
        ]
    )
    sections = dict(resolved_sections)
    unavailable = [
        name for name, section in sections.items() if section.status != "ok"
    ]

    response_status = "partial" if unavailable else "ok"
    bff_aggregate_request_inc(
        route=ROUTE_METRIC,
        tenant=resolved_tenant,
        status=response_status,
    )

    return AdminCommandCentreResponse(
        status=response_status,
        tenantCode=resolved_tenant,
        sections=sections,
        unavailableSections=unavailable,
        guardrail=(
            "Admin command-centre BFF response aggregates read-only operating "
            "signals. It does not replay events, create finance evidence, "
            "change settlement state, or send channel messages."
        ),
    )
