from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import datetime
import json
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException

from services import partner_seam_service as service


class FakeConnection:
    def __init__(self):
        self.executed = []
        self.client_secret = "secret"

    async def fetchrow(self, query, *args):
        if "FROM partner_clients" in query and "WHERE client_id" in query:
            return {
                "client_id": args[0],
                "tenant_code": "FNB",
                "client_secret_hash": service._hash_secret(self.client_secret),
                "scopes": ["events:write", "referrals:read"],
                "status": "ACTIVE",
            }
        if "FROM partner_access_tokens" in query:
            return {
                "client_id": "client-1",
                "tenant_code": "FNB",
                "scopes": ["events:write"],
                "status": "ACTIVE",
            }
        return None

    async def fetch(self, query, *args):
        return []

    async def execute(self, query, *args):
        self.executed.append((query, args))


class FakePartnerClientCreateConnection:
    def __init__(self):
        self.args = None

    async def fetchrow(self, query, *args):
        self.args = args
        return {
            "client_id": args[0],
            "tenant_code": args[1],
            "client_name": args[2],
            "client_secret_hash": args[3],
            "scopes": args[4],
            "metadata": {},
            "status": "ACTIVE",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }


class FakeWebhookCreateConnection:
    async def fetchrow(self, query, *args):
        if "SELECT client_id, tenant_code, status" in query:
            return {
                "client_id": args[0],
                "tenant_code": "FNB",
                "status": "ACTIVE",
            }
        return {
            "webhook_id": uuid4(),
            "client_id": args[0],
            "tenant_code": args[1],
            "event_type": args[2],
            "target_url": args[3],
            "signing_secret_value": args[4],
            "signing_secret_hash": args[5],
            "metadata": {},
            "status": "ACTIVE",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }


class FakeWebhookRotateConnection:
    def __init__(self, *, found=True):
        self.found = found
        self.args = None

    async def fetchrow(self, query, *args):
        self.args = args
        if not self.found:
            return None
        return {
            "webhook_id": args[2],
            "client_id": args[3],
            "tenant_code": args[4],
            "event_type": "OUTCOME_COMPLETED",
            "target_url": "https://partner.example/webhooks",
            "signing_secret_value": args[0],
            "signing_secret_hash": args[1],
            "metadata": {},
            "status": "ACTIVE",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }


class FakeLegacyWebhookSecretRotateConnection:
    def __init__(self, *, legacy_count=2):
        self.legacy_count = legacy_count
        self.fetch_args = None
        self.update_args = []
        self.webhook_ids = [uuid4() for _ in range(max(legacy_count, 0))]

    async def fetch(self, query, *args):
        self.fetch_args = args
        assert "signing_secret_value NOT LIKE" in query
        assert "status = 'ACTIVE'" in query
        return [
            {
                "webhook_id": webhook_id,
                "client_id": "client-1",
                "tenant_code": "FNB",
                "event_type": "OUTCOME_COMPLETED",
                "target_url": "https://partner.example/webhooks",
                "status": "ACTIVE",
            }
            for webhook_id in self.webhook_ids
        ]

    async def fetchrow(self, query, *args):
        self.update_args.append(args)
        assert "UPDATE partner_webhook_subscriptions" in query
        return {
            "webhook_id": args[2],
            "client_id": args[4],
            "tenant_code": args[3],
            "event_type": "OUTCOME_COMPLETED",
            "target_url": "https://partner.example/webhooks",
            "signing_secret_value": args[0],
            "signing_secret_hash": args[1],
            "metadata": {},
            "status": "ACTIVE",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }


class FakeWebhookExceptionConnection:
    async def fetch(self, query, *args):
        assert args == ("FNB", "client-1", 25)
        assert "delivery_status IN ('FAILED', 'CANCELLED')" in query
        return [
            {
                "delivery_id": uuid4(),
                "webhook_id": uuid4(),
                "client_id": "client-1",
                "tenant_code": "FNB",
                "event_type": "OUTCOME_COMPLETED",
                "payload": {"referralTrackId": "ref-1"},
                "delivery_status": "FAILED",
                "attempt_count": 3,
                "last_error": "HTTP 500: failed",
                "next_attempt_at": None,
                "delivered_at": None,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            }
        ]


