from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from scripts import (
    admin_audit_smoke,
    core_role_journey_smoke,
    distribution_marketplace_smoke,
    multi_currency_smoke,
)


EXPECTED_SCHEMA_GROUPS = [
    "foundation",
    "funding",
    "distribution",
    "multi_currency",
    "admin_audit",
]

EXPECTED_OPENAPI_PATHS = [
    "/enterprise/events",
    "/admin/enterprise-events/summary",
    "/admin/enterprise-events/dashboard",
    "/admin/enterprise-events/{inbox_event_id}/replay",
    "/admin/multi-currency/fx-rates",
    "/admin/multi-currency/quotes",
    "/admin/multi-currency/cross-border-settlements",
    "/admin/distribution/distributors",
    "/admin/distribution/distributor-wallets",
    "/admin/distribution/commissions/calculate",
    "/admin/distribution/opportunities",
    "/admin/distribution/routing/routes",
    "/distribution/portal/offers",
    "/admin/audit",
    "/admin/audit/summary",
    "/v1/experience/admin-command-centre",
    "/v1/experience/distributor",
    "/v1/experience/sponsor",
]

EXPECTED_METRICS = [
    "http_requests_total",
    "http_request_duration_seconds",
    "db_ready",
    "sqs_ready",
    "kafka_ready",
    "enterprise_events_ingested_total",
    "enterprise_event_replays_total",
    "enterprise_event_inbox_current",
    "admin_audit_writes_total",
    "bff_aggregate_requests_total",
    "bff_aggregate_sections_total",
    "bff_aggregate_section_latency_seconds",
]


class SmokeFailure(Exception):
    pass


def _url(base_url: str, path: str) -> str:
    return f"{base_url.rstrip('/')}{path}"


def _print_step(message: str) -> None:
    print(f"[target-state-smoke] {message}")


def _request(
    method: str,
    base_url: str,
    path: str,
    *,
    admin_key: str | None = None,
    partner_key: str | None = None,
    expected_status: int | tuple[int, ...] = 200,
    **kwargs: Any,
) -> Any:
    headers = dict(kwargs.pop("headers", {}) or {})
    if admin_key:
        headers["x-api-key"] = admin_key
    if partner_key:
        headers["x-api-key"] = partner_key

    response = requests.request(
        method,
        _url(base_url, path),
        headers=headers,
        timeout=30,
        **kwargs,
    )

    expected = expected_status if isinstance(expected_status, tuple) else (expected_status,)
    if response.status_code not in expected:
        raise SmokeFailure(
            f"{method} {path} returned {response.status_code}; expected {expected}. "
            f"Body: {response.text[:1000]}"
        )

    if not response.content:
        return None

    content_type = response.headers.get("content-type", "")
    if "application/json" not in content_type:
        return response.text

    return response.json()


def _assert_schema_ready(readyz: dict[str, Any]) -> None:
    schema = readyz.get("components", {}).get("schema", {})
    groups = schema.get("groups", {})
    missing_or_down = [
        group
        for group in EXPECTED_SCHEMA_GROUPS
        if not groups.get(group, {}).get("ok")
    ]
    if missing_or_down:
        raise SmokeFailure(
            "Schema readiness failed for groups: " + ", ".join(missing_or_down)
        )


def run_readiness_checks(base_url: str) -> None:
    _print_step("checking health and readiness")
    health = _request("GET", base_url, "/health")
    if health.get("status") != "ok":
        raise SmokeFailure(f"/health returned non-ok status: {health.get('status')}")

    readyz = _request("GET", base_url, "/readyz")
    if readyz.get("status") != "ok":
        raise SmokeFailure(f"/readyz returned non-ok status: {readyz.get('status')}")
    _assert_schema_ready(readyz)


def run_openapi_checks(base_url: str) -> None:
    _print_step("checking critical OpenAPI paths")
    openapi = _request("GET", base_url, "/openapi.json")
    paths = set(openapi.get("paths", {}))
    missing = [path for path in EXPECTED_OPENAPI_PATHS if path not in paths]
    if missing:
        raise SmokeFailure(f"OpenAPI is missing expected paths: {', '.join(missing)}")


def run_security_checks(base_url: str) -> None:
    _print_step("checking admin auth boundaries")
    _request("GET", base_url, "/admin/audit", expected_status=401)
    _request(
        "GET",
        base_url,
        "/admin/audit/summary",
        admin_key="test-finance-admin-key",
        expected_status=403,
    )


def run_enterprise_event_check(
    base_url: str,
    partner_key: str,
    admin_key: str,
    tenant_code: str,
) -> None:
    suffix = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    source_event_id = f"target-smoke-ignored-{suffix}"

    _print_step("checking IDS/Hogan enterprise event ingestion")
    response = _request(
        "POST",
        base_url,
        "/enterprise/events",
        partner_key=partner_key,
        json={
            "tenantCode": tenant_code,
            "source": "HOGAN",
            "sourceEventId": source_event_id,
            "eventType": "CUSTOMER_PROFILE_UPDATED",
            "occurredAt": datetime.now(timezone.utc).isoformat(),
            "payload": {"smoke_test": True, "target_state_smoke": True},
        },
    )
    if response.get("processingStatus") != "IGNORED":
        raise SmokeFailure(
            "Expected harmless enterprise event to be IGNORED, got "
            f"{response.get('processingStatus')}"
        )

    _print_step("checking enterprise inbox admin summary")
    _request(
        "GET",
        base_url,
        "/admin/enterprise-events/summary",
        admin_key=admin_key,
    )


