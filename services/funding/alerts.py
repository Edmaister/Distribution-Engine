from __future__ import annotations

from typing import Any
from uuid import uuid4

from utils.db import db_connection
from services.funding.forecasting import (
    list_funding_forecasts,
    list_settlement_exposure_forecasts,
    list_sponsor_funding_forecasts,
)


ALERT_STATUS_OPEN = "OPEN"
ALERT_STATUS_ACKNOWLEDGED = "ACKNOWLEDGED"
ALERT_STATUS_RESOLVED = "RESOLVED"


def determine_forecast_alert(
    *,
    days_remaining,
    available_balance,
    reserved_amount,
) -> tuple[str, str, str] | None:
    if available_balance <= 0:
        return (
            "FUNDING_DEPLETED",
            "CRITICAL",
            "Funding account has depleted available balance.",
        )

    if reserved_amount > available_balance:
        return (
            "EXPOSURE_BREACH",
            "CRITICAL",
            "Reserved funding exceeds available balance.",
        )

    if days_remaining is None:
        return None

    if days_remaining < 7:
        return (
            "FUNDING_CRITICAL",
            "CRITICAL",
            "Funding account is forecast to deplete in less than 7 days.",
        )

    if days_remaining < 15:
        return (
            "FUNDING_LOW",
            "WARNING",
            "Funding account is forecast to deplete in less than 15 days.",
        )

    if days_remaining < 30:
        return (
            "FUNDING_WATCH",
            "INFO",
            "Funding account is forecast to deplete in less than 30 days.",
        )

    return None


def determine_status_alert(
    *,
    forecast_status: str,
    critical_type: str,
    low_type: str,
    watch_type: str,
    critical_message: str,
    low_message: str,
    watch_message: str,
) -> tuple[str, str, str] | None:
    if forecast_status in {"DEPLETED", "CRITICAL"}:
        return (critical_type, "CRITICAL", critical_message)

    if forecast_status == "LOW":
        return (low_type, "WARNING", low_message)

    if forecast_status == "WATCH":
        return (watch_type, "INFO", watch_message)

    return None


def _forecast_risk_item(
    *,
    tenant_code: str,
    risk_scope: str,
    risk_key: str,
    alert: tuple[str, str, str],
    forecast: dict[str, Any],
) -> dict[str, Any]:
    alert_type, severity, alert_message = alert

    return {
        "tenant_code": tenant_code,
        "risk_scope": risk_scope,
        "risk_key": risk_key,
        "alert_type": alert_type,
        "severity": severity,
        "alert_message": alert_message,
        "forecast": forecast,
    }


async def create_funding_alert(
    *,
    tenant_code: str,
    account_id: str,
    alert_type: str,
    severity: str,
    alert_message: str,
    correlation_id: str | None = None,
) -> dict[str, Any]:
    async with db_connection() as conn:
        existing = await conn.fetchrow(
            """
            SELECT
                alert_id,
                tenant_code,
                account_id,
                alert_type,
                severity,
                alert_message,
                status,
                correlation_id,
                created_at,
                acknowledged_at,
                resolved_at
            FROM funding_alerts
            WHERE tenant_code = $1
              AND account_id = $2
              AND alert_type = $3
              AND status IN ('OPEN', 'ACKNOWLEDGED')
            ORDER BY created_at DESC
            LIMIT 1
            """,
            tenant_code,
            account_id,
            alert_type,
        )

        if existing:
            return dict(existing)

        row = await conn.fetchrow(
            """
            INSERT INTO funding_alerts (
                alert_id,
                tenant_code,
                account_id,
                alert_type,
                severity,
                alert_message,
                status,
                correlation_id
            )
            VALUES ($1, $2, $3, $4, $5, $6, 'OPEN', $7)
            RETURNING
                alert_id,
                tenant_code,
                account_id,
                alert_type,
                severity,
                alert_message,
                status,
                correlation_id,
                created_at,
                acknowledged_at,
                resolved_at
            """,
            uuid4(),
            tenant_code,
            account_id,
            alert_type,
            severity,
            alert_message,
            correlation_id,
        )

    return dict(row)


async def list_funding_alerts(
    *,
    tenant_code: str | None = None,
    account_id: str | None = None,
    status: str | None = ALERT_STATUS_OPEN,
    limit: int = 100,
) -> list[dict[str, Any]]:
    async with db_connection() as conn:
        rows = await conn.fetch(
            """
            SELECT
                alert_id,
                tenant_code,
                account_id,
                alert_type,
                severity,
                alert_message,
                status,
                correlation_id,
                created_at,
                acknowledged_at,
                resolved_at
            FROM funding_alerts
            WHERE ($1::text IS NULL OR tenant_code = $1)
              AND ($2::uuid IS NULL OR account_id = $2)
              AND ($3::text IS NULL OR status = $3)
            ORDER BY created_at DESC
            LIMIT $4
            """,
            tenant_code,
            account_id,
            status,
            limit,
        )

    return [dict(row) for row in rows]


async def acknowledge_funding_alert(
    *,
    alert_id: str,
) -> dict[str, Any] | None:
    async with db_connection() as conn:
        row = await conn.fetchrow(
            """
            UPDATE funding_alerts
            SET
                status = 'ACKNOWLEDGED',
                acknowledged_at = NOW()
            WHERE alert_id = $1
              AND status = 'OPEN'
            RETURNING
                alert_id,
                tenant_code,
                account_id,
                alert_type,
                severity,
                alert_message,
                status,
                correlation_id,
                created_at,
                acknowledged_at,
                resolved_at
            """,
            alert_id,
        )

    return dict(row) if row else None