class FakeWebhookAlertConnection:
    async def fetch(self, query, *args):
        assert args == ("FNB", "client-1", 25)
        assert "delivery_status IN ('FAILED', 'CANCELLED')" in query
        assert "GROUP BY delivery.tenant_code" in query
        return [
            {
                "tenant_code": "FNB",
                "client_id": "client-1",
                "webhook_id": uuid4(),
                "event_type": "OUTCOME_COMPLETED",
                "target_url": "https://partner.example/webhooks",
                "failed_count": 5,
                "max_attempt_count": 3,
                "last_failed_at": datetime.utcnow(),
                "failure_reasons": "HTTP 500: failed",
                "last_notified_at": datetime.utcnow(),
                "notification_count": 1,
                "last_notification_status": "SENT",
            },
            {
                "tenant_code": "FNB",
                "client_id": "client-1",
                "webhook_id": uuid4(),
                "event_type": "CUSTOMER_ACTIVATED",
                "target_url": "https://partner.example/activations",
                "failed_count": 2,
                "max_attempt_count": 1,
                "last_failed_at": datetime.utcnow(),
                "failure_reasons": "HTTP 429: throttled",
                "last_notified_at": None,
                "notification_count": 0,
                "last_notification_status": None,
            },
        ]


class FakeWebhookAlertNotifyConnection(FakeWebhookAlertConnection):
    def __init__(self):
        self.insert_args = []

    async def fetchrow(self, query, *args):
        self.insert_args.append(args)
        assert "INSERT INTO partner_webhook_alert_notifications" in query
        return {
            "notification_id": uuid4(),
            "tenant_code": args[0],
            "client_id": args[1],
            "webhook_id": args[2],
            "event_type": args[3],
            "severity": args[4],
            "channel": args[5],
            "notification_status": args[6],
            "subject": args[7],
            "message": args[8],
            "metadata": json.loads(args[9]),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }


class FakeWebhookSecretReadinessConnection:
    def __init__(self, *, legacy_count=1):
        self.args = None
        self.legacy_count = legacy_count

    async def fetchrow(self, query, *args):
        self.args = args
        assert "signing_secret_value LIKE" in query
        return {
            "total_subscriptions": 3,
            "protected_subscriptions": 3 - self.legacy_count,
            "legacy_plaintext_subscriptions": self.legacy_count,
        }


class FakeWebhookRetryConnection:
    def __init__(self, *, found=True):
        self.found = found
        self.args = None

    async def fetchrow(self, query, *args):
        self.args = args
        assert "delivery_status IN ('FAILED', 'CANCELLED')" in query
        if not self.found:
            return None
        return {
            "delivery_id": args[0],
            "webhook_id": uuid4(),
            "client_id": args[2] if len(args) > 2 else "client-1",
            "tenant_code": args[1] if len(args) > 1 else "FNB",
            "event_type": "OUTCOME_COMPLETED",
            "payload": {"referralTrackId": "ref-1"},
            "delivery_status": "PENDING",
            "attempt_count": 3,
            "last_error": None,
            "next_attempt_at": datetime.utcnow(),
            "delivered_at": None,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }


class FakeWebhookSummaryConnection:
    async def fetch(self, query, *args):
        assert args == (24, "FNB")
        return [
            {"delivery_status": "SENT", "count": 3},
            {"delivery_status": "PENDING", "count": 2},
            {"delivery_status": "FAILED", "count": 1},
        ]


class FakeIntegrationConnection:
    async def fetchrow(self, query, *args):
        if "FROM partner_webhook_subscriptions" in query:
            return {
                "total_subscriptions": 1,
                "protected_subscriptions": 1,
                "legacy_plaintext_subscriptions": 0,
            }
        return None

    async def fetch(self, query, *args):
        if "FROM partner_clients" in query:
            return [
                {
                    "client_id": "client-1",
                    "tenant_code": "FNB",
                    "client_name": "Partner Client",
                    "scopes": ["events:write"],
                    "status": "ACTIVE",
                    "metadata": {},
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                }
            ]
        if "FROM partner_webhook_subscriptions" in query:
            return [
                {
                    "webhook_id": uuid4(),
                    "client_id": "client-1",
                    "tenant_code": "FNB",
                    "event_type": "OUTCOME_COMPLETED",
                    "target_url": "https://partner.example/webhooks",
                    "status": "ACTIVE",
                    "metadata": {},
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                }
            ]
        if (
            "FROM partner_webhook_deliveries" in query
            and "GROUP BY delivery_status" in query
        ):
            return [{"delivery_status": "SENT", "count": 4}]
        if "FROM partner_webhook_deliveries" in query:
            return [
                {
                    "delivery_id": uuid4(),
                    "webhook_id": uuid4(),
                    "client_id": "client-1",
                    "tenant_code": "FNB",
                    "event_type": "OUTCOME_COMPLETED",
                    "payload": {"ok": True},
                    "delivery_status": "SENT",
                    "attempt_count": 1,
                    "last_error": None,
                    "next_attempt_at": None,
                    "delivered_at": datetime.utcnow(),
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                }
            ]
        return []


