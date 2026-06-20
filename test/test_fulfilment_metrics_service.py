import services.fulfilment_metrics_service as service


def test_record_fulfilment_success(monkeypatch):
    calls = {}

    def fake_metric(**labels):
        calls.update(labels)

    monkeypatch.setattr(service, "fulfilment_success_inc", fake_metric)

    service.record_fulfilment_success(
        tenant_code="FNB",
        reward_type="CASH",
        provider_key="CASH_PROVIDER",
    )

    assert calls == {
        "tenant_code": "FNB",
        "reward_type": "CASH",
        "provider_key": "CASH_PROVIDER",
    }


def test_record_fulfilment_failed(monkeypatch):
    calls = {}

    def fake_metric(**labels):
        calls.update(labels)

    monkeypatch.setattr(service, "fulfilment_failed_inc", fake_metric)

    service.record_fulfilment_failed(
        tenant_code="FNB",
        reward_type="CASH",
        provider_key="CASH_PROVIDER",
        retryable=True,
    )

    assert calls == {
        "tenant_code": "FNB",
        "reward_type": "CASH",
        "provider_key": "CASH_PROVIDER",
        "retryable": "true",
    }


def test_record_fulfilment_retry(monkeypatch):
    calls = {}

    def fake_metric(**labels):
        calls.update(labels)

    monkeypatch.setattr(service, "fulfilment_retry_inc", fake_metric)

    service.record_fulfilment_retry(
        tenant_code="FNB",
        reward_type="CASH",
        provider_key="CASH_PROVIDER",
    )

    assert calls == {
        "tenant_code": "FNB",
        "reward_type": "CASH",
        "provider_key": "CASH_PROVIDER",
    }


def test_record_fulfilment_dlq(monkeypatch):
    calls = {}

    def fake_metric(**labels):
        calls.update(labels)

    monkeypatch.setattr(service, "fulfilment_dlq_inc", fake_metric)

    service.record_fulfilment_dlq(
        tenant_code="FNB",
        reward_type="CASH",
        provider_key="CASH_PROVIDER",
    )

    assert calls == {
        "tenant_code": "FNB",
        "reward_type": "CASH",
        "provider_key": "CASH_PROVIDER",
    }


def test_record_fulfilment_duplicate_skipped(monkeypatch):
    calls = {}

    def fake_metric(**labels):
        calls.update(labels)

    monkeypatch.setattr(service, "fulfilment_duplicate_skipped_inc", fake_metric)

    service.record_fulfilment_duplicate_skipped(
        tenant_code="FNB",
        reward_type="CASH",
        provider_key="CASH_PROVIDER",
    )

    assert calls == {
        "tenant_code": "FNB",
        "reward_type": "CASH",
        "provider_key": "CASH_PROVIDER",
    }


def test_safe_call_ignores_missing_metric():
    service._safe_call(
        None,
        tenant_code="FNB",
    )


def test_safe_call_swallows_metric_exception():
    def broken_metric(**labels):
        raise RuntimeError("metrics unavailable")

    service._safe_call(
        broken_metric,
        tenant_code="FNB",
    )