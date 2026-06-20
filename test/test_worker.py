from __future__ import annotations

import json

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import apps.api.routers.worker as worker_mod


@pytest.fixture()
def client(monkeypatch):
    monkeypatch.setattr(worker_mod, "WORKER_SECRET", "test-worker-secret")

    app = FastAPI()
    app.include_router(worker_mod.router)

    return TestClient(app)


def _headers(secret: str = "test-worker-secret"):
    return {"x-worker-secret": secret}


def test_unwrap_direct_referral_progress_event():
    payload = {"eventType": "REFERRAL_PROGRESS_RECORDED"}

    result = worker_mod._unwrap_sqsd_payload(payload)

    assert result == payload


@pytest.mark.parametrize("key", ["body", "Body", "Message", "message"])
def test_unwrap_nested_dict_payload(key):
    nested = {
        "eventType": "REFERRAL_PROGRESS_RECORDED",
        "tenant_code": "FNB",
    }

    result = worker_mod._unwrap_sqsd_payload({key: nested})

    assert result == nested


@pytest.mark.parametrize("key", ["body", "Body", "Message", "message"])
def test_unwrap_nested_json_string_payload(key):
    nested = {
        "eventType": "REFERRAL_PROGRESS_RECORDED",
        "tenant_code": "FNB",
    }

    result = worker_mod._unwrap_sqsd_payload({key: json.dumps(nested)})

    assert result == nested


def test_unwrap_invalid_nested_json_returns_original_payload(caplog):
    payload = {"body": "{not-valid-json"}

    result = worker_mod._unwrap_sqsd_payload(payload)

    assert result == payload
    assert "Failed to parse nested SQS payload field" in caplog.text


def test_unwrap_nested_non_dict_json_returns_original_payload():
    payload = {"body": json.dumps(["not", "a", "dict"])}

    result = worker_mod._unwrap_sqsd_payload(payload)

    assert result == payload


def test_unwrap_payload_without_nested_fields_returns_original_payload():
    payload = {"some": "payload"}

    result = worker_mod._unwrap_sqsd_payload(payload)

    assert result == payload


def test_validate_worker_auth_rejects_when_worker_secret_not_configured(monkeypatch):
    monkeypatch.setattr(worker_mod, "WORKER_SECRET", None)

    with pytest.raises(worker_mod.HTTPException) as exc:
        worker_mod._validate_worker_auth(
            incoming_secret="anything",
            event_secret=None,
        )

    assert exc.value.status_code == 500
    assert exc.value.detail == "Worker not configured"


def test_validate_worker_auth_accepts_header_secret(monkeypatch):
    monkeypatch.setattr(worker_mod, "WORKER_SECRET", "test-worker-secret")

    result = worker_mod._validate_worker_auth(
        incoming_secret="test-worker-secret",
        event_secret=None,
    )

    assert result is None


def test_validate_worker_auth_accepts_event_secret(monkeypatch):
    monkeypatch.setattr(worker_mod, "WORKER_SECRET", "test-worker-secret")

    result = worker_mod._validate_worker_auth(
        incoming_secret=None,
        event_secret="test-worker-secret",
    )

    assert result is None


def test_validate_worker_auth_rejects_wrong_secret(monkeypatch):
    monkeypatch.setattr(worker_mod, "WORKER_SECRET", "test-worker-secret")

    with pytest.raises(worker_mod.HTTPException) as exc:
        worker_mod._validate_worker_auth(
            incoming_secret="wrong-secret",
            event_secret="also-wrong",
        )

    assert exc.value.status_code == 401
    assert exc.value.detail == "Unauthorized"


def test_worker_invalid_json_is_ignored(client):
    response = client.post(
        "/worker/referral-events",
        content="{bad-json",
        headers=_headers(),
    )

    assert response.status_code == 200
    assert response.json() == {
        "status": "ignored",
        "reason": "invalid json",
    }


