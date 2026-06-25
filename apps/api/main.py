import os

from dotenv import load_dotenv

load_dotenv()

import uuid
import logging
from time import time
from typing import Tuple, Dict, Any

import boto3
import asyncpg
from fastapi import FastAPI, Response, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from apps.api.routers.worker import router as worker_router
from apps.api.routers.internal_replay import router as replay_router
from apps.api.routers import leaderboards
from apps.api.routers.admin_failure import router as admin_failures_router
from apps.api.routers.referral_bootstrap import router as referral_bootstrap_router
from apps.api.routers import missions, reward_summary
from apps.api.routers.badges import router as badges_router
from apps.api.routers.dashboard import router as dashboard_router
from apps.api.routers import admin_tenants
from apps.api.routers import privacy
from apps.api.routers import admin_audit
from apps.api.routers import admin_analytics
from apps.api.routers import admin_campaign_readiness
from apps.api.routers import admin_links
from apps.api.routers import admin_outcomes
from apps.api.routers import admin_dlq_replay
from apps.api.routers.admin_fulfilment import router as admin_fulfilment_router
from apps.api.routers import admin_settlement
from apps.api.routers import admin_finance
from apps.api.routers import admin_reconciliation
from apps.api.routers import admin_reconciliation_exceptions
from apps.api.routers import provider_sla
from apps.api.routers import enterprise_events
from apps.api.routers import admin_enterprise_events
from apps.api.routers import admin_funding
from apps.api.routers import admin_multi_currency
from apps.api.routers.admin_funding_rules import router as funding_rules_router
from apps.api.routers.admin_funding_audit import router as funding_audit_router
from apps.api.routers import admin_funding_forecast
from apps.api.routers import admin_funding_alerts
from apps.api.routers import admin_funding_reconciliation
from apps.api.routers import admin_verticals
from apps.api.routers import admin_channels
from apps.api.routers import admin_settlement_batches
from apps.api.routers import admin_settlement_approvals
from apps.api.routers import admin_settlement_exceptions
from apps.api.routers import admin_settlement_reversals
from apps.api.routers import admin_settlement_periods
from apps.api.routers.marketplace_funding import sponsor_wallets
from apps.api.routers import sponsor_billing
from apps.api.routers import sponsor_portal_billing
from apps.api.routers import producer_supply
from apps.api.routers import session
from apps.api.routers import partner_seam
from apps.api.routers import consumer_experience
from apps.api.routers import admin_experience
from apps.api.routers import operator_control_plane
from apps.api.routers import distributor_experience
from apps.api.routers import sponsor_experience
from apps.api.routers import admin_budget_governance
from apps.api.routers.distribution import admin_distributors
from apps.api.routers.distribution import admin_distributor_wallets
from apps.api.routers.distribution import admin_commissions
from apps.api.routers.distribution import admin_opportunities
from apps.api.routers.distribution import admin_routing
from apps.api.routers.distribution import distributor_portal
from apps.api.routers.distribution import admin_governance
from apps.api.routers.distribution import admin_reporting
from apps.api.routers.admin_settlement_certifications import (
    router as admin_settlement_certifications_router,
)
from apps.api.routers.admin_settlement_lock_enforcement import (
    router as admin_settlement_lock_enforcement_router,
)
from apps.api.routers import funding_contracts
from apps.api.middleware.rate_limit import RateLimitMiddleware
from utils.db import (
    init_async_pool,
    close_async_pool,
    get_async_connection,
)

try:
    from kafka import KafkaProducer
except Exception:
    KafkaProducer = None

from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    generate_latest,
    CONTENT_TYPE_LATEST,
)


logger = logging.getLogger(__name__)

app = FastAPI(title="Referral, Campaign & Composite Code API")


