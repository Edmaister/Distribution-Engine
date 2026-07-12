from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from typing import Any

from fastapi import Header, HTTPException, status

from apps.api.settings import get_settings

TEST_ADMIN_KEYS = "test-admin-key"
TEST_FINANCE_ADMIN_KEYS = "test-finance-admin-key"
TEST_DISTRIBUTION_ADMIN_KEYS = "test-distribution-admin-key"
TEST_SYSTEM_ADMIN_KEYS = "test-system-admin-key"
TEST_FNB_PARTNER_KEYS = "test-partner-key,test-fnb-key"
TEST_PNP_PARTNER_KEYS = "test-pnp-key"
TEST_FNB_PRODUCER_KEYS = {"test-fnb-producer-insureco-key": "INSURECO"}
TEST_FNB_DISTRIBUTOR_KEYS = {
    "test-fnb-distributor-insurance-advocate-key": "DIST-INSURANCE-ADVOCATE"
}
TEST_FNB_CONSUMER_KEYS = "test-fnb-consumer-key"
TEST_KEY_ENVS = {"local", "dev", "test"}


def _configured_keys(value: str | None) -> list[str]:
    if not value:
        return []
    return [key.strip() for key in value.split(",") if key.strip()]


def _is_valid_key(provided: str | None, configured: str | None) -> bool:
    if not isinstance(provided, str) or not provided:
        return False
    return provided in _configured_keys(configured)


def _unauthorized():
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing API key",
    )


def _forbidden(required_role: str):
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=f"API key is not authorised for {required_role}",
    )


def _server_config_error(key_name: str):
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"{key_name} not configured",
    )


def _identity(role: str, tenant_code: str, **claims):
    return {
        "authenticated": True,
        "role": role.upper(),
        "tenant_code": tenant_code,
        "tenant": tenant_code,
        "auth_source": claims.pop("auth_source", "api_key"),
        **claims,
    }


def _claim_names(value: str | None, fallback: str) -> list[str]:
    return _configured_keys(value or fallback)


def _claim_value(payload: dict[str, Any], configured_names: str | None, fallback: str):
    for name in _claim_names(configured_names, fallback):
        value = payload.get(name)
        if value is not None:
            return value
    return None


def _b64url_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode((value + padding).encode("ascii"))


def _decode_hs256_jwt(token: str, secret: str) -> dict[str, Any]:
    try:
        header_part, payload_part, signature_part = token.split(".")
        header = json.loads(_b64url_decode(header_part))
        payload = json.loads(_b64url_decode(payload_part))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid bearer token"
        ) from exc

    if header.get("alg") != "HS256":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unsupported bearer token algorithm",
        )

    signing_input = f"{header_part}.{payload_part}".encode("ascii")
    expected = hmac.new(secret.encode("utf-8"), signing_input, hashlib.sha256).digest()
    try:
        provided = _b64url_decode(signature_part)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid bearer token signature",
        ) from exc

    if not hmac.compare_digest(expected, provided):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid bearer token signature",
        )

    now = int(time.time())
    if payload.get("exp") is not None and int(payload["exp"]) < now:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Bearer token has expired"
        )
    if payload.get("nbf") is not None and int(payload["nbf"]) > now:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Bearer token is not active yet",
        )

    return payload


def _jwt_identity(authorization: str | None):
    if not isinstance(authorization, str) or not authorization:
        return None
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        return None

    settings = get_settings()
    secret = getattr(settings, "auth_jwt_secret", None)
    if not secret:
        return None

    payload = _decode_hs256_jwt(token, secret)
    expected_issuer = getattr(settings, "auth_jwt_issuer", None)
    expected_audience = getattr(settings, "auth_jwt_audience", None)
    if expected_issuer and payload.get("iss") != expected_issuer:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid bearer token issuer",
        )
    if expected_audience:
        audience = payload.get("aud")
        audiences = audience if isinstance(audience, list) else [audience]
        if expected_audience not in audiences:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid bearer token audience",
            )

    role = str(
        _claim_value(
            payload,
            getattr(settings, "auth_jwt_role_claims", None),
            "role,amplifi_role",
        )
        or ""
    ).upper()
    tenant_code = str(
        _claim_value(
            payload,
            getattr(settings, "auth_jwt_tenant_claims", None),
            "tenant_code,tenant",
        )
        or "INTERNAL"
    ).upper()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Bearer token role claim is required",
        )

    return _identity(
        role,
        tenant_code,
        auth_source="jwt",
        subject=_claim_value(
            payload, getattr(settings, "auth_jwt_subject_claims", None), "sub"
        ),
        producer_code=_claim_value(
            payload,
            getattr(settings, "auth_jwt_producer_claims", None),
            "producer_code",
        ),
        distributor_code=_claim_value(
            payload,
            getattr(settings, "auth_jwt_distributor_claims", None),
            "distributor_code",
        ),
        client_id=_claim_value(
            payload, getattr(settings, "auth_jwt_client_claims", None), "client_id"
        ),
        account_ref=_claim_value(
            payload, getattr(settings, "auth_jwt_account_claims", None), "account_ref"
        ),
        external_tenant_ref=_claim_value(
            payload,
            getattr(settings, "auth_jwt_external_tenant_claims", None),
            "external_tenant_ref",
        ),
        scopes=_claim_value(
            payload, getattr(settings, "auth_jwt_scope_claims", None), "scopes,scope"
        ),
    )


