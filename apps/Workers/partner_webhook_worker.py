from __future__ import annotations

import asyncio
import logging
import os

from services.partner_seam_service import process_pending_webhook_deliveries
from utils.db import close_async_pool, init_async_pool


logger = logging.getLogger(__name__)


async def run_once(limit: int = 25) -> dict:
    return await process_pending_webhook_deliveries(limit=limit)


async def run_loop(*, limit: int, interval_seconds: int) -> None:
    await init_async_pool()
    try:
        while True:
            result = await run_once(limit=limit)
            logger.info(
                "Partner webhook delivery pass complete | processed=%s sent=%s pending=%s failed=%s",
                result.get("processed_count"),
                result.get("sent_count"),
                result.get("pending_count"),
                result.get("failed_count"),
            )
            await asyncio.sleep(interval_seconds)
    finally:
        await close_async_pool()


def main() -> None:
    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
    limit = int(os.getenv("PARTNER_WEBHOOK_WORKER_LIMIT", "25"))
    interval_seconds = int(os.getenv("PARTNER_WEBHOOK_WORKER_INTERVAL_SECONDS", "30"))
    asyncio.run(run_loop(limit=limit, interval_seconds=interval_seconds))


if __name__ == "__main__":
    main()
