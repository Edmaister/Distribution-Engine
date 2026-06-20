import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    from scripts.check_migrations import check_files
except ModuleNotFoundError:  # pragma: no cover - direct script execution path
    from check_migrations import check_files

from utils.db import close_async_pool, db_connection
from utils.logging import get_logger

logger = get_logger(__name__)


async def apply_sql_file(path: Path) -> None:
    logger.info("Applying migration: %s", path.name)

    async with db_connection() as conn:
        await conn.execute(path.read_text(encoding="utf-8"))


async def run() -> None:
    mig_dir = ROOT / "dp" / "migrations"

    migration_failures = check_files(ROOT)
    if migration_failures:
        logger.error("Migration readiness checks failed:")
        for failure in migration_failures:
            logger.error("- %s", failure)
        sys.exit(1)

    if not mig_dir.exists():
        logger.error("Migrations folder not found at %s", mig_dir)
        sys.exit(1)

    files = sorted(
        path
        for path in mig_dir.glob("*.sql")
        if path.name.split("_", 1)[0].isdigit()
    )
    legacy_files = sorted(path.name for path in mig_dir.glob("*.sql") if path not in files)
    if legacy_files:
        logger.info(
            "Ignoring unnumbered legacy SQL files: %s",
            ", ".join(legacy_files),
        )
    if not files:
        logger.warning("No migration files found in %s", mig_dir)

    try:
        for path in files:
            await apply_sql_file(path)
        logger.info("All migrations applied successfully.")
    finally:
        await close_async_pool()


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()
