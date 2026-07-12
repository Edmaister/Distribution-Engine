from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any

import asyncpg
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


REQUIRED_TABLES = [
    "tenants",
    "referrer_codes",
    "referral_instances",
    "referral_qr_scans",
    "referral_progress_events",
    "referral_event_failures",
    "referral_processing_audit",
    "marketing_campaigns",
    "marketing_campaign_policies",
    "campaign_attributions",
    "campaign_track_events",
    "campaign_referral_links",
    "distribution_route_referral_links",
    "enterprise_event_inbox",
    "admin_audit_log",
]

STATE_FIELDS = [
    ("referral_instances", "status"),
    ("referral_progress_events", "event_type"),
    ("referral_event_failures", "status"),
    ("referral_qr_scans", "status"),
    ("campaign_attributions", "status"),
    ("enterprise_event_inbox", "processing_status"),
    ("distribution_route_referral_links", "link_status"),
]

EXPECTED_CONSTRAINTS = {
    "referral_progress_events": ["chk_rpe_event_type"],
    "referral_event_failures": [
        "uq_referral_event_failures_source_event",
        "uq_referral_event_failures_dedupe_key",
    ],
    "enterprise_event_inbox": ["enterprise_event_inbox_status_chk"],
    "distribution_route_referral_links": [
        "uq_distribution_route_referral",
        "chk_distribution_route_referral_status",
    ],
}

EXPECTED_INDEXES = {
    "referral_progress_events": [
        "ux_progress_events_source_event",
        "ux_progress_events_dedupe_key",
        "ix_progress_events_track_occurred",
        "ix_progress_events_track_event_type",
    ],
    "referral_event_failures": [
        "idx_referral_event_failures_referral_track_id",
        "idx_referral_event_failures_source_event_id",
        "idx_referral_event_failures_status",
    ],
    "enterprise_event_inbox": [
        "ux_enterprise_event_inbox_dedupe_key",
        "idx_enterprise_event_inbox_status",
    ],
    "distribution_route_referral_links": [
        "idx_distribution_route_referral_links_referral",
    ],
}


def _quote_identifier(value: str) -> str:
    if not value.replace("_", "").isalnum():
        raise ValueError(f"Unsafe SQL identifier: {value}")
    return f'"{value}"'


def build_query_plan(schema: str = "public") -> list[dict[str, Any]]:
    schema_ref = _quote_identifier(schema)
    plan: list[dict[str, Any]] = [
        {
            "name": "required_tables",
            "category": "schema",
            "sql": """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = $1
                  AND table_name = ANY($2::text[])
                ORDER BY table_name
            """,
            "params": [schema, REQUIRED_TABLES],
        },
        {
            "name": "required_columns",
            "category": "schema",
            "sql": """
                SELECT table_name, column_name, data_type, udt_name,
                       is_nullable, column_default
                FROM information_schema.columns
                WHERE table_schema = $1
                  AND table_name = ANY($2::text[])
                ORDER BY table_name, ordinal_position
            """,
            "params": [schema, REQUIRED_TABLES],
        },
        {
            "name": "constraints",
            "category": "schema",
            "sql": """
                SELECT c.relname AS table_name,
                       con.conname,
                       con.contype,
                       pg_get_constraintdef(con.oid) AS definition
                FROM pg_constraint con
                JOIN pg_class c ON c.oid = con.conrelid
                JOIN pg_namespace n ON n.oid = c.relnamespace
                WHERE n.nspname = $1
                  AND c.relname = ANY($2::text[])
                ORDER BY c.relname, con.conname
            """,
            "params": [schema, REQUIRED_TABLES],
        },
        {
            "name": "indexes",
            "category": "schema",
            "sql": """
                SELECT tablename AS table_name, indexname, indexdef
                FROM pg_indexes
                WHERE schemaname = $1
                  AND tablename = ANY($2::text[])
                ORDER BY tablename, indexname
            """,
            "params": [schema, REQUIRED_TABLES],
        },
    ]

    for table, field in STATE_FIELDS:
        plan.append(
            {
                "name": f"state_counts.{table}.{field}",
                "category": "state",
                "sql": (
                    f"SELECT {_quote_identifier(field)} AS state_value, "
                    f"COUNT(*) AS row_count "
                    f"FROM {schema_ref}.{_quote_identifier(table)} "
                    f"GROUP BY {_quote_identifier(field)} "
                    f"ORDER BY {_quote_identifier(field)}"
                ),
                "params": [],
            }
        )

    return plan


def _rows_to_dicts(rows: list[Any]) -> list[dict[str, Any]]:
    return [dict(row) for row in rows]


def _evaluate_static_expectations(results: dict[str, list[dict[str, Any]]]) -> list[str]:
    findings: list[str] = []

    existing_tables = {row["table_name"] for row in results.get("required_tables", [])}
    for table in REQUIRED_TABLES:
        if table not in existing_tables:
            findings.append(f"missing table: {table}")

    constraints_by_table: dict[str, set[str]] = {}
    for row in results.get("constraints", []):
        constraints_by_table.setdefault(row["table_name"], set()).add(row["conname"])
    for table, expected in EXPECTED_CONSTRAINTS.items():
        existing = constraints_by_table.get(table, set())
        for name in expected:
            if name not in existing:
                findings.append(f"missing constraint: {table}.{name}")

    indexes_by_table: dict[str, set[str]] = {}
    for row in results.get("indexes", []):
        indexes_by_table.setdefault(row["table_name"], set()).add(row["indexname"])
    for table, expected in EXPECTED_INDEXES.items():
        existing = indexes_by_table.get(table, set())
        for name in expected:
            if name not in existing:
                findings.append(f"missing index: {table}.{name}")

    return findings


async def run_database_check(dsn: str, schema: str = "public") -> dict[str, Any]:
    conn = await asyncpg.connect(dsn)
    results: dict[str, list[dict[str, Any]]] = {}
    try:
        for query in build_query_plan(schema):
            rows = await conn.fetch(query["sql"], *query["params"])
            results[query["name"]] = _rows_to_dicts(rows)
    finally:
        await conn.close()

    findings = _evaluate_static_expectations(results)
    return {
        "ok": not findings,
        "schema": schema,
        "mode": "database",
        "findings": findings,
        "results": results,
    }


def build_dry_run(schema: str = "public") -> dict[str, Any]:
    return {
        "ok": True,
        "schema": schema,
        "mode": "dry_run",
        "requiredTables": REQUIRED_TABLES,
        "stateFields": [
            {"table": table, "field": field} for table, field in STATE_FIELDS
        ],
        "expectedConstraints": EXPECTED_CONSTRAINTS,
        "expectedIndexes": EXPECTED_INDEXES,
        "queryPlan": build_query_plan(schema),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run Referral SaaS read-only schema/status/index checks."
    )
    parser.add_argument(
        "--database",
        action="store_true",
        help="Execute read-only checks against APP_DB_DSN or --dsn.",
    )
    parser.add_argument("--dsn", help="Database DSN. Defaults to APP_DB_DSN.")
    parser.add_argument("--schema", default="public", help="Database schema.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    load_dotenv(ROOT / ".env")

    if args.database:
        dsn = args.dsn or os.getenv("APP_DB_DSN")
        if not dsn:
            print("APP_DB_DSN or --dsn is required for --database", file=sys.stderr)
            return 2
        payload = asyncio.run(run_database_check(dsn, schema=args.schema))
    else:
        payload = build_dry_run(schema=args.schema)

    print(json.dumps(payload, indent=2, sort_keys=True, default=str))
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