def _require_role(identity: dict | None, allowed_roles: set[str]):
    if identity and str(identity.get("role") or "").upper() in allowed_roles:
        return identity
    if identity:
        _forbidden("/".join(sorted(allowed_roles)))
    return None


def _test_keys(settings, keys: str) -> str:
    app_env = str(getattr(settings, "app_env", "") or "").lower()
    return keys if app_env in TEST_KEY_ENVS else ""


def _admin_keys(settings) -> str:
    return ",".join(
        filter(
            None,
            [
                getattr(settings, "admin_api_key", None),
                _test_keys(settings, TEST_ADMIN_KEYS),
            ],
        )
    )


def _finance_admin_keys(settings) -> str:
    return ",".join(
        filter(
            None,
            [
                getattr(settings, "finance_admin_api_key", None),
                _test_keys(settings, TEST_FINANCE_ADMIN_KEYS),
            ],
        )
    )


def _distribution_admin_keys(settings) -> str:
    return ",".join(
        filter(
            None,
            [
                getattr(settings, "distribution_admin_api_key", None),
                _test_keys(settings, TEST_DISTRIBUTION_ADMIN_KEYS),
            ],
        )
    )


def _system_admin_keys(settings) -> str:
    return ",".join(
        filter(
            None,
            [
                getattr(settings, "system_admin_api_key", None),
                _test_keys(settings, TEST_SYSTEM_ADMIN_KEYS),
            ],
        )
    )


def _scoped_admin_key(
    *,
    x_api_key: str | None,
    authorization: str | None,
    scoped_keys: str,
    scoped_role: str,
    config_name: str,
):
    settings = get_settings()
    if identity := _require_role(_jwt_identity(authorization), {"ADMIN", scoped_role}):
        return identity

    platform_keys = _admin_keys(settings)
    all_scoped_keys = {
        "FINANCE_ADMIN": _finance_admin_keys(settings),
        "DISTRIBUTION_ADMIN": _distribution_admin_keys(settings),
        "SYSTEM_ADMIN": _system_admin_keys(settings),
    }

    if not platform_keys and not scoped_keys:
        _server_config_error(config_name)

    if _is_valid_key(x_api_key, platform_keys):
        return _identity("ADMIN", "INTERNAL")

    if _is_valid_key(x_api_key, scoped_keys):
        return _identity(scoped_role, "INTERNAL")

    if any(
        role != scoped_role and _is_valid_key(x_api_key, keys)
        for role, keys in all_scoped_keys.items()
    ):
        _forbidden(scoped_role)

    _unauthorized()


def _fnb_keys(settings) -> str:
    return ",".join(
        filter(
            None,
            [
                getattr(settings, "fnb_partner_api_key", None),
                getattr(settings, "fnb_tenant_user_api_key", None),
                getattr(settings, "fnb_tenant_admin_api_key", None),
                _test_keys(settings, TEST_FNB_PARTNER_KEYS),
            ],
        )
    )


def _pnp_keys(settings) -> str:
    return ",".join(
        filter(
            None,
            [
                getattr(settings, "pnp_partner_api_key", None),
                getattr(settings, "pnp_tenant_user_api_key", None),
                getattr(settings, "pnp_tenant_admin_api_key", None),
                _test_keys(settings, TEST_PNP_PARTNER_KEYS),
            ],
        )
    )


def _configured_role_key_identity(
    *,
    provided: str | None,
    key_value: str | None,
    role: str,
    tenant_code: str,
    claims: dict,
):
    if key_value and provided == key_value:
        return _identity(role, tenant_code, **claims)
    return None


def _test_mapped_key_identity(
    *,
    settings,
    provided: str | None,
    mapping: dict[str, str],
    role: str,
    tenant_code: str,
    claim_name: str,
):
    app_env = str(getattr(settings, "app_env", "") or "").lower()
    if app_env not in TEST_KEY_ENVS or not provided:
        return None
    claim_value = mapping.get(provided)
    if not claim_value:
        return None
    return _identity(role, tenant_code, **{claim_name: claim_value})