def run_metrics_checks(base_url: str) -> None:
    _print_step("checking Prometheus metrics")
    metrics = _request("GET", base_url, "/metrics")
    missing = [metric for metric in EXPECTED_METRICS if metric not in metrics]
    if missing:
        raise SmokeFailure(f"/metrics is missing expected metrics: {', '.join(missing)}")


def run_domain_smokes(
    *,
    base_url: str,
    admin_key: str,
    consumer_key: str,
    producer_key: str,
    distributor_key: str,
    tenant_code: str,
    referrer_ucn: str,
    producer_code: str,
    distributor_code: str,
    write_flow: bool,
) -> None:
    _print_step("running core role journey smoke")
    core_role_journey_smoke.run_smoke(
        base_url=base_url,
        admin_key=admin_key,
        consumer_key=consumer_key,
        producer_key=producer_key,
        distributor_key=distributor_key,
        tenant_code=tenant_code,
        referrer_ucn=referrer_ucn,
        producer_code=producer_code,
        distributor_code=distributor_code,
    )

    _print_step("running multi-currency smoke")
    multi_currency_smoke.run_smoke(
        base_url=base_url,
        admin_key=admin_key,
        tenant_code=tenant_code,
    )

    _print_step("running admin audit smoke")
    admin_audit_smoke.run_smoke(
        base_url=base_url,
        admin_key=admin_key,
        tenant_code=tenant_code,
    )

    _print_step("running distribution smoke")
    distribution_marketplace_smoke.run_read_only_checks(
        base_url=base_url,
        admin_key=admin_key,
        tenant_code=tenant_code,
    )
    if write_flow:
        distribution_marketplace_smoke.run_write_flow(
            base_url=base_url,
            admin_key=admin_key,
            tenant_code=tenant_code,
        )


def run_smoke(
    *,
    base_url: str,
    admin_key: str,
    partner_key: str,
    consumer_key: str,
    producer_key: str,
    distributor_key: str,
    tenant_code: str,
    referrer_ucn: str,
    producer_code: str,
    distributor_code: str,
    write_flow: bool,
) -> None:
    run_readiness_checks(base_url)
    run_openapi_checks(base_url)
    run_security_checks(base_url)
    run_enterprise_event_check(base_url, partner_key, admin_key, tenant_code)
    run_domain_smokes(
        base_url=base_url,
        admin_key=admin_key,
        consumer_key=consumer_key,
        producer_key=producer_key,
        distributor_key=distributor_key,
        tenant_code=tenant_code,
        referrer_ucn=referrer_ucn,
        producer_code=producer_code,
        distributor_code=distributor_code,
        write_flow=write_flow,
    )
    run_metrics_checks(base_url)

    _print_step("checking admin audit summary")
    summary = _request(
        "GET",
        base_url,
        "/admin/audit/summary",
        admin_key=admin_key,
        params={"hours": 24},
    )
    if summary.get("summary", {}).get("total", 0) < 1:
        raise SmokeFailure("Expected admin audit summary to contain at least one row")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run a target-state smoke pack across readiness, enterprise events, "
            "multi-currency, distribution, admin audit, and metrics."
        )
    )
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--admin-key", default="test-admin-key")
    parser.add_argument("--partner-key", default="test-partner-key")
    parser.add_argument("--consumer-key", default="test-fnb-consumer-key")
    parser.add_argument("--producer-key", default="test-fnb-producer-insureco-key")
    parser.add_argument(
        "--distributor-key",
        default="test-fnb-distributor-insurance-advocate-key",
    )
    parser.add_argument("--tenant-code", default="FNB")
    parser.add_argument("--referrer-ucn", default="900010")
    parser.add_argument("--producer-code", default="INSURECO")
    parser.add_argument("--distributor-code", default="DIST-INSURANCE-ADVOCATE")
    parser.add_argument(
        "--write-flow",
        action="store_true",
        help="Also create distribution marketplace smoke records and run the full write flow.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    try:
        run_smoke(
            base_url=args.base_url,
            admin_key=args.admin_key,
            partner_key=args.partner_key,
            consumer_key=args.consumer_key,
            producer_key=args.producer_key,
            distributor_key=args.distributor_key,
            tenant_code=args.tenant_code,
            referrer_ucn=args.referrer_ucn,
            producer_code=args.producer_code,
            distributor_code=args.distributor_code,
            write_flow=args.write_flow,
        )
    except requests.RequestException as exc:
        print(f"[target-state-smoke] HTTP error: {exc}", file=sys.stderr)
        return 1
    except SmokeFailure as exc:
        print(f"[target-state-smoke] failed: {exc}", file=sys.stderr)
        return 1
    except (
        admin_audit_smoke.SmokeFailure,
        core_role_journey_smoke.SmokeFailure,
        distribution_marketplace_smoke.SmokeFailure,
        multi_currency_smoke.SmokeFailure,
    ) as exc:
        print(f"[target-state-smoke] domain smoke failed: {exc}", file=sys.stderr)
        return 1

    _print_step("passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
