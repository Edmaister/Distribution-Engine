from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Any


STATUS_NEW_REQUEST = "NEW_REQUEST"
STATUS_REPLAY_SAME_PAYLOAD = "REPLAY_SAME_PAYLOAD"
STATUS_CONFLICT_DIFFERENT_PAYLOAD = "CONFLICT_DIFFERENT_PAYLOAD"
STATUS_INVALID_IDEMPOTENCY_KEY = "INVALID_IDEMPOTENCY_KEY"

REASON_MISSING_IDEMPOTENCY_KEY = "MISSING_IDEMPOTENCY_KEY"
REASON_MISSING_SCOPE = "MISSING_SCOPE"
REASON_UNSUPPORTED_OPERATION = "UNSUPPORTED_OPERATION"

SUPPORTED_DRAFT_OPERATIONS = frozenset(
    {
        "ONBOARDING_DRAFT_CREATE",
        "ONBOARDING_DRAFT_UPDATE",
        "ONBOARDING_DRAFT_VALIDATE",
        "ONBOARDING_DRAFT_SUBMIT_FOR_REVIEW",
        "ONBOARDING_DRAFT_DISCARD",
    }
)


@dataclass(frozen=True)
class DraftIdempotencyDecision:
    status: str
    idempotency_key_hash: str | None = None
    scope_hash: str | None = None
    request_hash: str | None = None
    actor_ref: str | None = None
    external_tenant_ref: str | None = None
    operation_type: str | None = None
    draft_ref: str | None = None
    existing_result_status: str | None = None
    existing_response_hash: str | None = None
    reason: str | None = None

    @property
    def is_new_request(self) -> bool:
        return self.status == STATUS_NEW_REQUEST

    @property
    def is_replay(self) -> bool:
        return self.status == STATUS_REPLAY_SAME_PAYLOAD

    @property
    def is_conflict(self) -> bool:
        return self.status == STATUS_CONFLICT_DIFFERENT_PAYLOAD

    @property
    def is_valid(self) -> bool:
        return self.status != STATUS_INVALID_IDEMPOTENCY_KEY

    def repository_fields(self) -> dict[str, str | None]:
        if not self.is_valid:
            return {}
        return {
            "idempotency_key_hash": self.idempotency_key_hash,
            "scope_hash": self.scope_hash,
            "actor_ref": self.actor_ref,
            "external_tenant_ref": self.external_tenant_ref,
            "operation_type": self.operation_type,
            "request_hash": self.request_hash,
            "draft_ref": self.draft_ref,
        }


def sha256_hex(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def hash_idempotency_key(idempotency_key: str) -> str:
    return sha256_hex(_required_text(idempotency_key))


def hash_payload(payload: Mapping[str, Any] | None) -> str:
    return sha256_hex(canonical_payload(payload))


def build_scope_hash(
    *,
    actor_ref: str,
    external_tenant_ref: str,
    operation_type: str,
    draft_ref: str | None = None,
) -> str:
    scope = {
        "actor_ref": _required_text(actor_ref),
        "external_tenant_ref": _required_text(external_tenant_ref),
        "operation_type": _normalise_operation(operation_type),
        "draft_ref": _optional_text(draft_ref),
    }
    return sha256_hex(canonical_payload(scope))


def canonical_payload(payload: Mapping[str, Any] | None) -> str:
    normalised = _normalise_json_value(dict(payload or {}))
    return json.dumps(normalised, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def evaluate_draft_idempotency(
    *,
    idempotency_key: str | None,
    actor_ref: str | None,
    external_tenant_ref: str | None,
    operation_type: str | None,
    request_payload: Mapping[str, Any] | None,
    existing_reference: Mapping[str, Any] | None = None,
    draft_ref: str | None = None,
) -> DraftIdempotencyDecision:
    idempotency_key_text = _optional_text(idempotency_key)
    if not idempotency_key_text:
        return DraftIdempotencyDecision(
            status=STATUS_INVALID_IDEMPOTENCY_KEY,
            reason=REASON_MISSING_IDEMPOTENCY_KEY,
        )

    actor = _optional_text(actor_ref)
    external_ref = _optional_text(external_tenant_ref)
    operation = _normalise_operation(operation_type)
    if not actor or not external_ref or not operation:
        return DraftIdempotencyDecision(
            status=STATUS_INVALID_IDEMPOTENCY_KEY,
            reason=REASON_MISSING_SCOPE,
        )

    if operation not in SUPPORTED_DRAFT_OPERATIONS:
        return DraftIdempotencyDecision(
            status=STATUS_INVALID_IDEMPOTENCY_KEY,
            reason=REASON_UNSUPPORTED_OPERATION,
        )

    key_hash = hash_idempotency_key(idempotency_key_text)
    scope_hash = build_scope_hash(
        actor_ref=actor,
        external_tenant_ref=external_ref,
        operation_type=operation,
        draft_ref=draft_ref,
    )
    request_hash = hash_payload(request_payload)
    draft_ref_text = _optional_text(draft_ref)

    if not existing_reference:
        return DraftIdempotencyDecision(
            status=STATUS_NEW_REQUEST,
            idempotency_key_hash=key_hash,
            scope_hash=scope_hash,
            actor_ref=actor,
            external_tenant_ref=external_ref,
            operation_type=operation,
            request_hash=request_hash,
            draft_ref=draft_ref_text,
        )

    if (
        _optional_text(existing_reference.get("idempotency_key_hash")) != key_hash
        or _optional_text(existing_reference.get("scope_hash")) != scope_hash
    ):
        return DraftIdempotencyDecision(
            status=STATUS_NEW_REQUEST,
            idempotency_key_hash=key_hash,
            scope_hash=scope_hash,
            actor_ref=actor,
            external_tenant_ref=external_ref,
            operation_type=operation,
            request_hash=request_hash,
            draft_ref=draft_ref_text,
        )

    if _optional_text(existing_reference.get("request_hash")) == request_hash:
        return DraftIdempotencyDecision(
            status=STATUS_REPLAY_SAME_PAYLOAD,
            idempotency_key_hash=key_hash,
            scope_hash=scope_hash,
            actor_ref=actor,
            external_tenant_ref=external_ref,
            operation_type=operation,
            request_hash=request_hash,
            draft_ref=draft_ref_text,
            existing_result_status=_optional_text(existing_reference.get("result_status")),
            existing_response_hash=_optional_text(existing_reference.get("response_hash")),
        )

    return DraftIdempotencyDecision(
        status=STATUS_CONFLICT_DIFFERENT_PAYLOAD,
        idempotency_key_hash=key_hash,
        scope_hash=scope_hash,
        actor_ref=actor,
        external_tenant_ref=external_ref,
        operation_type=operation,
        request_hash=request_hash,
        draft_ref=draft_ref_text,
        existing_result_status=_optional_text(existing_reference.get("result_status")),
    )


def _normalise_json_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {
            str(key): _normalise_json_value(item)
            for key, item in sorted(value.items(), key=lambda item: str(item[0]))
        }
    if isinstance(value, Sequence) and not isinstance(value, str | bytes | bytearray):
        return [_normalise_json_value(item) for item in value]
    if isinstance(value, datetime | date):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    return value


def _normalise_operation(value: str | None) -> str:
    return _optional_text(value).upper().replace("-", "_")


def _optional_text(value: Any) -> str:
    return str(value or "").strip()


def _required_text(value: Any) -> str:
    text = _optional_text(value)
    if not text:
        raise ValueError("Expected a non-empty value")
    return text
