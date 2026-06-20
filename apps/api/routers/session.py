from __future__ import annotations

from fastapi import APIRouter, Depends

from utils.security import require_session_key


router = APIRouter(prefix="/auth", tags=["Session"])


PUBLIC_IDENTITY_FIELDS = {
    "authenticated",
    "role",
    "tenant_code",
    "tenant",
    "producer_code",
    "distributor_code",
    "auth_source",
    "subject",
}


def _public_identity(identity: dict) -> dict:
    return {
        key: value
        for key, value in identity.items()
        if key in PUBLIC_IDENTITY_FIELDS and value is not None
    }


WORKSPACE_DEFINITIONS = [
    {
        "code": "admin",
        "label": "Amplifi Admin",
        "path": "/admin",
        "allowed_roles": {"ADMIN"},
        "summary": "Platform command centre for operators.",
    },
    {
        "code": "admin_events",
        "label": "Event Fabric",
        "path": "/admin/events",
        "allowed_roles": {"ADMIN", "SYSTEM_ADMIN"},
        "summary": "Enterprise and Hogan event intake operations.",
    },
    {
        "code": "admin_distribution",
        "label": "Demand Marketplace",
        "path": "/admin/distribution",
        "allowed_roles": {"ADMIN", "DISTRIBUTION_ADMIN"},
        "summary": "Distributor eligibility, routing, and governance controls.",
    },
    {
        "code": "admin_billing",
        "label": "Funding Spine",
        "path": "/admin/billing",
        "allowed_roles": {"ADMIN", "FINANCE_ADMIN"},
        "summary": "Producer funding, billing, and invoice operations.",
    },
    {
        "code": "admin_multi_currency",
        "label": "Treasury Rail",
        "path": "/admin/multi-currency",
        "allowed_roles": {"ADMIN", "FINANCE_ADMIN"},
        "summary": "FX rates and cross-border settlement visibility.",
    },
    {
        "code": "admin_settlements",
        "label": "Settlement Rail",
        "path": "/admin/settlements",
        "allowed_roles": {"ADMIN", "FINANCE_ADMIN"},
        "summary": "Settlement batches, approvals, and exceptions.",
    },
    {
        "code": "admin_audit",
        "label": "Trust & Audit",
        "path": "/admin/audit",
        "allowed_roles": {"ADMIN"},
        "summary": "Audit evidence for platform-sensitive actions.",
    },
    {
        "code": "admin_health",
        "label": "Runtime Health",
        "path": "/admin/health",
        "allowed_roles": {"ADMIN", "SYSTEM_ADMIN"},
        "summary": "Platform readiness and dependency signals.",
    },
    {
        "code": "partner_integration",
        "label": "Partner Integration",
        "path": "/partner",
        "allowed_roles": {"ADMIN", "PARTNER"},
        "summary": "Partner credentials, webhook subscriptions, and delivery health.",
    },
    {
        "code": "producer_supply",
        "label": "Producer - Supply",
        "path": "/sponsor",
        "allowed_roles": {"ADMIN", "PARTNER", "PRODUCER"},
        "summary": "Producer campaign, funding, billing, and performance workspace.",
    },
    {
        "code": "distributor_demand",
        "label": "Distributor - Demand",
        "path": "/distributor",
        "allowed_roles": {"ADMIN", "PARTNER", "DISTRIBUTOR"},
        "summary": "Distributor opportunities, earnings, wallet, and recognition workspace.",
    },
    {
        "code": "consumer_journey",
        "label": "Consumer Journey",
        "path": "/consumer",
        "allowed_roles": {"ADMIN", "PARTNER", "CONSUMER"},
        "summary": "Customer conversion, reward visibility, and advocacy journey.",
    },
]


def _workspace_scope(identity: dict, workspace_code: str) -> dict:
    scope = {
        "tenant_code": identity.get("tenant_code"),
        "tenant": identity.get("tenant"),
    }

    if workspace_code == "producer_supply" and identity.get("producer_code"):
        scope["producer_code"] = identity["producer_code"]

    if workspace_code == "distributor_demand" and identity.get("distributor_code"):
        scope["distributor_code"] = identity["distributor_code"]

    return {key: value for key, value in scope.items() if value is not None}


def _session_workspaces(identity: dict) -> list[dict]:
    role = str(identity.get("role") or "").upper()
    workspaces = []

    for workspace in WORKSPACE_DEFINITIONS:
        allowed = role in workspace["allowed_roles"]
        workspaces.append(
            {
                "code": workspace["code"],
                "label": workspace["label"],
                "path": workspace["path"],
                "summary": workspace["summary"],
                "access": "allowed" if allowed else "blocked",
                "guidance": _workspace_guidance(identity, workspace, allowed),
                "scope": _workspace_scope(identity, workspace["code"]) if allowed else {},
            }
        )

    return workspaces


def _recommended_workspace(identity: dict, workspaces: list[dict]) -> dict | None:
    role = str(identity.get("role") or "").upper()
    preferred_codes = {
        "ADMIN": "admin",
        "FINANCE_ADMIN": "admin_billing",
        "DISTRIBUTION_ADMIN": "admin_distribution",
        "SYSTEM_ADMIN": "admin_health",
        "PRODUCER": "producer_supply",
        "DISTRIBUTOR": "distributor_demand",
        "CONSUMER": "consumer_journey",
        "PARTNER": "partner_integration",
    }
    preferred_code = preferred_codes.get(role)

    if preferred_code:
        for workspace in workspaces:
            if workspace["code"] == preferred_code and workspace["access"] == "allowed":
                return workspace

    return next((workspace for workspace in workspaces if workspace["access"] == "allowed"), None)


def _workspace_guidance(identity: dict, workspace: dict, allowed: bool) -> str:
    role = str(identity.get("role") or "").upper()
    label = workspace["label"]

    if allowed:
        if role == "PRODUCER" and workspace["code"] == "producer_supply":
            return "This session is scoped to the producer shown in the workspace identity."
        if role == "DISTRIBUTOR" and workspace["code"] == "distributor_demand":
            return "This session is scoped to the distributor shown in the workspace identity."
        if role == "CONSUMER" and workspace["code"] == "consumer_journey":
            return "This session can continue the customer conversion journey."
        if role == "PARTNER":
            if workspace["code"] == "partner_integration":
                return "This partner session can review integration health for its tenant."
            return f"This partner session can review and operate {label} for its tenant."
        if role == "FINANCE_ADMIN":
            return f"This finance admin session can operate {label}."
        if role == "DISTRIBUTION_ADMIN":
            return f"This distribution admin session can operate {label}."
        if role == "SYSTEM_ADMIN":
            return f"This system admin session can operate {label}."
        return f"This session can use {label}."

    if workspace["code"].startswith("admin"):
        return "Switch to an Amplifi Admin session for platform operations."
    if workspace["code"] == "producer_supply":
        return "Switch to Producer - Supply, FNB Partner, or Amplifi Admin."
    if workspace["code"] == "distributor_demand":
        return "Switch to Distributor - Demand, FNB Partner, or Amplifi Admin."
    if workspace["code"] == "consumer_journey":
        return "Switch to Consumer Journey, FNB Partner, or Amplifi Admin."
    return f"Switch to an authorised session for {label}."


@router.get("/session")
async def get_session(identity: dict = Depends(require_session_key)):
    workspaces = _session_workspaces(identity)
    return {
        "status": "ok",
        "session": _public_identity(identity),
        "recommended_workspace": _recommended_workspace(identity, workspaces),
        "workspaces": workspaces,
    }
