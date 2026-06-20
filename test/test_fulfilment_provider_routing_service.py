import services.fulfilment_provider_routing_service as service


def test_get_fallback_provider_returns_known_fallback():
    assert (
        service.get_fallback_provider("CASH_PROVIDER")
        == "CASH_PROVIDER_SECONDARY"
    )


def test_get_fallback_provider_is_case_insensitive():
    assert (
        service.get_fallback_provider("cash_provider")
        == "CASH_PROVIDER_SECONDARY"
    )


def test_get_fallback_provider_returns_none_for_unknown_provider():
    assert service.get_fallback_provider("UNKNOWN_PROVIDER") is None


def test_resolve_provider_primary_available(monkeypatch):
    def fake_can_execute_provider(*, provider_key):
        assert provider_key == "CASH_PROVIDER"
        return True

    monkeypatch.setattr(
        service,
        "can_execute_provider",
        fake_can_execute_provider,
    )

    result = service.resolve_provider("CASH_PROVIDER")

    assert result.requested_provider_key == "CASH_PROVIDER"
    assert result.selected_provider_key == "CASH_PROVIDER"
    assert result.reason == "PRIMARY_AVAILABLE"
    assert result.fallback_used is False


def test_resolve_provider_uses_fallback_when_primary_unavailable(monkeypatch):
    calls = []

    def fake_can_execute_provider(*, provider_key):
        calls.append(provider_key)
        return provider_key == "CASH_PROVIDER_SECONDARY"

    monkeypatch.setattr(
        service,
        "can_execute_provider",
        fake_can_execute_provider,
    )

    result = service.resolve_provider("CASH_PROVIDER")

    assert calls == [
        "CASH_PROVIDER",
        "CASH_PROVIDER_SECONDARY",
    ]

    assert result.requested_provider_key == "CASH_PROVIDER"
    assert result.selected_provider_key == "CASH_PROVIDER_SECONDARY"
    assert result.reason == "PRIMARY_CIRCUIT_OPEN_FALLBACK_AVAILABLE"
    assert result.fallback_used is True


def test_resolve_provider_no_available_provider(monkeypatch):
    def fake_can_execute_provider(*, provider_key):
        return False

    monkeypatch.setattr(
        service,
        "can_execute_provider",
        fake_can_execute_provider,
    )

    result = service.resolve_provider("CASH_PROVIDER")

    assert result.requested_provider_key == "CASH_PROVIDER"
    assert result.selected_provider_key == "CASH_PROVIDER"
    assert result.reason == "NO_AVAILABLE_PROVIDER"
    assert result.fallback_used is False


def test_resolve_provider_unknown_provider_without_fallback(monkeypatch):
    def fake_can_execute_provider(*, provider_key):
        assert provider_key == "UNKNOWN_PROVIDER"
        return False

    monkeypatch.setattr(
        service,
        "can_execute_provider",
        fake_can_execute_provider,
    )

    result = service.resolve_provider("UNKNOWN_PROVIDER")

    assert result.requested_provider_key == "UNKNOWN_PROVIDER"
    assert result.selected_provider_key == "UNKNOWN_PROVIDER"
    assert result.reason == "NO_AVAILABLE_PROVIDER"
    assert result.fallback_used is False