async def resolve_funding_alert(
    *,
    alert_id: str,
) -> dict[str, Any] | None:
    async with db_connection() as conn:
        row = await conn.fetchrow(
            """
            UPDATE funding_alerts
            SET
                status = 'RESOLVED',
                resolved_at = NOW()
            WHERE alert_id = $1
              AND status IN ('OPEN', 'ACKNOWLEDGED')
            RETURNING
                alert_id,
                tenant_code,
                account_id,
                alert_type,
                severity,
                alert_message,
                status,
                correlation_id,
                created_at,
                acknowledged_at,
                resolved_at
            """,
            alert_id,
        )

    return dict(row) if row else None


async def evaluate_funding_alerts(
    *,
    tenant_code: str | None = None,
    burn_window_days: int = 30,
    buffer_days: int = 30,
    limit: int = 100,
    correlation_id: str | None = None,
) -> dict[str, Any]:
    forecasts = await list_funding_forecasts(
        tenant_code=tenant_code,
        burn_window_days=burn_window_days,
        buffer_days=buffer_days,
        limit=limit,
    )

    created_alerts: list[dict[str, Any]] = []

    for forecast in forecasts:
        alert = determine_forecast_alert(
            days_remaining=forecast["days_remaining"],
            available_balance=forecast["available_balance"],
            reserved_amount=forecast["reserved_amount"],
        )

        if not alert:
            continue

        alert_type, severity, alert_message = alert

        created_alert = await create_funding_alert(
            tenant_code=forecast["tenant_code"],
            account_id=forecast["account_id"],
            alert_type=alert_type,
            severity=severity,
            alert_message=alert_message,
            correlation_id=correlation_id,
        )

        created_alerts.append(created_alert)

    sponsor_forecasts = await list_sponsor_funding_forecasts(
        tenant_code=tenant_code,
        burn_window_days=burn_window_days,
        buffer_days=buffer_days,
        limit=limit,
    )
    settlement_forecasts = await list_settlement_exposure_forecasts(
        tenant_code=tenant_code,
        burn_window_days=burn_window_days,
        buffer_days=buffer_days,
        limit=limit,
    )

    forecast_risks: list[dict[str, Any]] = []

    for forecast in sponsor_forecasts:
        wallet_alert = determine_status_alert(
            forecast_status=forecast["wallet"]["forecast_status"],
            critical_type="SPONSOR_WALLET_CRITICAL",
            low_type="SPONSOR_WALLET_LOW",
            watch_type="SPONSOR_WALLET_WATCH",
            critical_message="Sponsor wallet is forecast to deplete in less than 7 days.",
            low_message="Sponsor wallet is forecast to deplete in less than 15 days.",
            watch_message="Sponsor wallet is forecast to deplete in less than 30 days.",
        )
        if wallet_alert:
            forecast_risks.append(
                _forecast_risk_item(
                    tenant_code=forecast["tenant_code"],
                    risk_scope="SPONSOR_WALLET",
                    risk_key=f"{forecast['tenant_code']}:{forecast['sponsor_code']}:{forecast['currency']}",
                    alert=wallet_alert,
                    forecast=forecast["wallet"],
                )
            )

        contract_alert = determine_status_alert(
            forecast_status=forecast["contracts"]["forecast_status"],
            critical_type="SPONSOR_CONTRACT_CRITICAL",
            low_type="SPONSOR_CONTRACT_LOW",
            watch_type="SPONSOR_CONTRACT_WATCH",
            critical_message="Sponsor contracts are forecast to exhaust in less than 7 days.",
            low_message="Sponsor contracts are forecast to exhaust in less than 15 days.",
            watch_message="Sponsor contracts are forecast to exhaust in less than 30 days.",
        )
        if contract_alert:
            forecast_risks.append(
                _forecast_risk_item(
                    tenant_code=forecast["tenant_code"],
                    risk_scope="SPONSOR_CONTRACT",
                    risk_key=f"{forecast['tenant_code']}:{forecast['sponsor_code']}:{forecast['currency']}",
                    alert=contract_alert,
                    forecast=forecast["contracts"],
                )
            )

    for forecast in settlement_forecasts:
        settlement_alert = determine_status_alert(
            forecast_status=forecast["forecast_status"],
            critical_type="SETTLEMENT_EXPOSURE_CRITICAL",
            low_type="SETTLEMENT_EXPOSURE_LOW",
            watch_type="SETTLEMENT_EXPOSURE_WATCH",
            critical_message="Settlement exposure is under critical forecast pressure.",
            low_message="Settlement exposure is under elevated forecast pressure.",
            watch_message="Settlement exposure is under watch forecast pressure.",
        )
        if settlement_alert:
            forecast_risks.append(
                _forecast_risk_item(
                    tenant_code=forecast["tenant_code"],
                    risk_scope="SETTLEMENT_EXPOSURE",
                    risk_key=f"{forecast['tenant_code']}:{forecast['provider_key']}:{forecast['currency']}",
                    alert=settlement_alert,
                    forecast=forecast,
                )
            )

    return {
        "status": "ok",
        "evaluated_count": len(forecasts),
        "alert_count": len(created_alerts),
        "items": created_alerts,
        "forecast_risk_count": len(forecast_risks),
        "forecast_risks": forecast_risks,
    }
