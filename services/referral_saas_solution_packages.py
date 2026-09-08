"""TASK-464: commercial packaging over single-source platform capabilities.

Campaign attribution requires registered campaign evidence. It does not invoke
campaign creation, and the composite validator remains a shared dependency.
No quotas, service tiers, prices, or independent deployment are implied.
"""
from datetime import date, datetime, timezone

REFERRAL_MANAGEMENT = "REFERRAL_MANAGEMENT"
CAMPAIGN_ATTRIBUTION = "CAMPAIGN_ATTRIBUTION"
COMBINED = "REFERRAL_MANAGEMENT_AND_ATTRIBUTION"
SOLUTION_PACKAGES = {
    REFERRAL_MANAGEMENT: {
        "code": REFERRAL_MANAGEMENT,
        "name": "Referral Management",
        "description": "Create and manage referral campaigns, issue links and codes, and track referral progress.",
        "solutions": [REFERRAL_MANAGEMENT],
        "recommended": False,
    },
    CAMPAIGN_ATTRIBUTION: {
        "code": CAMPAIGN_ATTRIBUTION,
        "name": "Campaign Attribution",
        "description": "Validate registered campaign evidence and explain source and channel attribution. Campaign registration remains a shared prerequisite.",
        "solutions": [CAMPAIGN_ATTRIBUTION],
        "recommended": False,
    },
    COMBINED: {
        "code": COMBINED,
        "name": "Referral Management + Campaign Attribution",
        "description": "Manage referrals and attribute campaign outcomes through the same shared evidence chain.",
        "solutions": [REFERRAL_MANAGEMENT, CAMPAIGN_ATTRIBUTION],
        "recommended": True,
    },
}
SOLUTION_MODULES = {
    REFERRAL_MANAGEMENT: ["campaigns", "referrals", "referrers", "links", "progress", "attribution", "journeys", "products", "programmes"],
    CAMPAIGN_ATTRIBUTION: ["attribution"],
}


def package_for(evidence):
    if not isinstance(evidence, dict):
        return None
    return SOLUTION_PACKAGES.get(str(evidence.get("plan_code", "")).strip().upper())


def evidence_is_current(evidence, today=None):
    today = today or datetime.now(timezone.utc).date()
    if not package_for(evidence):
        return False
    if evidence.get("contract_source") not in {"APPROVED_CONTRACT", "SIGNED_ORDER_FORM", "INTERNAL_APPROVAL"}:
        return False
    if not str(evidence.get("entitlement_reference", "")).strip() or not str(evidence.get("responsible_owner", "")).strip():
        return False
    try:
        start = date.fromisoformat(evidence.get("effective_from", ""))
        end = date.fromisoformat(evidence["effective_until"]) if evidence.get("effective_until") else None
    except (ValueError, TypeError):
        return False
    return start <= today and (end is None or today <= end)


def package_modules(evidence):
    package = package_for(evidence)
    return [module for solution in package["solutions"] for module in SOLUTION_MODULES[solution]] if package else []


def solution_access_allowed(evidence, solution):
    # Uncontracted accounts retain existing safe setup. Production gates still fail closed.
    if not evidence:
        return True
    package = package_for(evidence)
    return bool(package and solution in package["solutions"] and evidence_is_current(evidence))