class FakeWebhookConnection:
    def __init__(self, *, status_code=200, attempt_count=0):
        self.delivery_id = uuid4()
        self.webhook_id = uuid4()
        self.status_code = status_code
        self.attempt_count = attempt_count
        self.update_args = None

    async def fetch(self, query, *args):
        return [
            {
                "delivery_id": self.delivery_id,
                "webhook_id": self.webhook_id,
                "client_id": "client-1",
                "tenant_code": "FNB",
                "event_type": "OUTCOME_COMPLETED",
                "payload": {"referralTrackId": "ref-1"},
                "attempt_count": self.attempt_count,
                "target_url": "https://partner.example/webhooks",
                "signing_secret_value": "signing-secret",
            }
        ]

    async def fetchrow(self, query, *args):
        self.update_args = args
        return {
            "delivery_id": self.delivery_id,
            "webhook_id": self.webhook_id,
            "client_id": "client-1",
            "tenant_code": "FNB",
            "event_type": "OUTCOME_COMPLETED",
            "payload": {"referralTrackId": "ref-1"},
            "delivery_status": args[0],
            "attempt_count": args[1],
            "last_error": args[2],
            "next_attempt_at": None,
            "delivered_at": None,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }


class FakeResponse:
    def __init__(self, status_code, text=""):
        self.status_code = status_code
        self.text = text


@asynccontextmanager
async def fake_db_connection(conn):
    yield conn


def test_normalize_scopes_sorts_and_deduplicates():
    assert service._normalize_scopes("events:write referrals:read events:write") == [
        "events:write",
        "referrals:read",
    ]


def test_webhook_signature_is_hmac_sha256_hex():
    signature = service._webhook_signature(
        signing_secret="secret",
        timestamp=123,
        body='{"ok":true}',
    )

    assert len(signature) == 64
    assert signature == service._webhook_signature(
        signing_secret="secret",
        timestamp=123,
        body='{"ok":true}',
    )


def test_protect_secret_round_trip_hides_plaintext():
    protected = service._protect_secret("signing-secret")

    assert protected.startswith(service.PROTECTED_SECRET_PREFIX)
    assert "signing-secret" not in protected
    assert service._unprotect_secret(protected) == "signing-secret"


def test_protect_secret_supports_managed_provider_prefix(monkeypatch):
    monkeypatch.setattr(
        service,
        "get_settings",
        lambda: SimpleNamespace(
            app_env="prod",
            partner_webhook_secret_provider="MANAGED_KMS",
            partner_webhook_kms_key_id="kms-key-1",
            partner_webhook_kms_backend="LOCAL_ENVELOPE",
            partner_webhook_secret_key=None,
        ),
    )

    protected = service._protect_secret("signing-secret")

    assert protected.startswith(service.MANAGED_SECRET_PREFIX)
    assert "signing-secret" not in protected
    assert service._unprotect_secret(protected) == "signing-secret"


def test_protect_secret_supports_aws_kms_backend(monkeypatch):
    class FakeKmsClient:
        def encrypt(self, *, KeyId, Plaintext):
            assert KeyId == "kms-key-1"
            return {"CiphertextBlob": b"kms:" + Plaintext[::-1]}

        def decrypt(self, *, CiphertextBlob):
            assert CiphertextBlob.startswith(b"kms:")
            return {"Plaintext": CiphertextBlob[4:][::-1]}

    monkeypatch.setattr(
        service,
        "get_settings",
        lambda: SimpleNamespace(
            app_env="prod",
            aws_region="af-south-1",
            partner_webhook_secret_provider="MANAGED_KMS",
            partner_webhook_kms_key_id="kms-key-1",
            partner_webhook_kms_backend="AWS_KMS",
            partner_webhook_secret_key=None,
        ),
    )
    monkeypatch.setattr(service, "_aws_kms_client", lambda: FakeKmsClient())

    protected = service._protect_secret("signing-secret")

    assert protected.startswith(service.MANAGED_SECRET_PREFIX)
    assert "signing-secret" not in protected
    assert service._unprotect_secret(protected) == "signing-secret"


def test_secret_provider_status_requires_physical_kms_backend_in_prod(monkeypatch):
    monkeypatch.setattr(
        service,
        "get_settings",
        lambda: SimpleNamespace(
            app_env="prod",
            partner_webhook_secret_provider="MANAGED_KMS",
            partner_webhook_kms_key_id="kms-key-1",
            partner_webhook_kms_backend="LOCAL_ENVELOPE",
            partner_webhook_secret_key=None,
        ),
    )

    status = service._secret_provider_status()

    assert status["config_status"] == "ATTENTION"
    assert status["kms_backend"] == "LOCAL_ENVELOPE"


def test_unprotect_secret_supports_legacy_plaintext():
    assert service._unprotect_secret("legacy-secret") == "legacy-secret"


