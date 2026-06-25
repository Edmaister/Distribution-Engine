from __future__ import annotations

from datetime import datetime
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from services.campaign_readiness_service import get_campaign_readiness
from services.liability_projection_service import get_outcome_liability_projection
from services.outcome_trace_service import OutcomeTraceNotFound, get_outcome_trace
from utils.security import require_session_key

router = APIRouter(
    prefix="/v1/experience/operator-control-plane",
    tags=["Operator Control Plane"],
)

CONTRACTED_SECTIONS = [
    "campaign_readiness",
    "outcome_trace",
    "funding_liability",
    "fulfilment",
    "settlement",
    "integration_health",
    "audit",
    "failures",
]
IMPLEMENTED_SECTIONS = {"campaign_readiness", "outcome_trace", "funding_liability"}
AGGREGATE_ROLES = {
    "ADMIN",
    "SYSTEM_ADMIN",
    "FINANCE_ADMIN",
    "DISTRIBUTION_ADMIN",
    "PLATFORM_ADMIN",
}
LIABILITY_ROLES = {"ADMIN", "SYSTEM_ADMIN", "FINANCE_ADMIN", "PLATFORM_ADMIN"}
CAMPAIGN_NOT_FOUND_BLOCKERS = {"CAMPAIGN_NOT_FOUND", "TENANT_MISMATCH"}


def _normalise_tenant_code(tenant_code: str) -> str:
    tenant = str(tenant_code or "").strip().upper()
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "validation_error",
                "message": "tenant_code is required",
            },
        )
    return tenant


def _normalise_sections(sections: list[str] | None) -> list[str]:
    if sections is None:
        return list(CONTRACTED_SECTIONS)

    requested: list[str] = []
    unsupported: list[str] = []
    for section in sections:
        normalised = str(section or "").strip().lower()
        if not normalised:
            continue
        if normalised not in CONTRACTED_SECTIONS:
            unsupported.append(section)
            continue
        if normalised not in requested:
            requested.append(normalised)

    if unsupported:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "validation_error",
                "message": (
                    "Unsupported operator control-plane section: "
                    + ", ".join(unsupported)
                ),
            },
        )
    return requested or list(CONTRACTED_SECTIONS)


def _require_operator_identity(identity: dict[str, Any], tenant_code: str) -> dict:
    role = str(identity.get("role") or "").upper()
    if role not in AGGREGATE_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "permission_denied",
                "message": (
                    "API key is not authorised for operator control-plane access"
                ),
            },
        )

    identity_tenant = (
        str(identity.get("tenant_code") or identity.get("tenant") or "").strip().upper()
    )
    if (
        identity_tenant
        and identity_tenant != "INTERNAL"
        and identity_tenant != tenant_code
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "permission_denied",
                "message": "API key is not authorised for this tenant",
            },
        )

    return identity


def _section(
    *,
    status: str,
    data: Any | None = None,
    missing_evidence: list[dict[str, Any]] | None = None,
    source_warnings: list[dict[str, Any]] | None = None,
    redactions: list[dict[str, Any]] | None = None,
    backend_sources: list[str] | None = None,
    safe_next_actions: list[dict[str, Any]] | None = None,
    error: dict[str, Any] | None = None,
) -> dict[str, Any]:
    result = {
        "status": status,
        "data": data,
        "missing_evidence": missing_evidence or [],
        "source_warnings": source_warnings or [],
        "redactions": redactions or [],
        "backend_sources": backend_sources or [],
        "safe_next_actions": safe_next_actions or [],
    }
    if error:
        result["error"] = error
    return result


def _not_implemented_section(name: str) -> dict[str, Any]:
    return _section(
        status="not_implemented",
        backend_sources=[],
        error={
            "code": "not_implemented",
            "message": f"{name} has no operator BFF implementation yet.",
            "retryable": False,
        },
    )


def _permission_denied_section(name: str) -> dict[str, Any]:
    return _section(
        status="permission_denied",
        error={
            "code": "permission_denied",
            "message": f"Authenticated actor is not authorized for {name}.",
            "retryable": False,
        },
    )


def _not_found_section(name: str) -> dict[str, Any]:
    return _section(
        status="unavailable",
        error={
            "code": "not_found",
            "message": f"{name} source evidence was not found for this tenant.",
            "retryable": False,
        },
    )


def _source_unavailable_section(name: str) -> dict[str, Any]:
    return _section(
        status="unavailable",
        error={
            "code": "section_unavailable",
            "message": f"{name} is temporarily unavailable.",
            "retryable": True,
        },
    )


def _validation_error_section(name: str, message: str) -> dict[str, Any]:
    return _section(
        status="unavailable",
        error={
            "code": "validation_error",
            "message": message,
            "retryable": False,
        },
    )


def _loaded_section(
    *,
    data: dict[str, Any],
    completeness_key: str,
    backend_source: str,
) -> dict[str, Any]:
    missing_evidence = list(data.get("missing_evidence") or [])
    source_warnings = list(data.get("source_warnings") or [])
    redactions = list(data.get("redactions") or [])
    completeness = str(data.get(completeness_key) or "COMPLETE").upper()
    section_status = (
        "ok"
        if completeness == "COMPLETE" and not missing_evidence and not source_warnings
        else "missing_evidence"
    )
    return _section(
        status=section_status,
        data=data,
        missing_evidence=missing_evidence,
        source_warnings=source_warnings,
        redactions=redactions,
        backend_sources=[backend_source],
    )


