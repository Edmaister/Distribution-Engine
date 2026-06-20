import { useQuery } from "@tanstack/react-query";

import {
  getAdminPartnerReadiness,
  getAdminPartnerWebhookAlerts,
  getPartnerClients,
  getPartnerIntegration,
  getPartnerWebhookDeliveries,
  getPartnerWebhookSummary,
} from "./endpoints/partnerSeam";
import { queryKeys } from "./queryKeys";

export function usePartnerIntegrationWorkspace(refreshKey = 0) {
  return useQuery({
    queryKey: queryKeys.partnerIntegrationWorkspace(refreshKey),
    queryFn: loadPartnerIntegrationWorkspace,
  });
}

async function loadPartnerIntegrationWorkspace(): Promise<
  Record<string, unknown>
> {
  try {
    const payload = await getPartnerIntegration();
    return { ...(payload.integration ?? {}), mode: "partner" };
  } catch (error) {
    const status = getErrorStatus(error);
    if (status === 401 || status === 403) {
      return loadAdminPartnerIntegration();
    }
    throw error;
  }
}

async function loadAdminPartnerIntegration(): Promise<Record<string, unknown>> {
  const [clients, deliveries, summary, alerts, readiness] = await Promise.all([
    getPartnerClients(),
    getPartnerWebhookDeliveries(),
    getPartnerWebhookSummary(),
    getAdminPartnerWebhookAlerts(),
    getAdminPartnerReadiness(),
  ]);
  const deliveryRows = asArray(deliveries.items);
  const alertRows = asArray(alerts.items);
  const clientRows = asArray(clients.items);
  const exceptionRows = deliveryRows.filter((delivery) => {
    const status = formatDisplay(
      getNestedValue(delivery, ["delivery_status"], ""),
    );
    return ["FAILED", "CANCELLED"].includes(status);
  });

  return {
    mode: "admin",
    identity: {
      role: "Amplifi Admin",
      tenant_code: "All tenants",
    },
    clients: clientRows,
    webhooks: [],
    deliveries: deliveryRows,
    exceptions: exceptionRows,
    alerts: alertRows,
    summary: summary.summary ?? {},
    production_readiness: readiness.readiness ?? {},
    secret_readiness: {
      status:
        clients.available === false || deliveries.available === false
          ? "CHECK"
          : "READY",
      provider: "Admin partner seam",
      protection_mode: "Read only",
      config_status: "Admin overview",
      recommended_action:
        clients.available === false || deliveries.available === false
          ? clients.message ||
            deliveries.message ||
            "Partner admin endpoints need attention."
          : "Use a partner bearer session for partner-owned setup actions.",
    },
    guardrails: [
      "Amplifi Admin read-only overview uses /admin/partners endpoints.",
      "Partner-owned webhook creation and secret rotation require a partner bearer session.",
      "Client secrets and signing secrets are still only returned at creation or rotation time.",
    ],
  };
}

function getErrorStatus(error: unknown): number | null {
  if (error && typeof error === "object" && "status" in error) {
    const status = Number((error as { status?: unknown }).status);
    return Number.isFinite(status) ? status : null;
  }

  return null;
}

function asArray(value: unknown): Record<string, unknown>[] {
  return Array.isArray(value)
    ? value.filter((item): item is Record<string, unknown> =>
        Boolean(item && typeof item === "object"),
      )
    : [];
}

function getNestedValue(
  source: unknown,
  path: string[],
  fallback: unknown = undefined,
): unknown {
  let current = source;
  for (const segment of path) {
    if (!current || typeof current !== "object" || !(segment in current)) {
      return fallback;
    }
    current = (current as Record<string, unknown>)[segment];
  }
  return current ?? fallback;
}

function formatDisplay(value: unknown): string {
  if (value === null || value === undefined || value === "") {
    return "-";
  }
  if (typeof value === "boolean") {
    return value ? "Yes" : "No";
  }
  return String(value);
}
