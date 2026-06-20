from __future__ import annotations

import sys
import pytest
from pathlib import Path
from unittest.mock import AsyncMock

from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import apps.api.main as main


def _clear_health_cache():
    main._HEALTH_CACHE["payload"] = None
    main._HEALTH_CACHE["ts"] = 0.0


def client():
    return TestClient(main.app, raise_server_exceptions=False)


class FakeAsyncConnection:
    async def fetchval(self, query, *params):
        assert query == "SELECT 1"
        return 1

    async def fetch(self, query, *params):
        tables = params[0]
        return [{"table_name": table} for table in tables]


class FakeAsyncConnectionContext:
    async def __aenter__(self):
        return FakeAsyncConnection()

    async def __aexit__(self, exc_type, exc, tb):
        return False


def patch_async_db(monkeypatch):
    monkeypatch.setattr(
        main,
        "get_async_connection",
        lambda: FakeAsyncConnectionContext(),
    )


def test_root():
    res = client().get("/")
    assert res.status_code == 200
    assert res.json()["service"] == "Referral, Campaign & Composite Code API"
    assert res.json()["docs"] == "/docs"


def test_healthz(monkeypatch):
    async def fake_compose_health(full=True):
        return {"status": "ok", "components": {"version": "dev"}}

    monkeypatch.setattr(main, "_compose_health", fake_compose_health)

    res = client().get("/healthz")

    assert res.status_code == 200
    assert res.json()["status"] == "ok"
    assert "version" in res.json()["components"]


@pytest.mark.asyncio
async def test_db_ping_success(monkeypatch):
    patch_async_db(monkeypatch)

    ok, msg = await main.db_ping()

    assert ok is True
    assert msg == "ok"


@pytest.mark.asyncio
async def test_db_ping_failure(monkeypatch):
    class BrokenContext:
        async def __aenter__(self):
            raise Exception("db down")

        async def __aexit__(self, exc_type, exc, tb):
            return False

    monkeypatch.setattr(main, "get_async_connection", lambda: BrokenContext())

    ok, msg = await main.db_ping()

    assert ok is False
    assert msg == "unavailable"


@pytest.mark.asyncio
async def test_schema_readiness_all_ok(monkeypatch):
    patch_async_db(monkeypatch)

    result = await main.schema_readiness()

    assert result["ok"] is True
    assert result["msg"] == "ok"
    assert result["groups"]["distribution"]["ok"] is True


@pytest.mark.asyncio
async def test_schema_readiness_reports_missing_group(monkeypatch):
    class PartialConnection:
        async def fetch(self, query, *params):
            requested_tables = params[0]
            return [
                {"table_name": table}
                for table in requested_tables
                if not table.startswith("distribution_")
            ]

    class PartialContext:
        async def __aenter__(self):
            return PartialConnection()

        async def __aexit__(self, exc_type, exc, tb):
            return False

    monkeypatch.setattr(main, "get_async_connection", lambda: PartialContext())

    result = await main.schema_readiness()

    assert result["ok"] is False
    assert result["msg"] == "missing schema objects"
    assert result["groups"]["distribution"]["ok"] is False
    assert "064_distribution_distributors.sql" in result["groups"]["distribution"]["migration_hint"]


@pytest.mark.asyncio
async def test_schema_readiness_unavailable(monkeypatch):
    class BrokenContext:
        async def __aenter__(self):
            raise Exception("db failed")

        async def __aexit__(self, exc_type, exc, tb):
            return False

    monkeypatch.setattr(main, "get_async_connection", lambda: BrokenContext())

    result = await main.schema_readiness()

    assert result["ok"] is False
    assert result["msg"] == "schema check unavailable"


def test_sqs_ping_stub_mode(monkeypatch):
    monkeypatch.delenv("APP_SQS_QUEUE_URL", raising=False)

    ok, msg = main.sqs_ping()

    assert ok is True
    assert msg == "stub mode"


def test_sqs_ping_success(monkeypatch):
    class DummySqs:
        def get_queue_attributes(self, QueueUrl, AttributeNames):
            assert QueueUrl == "https://example.com/queue"
            assert AttributeNames == ["QueueArn"]

    monkeypatch.setenv("APP_SQS_QUEUE_URL", "https://example.com/queue")
    monkeypatch.setenv("AWS_REGION", "af-south-1")
    monkeypatch.setattr(main.boto3, "client", lambda *args, **kwargs: DummySqs())

    ok, msg = main.sqs_ping()

    assert ok is True
    assert msg == "ok"


def test_sqs_ping_failure(monkeypatch):
    class FailingSqs:
        def get_queue_attributes(self, QueueUrl, AttributeNames):
            raise Exception("sqs down")

    monkeypatch.setenv("APP_SQS_QUEUE_URL", "https://example.com/queue")
    monkeypatch.setattr(main.boto3, "client", lambda *args, **kwargs: FailingSqs())

    ok, msg = main.sqs_ping()

    assert ok is False
    assert msg == "unavailable"


