from __future__ import annotations

import hashlib
import logging
import time
from typing import Optional

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from apps.api.settings import get_settings
from apps.core.cache import get_cache

logger = logging.getLogger(__name__)

_redis_unavailable_rate_limit_logged = False


DEFAULT_RATE_LIMIT_PER_MINUTE = 120
ADMIN_RATE_LIMIT_PER_MINUTE = 600


def _configured_keys(value: str | None) -> list[str]:
    if not value:
        return []
    return [key.strip() for key in value.split(",") if key.strip()]


def _hash_key(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]


def _resolve_tenant_from_key(api_key: str | None) -> str:
    if not api_key:
        return "anonymous"

    settings = get_settings()

    admin_keys = _configured_keys(getattr(settings, "admin_api_key", None))
    if api_key in admin_keys:
        return "admin"

    fnb_keys = []
    for field in (
        "fnb_partner_api_key",
        "fnb_tenant_user_api_key",
        "fnb_tenant_admin_api_key",
    ):
        fnb_keys.extend(_configured_keys(getattr(settings, field, None)))

    if api_key in fnb_keys:
        return "FNB"

    pnp_keys = []
    for field in (
        "pnp_partner_api_key",
        "pnp_tenant_user_api_key",
        "pnp_tenant_admin_api_key",
    ):
        pnp_keys.extend(_configured_keys(getattr(settings, field, None)))

    if api_key in pnp_keys:
        return "PNP"

    return f"unknown:{_hash_key(api_key)}"


def _resolve_client_from_request(request: Request) -> str:
    api_key = request.headers.get("x-api-key")
    if api_key:
        return f"api-key:{_hash_key(api_key)}"

    authorization = request.headers.get("authorization")
    if authorization:
        scheme, _, token = authorization.partition(" ")
        if scheme.lower() == "bearer" and token:
            return f"bearer:{_hash_key(token)}"

    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return f"ip:{_hash_key(forwarded_for.split(',', 1)[0].strip())}"

    host = request.client.host if request.client else "unknown"
    return f"ip:{_hash_key(host)}"


def _rate_limit_for_tenant(tenant: str) -> int:
    if tenant == "admin":
        return ADMIN_RATE_LIMIT_PER_MINUTE
    return DEFAULT_RATE_LIMIT_PER_MINUTE


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path in {"/healthz", "/readyz", "/metrics"}:
            return await call_next(request)

        client = get_cache()

        if client is None:
            global _redis_unavailable_rate_limit_logged
            if not _redis_unavailable_rate_limit_logged:
                logger.warning(
                    "Rate limiting disabled: Redis unavailable. "
                    "Set REDIS_URL and run Redis to enable per-tenant limits (safe to ignore for local dev)."
                )
                _redis_unavailable_rate_limit_logged = True
            return await call_next(request)

        api_key = request.headers.get("x-api-key")
        tenant = _resolve_tenant_from_key(api_key)
        client_subject = _resolve_client_from_request(request)
        limit = _rate_limit_for_tenant(tenant)

        window = int(time.time() // 60)
        key = f"rate-limit:{tenant}:{client_subject}:{window}"

        try:
            count = client.incr(key)
            if count == 1:
                client.expire(key, 70)

            if count > limit:
                return JSONResponse(
                    status_code=429,
                    content={
                        "detail": "Rate limit exceeded",
                        "tenant": tenant,
                        "client": client_subject,
                        "limitPerMinute": limit,
                    },
                    headers={
                        "Retry-After": "60",
                        "X-RateLimit-Limit": str(limit),
                        "X-RateLimit-Remaining": "0",
                    },
                )

            response = await call_next(request)
            response.headers["X-RateLimit-Limit"] = str(limit)
            response.headers["X-RateLimit-Remaining"] = str(max(0, limit - count))
            return response

        except Exception:
            logger.exception("Rate limiting failed open")
            return await call_next(request)