SCHEMA_GROUPS: dict[str, dict[str, Any]] = {
    "foundation": {
        "migration_hint": "Apply base migrations through 061_enterprise_event_inbox.sql.",
        "tables": [
            "referrer_codes",
            "referral_instances",
            "referral_progress_events",
            "enterprise_event_inbox",
        ],
    },
    "funding": {
        "migration_hint": "Apply funding migrations 057_sponsor_wallets.sql through 063_budget_governance.sql.",
        "tables": [
            "sponsor_wallets",
            "sponsor_wallet_ledger",
            "funding_contracts",
            "funding_contract_ledger",
            "sponsor_invoices",
            "sponsor_invoice_lines",
            "funding_budget_adjustment_requests",
        ],
    },
    "distribution": {
        "migration_hint": "Apply distribution migrations 064_distribution_distributors.sql through 069_distribution_governance.sql.",
        "tables": [
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
        ],
    },
    "multi_currency": {
        "migration_hint": "Apply multi-currency migration 072_multi_currency.sql.",
        "tables": [
            "fx_rates",
            "currency_conversion_quotes",
            "cross_border_settlements",
        ],
    },
    "admin_audit": {
        "migration_hint": "Apply admin audit migration 071_admin_audit_log.sql.",
        "tables": [
            "admin_audit_log",
        ],
    },
}


allowed_origins = [
    origin.strip()
    for origin in os.getenv("APP_CORS_ALLOW_ORIGINS", "").split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(worker_router)


@app.on_event("startup")
async def startup_event():
    await init_async_pool()


@app.on_event("shutdown")
async def shutdown_event():
    await close_async_pool()


@app.middleware("http")
async def correlation_middleware(request: Request, call_next):
    incoming_request_id = request.headers.get("X-Request-ID")
    correlation_id = incoming_request_id or str(uuid.uuid4())

    request.state.correlation_id = correlation_id

    response = await call_next(request)
    response.headers["X-Request-ID"] = correlation_id

    return response


REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "path", "status"],
)

REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "path"],
    buckets=(0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10),
)

DB_READY = Gauge("db_ready", "Database ping result (1=ok, 0=down)")
SQS_READY = Gauge("sqs_ready", "SQS ping result (1=ok, 0=down)")
KAFKA_READY = Gauge("kafka_ready", "Kafka ping result (1=ok, 0=down)")


@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start = time()
    response = await call_next(request)

    try:
        REQUEST_COUNT.labels(
            method=request.method,
            path=request.url.path,
            status=str(response.status_code),
        ).inc()

        REQUEST_LATENCY.labels(
            method=request.method,
            path=request.url.path,
        ).observe(time() - start)
    except Exception:
        logger.exception("Failed to record HTTP metrics")

    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    correlation_id = getattr(request.state, "correlation_id", "unknown")

    if isinstance(exc, asyncpg.UndefinedTableError):
        logger.exception(
            "Missing database table | correlation_id=%s | path=%s | method=%s",
            correlation_id,
            request.url.path,
            request.method,
        )

        return JSONResponse(
            status_code=503,
            content={
                "error": "SCHEMA_NOT_READY",
                "detail": "A required database table is missing. Check /readyz for schema readiness and apply the indicated migration.",
                "correlation_id": correlation_id,
            },
            headers={"X-Request-ID": correlation_id},
        )

    logger.exception(
        "Unhandled application error | correlation_id=%s | path=%s | method=%s",
        correlation_id,
        request.url.path,
        request.method,
    )

    return JSONResponse(
        status_code=500,
        content={
            "error": "INTERNAL_ERROR",
            "correlation_id": correlation_id,
        },
        headers={"X-Request-ID": correlation_id},
    )


async def db_ping() -> Tuple[bool, str]:
    try:
        async with get_async_connection() as conn:
            await conn.fetchval("SELECT 1")
        return True, "ok"
    except Exception:
        logger.exception("Database readiness check failed")
        return False, "unavailable"


