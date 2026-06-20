"""Async database helpers."""

from __future__ import annotations

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from typing import AsyncIterator

import asyncpg

logger = logging.getLogger(__name__)

APP_DB_DSN = os.environ.get(
    "APP_DB_DSN",
    "postgresql://user:pass@localhost:5432/referrals",
)

async_db_pool: asyncpg.Pool | None = None
_pool_loop = None


def _safe_dsn_for_log(dsn: str) -> str:
    try:
        if "@" in dsn:
            prefix, suffix = dsn.split("@", 1)
            if "://" in prefix:
                scheme = prefix.split("://", 1)[0]
                return f"{scheme}://***:***@{suffix}"
        return dsn
    except Exception:
        return "<unavailable>"


async def init_async_pool() -> None:
    await get_async_pool()


async def get_async_pool() -> asyncpg.Pool:
    global async_db_pool, _pool_loop

    current_loop = asyncio.get_running_loop()

    if async_db_pool is None or _pool_loop != current_loop:
        logger.info(
            "Initializing async DB pool: %s",
            _safe_dsn_for_log(APP_DB_DSN),
        )

        async_db_pool = await asyncpg.create_pool(
            dsn=APP_DB_DSN,
            min_size=2,
            max_size=20,
            command_timeout=30,
        )

        _pool_loop = current_loop

    return async_db_pool


@asynccontextmanager
async def db_connection() -> AsyncIterator[asyncpg.Connection]:
    pool = await get_async_pool()

    async with pool.acquire() as conn:
        yield conn


# Alias for backwards compatibility
@asynccontextmanager
async def async_db_connection() -> AsyncIterator[asyncpg.Connection]:
    async with db_connection() as conn:
        yield conn


# Alias for backwards compatibility
@asynccontextmanager
async def get_async_connection() -> AsyncIterator[asyncpg.Connection]:
    async with db_connection() as conn:
        yield conn


# NEW: used by migrated async tests/services
@asynccontextmanager
async def async_db_cursor() -> AsyncIterator[asyncpg.Connection]:
    """
    Async DB helper.

    Usage:

        async with async_db_cursor() as cur:
            row = await cur.fetchrow(
                "SELECT * FROM table WHERE id=$1",
                some_id
            )

    Note:
        cur is an asyncpg.Connection,
        not a psycopg cursor.
    """
    pool = await get_async_pool()

    async with pool.acquire() as conn:
        async with conn.transaction():
            yield conn


async def close_async_pool() -> None:
    global async_db_pool, _pool_loop

    if async_db_pool:
        logger.info("Closing async DB pool")

        await async_db_pool.close()

        async_db_pool = None
        _pool_loop = None


async def init_all_pools() -> None:
    await init_async_pool()


async def close_all_pools() -> None:
    await close_async_pool()