def test_kafka_ping_stdout(monkeypatch):
    monkeypatch.setenv("APP_KAFKA_CLIENT", "stdout")

    ok, msg = main.kafka_ping()

    assert ok is True
    assert msg == "stdout client"


def test_kafka_ping_missing_broker(monkeypatch):
    monkeypatch.setenv("APP_KAFKA_CLIENT", "kafka")
    monkeypatch.delenv("APP_KAFKA_BROKER", raising=False)

    ok, msg = main.kafka_ping()

    assert ok is False
    assert msg == "APP_KAFKA_BROKER missing"


def test_kafka_ping_no_lib(monkeypatch):
    monkeypatch.setattr(main, "KafkaProducer", None)
    monkeypatch.setenv("APP_KAFKA_CLIENT", "kafka")
    monkeypatch.setenv("APP_KAFKA_BROKER", "localhost:9092")

    ok, msg = main.kafka_ping()

    assert ok is False
    assert msg == "kafka-python not available"


def test_kafka_ping_success(monkeypatch):
    class DummyProducer:
        def __init__(self, **kwargs):
            assert kwargs["bootstrap_servers"] == ["localhost:9092"]

        def close(self):
            return None

    monkeypatch.setattr(main, "KafkaProducer", DummyProducer)
    monkeypatch.setenv("APP_KAFKA_CLIENT", "kafka")
    monkeypatch.setenv("APP_KAFKA_BROKER", "localhost:9092")

    ok, msg = main.kafka_ping()

    assert ok is True
    assert msg == "ok"


def test_kafka_ping_failure(monkeypatch):
    class FailingProducer:
        def __init__(self, **kwargs):
            raise Exception("kafka down")

    monkeypatch.setattr(main, "KafkaProducer", FailingProducer)
    monkeypatch.setenv("APP_KAFKA_CLIENT", "kafka")
    monkeypatch.setenv("APP_KAFKA_BROKER", "localhost:9092")

    ok, msg = main.kafka_ping()

    assert ok is False
    assert msg == "unavailable"


@pytest.mark.asyncio
async def test_compute_health_all_ok(monkeypatch):
    async def fake_db_ping():
        return True, "ok"

    monkeypatch.setattr(main, "db_ping", fake_db_ping)
    monkeypatch.setattr(
        main,
        "schema_readiness",
        AsyncMock(return_value={"ok": True, "msg": "ok", "groups": {}}),
    )
    monkeypatch.setattr(main, "sqs_ping", lambda: (True, "ok"))
    monkeypatch.setattr(main, "kafka_ping", lambda: (True, "ok"))

    payload = await main._compute_health()

    assert payload["status"] == "ok"
    assert payload["components"]["db"]["ok"] is True
    assert payload["components"]["schema"]["ok"] is True


@pytest.mark.asyncio
async def test_compute_health_kafka_down_still_ok(monkeypatch):
    async def fake_db_ping():
        return True, "ok"

    monkeypatch.setattr(main, "db_ping", fake_db_ping)
    monkeypatch.setattr(
        main,
        "schema_readiness",
        AsyncMock(return_value={"ok": True, "msg": "ok", "groups": {}}),
    )
    monkeypatch.setattr(main, "sqs_ping", lambda: (True, "ok"))
    monkeypatch.setattr(main, "kafka_ping", lambda: (False, "unavailable"))

    payload = await main._compute_health()

    assert payload["status"] == "ok"
    assert payload["components"]["kafka"]["ok"] is False


@pytest.mark.asyncio
async def test_compute_health_db_down_is_down(monkeypatch):
    async def fake_db_ping():
        return False, "unavailable"

    monkeypatch.setattr(main, "db_ping", fake_db_ping)
    schema_mock = AsyncMock()
    monkeypatch.setattr(main, "schema_readiness", schema_mock)
    monkeypatch.setattr(main, "sqs_ping", lambda: (True, "ok"))
    monkeypatch.setattr(main, "kafka_ping", lambda: (True, "ok"))

    payload = await main._compute_health()

    assert payload["status"] == "down"
    schema_mock.assert_not_awaited()
    assert payload["components"]["schema"]["msg"] == "skipped because database is unavailable"


@pytest.mark.asyncio
async def test_compute_health_schema_down_is_down(monkeypatch):
    async def fake_db_ping():
        return True, "ok"

    monkeypatch.setattr(main, "db_ping", fake_db_ping)
    monkeypatch.setattr(
        main,
        "schema_readiness",
        AsyncMock(
            return_value={
                "ok": False,
                "msg": "missing schema objects",
                "groups": {
                    "multi_currency": {
                        "ok": False,
                        "missing_tables": ["fx_rates"],
                        "migration_hint": "Apply multi-currency migration 072_multi_currency.sql.",
                    }
                },
            }
        ),
    )
    monkeypatch.setattr(main, "sqs_ping", lambda: (True, "ok"))
    monkeypatch.setattr(main, "kafka_ping", lambda: (True, "ok"))

    payload = await main._compute_health()

    assert payload["status"] == "down"
    assert payload["components"]["schema"]["groups"]["multi_currency"]["missing_tables"] == ["fx_rates"]