@pytest.mark.asyncio
async def test_issue_client_credentials_token_stores_hashed_token(monkeypatch):
    conn = FakeConnection()
    monkeypatch.setattr(service, "db_connection", lambda: fake_db_connection(conn))

    token = await service.issue_client_credentials_token(
        client_id="client-1",
        client_secret="secret",
        scope="events:write",
        ttl_seconds=120,
    )

    assert token["token_type"] == "Bearer"
    assert token["expires_in"] == 120
    assert token["scope"] == "events:write"
    assert len(conn.executed) == 1
    executed_args = conn.executed[0][1]
    assert executed_args[0] != token["access_token"]
    assert isinstance(executed_args[4], datetime)


@pytest.mark.asyncio
async def test_issue_client_credentials_token_rejects_unallowed_scope(monkeypatch):
    conn = FakeConnection()
    monkeypatch.setattr(service, "db_connection", lambda: fake_db_connection(conn))

    with pytest.raises(HTTPException) as exc:
        await service.issue_client_credentials_token(
            client_id="client-1",
            client_secret="secret",
            scope="settlements:write",
        )

    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_authenticate_partner_access_token_returns_identity(monkeypatch):
    conn = FakeConnection()
    monkeypatch.setattr(service, "db_connection", lambda: fake_db_connection(conn))

    identity = await service.authenticate_partner_access_token("Bearer token")

    assert identity == {
        "authenticated": True,
        "role": "PARTNER",
        "tenant_code": "FNB",
        "tenant": "FNB",
        "client_id": "client-1",
        "scopes": ["events:write"],
    }


@pytest.mark.asyncio
async def test_authenticate_partner_access_token_rejects_missing_bearer():
    with pytest.raises(HTTPException) as exc:
        await service.authenticate_partner_access_token(None)

    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_create_partner_client_for_identity_uses_tenant_scope(monkeypatch):
    conn = FakePartnerClientCreateConnection()
    monkeypatch.setattr(service, "db_connection", lambda: fake_db_connection(conn))

    client = await service.create_partner_client_for_identity(
        identity={"role": "PARTNER", "tenant_code": "FNB"},
        client_name="Claims Integration",
        scopes=["events:write"],
    )

    assert client["tenant_code"] == "FNB"
    assert client["client_name"] == "Claims Integration"
    assert client["client_secret"]
    assert conn.args[1] == "FNB"
    assert conn.args[4] == ["events:write"]


@pytest.mark.asyncio
async def test_create_partner_client_for_identity_rejects_client_scoped_bearer():
    with pytest.raises(HTTPException) as exc:
        await service.create_partner_client_for_identity(
            identity={"role": "PARTNER", "tenant_code": "FNB", "client_id": "client-1"},
            client_name="Sibling Client",
            scopes=["events:write"],
        )

    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_create_webhook_subscription_stores_protected_secret(monkeypatch):
    conn = FakeWebhookCreateConnection()
    monkeypatch.setattr(service, "db_connection", lambda: fake_db_connection(conn))

    webhook = await service.create_webhook_subscription(
        client_id="client-1",
        event_type="OUTCOME_COMPLETED",
        target_url="https://partner.example/webhooks",
    )

    assert webhook["signing_secret"]
    assert "signing_secret_value" not in webhook
    assert "signing_secret_hash" not in webhook


@pytest.mark.asyncio
async def test_create_partner_webhook_subscription_requires_client_scope():
    with pytest.raises(HTTPException) as exc:
        await service.create_partner_webhook_subscription(
            identity={"role": "PARTNER", "tenant_code": "FNB"},
            event_type="OUTCOME_COMPLETED",
            target_url="https://partner.example/webhooks",
        )

    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_create_partner_webhook_subscription_uses_partner_client(monkeypatch):
    conn = FakeWebhookCreateConnection()
    monkeypatch.setattr(service, "db_connection", lambda: fake_db_connection(conn))

    webhook = await service.create_partner_webhook_subscription(
        identity={
            "role": "PARTNER",
            "tenant_code": "FNB",
            "client_id": "client-1",
        },
        event_type="OUTCOME_COMPLETED",
        target_url="https://partner.example/webhooks",
    )

    assert webhook["client_id"] == "client-1"
    assert webhook["tenant_code"] == "FNB"
    assert webhook["signing_secret"]


@pytest.mark.asyncio
async def test_rotate_partner_webhook_secret_is_client_scoped(monkeypatch):
    conn = FakeWebhookRotateConnection()
    monkeypatch.setattr(service, "db_connection", lambda: fake_db_connection(conn))

    webhook_id = str(uuid4())
    webhook = await service.rotate_partner_webhook_signing_secret(
        identity={
            "role": "PARTNER",
            "tenant_code": "FNB",
            "client_id": "client-1",
        },
        webhook_id=webhook_id,
    )

    assert webhook["webhook_id"] == webhook_id
    assert webhook["client_id"] == "client-1"
    assert webhook["tenant_code"] == "FNB"
    assert webhook["signing_secret"]
    assert conn.args[2:] == (webhook_id, "client-1", "FNB")
    assert service._unprotect_secret(conn.args[0]) == webhook["signing_secret"]