def test_worker_missing_secret_returns_401(client):
    response = client.post(
        "/worker/referral-events",
        json={
            "eventType": "REFERRAL_PROGRESS_RECORDED",
            "tenant_code": "FNB",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Unauthorized"


def test_worker_wrong_secret_returns_401(client):
    response = client.post(
        "/worker/referral-events",
        json={
            "eventType": "REFERRAL_PROGRESS_RECORDED",
            "tenant_code": "FNB",
        },
        headers=_headers("wrong-secret"),
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Unauthorized"


def test_worker_secret_from_event_body_is_accepted(client, monkeypatch):
    called = {}

    async def fake_handle_referral_progress_recorded(event, tenant_code):
        called["event"] = event
        called["tenant_code"] = tenant_code

    monkeypatch.setattr(
        worker_mod,
        "handle_referral_progress_recorded",
        fake_handle_referral_progress_recorded,
    )

    response = client.post(
        "/worker/referral-events",
        json={
            "eventType": "REFERRAL_PROGRESS_RECORDED",
            "tenant_code": "FNB",
            "secret": "test-worker-secret",
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "processed": True,
    }
    assert called["tenant_code"] == "FNB"


def test_worker_missing_tenant_code_is_ignored(client, monkeypatch):
    called = {"count": 0}

    async def fake_handle_referral_progress_recorded(event, tenant_code):
        called["count"] += 1

    monkeypatch.setattr(
        worker_mod,
        "handle_referral_progress_recorded",
        fake_handle_referral_progress_recorded,
    )

    response = client.post(
        "/worker/referral-events",
        json={
            "eventType": "REFERRAL_PROGRESS_RECORDED",
        },
        headers=_headers(),
    )

    assert response.status_code == 200
    assert response.json() == {
        "status": "ignored",
        "reason": "missing tenant_code",
    }
    assert called["count"] == 0


def test_worker_processes_referral_progress_with_tenant_code(client, monkeypatch):
    called = {}

    async def fake_handle_referral_progress_recorded(event, tenant_code):
        called["event"] = event
        called["tenant_code"] = tenant_code

    monkeypatch.setattr(
        worker_mod,
        "handle_referral_progress_recorded",
        fake_handle_referral_progress_recorded,
    )

    response = client.post(
        "/worker/referral-events",
        json={
            "eventType": "REFERRAL_PROGRESS_RECORDED",
            "tenant_code": "FNB",
        },
        headers=_headers(),
    )

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "processed": True,
    }
    assert called["tenant_code"] == "FNB"
    assert called["event"]["eventType"] == "REFERRAL_PROGRESS_RECORDED"


def test_worker_processes_referral_progress_with_camel_case_tenant_code(
    client,
    monkeypatch,
):
    called = {}

    async def fake_handle_referral_progress_recorded(event, tenant_code):
        called["event"] = event
        called["tenant_code"] = tenant_code

    monkeypatch.setattr(
        worker_mod,
        "handle_referral_progress_recorded",
        fake_handle_referral_progress_recorded,
    )

    response = client.post(
        "/worker/referral-events",
        json={
            "eventType": "REFERRAL_PROGRESS_RECORDED",
            "tenantCode": "FNB",
        },
        headers=_headers(),
    )

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "processed": True,
    }
    assert called["tenant_code"] == "FNB"


def test_worker_unsupported_event_returns_processed_false(client):
    response = client.post(
        "/worker/referral-events",
        json={
            "eventType": "SOMETHING_ELSE",
            "tenant_code": "FNB",
            "some": "value",
        },
        headers=_headers(),
    )

    assert response.status_code == 200

    body = response.json()

    assert body["status"] == "ok"
    assert body["processed"] is False
    assert body["reason"].startswith(
        "unsupported or unrecognized event payload: keys="
    )


def test_worker_nested_sqs_body_payload_is_processed(client, monkeypatch):
    called = {}

    async def fake_handle_referral_progress_recorded(event, tenant_code):
        called["event"] = event
        called["tenant_code"] = tenant_code

    monkeypatch.setattr(
        worker_mod,
        "handle_referral_progress_recorded",
        fake_handle_referral_progress_recorded,
    )

    response = client.post(
        "/worker/referral-events",
        json={
            "body": json.dumps(
                {
                    "eventType": "REFERRAL_PROGRESS_RECORDED",
                    "tenant_code": "FNB",
                }
            )
        },
        headers=_headers(),
    )

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "processed": True,
    }
    assert called["tenant_code"] == "FNB"

def test_worker_failure_publishes_to_dlq(client, monkeypatch):
    captured = {}

    async def fake_handle_referral_progress_recorded(event, tenant_code):
        raise RuntimeError("orchestrator exploded")

    def fake_publish_to_dlq(event, error):
        captured["event"] = event
        captured["error"] = error

    monkeypatch.setattr(
        worker_mod,
        "handle_referral_progress_recorded",
        fake_handle_referral_progress_recorded,
    )
    monkeypatch.setattr(worker_mod, "publish_to_dlq", fake_publish_to_dlq)

    response = client.post(
        "/worker/referral-events",
        json={
            "eventType": "REFERRAL_PROGRESS_RECORDED",
            "tenant_code": "FNB",
            "referralTrackId": "track-123",
        },
        headers=_headers(),
    )

    assert response.status_code == 200
    assert response.json() == {
        "status": "failed",
        "processed": False,
        "eventType": "REFERRAL_PROGRESS_RECORDED",
    }

    assert captured["event"]["eventType"] == "REFERRAL_PROGRESS_RECORDED"
    assert captured["event"]["tenant_code"] == "FNB"
    assert captured["error"] == "orchestrator exploded"


def test_worker_leaderboard_rebuild_failure_publishes_to_dlq(client, monkeypatch):
    captured = {}

    def fake_rebuild_leaderboard_for_referrer(*, tenant_code, referrer_ucn):
        raise RuntimeError("leaderboard exploded")

    def fake_publish_to_dlq(event, error):
        captured["event"] = event
        captured["error"] = error

    monkeypatch.setattr(
        worker_mod,
        "rebuild_leaderboard_for_referrer",
        fake_rebuild_leaderboard_for_referrer,
    )
    monkeypatch.setattr(worker_mod, "publish_to_dlq", fake_publish_to_dlq)

    response = client.post(
        "/worker/referral-events",
        json={
            "eventType": worker_mod.EVENT_TYPE_LEADERBOARD_REBUILD_REQUESTED,
            "tenantCode": "FNB",
            "referrerUcn": "123",
            "correlationId": "corr-123",
            "referralTrackId": "track-123",
        },
        headers=_headers(),
    )

    assert response.status_code == 200
    assert response.json() == {
        "status": "failed",
        "processed": False,
        "eventType": worker_mod.EVENT_TYPE_LEADERBOARD_REBUILD_REQUESTED,
    }

    assert captured["event"]["eventType"] == worker_mod.EVENT_TYPE_LEADERBOARD_REBUILD_REQUESTED
    assert captured["event"]["tenantCode"] == "FNB"
    assert captured["error"] == "leaderboard exploded"


def test_worker_missing_referrer_ucn_does_not_publish_to_dlq(client, monkeypatch):
    called = {"dlq": 0}

    def fake_publish_to_dlq(event, error):
        called["dlq"] += 1

    monkeypatch.setattr(worker_mod, "publish_to_dlq", fake_publish_to_dlq)

    response = client.post(
        "/worker/referral-events",
        json={
            "eventType": worker_mod.EVENT_TYPE_LEADERBOARD_REBUILD_REQUESTED,
            "tenantCode": "FNB",
        },
        headers=_headers(),
    )

    assert response.status_code == 200
    assert response.json() == {
        "status": "ignored",
        "reason": "missing referrerUcn",
    }
    assert called["dlq"] == 0

@pytest.mark.asyncio
async def test_get_event_value_prefers_camel_case():
    event = {
        "rewardId": "camel",
        "reward_id": "snake",
    }

    result = worker_mod._get_event_value(
        event,
        "rewardId",
        "reward_id",
    )

    assert result == "camel"


@pytest.mark.asyncio
async def test_get_event_value_uses_snake_case():
    event = {
        "reward_id": "snake",
    }

    result = worker_mod._get_event_value(
        event,
        "rewardId",
        "reward_id",
    )

    assert result == "snake"


def test_worker_missing_reward_id_returns_ignored(client):
    response = client.post(
        "/worker/referral-events",
        json={
            "eventType":
                worker_mod.REWARD_FULFILMENT_REQUESTED,

            "tenantCode":
                "FNB",

            "rewardType":
                "CASH",

            "rewardValue":
                100,
        },
        headers=_headers(),
    )

    assert response.status_code == 200

    assert response.json() == {
        "status":
            "ignored",

        "reason":
            "missing rewardId",
    }


def test_worker_missing_reward_type_returns_ignored(client):
    response = client.post(
        "/worker/referral-events",
        json={
            "eventType":
                worker_mod.REWARD_FULFILMENT_REQUESTED,

            "tenantCode":
                "FNB",

            "rewardId":
                "reward-1",

            "rewardValue":
                100,
        },
        headers=_headers(),
    )

    assert response.status_code == 200

    assert response.json() == {
        "status":
            "ignored",

        "reason":
            "missing rewardType",
    }


def test_worker_missing_reward_value_returns_ignored(client):
    response = client.post(
        "/worker/referral-events",
        json={
            "eventType":
                worker_mod.REWARD_FULFILMENT_REQUESTED,

            "tenantCode":
                "FNB",

            "rewardId":
                "reward-1",

            "rewardType":
                "CASH",
        },
        headers=_headers(),
    )

    assert response.status_code == 200

    assert response.json() == {
        "status":
            "ignored",

        "reason":
            "missing rewardValue",
    }


def test_worker_processes_reward_fulfilment(
    client,
    monkeypatch,
):
    captured = {}

    async def fake_fulfil_reward(request):

        captured["request"] = request

        class Result:
            status = "PENDING"
            provider_reference = "provider-123"

        return Result()

    monkeypatch.setattr(
        worker_mod,
        "fulfil_reward",
        fake_fulfil_reward,
    )

    response = client.post(
        "/worker/referral-events",
        json={
            "eventType":
                worker_mod.REWARD_FULFILMENT_REQUESTED,

            "tenantCode":
                "FNB",

            "rewardId":
                "reward-1",

            "rewardType":
                "CASH",

            "rewardValue":
                100,

            "recipientUcn":
                "123",

            "journeyCode":
                "MAIN_BANK",

            "milestoneCode":
                "ACCOUNT_OPENED",
        },
        headers=_headers(),
    )

    assert response.status_code == 200

    body = response.json()

    assert body["status"] == "ok"
    assert body["processed"] is True
    assert body["eventType"] == worker_mod.REWARD_FULFILMENT_REQUESTED
    assert body["fulfilmentStatus"] == "PENDING"
    assert body["providerReference"] == "provider-123"

    assert captured["request"].reward_id == "reward-1"
    assert captured["request"].tenant_code == "FNB"


def test_worker_fulfilment_failure_goes_to_dlq(
    client,
    monkeypatch,
):
    captured = {}

    async def fake_fulfil_reward(request):
        raise RuntimeError(
            "fulfilment exploded"
        )

    def fake_publish_to_dlq(
        event,
        error,
    ):
        captured["event"] = event
        captured["error"] = error

    monkeypatch.setattr(
        worker_mod,
        "fulfil_reward",
        fake_fulfil_reward,
    )

    monkeypatch.setattr(
        worker_mod,
        "publish_to_dlq",
        fake_publish_to_dlq,
    )

    response = client.post(
        "/worker/referral-events",
        json={
            "eventType":
                worker_mod.REWARD_FULFILMENT_REQUESTED,

            "tenantCode":
                "FNB",

            "rewardId":
                "reward-1",

            "rewardType":
                "CASH",

            "rewardValue":
                100,
        },
        headers=_headers(),
    )

    assert response.status_code == 200

    assert response.json() == {
        "status":
            "failed",

        "processed":
            False,

        "eventType":
            worker_mod.REWARD_FULFILMENT_REQUESTED,
    }

    assert captured["error"] == "fulfilment exploded"