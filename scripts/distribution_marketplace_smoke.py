from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from typing import Any

import requests


EXPECTED_OPENAPI_PATHS = [
    "/admin/distribution/distributors",
    "/admin/distribution/distributor-wallets",
    "/admin/distribution/commissions/rules",
    "/admin/distribution/commissions/calculate",
    "/admin/distribution/opportunities",
    "/admin/distribution/routing/routes",
    "/distribution/portal/profile",
    "/admin/distribution/governance/compliance-reviews",
    "/admin/distribution/reporting/overview",
    "/admin/distribution/reporting/opportunities",
    "/admin/distribution/reporting/distributors",
    "/admin/distribution/reporting/governance",
]


class SmokeFailure(Exception):
    pass


def _url(base_url: str, path: str) -> str:
    return f"{base_url.rstrip('/')}{path}"


def _print_step(message: str) -> None:
    print(f"[distribution-smoke] {message}")


def _request(
    method: str,
    base_url: str,
    path: str,
    *,
    admin_key: str | None = None,
    expected_status: int | tuple[int, ...] = 200,
    **kwargs: Any,
) -> Any:
    headers = dict(kwargs.pop("headers", {}) or {})
    if admin_key:
        headers["x-api-key"] = admin_key

    response = requests.request(
        method,
        _url(base_url, path),
        headers=headers,
        timeout=20,
        **kwargs,
    )

    expected = (
        expected_status
        if isinstance(expected_status, tuple)
        else (expected_status,)
    )
    if response.status_code not in expected:
        body = response.text[:1000]
        raise SmokeFailure(
            f"{method} {path} returned {response.status_code}; expected {expected}. Body: {body}"
        )

    if not response.content:
        return None

    return response.json()


def run_read_only_checks(base_url: str, admin_key: str, tenant_code: str) -> None:
    _print_step("checking health endpoint")
    _request("GET", base_url, "/health")

    _print_step("checking OpenAPI document and distribution paths")
    openapi = _request("GET", base_url, "/openapi.json")
    paths = set(openapi.get("paths", {}))
    missing = [path for path in EXPECTED_OPENAPI_PATHS if path not in paths]
    if missing:
        raise SmokeFailure(f"OpenAPI is missing expected paths: {', '.join(missing)}")

    _print_step("checking admin auth rejection without API key")
    _request(
        "GET",
        base_url,
        "/admin/distribution/reporting/overview",
        params={"tenant_code": tenant_code},
        expected_status=401,
    )

    _print_step("checking reporting endpoints with admin API key")
    for path in (
        "/admin/distribution/reporting/overview",
        "/admin/distribution/reporting/opportunities",
        "/admin/distribution/reporting/distributors",
        "/admin/distribution/reporting/governance",
    ):
        _request(
            "GET",
            base_url,
            path,
            admin_key=admin_key,
            params={"tenant_code": tenant_code, "limit": 5},
        )


