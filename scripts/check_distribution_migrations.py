from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path

import asyncpg
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    from scripts.check_migrations import check_files as check_all_migration_files
except ModuleNotFoundError:  # pragma: no cover - direct script execution path
    from check_migrations import check_files as check_all_migration_files


REQUIRED_MIGRATIONS = [
    "064_distribution_distributors.sql",
    "065_distribution_distributor_wallets.sql",
    "066_distribution_commissions.sql",
    "067_distribution_opportunities.sql",
    "068_distribution_offer_routes.sql",
    "069_distribution_governance.sql",
    "070_distribution_route_referral_links.sql",
    "071_admin_audit_log.sql",
    "072_multi_currency.sql",
]

REQUIRED_TABLES = [
    "distribution_distributors",
    "distribution_distributor_wallets",
    "distribution_distributor_wallet_ledger",
    "distribution_commission_rules",
    "distribution_commission_events",
    "distribution_opportunities",
    "distribution_offer_routes",
    "distribution_compliance_reviews",
    "distribution_disputes",
    "distribution_governance_audit",
    "distribution_route_referral_links",
]

def check_files(root: Path) -> list[str]:
    migration_dir = root / "dp" / "migrations"
    failures: list[str] = check_all_migration_files(root)

    if not migration_dir.exists():
        return [f"Migration folder not found: {migration_dir}"]

    existing = {path.name for path in migration_dir.glob("*.sql")}
    for migration in REQUIRED_MIGRATIONS:
        if migration not in existing:
            failures.append(f"Missing required migration: {migration}")

    return failures


async def check_database(dsn: str) -> list[str]:
    failures: list[str] = []
    conn = await asyncpg.connect(dsn)
    try:
        rows = await conn.fetch(
            """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
              AND table_name = ANY($1::text[])
            """,
            REQUIRED_TABLES,
        )
    finally:
        await conn.close()

    existing = {row["table_name"] for row in rows}
    for table in REQUIRED_TABLES:
        if table not in existing:
            failures.append(f"Database table not found: {table}")

    return failures


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Distribution Marketplace migration readiness."
    )
    parser.add_argument(
        "--database",
        action="store_true",
        help="Also check the live database using APP_DB_DSN.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = Path(__file__).resolve().parents[1]
    load_dotenv(root / ".env")

    failures = check_files(root)
    if args.database:
        dsn = os.getenv("APP_DB_DSN")
        if not dsn:
            failures.append("APP_DB_DSN is required for --database checks")
        else:
            failures.extend(asyncio.run(check_database(dsn)))

    if failures:
        print("[distribution-migrations] failed")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("[distribution-migrations] passed")
    print("- Required migration files are present.")
    if args.database:
        print("- Required distribution tables exist in the configured database.")
    else:
        print("- Database checks were skipped; pass --database to verify live tables.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
