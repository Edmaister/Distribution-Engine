from __future__ import annotations

import argparse
import sys
from datetime import date
from typing import Any

import requests


EXPECTED_OPENAPI_PATHS = [
    "/admin/multi-currency/fx-rates",
    "/admin/multi-currency/quotes",
    "/admin/multi-currency/cross-border-settlements",
]


class SmokeFailure(Exception):
    pass


def _url(base_url: str, path: str) -> str:
    return f"{base_url.rstrip('/')}{path}"


def _print_step(message: str) -> None:
    print(f"[multi-currency-smoke] {message}")


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


def run_smoke(base_url: str, admin_key: str, tenant_code: str) -> None:
    today = date.today().isoformat()

    _print_step("checking health endpoint")
    _request("GET", base_url, "/health")

    _print_step("checking OpenAPI document and multi-currency paths")
    openapi = _request("GET", base_url, "/openapi.json")
    paths = set(openapi.get("paths", {}))
    missing = [path for path in EXPECTED_OPENAPI_PATHS if path not in paths]
    if missing:
        raise SmokeFailure(f"OpenAPI is missing expected paths: {', '.join(missing)}")

    _print_step("checking admin auth rejection without API key")
    _request(
        "GET",
        base_url,
        "/admin/multi-currency/fx-rates",
        params={"tenant_code": tenant_code},
        expected_status=401,
    )

    _print_step("creating FX rate")
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
            "source_system": "SMOKE_TEST",
            "source_reference": f"FX-{today}",
            "metadata": {"smoke_test": True},
        },
    )
    if rate["base_currency"] != "ZAR" or rate["quote_currency"] != "USD":
        raise SmokeFailure("FX rate response did not preserve expected currency pair")

    _print_step("listing FX rates")
    rates = _request(
        "GET",
        base_url,
        "/admin/multi-currency/fx-rates",
        admin_key=admin_key,
        params={
            "tenant_code": tenant_code,
            "base_currency": "ZAR",
            "quote_currency": "USD",
        },
    )
    if not rates:
        raise SmokeFailure("Expected at least one FX rate")

    _print_step("quoting direct conversion")
    quote = _request(
        "POST",
        base_url,
        "/admin/multi-currency/quotes",
        admin_key=admin_key,
        json={
            "tenant_code": tenant_code,
            "source_currency": "ZAR",
            "target_currency": "USD",
            "source_amount": "1000.00",
            "as_of_date": today,
            "persist_quote": True,
            "metadata": {"smoke_test": True, "direction": "direct"},
        },
    )
    if quote["target_amount"] != "54.00":
        raise SmokeFailure(f"Expected direct target amount 54.00, got {quote['target_amount']}")

    _print_step("quoting inverse conversion")
    inverse_quote = _request(
        "POST",
        base_url,
        "/admin/multi-currency/quotes",
        admin_key=admin_key,
        json={
            "tenant_code": tenant_code,
            "source_currency": "USD",
            "target_currency": "ZAR",
            "source_amount": "54.00",
            "as_of_date": today,
            "persist_quote": True,
            "metadata": {"smoke_test": True, "direction": "inverse"},
        },
    )
    if inverse_quote["conversion_direction"] != "INVERSE":
        raise SmokeFailure("Expected inverse conversion to use INVERSE direction")

    _print_step("creating cross-border settlement instruction")
    settlement = _request(
        "POST",
        base_url,
        "/admin/multi-currency/cross-border-settlements",
        admin_key=admin_key,
        json={
            "tenant_code": tenant_code,
            "source_currency": "ZAR",
            "target_currency": "USD",
            "source_amount": "1000.00",
            "sponsor_code": "SMOKE-SPONSOR",
            "as_of_date": today,
            "corridor": "ZA-US",
            "provider_key": "SMOKE_BANK",
            "provider_reference": f"CB-{today}",
            "metadata": {"smoke_test": True},
        },
    )
    if settlement["settlement_status"] != "PENDING":
        raise SmokeFailure("Expected cross-border settlement to start as PENDING")

    _print_step("listing cross-border settlement instructions")
    settlements = _request(
        "GET",
        base_url,
        "/admin/multi-currency/cross-border-settlements",
        admin_key=admin_key,
        params={"tenant_code": tenant_code, "settlement_status": "PENDING"},
    )
    if not settlements:
        raise SmokeFailure("Expected at least one cross-border settlement instruction")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Smoke-test the live multi-currency API."
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
        print(f"[multi-currency-smoke] HTTP error: {exc}", file=sys.stderr)
        return 1
    except SmokeFailure as exc:
        print(f"[multi-currency-smoke] failed: {exc}", file=sys.stderr)
        return 1

    _print_step("passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