def run_write_flow(base_url: str, admin_key: str, tenant_code: str) -> None:
    suffix = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    distributor_code = f"SMOKE-DIST-{suffix}"
    sponsor_code = "SMOKE-SPONSOR"
    campaign_code = f"SMOKE-CAMPAIGN-{suffix}"
    opportunity_code = f"SMOKE-OPP-{suffix}"

    _print_step("creating distributor")
    distributor_response = _request(
        "POST",
        base_url,
        "/admin/distribution/distributors",
        admin_key=admin_key,
        json={
            "tenant_code": tenant_code,
            "distributor_code": distributor_code,
            "distributor_name": "Smoke Distributor",
            "distributor_type": "BROKER",
            "contact_email": "smoke.distributor@example.com",
            "channels": ["BRANCH", "DIGITAL"],
            "segments": ["MASS"],
            "regions": ["ZA-GP"],
            "capabilities": {"sales": True},
            "eligibility": {"kyc": "PASSED"},
            "operating_limits": {"daily_allocations": 10},
            "metadata": {"smoke_test": True},
        },
    )
    distributor = distributor_response["distributor"]
    distributor_id = distributor["distributor_id"]

    _print_step("activating distributor")
    _request(
        "POST",
        base_url,
        f"/admin/distribution/distributors/{distributor_id}/activate",
        admin_key=admin_key,
    )

    _print_step("creating distributor wallet")
    wallet = _request(
        "POST",
        base_url,
        "/admin/distribution/distributor-wallets",
        admin_key=admin_key,
        json={
            "distributor_id": distributor_id,
            "currency": "ZAR",
            "metadata": {"smoke_test": True},
        },
    )
    wallet_id = wallet["wallet_id"]

    _print_step("creating commission rule")
    rule = _request(
        "POST",
        base_url,
        "/admin/distribution/commissions/rules",
        admin_key=admin_key,
        json={
            "tenant_code": tenant_code,
            "sponsor_code": sponsor_code,
            "campaign_code": campaign_code,
            "distributor_type": "BROKER",
            "commission_type": "FIXED",
            "fixed_amount": "25.00",
            "currency": "ZAR",
            "priority": 1,
            "description": "Distribution marketplace smoke rule",
            "metadata": {"smoke_test": True},
        },
    )

    _print_step("creating and publishing opportunity")
    opportunity = _request(
        "POST",
        base_url,
        "/admin/distribution/opportunities",
        admin_key=admin_key,
        json={
            "tenant_code": tenant_code,
            "sponsor_code": sponsor_code,
            "campaign_code": campaign_code,
            "opportunity_code": opportunity_code,
            "title": "Smoke Opportunity",
            "description": "End-to-end distribution smoke opportunity",
            "product_code": "SMOKE-PRODUCT",
            "product_name": "Smoke Product",
            "target_segments": ["MASS"],
            "target_regions": ["ZA-GP"],
            "target_channels": ["DIGITAL"],
            "distributor_types": ["BROKER"],
            "commission_rule_id": rule["rule_id"],
            "estimated_reward_amount": "10.00",
            "estimated_commission_amount": "25.00",
            "total_budget": "1000.00",
            "max_allocations": 20,
            "metadata": {"smoke_test": True},
        },
    )
    opportunity_id = opportunity["opportunity_id"]
    _request(
        "POST",
        base_url,
        f"/admin/distribution/opportunities/{opportunity_id}/publish",
        admin_key=admin_key,
    )

    _print_step("matching and routing opportunity")
    matches = _request(
        "POST",
        base_url,
        f"/admin/distribution/routing/opportunities/{opportunity_id}/matches",
        admin_key=admin_key,
        json={"minimum_score": "1", "limit": 5},
    )
    if matches["count"] < 1:
        raise SmokeFailure("Expected at least one matched distributor")

    routes = _request(
        "POST",
        base_url,
        f"/admin/distribution/routing/opportunities/{opportunity_id}/routes",
        admin_key=admin_key,
        json={"minimum_score": "1", "limit": 5, "metadata": {"smoke_test": True}},
    )
    if routes["count"] < 1:
        raise SmokeFailure("Expected at least one created route")
    route_id = routes["items"][0]["route_id"]

    _print_step("checking distributor portal and accepting offer")
    _request(
        "GET",
        base_url,
        "/distribution/portal/profile",
        admin_key=admin_key,
        params={"tenant_code": tenant_code, "distributor_code": distributor_code},
    )
    _request(
        "GET",
        base_url,
        "/distribution/portal/offers",
        admin_key=admin_key,
        params={"tenant_code": tenant_code, "distributor_code": distributor_code},
    )
    _request(
        "POST",
        base_url,
        f"/distribution/portal/offers/{route_id}/accept",
        admin_key=admin_key,
        params={"tenant_code": tenant_code, "distributor_code": distributor_code},
    )

    _print_step("calculating commission and crediting wallet")
    _request(
        "POST",
        base_url,
        "/admin/distribution/commissions/calculate",
        admin_key=admin_key,
        json={
            "tenant_code": tenant_code,
            "distributor_id": distributor_id,
            "activity_type": "SALE",
            "sale_amount": "100.00",
            "sponsor_code": sponsor_code,
            "campaign_code": campaign_code,
            "source_event_id": f"smoke-event-{suffix}",
            "wallet_id": wallet_id,
            "credit_wallet": True,
            "correlation_id": f"smoke-correlation-{suffix}",
            "metadata": {"smoke_test": True},
        },
    )
    _request(
        "GET",
        base_url,
        f"/admin/distribution/distributor-wallets/{wallet_id}/ledger",
        admin_key=admin_key,
    )

    _print_step("creating and completing compliance review")
    review = _request(
        "POST",
        base_url,
        "/admin/distribution/governance/compliance-reviews",
        admin_key=admin_key,
        json={
            "distributor_id": distributor_id,
            "review_type": "SMOKE_REVIEW",
            "reviewer": "smoke-test",
            "notes": "Smoke compliance review",
            "metadata": {"smoke_test": True},
        },
    )
    _request(
        "POST",
        base_url,
        f"/admin/distribution/governance/compliance-reviews/{review['review_id']}/complete",
        admin_key=admin_key,
        json={
            "review_result": "PASSED",
            "reviewer": "smoke-test",
            "notes": "Smoke compliance review passed",
            "metadata": {"smoke_test": True},
        },
    )

    _print_step("creating and resolving dispute")
    dispute = _request(
        "POST",
        base_url,
        "/admin/distribution/governance/disputes",
        admin_key=admin_key,
        json={
            "route_id": route_id,
            "raised_by": "smoke-test",
            "reason_code": "SMOKE_DISPUTE",
            "description": "Smoke dispute",
            "metadata": {"smoke_test": True},
        },
    )
    _request(
        "POST",
        base_url,
        f"/admin/distribution/governance/disputes/{dispute['dispute_id']}/resolve",
        admin_key=admin_key,
        json={
            "dispute_status": "RESOLVED",
            "resolved_by": "smoke-test",
            "resolution_notes": "Smoke dispute resolved",
            "metadata": {"smoke_test": True},
        },
    )

    _print_step("checking reporting after write flow")
    run_read_only_checks(base_url, admin_key, tenant_code)
    _request(
        "GET",
        base_url,
        "/distribution/portal/performance",
        admin_key=admin_key,
        params={"tenant_code": tenant_code, "distributor_code": distributor_code},
    )

    _print_step(
        "write flow created "
        f"distributor={distributor_code}, opportunity={opportunity_code}, route={route_id}"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Smoke-test the live Distribution Marketplace API."
    )
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--admin-key", default="test-admin-key")
    parser.add_argument("--tenant-code", default="FNB")
    parser.add_argument(
        "--write-flow",
        action="store_true",
        help="Create smoke-test marketplace records and run the full flow.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    try:
        run_read_only_checks(
            base_url=args.base_url,
            admin_key=args.admin_key,
            tenant_code=args.tenant_code,
        )
        if args.write_flow:
            run_write_flow(
                base_url=args.base_url,
                admin_key=args.admin_key,
                tenant_code=args.tenant_code,
            )

    except requests.RequestException as exc:
        print(f"[distribution-smoke] HTTP error: {exc}", file=sys.stderr)
        return 1
    except SmokeFailure as exc:
        print(f"[distribution-smoke] failed: {exc}", file=sys.stderr)
        return 1

    _print_step("passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
