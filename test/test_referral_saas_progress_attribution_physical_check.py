from __future__ import annotations

import pytest

from scripts import referral_saas_account_setup_ui_physical_check as setup_check
from scripts import referral_saas_progress_attribution_physical_check as script


def _ok(payload: dict | None = None, *, status_code: int = 200) -> setup_check.ApiResult:
    return setup_check.ApiResult(status_code=status_code, payload=payload or {"status": "ok"})


def _mutation_result() -> dict:
    return {
        "status": "passed",
        "task": "TASK-271",
        "selected_customer": {
            "accountRef": "acct-340",
            "accountName": "Task 340 Customer",
            "externalTenantRef": "task-340-customer",
            "organisationRef": "org-task-340",
        },
        "created_campaign": {
            "campaignCode": "TASK340",
            "name": "Task 340 campaign",
            "segment": "proof",
        },
        "issued_referral_code": "REF340",
        "referral_track_id": "11111111-1111-4111-8111-111111111111",
    }


def test_run_records_progress_replay_trace_and_report(monkeypatch):
    calls: list[tuple[str, str, dict | None]] = []

    def fake_mutation_run(args):
        assert args.suffix == "340001"
        return _mutation_result()

    def fake_post_json(**kwargs):
        calls.append(("POST", kwargs["path"], kwargs["payload"]))
        if kwargs["path"] == "/v1/progress":
            payload = kwargs["payload"]
            if payload["sourceEventId"] == "task-340-ucn-captured-340001":
                count = sum(
                    1
                    for method, path, body in calls
                    if method == "POST"
                    and path == "/v1/progress"
                    and body["sourceEventId"] == "task-340-ucn-captured-340001"
                )
                return _ok(
                    {
                        "status": "ok",
                        "referralTrackId": payload["referralTrackId"],
                        "eventType": "UCN_CAPTURED",
                        "deduped": count > 1,
                        "sourceSystem": payload["sourceSystem"],
                        "sourceEventId": payload["sourceEventId"],
                    },
                    status_code=200 if count > 1 else 201,
                )
            if payload["sourceEventId"] == "task-340-account-opened-340001":
                return _ok(
                    {
                        "status": "ok",
                        "referralTrackId": payload["referralTrackId"],
                        "eventType": "ACCOUNT_OPENED",
                        "deduped": False,
                        "sourceSystem": payload["sourceSystem"],
                        "sourceEventId": payload["sourceEventId"],
                    },
                    status_code=201,
                )
        raise AssertionError(f"unexpected POST {kwargs['path']}")

    def fake_get_json(**kwargs):
        calls.append(("GET", kwargs["path"], kwargs.get("query")))
        if kwargs["path"].endswith("/progress-status"):
            assert kwargs["query"]["tenant_code"] == "FNB"
            return _ok({"status": "ok", "progressStatus": {"safeStatus": {"redactions": []}}})
        if kwargs["path"].endswith("/trace"):
            assert kwargs["query"]["tenant_code"] == "FNB"
            return _ok(
                {
                    "status": "ok",
                    "attributionTrace": {
                        "traceStatus": "PARTIAL",
                        "missingEvidence": ["REPORT_SOURCE_PENDING"],
                        "redactions": ["referrer_ucn", "referee_ucn"],
                    },
                }
            )
        if kwargs["path"] == "/v1/referral-saas/accounts/acct-340/reports/campaign_performance":
            assert kwargs["query"]["campaign_code"] == "TASK340"
            return _ok({"status": "ok", "report": {"rows": []}})
        raise AssertionError(f"unexpected GET {kwargs['path']}")

    monkeypatch.setattr(script.mutation_check, "run", fake_mutation_run)
    monkeypatch.setattr(script.setup_check, "post_json", fake_post_json)
    monkeypatch.setattr(script.setup_check, "get_json", fake_get_json)

    result = script.run(
        script.parse_args(
            [
                "--base-url",
                "http://127.0.0.1:8000",
                "--admin-key",
                "test-admin-key",
                "--tenant-code",
                "FNB",
                "--external-tenant-ref",
                "task-340-customer",
                "--suffix",
                "340001",
            ]
        )
    )

    assert result["status"] == "passed"
    assert result["task"] == "TASK-340"
    assert result["referral_track_id"] == "11111111-1111-4111-8111-111111111111"
    assert result["progress_events"]["first"]["deduped"] is False
    assert result["progress_events"]["replay"]["deduped"] is True
    assert result["progress_events"]["later"]["eventType"] == "ACCOUNT_OPENED"
    assert result["readbacks"]["trace_status"] == "PARTIAL"
    assert result["no_billing_or_money_movement"] is True


def test_run_fails_when_progress_replay_is_not_deduped(monkeypatch):
    def fake_mutation_run(args):
        return _mutation_result()

    def fake_post_json(**kwargs):
        return _ok(
            {
                "status": "ok",
                "referralTrackId": "11111111-1111-4111-8111-111111111111",
                "eventType": "UCN_CAPTURED",
                "deduped": False,
            },
            status_code=201,
        )

    monkeypatch.setattr(script.mutation_check, "run", fake_mutation_run)
    monkeypatch.setattr(script.setup_check, "post_json", fake_post_json)

    with pytest.raises(RuntimeError, match="expected deduped=True"):
        script.run(script.parse_args(["--suffix", "340002"]))


def test_run_fails_when_validation_does_not_return_track_id(monkeypatch):
    def fake_mutation_run(args):
        payload = _mutation_result()
        payload.pop("referral_track_id")
        return payload

    monkeypatch.setattr(script.mutation_check, "run", fake_mutation_run)

    with pytest.raises(RuntimeError, match="referral_track_id"):
        script.run(script.parse_args(["--suffix", "340003"]))


def test_operator_read_rejects_secret_payload():
    with pytest.raises(RuntimeError, match="clientSecret"):
        script._require_operator_read_result(
            _ok({"status": "ok", "clientSecret": "unsafe"}),
            step="unsafe read",
        )