@pytest.mark.asyncio
async def test_rotate_partner_webhook_secret_rejects_unknown_webhook(monkeypatch):
    conn = FakeWebhookRotateConnection(found=False)
    monkeypatch.setattr(service, "db_connection", lambda: fake_db_connection(conn))

    with pytest.raises(HTTPException) as exc:
        await service.rotate_partner_webhook_signing_secret(
            identity={
                "role": "PARTNER",
                "tenant_code": "FNB",
                "client_id": "client-1",
            },
            webhook_id=str(uuid4()),
        )

    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_rotate_partner_legacy_webhook_secrets_is_client_scoped(monkeypatch):
    conn = FakeLegacyWebhookSecretRotateConnection(legacy_count=2)
    monkeypatch.setattr(service, "db_connection", lambda: fake_db_connection(conn))

    rotation = await service.rotate_partner_legacy_webhook_secrets(
        identity={
            "role": "PARTNER",
            "tenant_code": "FNB",
            "client_id": "client-1",
        },
        limit=25,
    )

    assert rotation["status"] == "rotated"
    assert rotation["tenant_code"] == "FNB"
    assert rotation["client_id"] == "client-1"
    assert rotation["rotated_count"] == 2
    assert len(rotation["items"]) == 2
    assert rotation["items"][0]["signing_secret"]
    assert "signing_secret_value" not in rotation["items"][0]
    assert conn.fetch_args == (
        "FNB",
        "client-1",
        f"{service.PROTECTED_SECRET_PREFIX}%",
        f"{service.MANAGED_SECRET_PREFIX}%",
        25,
    )
    assert len(conn.update_args) == 2
    assert (
        service._unprotect_secret(conn.update_args[0][0])
        == rotation["items"][0]["signing_secret"]
    )


@pytest.mark.asyncio
async def test_rotate_partner_legacy_webhook_secrets_returns_noop_when_clean(
    monkeypatch,
):
    conn = FakeLegacyWebhookSecretRotateConnection(legacy_count=0)
    monkeypatch.setattr(service, "db_connection", lambda: fake_db_connection(conn))

    rotation = await service.rotate_partner_legacy_webhook_secrets(
        identity={
            "role": "PARTNER",
            "tenant_code": "FNB",
            "client_id": "client-1",
        },
        limit=25,
    )

    assert rotation["status"] == "noop"
    assert rotation["rotated_count"] == 0
    assert rotation["items"] == []
    assert conn.update_args == []


@pytest.mark.asyncio
async def test_list_partner_webhook_exceptions_is_client_scoped(monkeypatch):
    conn = FakeWebhookExceptionConnection()
    monkeypatch.setattr(service, "db_connection", lambda: fake_db_connection(conn))

    rows = await service.list_partner_webhook_exceptions(
        identity={
            "role": "PARTNER",
            "tenant_code": "FNB",
            "client_id": "client-1",
        },
        limit=25,
    )

    assert len(rows) == 1
    assert rows[0]["client_id"] == "client-1"
    assert rows[0]["delivery_status"] == "FAILED"


@pytest.mark.asyncio
async def test_export_partner_webhook_dead_letters_returns_csv(monkeypatch):
    conn = FakeWebhookExceptionConnection()
    monkeypatch.setattr(service, "db_connection", lambda: fake_db_connection(conn))

    export = await service.export_partner_webhook_dead_letters(
        identity={
            "role": "PARTNER",
            "tenant_code": "FNB",
            "client_id": "client-1",
        },
        limit=25,
    )

    assert export["content_type"] == "text/csv"
    assert export["count"] == 1
    assert export["filename"].startswith("partner-webhook-dead-letters-fnb-client-1-")
    assert "delivery_id,webhook_id,client_id" in export["csv"]
    assert "FAILED" in export["csv"]
    assert "signing_secret" not in export["csv"]


@pytest.mark.asyncio
async def test_get_partner_webhook_delivery_alerts_adds_operating_severity(monkeypatch):
    conn = FakeWebhookAlertConnection()
    monkeypatch.setattr(service, "db_connection", lambda: fake_db_connection(conn))

    alerts = await service.get_partner_webhook_delivery_alerts(
        identity={
            "role": "PARTNER",
            "tenant_code": "FNB",
            "client_id": "client-1",
        },
        limit=25,
    )

    assert alerts[0]["severity"] == "CRITICAL"
    assert alerts[1]["severity"] == "WARNING"
    assert alerts[0]["notification_count"] == 1
    assert alerts[0]["last_notification_status"] == "SENT"
    assert "recommended_action" in alerts[0]
    assert "signing-secret" in alerts[0]["recommended_action"]


