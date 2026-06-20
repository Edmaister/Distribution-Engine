from __future__ import annotations

import argparse
import sys
from typing import Any

import requests


class SmokeFailure(Exception):
    pass


def _url(base_url: str, path: str) -> str:
    return f"{base_url.rstrip('/')}{path}"


def _print_step(message: str) -> None:
    print(f"[core-role-smoke] {message}")


def _request(
    method: str,
    base_url: str,
    path: str,
    *,
    api_key: str | None = None,
    expected_status: int | tuple[int, ...] = 200,
    **kwargs: Any,
) -> Any:
    headers = dict(kwargs.pop("headers", {}) or {})
    if api_key:
        headers["x-api-key"] = api_key

    response = requests.request(
        method,
        _url(base_url, path),
        headers=headers,
        timeout=20,
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


def _assert_session(
    *,
    base_url: str,
    api_key: str,
    expected_role: str,
    expected_workspace: str,
) -> None:
    session = _request("GET", base_url, "/auth/session", api_key=api_key)
    role = str(session.get("session", {}).get("role") or "").upper()
    workspace = (session.get("recommended_workspace") or {}).get("code")

    if role != expected_role:
        raise SmokeFailure(f"Expected session role {expected_role}, got {role or 'missing'}")
    if workspace != expected_workspace:
        raise SmokeFailure(
            f"Expected recommended workspace {expected_workspace}, got {workspace or 'missing'}"
        )


def _assert_json_keys(body: dict[str, Any], keys: set[str], label: str) -> None:
    missing = sorted(keys.difference(body))
    if missing:
        raise SmokeFailure(f"{label} response missing keys: {', '.join(missing)}")


def run_consumer_check(
    *,
    base_url: str,
    consumer_key: str,
    tenant_code: str,
    referrer_ucn: str,
) -> None:
    _print_step("checking consumer journey")
    _assert_session(
        base_url=base_url,
        api_key=consumer_key,
        expected_role="CONSUMER",
        expected_workspace="consumer_journey",
    )
    body = _request(
        "GET",
        base_url,
        "/v1/experience/consumer",
        api_key=consumer_key,
        params={"tenant_code": tenant_code, "referrer_ucn": referrer_ucn},
    )
    _assert_json_keys(
        body,
        {"status", "tenantCode", "referrerUcn", "sections", "unavailableSections"},
        "consumer journey",
    )
    _request(
        "GET",
        base_url,
        "/v1/experience/consumer",
        api_key=consumer_key,
        params={"tenant_code": "PNP", "referrer_ucn": referrer_ucn},
        expected_status=403,
    )


def run_producer_check(
    *,
    base_url: str,
    producer_key: str,
    tenant_code: str,
    producer_code: str,
) -> None:
    _print_step("checking producer supply journey")
    _assert_session(
        base_url=base_url,
        api_key=producer_key,
        expected_role="PRODUCER",
        expected_workspace="producer_supply",
    )
    path = f"/v1/tenants/{tenant_code}/producers/{producer_code}/supply/proof/insurance"
    body = _request("GET", base_url, path, api_key=producer_key)
    _assert_json_keys(body, {"status", "scope", "surface", "tenant_code"}, "producer proof")

    wrong_path = f"/v1/tenants/{tenant_code}/producers/OTHER/supply/proof/insurance"
    _request("GET", base_url, wrong_path, api_key=producer_key, expected_status=403)


def run_distributor_check(
    *,
    base_url: str,
    distributor_key: str,
    tenant_code: str,
    distributor_code: str,
) -> None:
    _print_step("checking distributor demand journey")
    _assert_session(
        base_url=base_url,
        api_key=distributor_key,
        expected_role="DISTRIBUTOR",
        expected_workspace="distributor_demand",
    )
    body = _request(
        "GET",
        base_url,
        "/distribution/portal/proof/insurance",
        api_key=distributor_key,
        params={"tenant_code": tenant_code, "distributor_code": distributor_code},
    )
    _assert_json_keys(body, {"status", "scope", "surface", "tenant_code"}, "distributor proof")
    _request(
        "GET",
        base_url,
        "/distribution/portal/proof/insurance",
        api_key=distributor_key,
        params={"tenant_code": tenant_code, "distributor_code": "OTHER"},
        expected_status=403,
    )


def run_admin_check(*, base_url: str, admin_key: str) -> None:
    _print_step("checking admin operations journey")
    _assert_session(
        base_url=base_url,
        api_key=admin_key,
        expected_role="ADMIN",
        expected_workspace="admin",
    )
    body = _request("GET", base_url, "/admin/audit/summary", api_key=admin_key)
    _assert_json_keys(body, {"summary"}, "admin audit summary")
    _request("GET", base_url, "/admin/audit/summary", expected_status=401)


def run_smoke(
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
) -> None:
    run_consumer_check(
        base_url=base_url,
        consumer_key=consumer_key,
        tenant_code=tenant_code,
        referrer_ucn=referrer_ucn,
    )
    run_producer_check(
        base_url=base_url,
        producer_key=producer_key,
        tenant_code=tenant_code,
        producer_code=producer_code,
    )
    run_distributor_check(
        base_url=base_url,
        distributor_key=distributor_key,
        tenant_code=tenant_code,
        distributor_code=distributor_code,
    )
    run_admin_check(base_url=base_url, admin_key=admin_key)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Smoke-test core consumer, producer, distributor, and admin journeys."
    )
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--admin-key", default="test-admin-key")
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
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    try:
        run_smoke(
            base_url=args.base_url,
            admin_key=args.admin_key,
            consumer_key=args.consumer_key,
            producer_key=args.producer_key,
            distributor_key=args.distributor_key,
            tenant_code=args.tenant_code,
            referrer_ucn=args.referrer_ucn,
            producer_code=args.producer_code,
            distributor_code=args.distributor_code,
        )
    except requests.RequestException as exc:
        print(f"[core-role-smoke] HTTP error: {exc}", file=sys.stderr)
        return 1
    except SmokeFailure as exc:
        print(f"[core-role-smoke] failed: {exc}", file=sys.stderr)
        return 1

    _print_step("passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