async def schema_readiness() -> dict[str, Any]:
    required_tables = sorted(
        {table for group in SCHEMA_GROUPS.values() for table in group["tables"]}
    )

    try:
        async with get_async_connection() as conn:
            rows = await conn.fetch(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                  AND table_name = ANY($1::text[])
                """,
                required_tables,
            )

    except Exception:
        logger.exception("Schema readiness check failed")
        return {
            "ok": False,
            "msg": "schema check unavailable",
            "groups": {},
        }

    found_tables = {row["table_name"] for row in rows}
    groups: dict[str, Any] = {}

    for group_name, config in SCHEMA_GROUPS.items():
        missing = [table for table in config["tables"] if table not in found_tables]
        groups[group_name] = {
            "ok": not missing,
            "missing_tables": missing,
            "migration_hint": None if not missing else config["migration_hint"],
        }

    ok = all(group["ok"] for group in groups.values())

    return {
        "ok": ok,
        "msg": "ok" if ok else "missing schema objects",
        "groups": groups,
    }


def sqs_ping() -> Tuple[bool, str]:
    queue_url = os.getenv("APP_SQS_QUEUE_URL")

    if not queue_url:
        return True, "stub mode"

    try:
        sqs = boto3.client("sqs", region_name=os.getenv("AWS_REGION"))
        sqs.get_queue_attributes(
            QueueUrl=queue_url,
            AttributeNames=["QueueArn"],
        )
        return True, "ok"
    except Exception:
        logger.exception("SQS readiness check failed")
        return False, "unavailable"


def kafka_ping() -> Tuple[bool, str]:
    client = os.getenv("APP_KAFKA_CLIENT", "stdout")
    if client == "stdout":
        return True, "stdout client"

    broker = os.getenv("APP_KAFKA_BROKER")
    if not broker:
        return False, "APP_KAFKA_BROKER missing"

    if KafkaProducer is None:
        return False, "kafka-python not available"

    try:
        prod = KafkaProducer(
            bootstrap_servers=[broker],
            api_version_auto_timeout_ms=3000,
            request_timeout_ms=3000,
            metadata_max_age_ms=3000,
        )
        prod.close()
        return True, "ok"
    except Exception:
        logger.exception("Kafka readiness check failed")
        return False, "unavailable"


class HealthPayload(BaseModel):
    status: str
    components: dict


_HEALTH_CACHE: Dict[str, Any] = {"ts": 0.0, "payload": None}
_HEALTH_CACHE_TTL_SECONDS = int(os.getenv("HEALTH_CACHE_TTL_SECONDS", "10"))


async def _compute_health() -> Dict[str, Any]:
    db_ok, db_msg = await db_ping()
    sqs_ok, sqs_msg = sqs_ping()
    kafka_ok, kafka_msg = kafka_ping()
    schema = (
        await schema_readiness()
        if db_ok
        else {
            "ok": False,
            "msg": "skipped because database is unavailable",
            "groups": {},
        }
    )

    DB_READY.set(1 if db_ok else 0)
    SQS_READY.set(1 if sqs_ok else 0)
    KAFKA_READY.set(1 if kafka_ok else 0)

    overall_ok = db_ok and schema["ok"] and sqs_ok

    return {
        "status": "ok" if overall_ok else "down",
        "components": {
            "db": {"ok": db_ok, "msg": db_msg},
            "schema": schema,
            "sqs": {"ok": sqs_ok, "msg": sqs_msg},
            "kafka": {"ok": kafka_ok, "msg": kafka_msg},
            "version": os.getenv("APP_VERSION", "dev"),
        },
    }


async def _compose_health(full: bool = True) -> Dict[str, Any]:
    if not full:
        return {
            "status": "ok",
            "components": {"version": os.getenv("APP_VERSION", "dev")},
        }

    now = time()
    cached = _HEALTH_CACHE.get("payload")
    ts = float(_HEALTH_CACHE.get("ts") or 0.0)

    if cached is not None and (now - ts) < _HEALTH_CACHE_TTL_SECONDS:
        return cached

    payload = await _compute_health()
    _HEALTH_CACHE["payload"] = payload
    _HEALTH_CACHE["ts"] = now

    return payload


@app.get("/metrics")
def metrics_endpoint():
    data = generate_latest()
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)


@app.get("/", include_in_schema=False)
def root():
    return {
        "service": "Referral, Campaign & Composite Code API",
        "docs": "/docs",
    }


@app.get("/healthz", response_model=HealthPayload, tags=["health"])
async def liveness():
    return await _compose_health(full=False)


@app.get("/readyz", response_model=HealthPayload, tags=["health"])
async def readiness(response: Response):
    payload = await _compose_health(full=True)

    if payload["status"] != "ok":
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return payload


@app.get("/health", response_model=HealthPayload, tags=["health"])
async def combined_health(response: Response):
    payload = await _compose_health(full=True)

    if payload["status"] != "ok":
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return payload


from apps.api.routers import (
    campaigns,
    referrals,
    composite_codes,
    rewards,
    progress,
    recommendations,
    admin_recommendations,
    channels,
)

app.include_router(campaigns.public_router)
app.include_router(campaigns.router)
app.include_router(referrals.public_router)
app.include_router(referrals.router)
app.include_router(composite_codes.router)
app.include_router(rewards.router)
app.include_router(progress.router)
app.include_router(recommendations.router)
app.include_router(admin_recommendations.router)
app.include_router(channels.router)
app.include_router(session.router)
app.include_router(replay_router)
app.include_router(admin_failures_router)
app.include_router(leaderboards.router)
app.include_router(referral_bootstrap_router)
app.include_router(missions.router)
app.include_router(reward_summary.router)
app.include_router(badges_router)
app.include_router(dashboard_router)
app.include_router(admin_tenants.router)
app.include_router(privacy.router)
app.include_router(admin_audit.router)
app.include_router(admin_analytics.router)
app.include_router(admin_campaign_readiness.router)
app.include_router(admin_links.router)
app.include_router(admin_outcomes.router)
app.add_middleware(RateLimitMiddleware)
app.include_router(admin_dlq_replay.router)
app.include_router(admin_fulfilment_router)
app.include_router(admin_settlement.router)
app.include_router(admin_finance.router)
app.include_router(admin_reconciliation.router)
app.include_router(admin_reconciliation_exceptions.router)
app.include_router(provider_sla.router)
app.include_router(enterprise_events.router)
app.include_router(admin_enterprise_events.router)
app.include_router(admin_funding.router)
app.include_router(admin_multi_currency.router)
app.include_router(funding_rules_router)
app.include_router(funding_audit_router)
app.include_router(admin_funding_forecast.router)
app.include_router(admin_funding_alerts.router)
app.include_router(admin_funding_reconciliation.router)
app.include_router(admin_verticals.router)
app.include_router(admin_channels.router)
app.include_router(admin_settlement_batches.router)
app.include_router(admin_settlement_approvals.router)
app.include_router(admin_settlement_exceptions.router)
app.include_router(admin_settlement_reversals.router)
app.include_router(admin_settlement_periods.router)
app.include_router(admin_settlement_certifications_router)
app.include_router(admin_settlement_lock_enforcement_router)
app.include_router(sponsor_wallets.router)
app.include_router(funding_contracts.router)
app.include_router(admin_budget_governance.router)
app.include_router(admin_distributors.router)
app.include_router(admin_distributor_wallets.router)
app.include_router(admin_commissions.router)
app.include_router(admin_opportunities.router)
app.include_router(admin_routing.router)
app.include_router(distributor_portal.router)
app.include_router(admin_governance.router)
app.include_router(admin_reporting.router)
app.include_router(sponsor_billing.router)
app.include_router(sponsor_portal_billing.router)
app.include_router(producer_supply.router)
app.include_router(partner_seam.router)
app.include_router(partner_seam.admin_router)
app.include_router(consumer_experience.router)
app.include_router(admin_experience.router)
app.include_router(operator_control_plane.router)
app.include_router(distributor_experience.router)
app.include_router(sponsor_experience.router)
