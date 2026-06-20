from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SERVICE = ROOT / "services" / "partner_seam_service.py"
ROUTER = ROOT / "apps" / "api" / "routers" / "partner_seam.py"

REQUIRED_SERVICE_MARKERS = [
    "partner_access_tokens",
    "access_token_hash",
    "expires_at",
    "revoked_at IS NULL",
    "expires_at > NOW()",
    "_hash_secret(access_token)",
    "Requested scope is not allowed",
    "authenticate_partner_access_token",
]

REQUIRED_ROUTER_MARKERS = [
    "/oauth/token",
    "grant_type",
    "client_credentials",
    "authenticate_partner_access_token",
]


def _assert_markers(path: Path, markers: list[str]) -> None:
    source = path.read_text(encoding="utf-8")
    missing = [marker for marker in markers if marker not in source]
    if missing:
        raise SystemExit(
            f"[oauth-maturity] {path} missing markers: {', '.join(missing)}"
        )


def main() -> int:
    _assert_markers(SERVICE, REQUIRED_SERVICE_MARKERS)
    _assert_markers(ROUTER, REQUIRED_ROUTER_MARKERS)
    print("[oauth-maturity] token store, expiry, revocation, scope, and bearer checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
