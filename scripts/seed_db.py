import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from utils.db import close_async_pool, db_connection
from utils.logging import get_logger

logger = get_logger(__name__)


async def apply_sql_file(path: Path) -> None:
    logger.info("Applying seed: %s", path.name)

    async with db_connection() as conn:
        await conn.execute(path.read_text(encoding="utf-8"))


async def run() -> None:
    seeds_dir = ROOT / "dp" / "seeds"

    if not seeds_dir.exists():
        logger.error("Seeds folder not found at %s", seeds_dir)
        sys.exit(1)

    files = sorted(seeds_dir.glob("*.sql"))
    if not files:
        logger.warning("No seed files found in %s", seeds_dir)

    try:
        for path in files:
            await apply_sql_file(path)
        logger.info("All seeds applied successfully.")
    finally:
        await close_async_pool()


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()
