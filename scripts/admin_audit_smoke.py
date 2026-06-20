from __future__ import annotations

import argparse
import sys
from datetime import date, datetime, timezone
from typing import Any

import requests


class SmokeFailure(Exception):
    pass


def _url(base_url: str, path: str) -> str:
    return f"{base_url.rstrip('/')}{path}"


def _print_step(message: str) -> None:
    print(f"[admin-audit-smoke] {message}")


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
        raise SmokeFailure(
            f"{method} {path} returned {response.status_code}; expected {expected}. "
            f"Body: {response.text[:1000]}"
        )

    if not response.content:
        return None

    return response.json()


def _schema_group_is_ready(readyz: dict[str, Any], group_name: str) -> bool:
    schema = readyz.get("components", {}).get("schema", {})
    groups = schema.get("groups", {})
    group = groups.get(group_name, {})
    return bool(group.get("ok"))


def run_smoke(base_url: str, admin_key: str, tenant_code: str) -> None:
    today = date.today().isoformat()
    suffix = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    source_reference = f"AUDIT-SMOKE-FX-{suffix}"

    _print_step("checking readiness and admin audit schema")
    readyz = _request("GET", base_url, "/readyz")
    if not _schema_group_is_ready(readyz, "admin_audit"):
        raise SmokeFailure(
            "The admin_audit schema group is not ready. "
            "Apply dp/migrations/071_admin_audit_log.sql and restart the app."
        )

    _print_step("checking admin audit auth rejection without API key")
    _request(
        "GET",
        base_url,
        "/admin/audit",
        expected_status=401,
    )

    _print_step("creating an audited FX rate")
    rate = _request(
        "POST",
        base_url,
        "/admin/multi-currency/fx-rates",
        admin_key=admin_key,
        json={
            "tenant_code": tenant_code,
            "base_currency": "ZAR",
            "quote_currency": "USD",
            "rate": "0.05400000",
            "rate_date": today,
            "source_system": "ADMIN_AUDIT_SMOKE",
            "source_reference": source_reference,
            "metadata": {"smoke_test": True, "audit_smoke": True},
        },
    )
    fx_rate_id = rate.get("fx_rate_id")
    if not fx_rate_id:
        raise SmokeFailure("FX rate response did not include fx_rate_id")

    _print_step("checking audit log for matching FX_RATE_UPSERT row")
    audit = _request(
        "GET",
        base_url,
        "/admin/audit",
        admin_key=admin_key,
        params={
            "action_domain": "FINANCE",
            "action_type": "FX_RATE_UPSERT",
            "target_type": "fx_rate",
            "target_id": fx_rate_id,
            "limit": 10,
        },
    )
    items = audit.get("items", [])
    if not items:
        raise SmokeFailure(
            f"No admin audit row found for FX rate {fx_rate_id}. "
            "Check application logs for admin audit write failures."
        )

    first = items[0]
    if first.get("action_status") != "SUCCESS":
        raise SmokeFailure(
            f"Expected SUCCESS audit status, got {first.get('action_status')}"
        )

    _print_step(f"found audit row {first.get('admin_audit_id')}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Smoke-test that sensitive admin actions write admin audit rows."
    )
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--admin-key", default="test-admin-key")
    parser.add_argument("--tenant-code", default="FNB")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    try:
        run_smoke(
            base_url=args.base_url,
            admin_key=args.admin_key,
            tenant_code=args.tenant_code,
        )
    except requests.RequestException as exc:
        print(f"[admin-audit-smoke] HTTP error: {exc}", file=sys.stderr)
        return 1
    except SmokeFailure as exc:
        print(f"[admin-audit-smoke] failed: {exc}", file=sys.stderr)
        return 1

    _print_step("passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
