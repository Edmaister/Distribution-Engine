from __future__ import annotations

import logging
from pprint import pformat

from services.privacy_service import purge_expired_data

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def run_privacy_purge() -> dict:
    tenants = ["FNB", "DEFAULT"]
    results = []

    for tenant_code in tenants:
        try:
            result = purge_expired_data(tenant_code=tenant_code)
            results.append(result)

            logger.info(
                "PRIVACY_PURGE_COMPLETED tenant_code=%s result=%s",
                tenant_code,
                pformat(result),
            )

        except Exception as exc:
            error_result = {
                "status": "failed",
                "tenant_code": tenant_code,
                "error": str(exc),
            }

            results.append(error_result)

            logger.exception(
                "PRIVACY_PURGE_FAILED tenant_code=%s error=%s",
                tenant_code,
                str(exc),
            )

    return {
        "status": "completed",
        "results": results,
    }


if __name__ == "__main__":
    print(run_privacy_purge())