def _test_consumer_key_identity(settings, provided: str | None):
    app_env = str(getattr(settings, "app_env", "") or "").lower()
    if app_env in TEST_KEY_ENVS and _is_valid_key(provided, TEST_FNB_CONSUMER_KEYS):
        return _identity("CONSUMER", "FNB")
    return None


def _producer_key_identity(settings, provided: str | None):
    return _configured_role_key_identity(
        provided=provided,
        key_value=getattr(settings, "fnb_producer_api_key", None),
        role="PRODUCER",
        tenant_code="FNB",
        claims={"producer_code": getattr(settings, "fnb_producer_code", None)},
    ) or _test_mapped_key_identity(
        settings=settings,
        provided=provided,
        mapping=TEST_FNB_PRODUCER_KEYS,
        role="PRODUCER",
        tenant_code="FNB",
        claim_name="producer_code",
    )


def _distributor_key_identity(settings, provided: str | None):
    return _configured_role_key_identity(
        provided=provided,
        key_value=getattr(settings, "fnb_distributor_api_key", None),
        role="DISTRIBUTOR",
        tenant_code="FNB",
        claims={"distributor_code": getattr(settings, "fnb_distributor_code", None)},
    ) or _test_mapped_key_identity(
        settings=settings,
        provided=provided,
        mapping=TEST_FNB_DISTRIBUTOR_KEYS,
        role="DISTRIBUTOR",
        tenant_code="FNB",
        claim_name="distributor_code",
    )


def _consumer_key_identity(settings, provided: str | None):
    return _test_consumer_key_identity(
        settings, provided
    ) or _configured_role_key_identity(
        provided=provided,
        key_value=getattr(settings, "fnb_consumer_api_key", None),
        role="CONSUMER",
        tenant_code="FNB",
        claims={},
    )


def _scoped_admin_identity(settings, provided: str | None):
    scoped_admin_keys = [
        ("FINANCE_ADMIN", _finance_admin_keys(settings)),
        ("DISTRIBUTION_ADMIN", _distribution_admin_keys(settings)),
        ("SYSTEM_ADMIN", _system_admin_keys(settings)),
    ]

    for role, keys in scoped_admin_keys:
        if _is_valid_key(provided, keys):
            return _identity(role, "INTERNAL")

    return None


def require_admin_key(
    x_api_key: str | None = Header(default=None),
    authorization: str | None = Header(default=None),
):
    settings = get_settings()
    if identity := _require_role(_jwt_identity(authorization), {"ADMIN"}):
        return identity

    if not _admin_keys(settings):
        _server_config_error("ADMIN_API_KEY")

    if not _is_valid_key(x_api_key, _admin_keys(settings)):
        _unauthorized()

    return _identity("ADMIN", "INTERNAL")


def require_finance_admin_key(
    x_api_key: str | None = Header(default=None),
    authorization: str | None = Header(default=None),
):
    settings = get_settings()
    return _scoped_admin_key(
        x_api_key=x_api_key,
        authorization=authorization,
        scoped_keys=_finance_admin_keys(settings),
        scoped_role="FINANCE_ADMIN",
        config_name="FINANCE_ADMIN_API_KEY",
    )


def require_distribution_admin_key(
    x_api_key: str | None = Header(default=None),
    authorization: str | None = Header(default=None),
):
    settings = get_settings()
    return _scoped_admin_key(
        x_api_key=x_api_key,
        authorization=authorization,
        scoped_keys=_distribution_admin_keys(settings),
        scoped_role="DISTRIBUTION_ADMIN",
        config_name="DISTRIBUTION_ADMIN_API_KEY",
    )


def require_system_admin_key(
    x_api_key: str | None = Header(default=None),
    authorization: str | None = Header(default=None),
):
    settings = get_settings()
    return _scoped_admin_key(
        x_api_key=x_api_key,
        authorization=authorization,
        scoped_keys=_system_admin_keys(settings),
        scoped_role="SYSTEM_ADMIN",
        config_name="SYSTEM_ADMIN_API_KEY",
    )


def require_partner_key(
    x_api_key: str | None = Header(default=None),
    authorization: str | None = Header(default=None),
):
    settings = get_settings()
    if identity := _require_role(_jwt_identity(authorization), {"ADMIN", "PARTNER"}):
        return identity

    if _is_valid_key(x_api_key, _fnb_keys(settings)):
        return _identity("PARTNER", "FNB")

    if _is_valid_key(x_api_key, _pnp_keys(settings)):
        return _identity("PARTNER", "PNP")

    _unauthorized()