@pytest.mark.asyncio
async def test_notify_partner_webhook_delivery_alerts_records_notification_evidence(
    monkeypatch,
):
    conn = FakeWebhookAlertNotifyConnection()
    monkeypatch.setattr(service, "db_connection", lambda: fake_db_connection(conn))

    result = await service.notify_partner_webhook_delivery_alerts(
        tenant_code="fnb",
        client_id="client-1",
        limit=25,
    )

    assert result["status"] == "notified"
    assert result["channel"] == "IN_APP"
    assert result["notified_count"] == 2
    assert len(result["items"]) == 2
    assert len(conn.insert_args) == 2
    assert conn.insert_args[0][0] == "FNB"
    assert conn.insert_args[0][1] == "client-1"
    assert conn.insert_args[0][4] == "CRITICAL"
    assert conn.insert_args[0][6] == "SENT"
    assert "failed or cancelled" in conn.insert_args[0][8]


@pytest.mark.asyncio
async def test_notify_partner_webhook_delivery_alerts_sends_physical_webhook(
    monkeypatch,
):
    class FakeResponse:
        status_code = 202
        text = "accepted"

    sent_payloads = []
    conn = FakeWebhookAlertNotifyConnection()
    monkeypatch.setattr(service, "db_connection", lambda: fake_db_connection(conn))
    monkeypatch.setattr(
        service,
        "get_settings",
        lambda: SimpleNamespace(
            partner_webhook_alert_notification_url="https://ops.example/alerts",
            partner_webhook_alert_notification_secret="notify-secret",
        ),
    )

    async def fake_post_alert_notification(url, payload, secret):
        sent_payloads.append((url, payload, secret))
        return FakeResponse()

    monkeypatch.setattr(
        service,
        "_post_alert_notification",
        fake_post_alert_notification,
    )

    result = await service.notify_partner_webhook_delivery_alerts(
        tenant_code="fnb",
        client_id="client-1",
        limit=25,
        channel="WEBHOOK",
    )

    assert result["status"] == "notified"
    assert result["channel"] == "WEBHOOK"
    assert result["notified_count"] == 2
    assert sent_payloads[0][0] == "https://ops.example/alerts"
    assert sent_payloads[0][2] == "notify-secret"
    assert sent_payloads[0][1]["tenant_code"] == "FNB"
    assert conn.insert_args[0][5] == "WEBHOOK"
    assert conn.insert_args[0][6] == "SENT"
    assert json.loads(conn.insert_args[0][9])["provider_status"] == 202


@pytest.mark.asyncio
async def test_get_partner_webhook_secret_readiness_flags_legacy_rotation(monkeypatch):
    conn = FakeWebhookSecretReadinessConnection(legacy_count=1)
    monkeypatch.setattr(service, "db_connection", lambda: fake_db_connection(conn))

    readiness = await service.get_partner_webhook_secret_readiness(
        {
            "role": "PARTNER",
            "tenant_code": "FNB",
            "client_id": "client-1",
        }
    )

    assert readiness["status"] == "ATTENTION"
    assert readiness["protection_mode"] in {"APPLICATION_KEY", "LOCAL_DEV_FALLBACK"}
    assert readiness["provider"] == "APPLICATION_KEY"
    assert readiness["legacy_plaintext_subscriptions"] == 1
    assert readiness["rotation_status"] == "ATTENTION"
    assert "Rotate legacy" in readiness["recommended_action"]
    assert conn.args == (
        "FNB",
        "client-1",
        f"{service.PROTECTED_SECRET_PREFIX}%",
        f"{service.MANAGED_SECRET_PREFIX}%",
    )


@pytest.mark.asyncio
async def test_get_partner_webhook_secret_readiness_is_ready_when_all_protected(
    monkeypatch,
):
    conn = FakeWebhookSecretReadinessConnection(legacy_count=0)
    monkeypatch.setattr(service, "db_connection", lambda: fake_db_connection(conn))

    readiness = await service.get_partner_webhook_secret_readiness(
        {
            "role": "PARTNER",
            "tenant_code": "FNB",
            "client_id": "client-1",
        }
    )

    assert readiness["status"] == "READY"
    assert readiness["protected_subscriptions"] == 3
    assert readiness["legacy_plaintext_subscriptions"] == 0


