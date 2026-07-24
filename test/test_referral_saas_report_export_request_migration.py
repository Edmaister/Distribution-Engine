from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MIGRATION_DIR = ROOT / "dp" / "migrations"
MIGRATION_NAME = "085_referral_saas_report_export_requests.sql"
MIGRATION_PATH = MIGRATION_DIR / MIGRATION_NAME

EXPECTED_COLUMNS = {
    "export_request_id",
    "account_id",
    "account_tenant_id",
    "external_ref_id",
    "tenant_code",
    "report_type",
    "export_format",
    "redaction_profile",
    "row_limit",
    "row_count",
    "request_status",
    "storage_status",
    "delivery_status",
    "download_status",
    "download_url",
    "dimensions",
    "filters",
    "metadata",
    "redactions",
    "reason_code",
    "correlation_id",
    "idempotency_key_hash",
    "request_payload_hash",
    "requested_by_ref",
    "requested_by_role",
    "requested_at",
    "expires_at",
    "created_at",
    "updated_at",
}

EXPECTED_INDEXES = {
    "idx_referral_saas_report_export_requests_idem",
    "idx_referral_saas_report_export_requests_account",
    "idx_referral_saas_report_export_requests_tenant",
    "idx_referral_saas_report_export_requests_correlation",
}

FORBIDDEN_ACTION_TOKENS = (
    "send_email",
    "webhook_delivery",
    "billing_event",
    "invoice_line",
    "wallet_ledger",
    "funding_transaction",
    "settlement_batch",
)


def _sql() -> str:
    return MIGRATION_PATH.read_text(encoding="utf-8")


def _table_block() -> str:
    sql = _sql()
    match = re.search(
        r"CREATE\s+TABLE\s+IF\s+NOT\s+EXISTS\s+referral_saas_report_export_requests\s*\(",
        sql,
        flags=re.IGNORECASE,
    )
    assert match is not None

    start = sql.index("(", match.end() - 1)
    depth = 0
    for index in range(start, len(sql)):
        char = sql[index]
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth == 0:
                return sql[start + 1 : index]
    raise AssertionError("Could not find export request table definition.")


def _column_names() -> set[str]:
    columns: set[str] = set()
    for line in _table_block().splitlines():
        stripped = line.strip().rstrip(",")
        if not stripped or stripped.upper().startswith("CONSTRAINT"):
            continue
        column_name = stripped.split(maxsplit=1)[0]
        if re.fullmatch(r"[a-z_][a-z0-9_]*", column_name):
            columns.add(column_name)
    return columns


def test_referral_saas_report_export_request_migration_is_ordered() -> None:
    migration_names = sorted(
        path.name
        for path in MIGRATION_DIR.glob("*.sql")
        if path.name.split("_", 1)[0].isdigit()
    )

    assert migration_names.index("084_referral_saas_campaign_manager_role_family.sql") < (
        migration_names.index(MIGRATION_NAME)
    )
    assert migration_names.index(MIGRATION_NAME) < migration_names.index(
        "999_indexes.sql"
    )


def test_referral_saas_report_export_request_table_shape() -> None:
    block = _table_block()

    assert EXPECTED_COLUMNS <= _column_names()
    assert "REFERENCES platform_accounts(account_id)" in block
    assert "REFERENCES platform_account_tenants(account_tenant_id)" in block
    assert "REFERENCES platform_external_tenant_refs(external_ref_id)" in block
    assert "REFERENCES tenants(tenant_code)" in block
    assert "export_format IN ('json', 'csv')" in block
    assert "redaction_profile = 'tenant_safe'" in block
    assert "row_limit BETWEEN 1 AND 50000" in block
    assert "'READY_FOR_FILE_STORAGE'" in block
    assert "'NOT_STORED'" in block
    assert "'NOT_REQUESTED'" in block
    assert "'NOT_AVAILABLE'" in block


def test_referral_saas_report_export_request_indexes_and_boundaries() -> None:
    sql = _sql()

    for index_name in EXPECTED_INDEXES:
        assert index_name in sql
    assert "idempotency_key_hash" in sql
    assert "request_payload_hash" in sql
    assert "No_TENANT_CODE_EXPOSURE".lower() in sql.lower()
    for forbidden in FORBIDDEN_ACTION_TOKENS:
        assert forbidden not in sql.lower()