def require_admin_or_partner_key(
    x_api_key: str | None = Header(default=None),
    authorization: str | None = Header(default=None),
):
    settings = get_settings()
    if identity := _require_role(_jwt_identity(authorization), {"ADMIN", "PARTNER"}):
        return identity

    if _is_valid_key(x_api_key, _admin_keys(settings)):
        return _identity("ADMIN", "INTERNAL")

    if _is_valid_key(x_api_key, _fnb_keys(settings)):
        return _identity("PARTNER", "FNB")

    if _is_valid_key(x_api_key, _pnp_keys(settings)):
        return _identity("PARTNER", "PNP")

    _unauthorized()


def require_any_key(
    x_api_key: str | None = Header(default=None),
    authorization: str | None = Header(default=None),
):
    settings = get_settings()
    if identity := _jwt_identity(authorization):
        return identity

    if _is_valid_key(x_api_key, _admin_keys(settings)):
        return _identity("ADMIN", "INTERNAL")

    if _is_valid_key(x_api_key, _fnb_keys(settings)):
        return _identity("PARTNER", "FNB")

    if _is_valid_key(x_api_key, _pnp_keys(settings)):
        return _identity("PARTNER", "PNP")

    _unauthorized()


async def require_partner_identity(
    authorization: str | None = Header(default=None),
    x_api_key: str | None = Header(default=None),
):
    if isinstance(authorization, str) and authorization:
        if identity := _require_role(
            _jwt_identity(authorization), {"ADMIN", "PARTNER"}
        ):
            return identity

        from services import partner_seam_service

        return await partner_seam_service.authenticate_partner_access_token(
            authorization
        )

    return require_partner_key(x_api_key=x_api_key, authorization=None)


def require_session_key(
    x_api_key: str | None = Header(default=None),
    authorization: str | None = Header(default=None),
):
    settings = get_settings()
    if identity := _jwt_identity(authorization):
        return identity

    if _is_valid_key(x_api_key, _admin_keys(settings)):
        return _identity("ADMIN", "INTERNAL")

    if scoped_admin_identity := _scoped_admin_identity(settings, x_api_key):
        return scoped_admin_identity

    if producer_identity := _producer_key_identity(settings, x_api_key):
        return producer_identity

    if distributor_identity := _distributor_key_identity(settings, x_api_key):
        return distributor_identity

    if consumer_identity := _consumer_key_identity(settings, x_api_key):
        return consumer_identity

    if _is_valid_key(x_api_key, _fnb_keys(settings)):
        return _identity("PARTNER", "FNB")

    if _is_valid_key(x_api_key, _pnp_keys(settings)):
        return _identity("PARTNER", "PNP")

    _unauthorized()


def require_admin_partner_or_producer_key(
    x_api_key: str | None = Header(default=None),
    authorization: str | None = Header(default=None),
):
    settings = get_settings()
    if identity := _require_role(
        _jwt_identity(authorization), {"ADMIN", "PARTNER", "PRODUCER"}
    ):
        return identity

    if _is_valid_key(x_api_key, _admin_keys(settings)):
        return _identity("ADMIN", "INTERNAL")

    if producer_identity := _producer_key_identity(settings, x_api_key):
        return producer_identity

    if _is_valid_key(x_api_key, _fnb_keys(settings)):
        return _identity("PARTNER", "FNB")

    if _is_valid_key(x_api_key, _pnp_keys(settings)):
        return _identity("PARTNER", "PNP")

    _unauthorized()


def require_admin_partner_or_distributor_key(
    x_api_key: str | None = Header(default=None),
    authorization: str | None = Header(default=None),
):
    settings = get_settings()
    if identity := _require_role(
        _jwt_identity(authorization), {"ADMIN", "PARTNER", "DISTRIBUTOR"}
    ):
        return identity

    if _is_valid_key(x_api_key, _admin_keys(settings)):
        return _identity("ADMIN", "INTERNAL")

    if distributor_identity := _distributor_key_identity(settings, x_api_key):
        return distributor_identity

    if _is_valid_key(x_api_key, _fnb_keys(settings)):
        return _identity("PARTNER", "FNB")

    if _is_valid_key(x_api_key, _pnp_keys(settings)):
        return _identity("PARTNER", "PNP")

    _unauthorized()


def require_admin_partner_or_consumer_key(
    x_api_key: str | None = Header(default=None),
    authorization: str | None = Header(default=None),
):
    settings = get_settings()
    if identity := _require_role(
        _jwt_identity(authorization), {"ADMIN", "PARTNER", "CONSUMER"}
    ):
        return identity

    if _is_valid_key(x_api_key, _admin_keys(settings)):
        return _identity("ADMIN", "INTERNAL")

    if consumer_identity := _consumer_key_identity(settings, x_api_key):
        return consumer_identity

    if _is_valid_key(x_api_key, _fnb_keys(settings)):
        return _identity("PARTNER", "FNB")

    if _is_valid_key(x_api_key, _pnp_keys(settings)):
        return _identity("PARTNER", "PNP")

    _unauthorized()