@pytest.mark.asyncio
async def test_get_partner_webhook_secret_readiness_reports_managed_kms(monkeypatch):
    conn = FakeWebhookSecretReadinessConnection(legacy_count=0)
    monkeypatch.setattr(service, "db_connection", lambda: fake_db_connection(conn))
    monkeypatch.setattr(
        service,
        "get_settings",
        lambda: SimpleNamespace(
            app_env="prod",
            partner_webhook_secret_provider="MANAGED_KMS",
            partner_webhook_kms_key_id="kms-key-1",
            partner_webhook_kms_backend="AWS_KMS",
            partner_webhook_secret_key=None,
        ),
    )

    readiness = await service.get_partner_webhook_secret_readiness(
        {
            "role": "PARTNER",
            "tenant_code": "FNB",
            "client_id": "client-1",
        }
    )

    assert readiness["status"] == "READY"
    assert readiness["provider"] == "MANAGED_KMS"
    assert readiness["protection_mode"] == "MANAGED_KMS"
    assert readiness["kms_key_configured"] is True
    assert readiness["kms_backend"] == "AWS_KMS"
    assert readiness["key_reference"] == "kms-key-1"


def test_get_partner_seam_production_readiness_is_ready_with_physical_providers(
    monkeypatch,
):
    monkeypatch.setattr(
        service,
        "get_settings",
        lambda: SimpleNamespace(
            app_env="prod",
            partner_webhook_secret_provider="MANAGED_KMS",
            partner_webhook_kms_key_id="kms-key-1",
            partner_webhook_kms_backend="AWS_KMS",
            partner_webhook_secret_key=None,
            partner_webhook_alert_notification_url="https://ops.example/alerts",
            partner_webhook_alert_notification_secret="notify-secret",
        ),
    )

    readiness = service.get_partner_seam_production_readiness()

    assert readiness["code_status"] == "READY"
    assert readiness["deployment_status"] == "READY"
    assert readiness["code_complete"] is True
    assert readiness["production_ready"] is True
    assert readiness["attention_count"] == 0
    assert readiness["secret_provider"]["kms_backend"] == "AWS_KMS"
    assert readiness["alert_notification_provider"]["configured"] is True
    assert {item["code"] for item in readiness["checks"]} == {
        "CLIENT_CREDENTIALS",
        "OUTBOUND_WEBHOOKS",
        "DELIVERY_OPERATIONS",
        "SECRET_PROTECTION",
        "ALERT_NOTIFICATIONS",
    }


def test_get_partner_seam_production_readiness_separates_deployment_attention(
    monkeypatch,
):
    monkeypatch.setattr(
        service,
        "get_settings",
        lambda: SimpleNamespace(
            app_env="prod",
            partner_webhook_secret_provider="APPLICATION_KEY",
            partner_webhook_kms_key_id=None,
            partner_webhook_kms_backend="LOCAL_ENVELOPE",
            partner_webhook_secret_key=None,
            partner_webhook_alert_notification_url=None,
            partner_webhook_alert_notification_secret=None,
        ),
    )

    readiness = service.get_partner_seam_production_readiness()

    assert readiness["code_status"] == "READY"
    assert readiness["deployment_status"] == "ATTENTION"
    assert readiness["code_complete"] is True
    assert readiness["production_ready"] is False
    assert readiness["attention_count"] == 2
    assert "code-complete" in readiness["recommended_action"]


@pytest.mark.asyncio
async def test_mark_partner_webhook_delivery_for_retry_is_client_scoped(monkeypatch):
    conn = FakeWebhookRetryConnection()
    monkeypatch.setattr(service, "db_connection", lambda: fake_db_connection(conn))
    audit_calls = []

    async def fake_audit(**kwargs):
        audit_calls.append(kwargs)

    monkeypatch.setattr(
        service,
        "try_write_admin_audit",
        fake_audit,
    )

    delivery_id = str(uuid4())
    delivery = await service.mark_partner_webhook_delivery_for_retry(
        identity={
            "role": "PARTNER",
            "tenant_code": "FNB",
            "client_id": "client-1",
        },
        delivery_id=delivery_id,
    )

    assert delivery["delivery_id"] == delivery_id
    assert delivery["tenant_code"] == "FNB"
    assert delivery["client_id"] == "client-1"
    assert delivery["delivery_status"] == "PENDING"
    assert conn.args == (delivery_id, "FNB", "client-1")
    assert audit_calls[0]["action_type"] == "PARTNER_WEBHOOK_DELIVERY_RETRY"
    assert audit_calls[0]["action_domain"] == "PARTNER_WEBHOOK"
    assert audit_calls[0]["metadata"]["retry_scope"] == "partner"


@pytest.mark.asyncio
async def test_mark_admin_webhook_delivery_for_retry_is_audited(monkeypatch):
    conn = FakeWebhookRetryConnection()
    monkeypatch.setattr(service, "db_connection", lambda: fake_db_connection(conn))
    audit_calls = []

    async def fake_audit(**kwargs):
        audit_calls.append(kwargs)

    monkeypatch.setattr(
        service,
        "try_write_admin_audit",
        fake_audit,
    )

    delivery_id = str(uuid4())
    delivery = await service.mark_webhook_delivery_for_retry(
        identity={"role": "SYSTEM_ADMIN", "tenant_code": "INTERNAL"},
        delivery_id=delivery_id,
    )

    assert delivery["delivery_id"] == delivery_id
    assert delivery["delivery_status"] == "PENDING"
    assert audit_calls[0]["identity"]["role"] == "SYSTEM_ADMIN"
    assert audit_calls[0]["tenant_code"] == "FNB"
    assert audit_calls[0]["metadata"]["retry_scope"] == "admin"


