from fastapi import APIRouter
from utils.db import db_cursor
import logging

router = APIRouter(tags=["health"])
logger = logging.getLogger(__name__)


@router.get("/healthz")
def healthz():
    return {"status": "ok"}


@router.get("/readyz")
def readyz():
    try:
        # ✅ Borrow + auto-return connection to pool
        with db_cursor() as cur:
            cur.execute("SELECT 1")
            cur.fetchone()

        return {"status": "ready"}

    except Exception:
        logger.exception("Readiness check failed")
        return {"status": "not_ready"}