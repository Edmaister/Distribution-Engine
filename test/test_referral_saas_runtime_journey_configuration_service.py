from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import datetime, timezone

import pytest

import services.referral_saas_runtime_journey_configuration_service as service


pytestmark = pytest.mark.asyncio


class FakeConn:
    def __init__(self, row):
        self.row = row
        self.calls = []

    async def fetchrow(self, query, *params):
        self.calls.append(("fetchrow", query, params))
        return self.row


def patch_db(monkeypatch, conn):
    @asynccontextmanager
    async def fake_db_connection():
        yield conn

    monkeypatch.setattr(service, "db_connection", fake_db_connection)


def _published_version_row(**overrides):
    values = {
        "customer_journey_version_id": "version-1",
        "account_id": "account-1",
        "customer_journey_code": "MORTGAGE_APPLICATION",
        "version_number": 3,
        "version_status": "PUBLISHED",
        "published_configuration_payload": {
            "milestones": [
                {
                    "code": "REFERRED",
                    "label": "Referral received",
                    "progressPercent": 10,
                },
                {
                    "code": "APPLICATION_SUBMITTED",
                    "label": "Application submitted",
                    "progressPercent": 45,
                },
                {
                    "code": "BOND_REGISTERED",
                    "label": "Bond registered",
                    "progressPercent": 100,
                },
            ],
            "transitions": [
                {"from": "REFERRED", "to": "APPLICATION_SUBMITTED"},
                {"from": "APPLICATION_SUBMITTED", "to": "BOND_REGISTERED"},
            ],
            "completionEvents": ["BOND_REGISTERED"],
            "secret": "must-not-leak",
        },
        "archived_at": None,
        "template_code": "MORTGAGE_APPLICATION",
        "template_version": "1.0.0",
        "template_status": "APPROVED",
        "milestone_schema": [
            {"code": "REFERRED"},
            {"code": "APPLICATION_SUBMITTED"},
            {"code": "BOND_REGISTERED"},
        ],
        "transition_rules": [
            {"from": "REFERRED", "to": "APPLICATION_SUBMITTED"},
            {"from": "APPLICATION_SUBMITTED", "to": "BOND_REGISTERED"},
        ],
        "published_at": datetime(2026, 8, 15, tzinfo=timezone.utc),
    }
    values.update(overrides)
    return values


async def test_runtime_journey_configuration_falls_back_to_code_baseline_without_flag(
    monkeypatch,
):
    conn = FakeConn(row=None)
    patch_db(monkeypatch, conn)

    resolved = await service.resolve_runtime_journey_configuration(
        customer_journey_version_id="version-1",
        published_runtime_enabled=False,
    )

    assert resolved.source == "CODE_BASELINE"
    assert resolved.journey_definition.journey_code == "BANKING_TRANSACTIONAL"
    assert resolved.progress_definition.journey_version == "v1"
    assert conn.calls == []


async def test_runtime_journey_configuration_maps_published_version(monkeypatch):
    conn = FakeConn(row=_published_version_row())
    patch_db(monkeypatch, conn)

    resolved = await service.resolve_runtime_journey_configuration(
        account_id="account-1",
        customer_journey_version_id="version-1",
        published_runtime_enabled=True,
    )

    journey_definition = resolved.journey_definition
    progress_definition = resolved.progress_definition

    assert resolved.source == "PUBLISHED_CUSTOMER_JOURNEY_VERSION"
    assert journey_definition.journey_code == "MORTGAGE_APPLICATION"
    assert journey_definition.journey_version == "published-v3"
    assert journey_definition.core_sequence == [
        "REFERRED",
        "APPLICATION_SUBMITTED",
        "BOND_REGISTERED",
    ]
    assert journey_definition.allowed_transitions[None] == {"REFERRED"}
    assert journey_definition.allowed_transitions["REFERRED"] == {
        "APPLICATION_SUBMITTED"
    }
    assert journey_definition.completion_events == {"BOND_REGISTERED"}
    assert progress_definition.milestones["REFERRED"].display_status == (
        "Referral received"
    )
    assert progress_definition.milestones["BOND_REGISTERED"].progress_percent == 100

    _, query, params = conn.calls[0]
    assert "referral_saas_customer_journey_versions" in query
    assert params == ("version-1", "account-1")


async def test_runtime_journey_configuration_rejects_missing_account(monkeypatch):
    conn = FakeConn(row=_published_version_row())
    patch_db(monkeypatch, conn)

    with pytest.raises(service.RuntimeJourneyConfigurationError):
        await service.resolve_runtime_journey_configuration(
            customer_journey_version_id="version-1",
            published_runtime_enabled=True,
        )

    assert conn.calls == []


async def test_runtime_journey_configuration_rejects_drafts_and_archives():
    with pytest.raises(service.RuntimeJourneyConfigurationError):
        service.runtime_journey_configuration_from_row(
            _published_version_row(version_status="DRAFT")
        )

    with pytest.raises(service.RuntimeJourneyConfigurationError):
        service.runtime_journey_configuration_from_row(
            _published_version_row(archived_at=datetime(2026, 8, 15))
        )


async def test_runtime_journey_configuration_rejects_unapproved_template():
    with pytest.raises(service.RuntimeJourneyConfigurationError):
        service.runtime_journey_configuration_from_row(
            _published_version_row(template_status="DRAFT")
        )


async def test_runtime_journey_configuration_safe_dict_redacts_raw_payloads():
    resolved = service.runtime_journey_configuration_from_row(_published_version_row())

    body = resolved.to_safe_dict()

    assert body["source"] == "PUBLISHED_CUSTOMER_JOURNEY_VERSION"
    assert body["customerJourneyVersionId"] == "version-1"
    assert body["milestoneCount"] == 3
    assert "published_configuration_payload" in body["redactions"]
    assert "secret" in body["redactions"]
    assert "must-not-leak" not in str(body)
    assert body["noProviderAuthBillingOrMoneyActionConfirmed"] is True