@pytest.mark.asyncio
async def test_mark_partner_webhook_delivery_for_retry_rejects_unknown_row(monkeypatch):
    conn = FakeWebhookRetryConnection(found=False)
    monkeypatch.setattr(service, "db_connection", lambda: fake_db_connection(conn))

    with pytest.raises(HTTPException) as exc:
        await service.mark_partner_webhook_delivery_for_retry(
            identity={
                "role": "PARTNER",
                "tenant_code": "FNB",
                "client_id": "client-1",
            },
            delivery_id=str(uuid4()),
        )

    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_get_webhook_delivery_summary_returns_operating_status(monkeypatch):
    conn = FakeWebhookSummaryConnection()
    monkeypatch.setattr(service, "db_connection", lambda: fake_db_connection(conn))

    summary = await service.get_webhook_delivery_summary(tenant_code="fnb")

    assert summary["status"] == "ATTENTION"
    assert summary["sent_count"] == 3
    assert summary["pending_count"] == 2
    assert summary["failed_count"] == 1


@pytest.mark.asyncio
async def test_get_partner_integration_overview_is_tenant_scoped(monkeypatch):
    conn = FakeIntegrationConnection()
    monkeypatch.setattr(service, "db_connection", lambda: fake_db_connection(conn))

    overview = await service.get_partner_integration_overview(
        {"role": "PARTNER", "tenant_code": "FNB"}
    )

    assert overview["identity"]["tenant_code"] == "FNB"
    assert overview["clients"][0]["client_id"] == "client-1"
    assert overview["webhooks"][0]["event_type"] == "OUTCOME_COMPLETED"
    assert overview["summary"]["status"] == "HEALTHY"
    assert overview["guardrails"]


@pytest.mark.asyncio
async def test_process_pending_webhook_delivery_marks_success(monkeypatch):
    conn = FakeWebhookConnection(status_code=204)
    monkeypatch.setattr(service, "db_connection", lambda: fake_db_connection(conn))
    captured = {}
    metric_calls = []
    monkeypatch.setattr(
        service,
        "partner_webhook_delivery_observe",
        lambda **kwargs: metric_calls.append(kwargs),
    )

    async def fake_post(url, body, headers):
        captured.update({"url": url, "body": body, "headers": headers})
        return FakeResponse(204)

    result = await service.process_pending_webhook_deliveries(http_post=fake_post)

    assert result["sent_count"] == 1
    assert result["items"][0]["delivery_status"] == "SENT"
    assert captured["url"] == "https://partner.example/webhooks"
    assert captured["headers"]["X-Amplifi-Signature"]
    assert captured["headers"]["X-Amplifi-Event-Type"] == "OUTCOME_COMPLETED"
    assert conn.update_args[0] == "SENT"
    assert metric_calls == [
        {
            "tenant": "FNB",
            "client_id": "client-1",
            "event_type": "OUTCOME_COMPLETED",
            "delivery_status": "SENT",
            "http_status": 204,
            "latency_seconds": metric_calls[0]["latency_seconds"],
        }
    ]
    assert metric_calls[0]["latency_seconds"] >= 0


@pytest.mark.asyncio
async def test_process_pending_webhook_delivery_schedules_retry(monkeypatch):
    conn = FakeWebhookConnection(status_code=500, attempt_count=0)
    monkeypatch.setattr(service, "db_connection", lambda: fake_db_connection(conn))

    async def fake_post(url, body, headers):
        return FakeResponse(500, "temporary failure")

    result = await service.process_pending_webhook_deliveries(http_post=fake_post)

    assert result["pending_count"] == 1
    assert result["items"][0]["delivery_status"] == "PENDING"
    assert conn.update_args[0] == "PENDING"
    assert conn.update_args[3] == "60 seconds"


@pytest.mark.asyncio
async def test_process_pending_webhook_delivery_marks_failed_after_max_attempts(
    monkeypatch,
):
    conn = FakeWebhookConnection(status_code=500, attempt_count=2)
    monkeypatch.setattr(service, "db_connection", lambda: fake_db_connection(conn))

    async def fake_post(url, body, headers):
        return FakeResponse(500, "still failing")

    result = await service.process_pending_webhook_deliveries(http_post=fake_post)

    assert result["failed_count"] == 1
    assert result["items"][0]["delivery_status"] == "FAILED"
    assert conn.update_args[0] == "FAILED"
    assert conn.update_args[3] is None