def _has_blocker(data: dict[str, Any], codes: set[str]) -> bool:
    return any(
        str(blocker.get("code") or "").upper() in codes
        for blocker in data.get("blockers", [])
        if isinstance(blocker, dict)
    )


def _campaign_readiness_section(data: dict[str, Any]) -> dict[str, Any]:
    blockers = list(data.get("blockers") or [])
    warnings = list(data.get("warnings") or [])
    unknowns = list(data.get("unknowns") or [])
    readiness = str(data.get("readiness") or "").upper()
    section_status = (
        "ok"
        if readiness == "READY" and not blockers and not warnings and not unknowns
        else "missing_evidence"
    )
    return _section(
        status=section_status,
        data=data,
        missing_evidence=blockers + unknowns,
        source_warnings=warnings,
        backend_sources=["services.campaign_readiness_service.get_campaign_readiness"],
    )


def _top_level_status(sections: dict[str, dict[str, Any]]) -> str:
    if not sections:
        return "unavailable"

    statuses = [str(section.get("status")) for section in sections.values()]
    loaded = {"ok", "missing_evidence"}
    if all(section_status == "ok" for section_status in statuses):
        return "ok"
    if any(section_status in loaded for section_status in statuses):
        return "partial"
    return "unavailable"


def _collect_redactions(sections: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    redactions: list[dict[str, Any]] = []
    seen: set[tuple[Any, ...]] = set()
    for section in sections.values():
        for redaction in section.get("redactions", []):
            identity = tuple(sorted(redaction.items()))
            if identity in seen:
                continue
            seen.add(identity)
            redactions.append(redaction)
    return redactions


@router.get("/outcomes/{referral_track_id}")
async def get_operator_control_plane_outcome(
    referral_track_id: UUID,
    tenant_code: Annotated[str, Query(min_length=1)],
    campaign_code: str | None = Query(default=None),
    campaign_operation: Annotated[str, Query(min_length=1)] = "CONTROL_PLANE_VIEW",
    opportunity_id: str | None = Query(default=None),
    include_campaign_evidence: bool = Query(default=True),
    requested_sections: Annotated[
        list[str] | None,
        Query(alias="sections"),
    ] = None,
    identity: dict = Depends(require_session_key),
):
    resolved_tenant = _normalise_tenant_code(tenant_code)
    operator_identity = _require_operator_identity(identity, resolved_tenant)
    sections_to_load = _normalise_sections(requested_sections)
    role = str(operator_identity.get("role") or "").upper()

    resolved_sections: dict[str, dict[str, Any]] = {}

    for section_name in sections_to_load:
        if section_name not in IMPLEMENTED_SECTIONS:
            resolved_sections[section_name] = _not_implemented_section(section_name)
            continue

        if section_name == "funding_liability" and role not in LIABILITY_ROLES:
            resolved_sections[section_name] = _permission_denied_section(section_name)
            continue

        try:
            if section_name == "campaign_readiness":
                if not str(campaign_code or "").strip():
                    resolved_sections[section_name] = _validation_error_section(
                        section_name,
                        "campaign_code is required for campaign_readiness.",
                    )
                    continue

                readiness = await get_campaign_readiness(
                    tenant_code=resolved_tenant,
                    campaign_code=str(campaign_code),
                    operation=campaign_operation,
                    opportunity_id=opportunity_id,
                    include_evidence=include_campaign_evidence,
                )
                if _has_blocker(readiness, CAMPAIGN_NOT_FOUND_BLOCKERS):
                    resolved_sections[section_name] = _not_found_section(section_name)
                else:
                    resolved_sections[section_name] = _campaign_readiness_section(
                        readiness
                    )
            elif section_name == "outcome_trace":
                trace = await get_outcome_trace(
                    tenant_code=resolved_tenant,
                    referral_track_id=str(referral_track_id),
                    identity=operator_identity,
                )
                resolved_sections[section_name] = _loaded_section(
                    data=trace,
                    completeness_key="trace_completeness",
                    backend_source="services.outcome_trace_service.get_outcome_trace",
                )
            elif section_name == "funding_liability":
                projection = await get_outcome_liability_projection(
                    tenant_code=resolved_tenant,
                    referral_track_id=str(referral_track_id),
                    identity=operator_identity,
                )
                resolved_sections[section_name] = _loaded_section(
                    data=projection,
                    completeness_key="liability_completeness",
                    backend_source=(
                        "services.liability_projection_service."
                        "get_outcome_liability_projection"
                    ),
                )
        except ValueError as exc:
            resolved_sections[section_name] = _validation_error_section(
                section_name,
                str(exc),
            )
        except OutcomeTraceNotFound:
            resolved_sections[section_name] = _not_found_section(section_name)
        except Exception:  # pragma: no cover - defensive BFF section boundary
            resolved_sections[section_name] = _source_unavailable_section(section_name)

    unavailable_sections = [
        name
        for name, section in resolved_sections.items()
        if section["status"] in {"timeout", "unavailable", "not_implemented"}
    ]
    permission_denied_sections = [
        name
        for name, section in resolved_sections.items()
        if section["status"] == "permission_denied"
    ]

    return {
        "status": _top_level_status(resolved_sections),
        "tenant_code": resolved_tenant,
        "generated_at": datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
        "requested_sections": sections_to_load,
        "sections": resolved_sections,
        "unavailable_sections": unavailable_sections,
        "permission_denied_sections": permission_denied_sections,
        "redactions": _collect_redactions(resolved_sections),
        "guardrail": (
            "Read-only aggregate. Command workflows require separately "
            "authorized routes."
        ),
    }