@pytest.mark.asyncio
async def test_compute_health_sqs_down_is_down(monkeypatch):
    async def fake_db_ping():
        return True, "ok"

    monkeypatch.setattr(main, "db_ping", fake_db_ping)
    monkeypatch.setattr(
        main,
        "schema_readiness",
        AsyncMock(return_value={"ok": True, "msg": "ok", "groups": {}}),
    )
    monkeypatch.setattr(main, "sqs_ping", lambda: (False, "unavailable"))
    monkeypatch.setattr(main, "kafka_ping", lambda: (True, "ok"))

    payload = await main._compute_health()

    assert payload["status"] == "down"


@pytest.mark.asyncio
async def test_health_cache(monkeypatch):
    _clear_health_cache()
    calls = {"count": 0}

    async def fake_compute_health():
        calls["count"] += 1
        return {"status": "ok", "components": {"version": "dev"}}

    monkeypatch.setattr(main, "_compute_health", fake_compute_health)

    result1 = await main._compose_health(full=True)
    result2 = await main._compose_health(full=True)

    assert result1 == result2
    assert calls["count"] == 1


@pytest.mark.asyncio
async def test_health_partial(monkeypatch):
    monkeypatch.setenv("APP_VERSION", "test-version")

    result = await main._compose_health(full=False)

    assert result == {
        "status": "ok",
        "components": {"version": "test-version"},
    }


def test_readyz_ok(monkeypatch):
    async def fake_compose_health(full=True):
        return {"status": "ok", "components": {}}

    monkeypatch.setattr(main, "_compose_health", fake_compose_health)

    res = client().get("/readyz")

    assert res.status_code == 200
    assert res.json()["status"] == "ok"


def test_readyz_down(monkeypatch):
    async def fake_compose_health(full=True):
        return {"status": "down", "components": {}}

    monkeypatch.setattr(main, "_compose_health", fake_compose_health)

    res = client().get("/readyz")

    assert res.status_code == 503
    assert res.json()["status"] == "down"


def test_health_endpoint_ok(monkeypatch):
    async def fake_compose_health(full=True):
        return {"status": "ok", "components": {}}

    monkeypatch.setattr(main, "_compose_health", fake_compose_health)

    res = client().get("/health")

    assert res.status_code == 200
    assert res.json()["status"] == "ok"


def test_health_endpoint_down(monkeypatch):
    async def fake_compose_health(full=True):
        return {"status": "down", "components": {}}

    monkeypatch.setattr(main, "_compose_health", fake_compose_health)

    res = client().get("/health")

    assert res.status_code == 503
    assert res.json()["status"] == "down"


def test_metrics_endpoint():
    res = client().get("/metrics")

    assert res.status_code == 200
    assert "http_requests_total" in res.text


def test_correlation_id_header_added():
    res = client().get("/")
    assert "X-Request-ID" in res.headers


def test_correlation_id_passthrough():
    res = client().get("/", headers={"X-Request-ID": "test-id"})
    assert res.headers["X-Request-ID"] == "test-id"


def test_metrics_middleware_swallows_metric_errors(monkeypatch):
    class BrokenCounter:
        def labels(self, **kwargs):
            raise Exception("metrics failed")

    monkeypatch.setattr(main, "REQUEST_COUNT", BrokenCounter())

    res = client().get("/")

    assert res.status_code == 200


def test_global_exception_handler():
    path = f"/boom-test-main-{id(object())}"

    @main.app.get(path)
    def boom():
        raise Exception("fail")

    res = client().get(path, headers={"X-Request-ID": "boom-id"})

    assert res.status_code == 500
    assert res.json() == {
        "error": "INTERNAL_ERROR",
        "correlation_id": "boom-id",
    }
    assert res.headers["X-Request-ID"] == "boom-id"


def test_global_exception_handler_for_missing_table():
    path = f"/missing-table-test-main-{id(object())}"

    @main.app.get(path)
    def boom():
        raise main.asyncpg.UndefinedTableError("relation missing")

    res = client().get(path, headers={"X-Request-ID": "schema-id"})

    assert res.status_code == 503
    assert res.json()["error"] == "SCHEMA_NOT_READY"
    assert res.json()["correlation_id"] == "schema-id"
    assert res.headers["X-Request-ID"] == "schema-id"


@pytest.mark.asyncio
async def test_startup_shutdown(monkeypatch):
    async_init_mock = AsyncMock()
    async_close_mock = AsyncMock()

    monkeypatch.setattr(main, "init_async_pool", async_init_mock)
    monkeypatch.setattr(main, "close_async_pool", async_close_mock)

    await main.startup_event()
    await main.shutdown_event()

    async_init_mock.assert_awaited_once()
    async_close_mock.assert_awaited_once()
