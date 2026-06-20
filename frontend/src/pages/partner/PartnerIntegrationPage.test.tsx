import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type { ReactElement } from "react";
import { createMemoryRouter, Outlet, RouterProvider } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  createPartnerClient,
  createPartnerWebhook,
  exportPartnerWebhookDeadLetters,
  getAdminPartnerReadiness,
  getAdminPartnerWebhookAlerts,
  getPartnerClients,
  getPartnerIntegration,
  getPartnerWebhookDeliveries,
  getPartnerWebhookSummary,
  retryPartnerWebhookDelivery,
  rotatePartnerLegacyWebhookSecrets,
  rotatePartnerWebhookSecret,
} from "../../api/endpoints/partnerSeam";
import { PartnerIntegrationPage } from "./PartnerIntegrationPage";

vi.mock("../../api/endpoints/partnerSeam", () => ({
  createPartnerClient: vi.fn(),
  createPartnerWebhook: vi.fn(),
  exportPartnerWebhookDeadLetters: vi.fn(),
  getAdminPartnerReadiness: vi.fn(),
  getAdminPartnerWebhookAlerts: vi.fn(),
  getPartnerClients: vi.fn(),
  getPartnerIntegration: vi.fn(),
  getPartnerWebhookDeliveries: vi.fn(),
  getPartnerWebhookSummary: vi.fn(),
  retryPartnerWebhookDelivery: vi.fn(),
  rotatePartnerLegacyWebhookSecrets: vi.fn(),
  rotatePartnerWebhookSecret: vi.fn(),
}));

const mockedCreatePartnerClient = vi.mocked(createPartnerClient);
const mockedCreatePartnerWebhook = vi.mocked(createPartnerWebhook);
const mockedExportPartnerWebhookDeadLetters = vi.mocked(exportPartnerWebhookDeadLetters);
const mockedGetAdminPartnerReadiness = vi.mocked(getAdminPartnerReadiness);
const mockedGetAdminPartnerWebhookAlerts = vi.mocked(getAdminPartnerWebhookAlerts);
const mockedGetPartnerClients = vi.mocked(getPartnerClients);
const mockedGetPartnerIntegration = vi.mocked(getPartnerIntegration);
const mockedGetPartnerWebhookDeliveries = vi.mocked(getPartnerWebhookDeliveries);
const mockedGetPartnerWebhookSummary = vi.mocked(getPartnerWebhookSummary);
const mockedRetryPartnerWebhookDelivery = vi.mocked(retryPartnerWebhookDelivery);
const mockedRotatePartnerLegacyWebhookSecrets = vi.mocked(rotatePartnerLegacyWebhookSecrets);
const mockedRotatePartnerWebhookSecret = vi.mocked(rotatePartnerWebhookSecret);

function renderWorkspace(ui: ReactElement) {
  const client = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });
  const router = createMemoryRouter([
    {
      path: "/",
      element: <Outlet context={{ refreshKey: 0 }} />,
      children: [{ index: true, element: ui }],
    },
  ]);

  return render(
    <QueryClientProvider client={client}>
      <RouterProvider router={router} />
    </QueryClientProvider>,
  );
}

function fieldByLabel(label: string) {
  return screen.getByLabelText(label, { selector: "input" }) as HTMLInputElement;
}

function panelByHeading(container: HTMLElement, heading: string) {
  const headingElement = screen.getByRole("heading", { name: heading });
  const panel = headingElement.closest(".panel");
  if (!panel) {
    throw new Error(`${heading} panel was not rendered`);
  }
  return within(panel as HTMLElement);
}

function partnerIntegration() {
  return {
    identity: { tenant_code: "FNB", client_id: "CLIENT-1", role: "PARTNER" },
    clients: [
      {
        client_id: "CLIENT-1",
        client_name: "FNB Rewards Partner",
        scopes: ["events:write", "referrals:read"],
        status: "ACTIVE",
      },
    ],
    webhooks: [
      {
        webhook_id: "WEBHOOK-1",
        event_type: "OUTCOME_COMPLETED",
        target_url: "https://partner.example/webhooks/outcomes",
        status: "ACTIVE",
      },
    ],
    deliveries: [
      {
        delivery_id: "DELIVERY-1",
        event_type: "OUTCOME_COMPLETED",
        delivery_status: "FAILED",
        attempt_count: 3,
        last_error: "HTTP 500 from partner endpoint",
      },
    ],
    exceptions: [
      {
        delivery_id: "DELIVERY-1",
        event_type: "OUTCOME_COMPLETED",
        delivery_status: "FAILED",
        attempt_count: 3,
        last_error: "HTTP 500 from partner endpoint",
      },
    ],
    alerts: [
      {
        webhook_id: "WEBHOOK-1",
        event_type: "OUTCOME_COMPLETED",
        target_url: "https://partner.example/webhooks/outcomes",
        failed_count: 3,
        max_attempt_count: 3,
        severity: "WARNING",
        recommended_action: "Confirm the endpoint is healthy before retrying.",
      },
    ],
    summary: { status: "CHECK", sent_count: 8, pending_count: 1, failed_count: 1 },
    secret_readiness: {
      status: "CHECK",
      provider: "Partner seam",
      protection_mode: "Hashed",
      config_status: "Ready",
      legacy_plaintext_subscriptions: 1,
      rotation_status: "ACTION_REQUIRED",
      recommended_action: "Rotate legacy plaintext signing secrets.",
    },
    production_readiness: {
      code_status: "READY",
      deployment_status: "READY",
      app_env: "test",
      attention_count: 0,
      checks: [
        {
          code: "SIGNED_WEBHOOKS",
          label: "Signed webhook callbacks",
          status: "READY",
          recommended_action: "No action required.",
        },
      ],
    },
    guardrails: ["Secrets are shown once and then hidden.", "Retries preserve delivery evidence."],
  };
}

function mockPartnerData(integration = partnerIntegration()) {
  mockedGetPartnerIntegration.mockResolvedValue({ status: "ok", integration });
  mockedGetAdminPartnerReadiness.mockResolvedValue({ status: "ok", readiness: {} });
  mockedGetAdminPartnerWebhookAlerts.mockResolvedValue({ status: "ok", items: [] });
  mockedGetPartnerClients.mockResolvedValue({ status: "ok", items: [] });
  mockedGetPartnerWebhookDeliveries.mockResolvedValue({ status: "ok", items: [] });
  mockedGetPartnerWebhookSummary.mockResolvedValue({ status: "ok", summary: {} });
  mockedCreatePartnerClient.mockResolvedValue({
    status: "ok",
    client: { client_id: "CLIENT-2", client_secret: "new-client-secret" },
  });
  mockedCreatePartnerWebhook.mockResolvedValue({
    status: "ok",
    webhook: { webhook_id: "WEBHOOK-2", signing_secret: "new-webhook-secret" },
  });
  mockedRotatePartnerWebhookSecret.mockResolvedValue({
    status: "ok",
    webhook: { webhook_id: "WEBHOOK-1", signing_secret: "rotated-secret" },
  });
  mockedRotatePartnerLegacyWebhookSecrets.mockResolvedValue({
    status: "ok",
    rotated_count: 1,
    items: [{ webhook_id: "WEBHOOK-1", status: "ROTATED" }],
  });
  mockedRetryPartnerWebhookDelivery.mockResolvedValue({ status: "queued", delivery_id: "DELIVERY-1" });
  mockedExportPartnerWebhookDeadLetters.mockResolvedValue({
    status: "ok",
    export: {
      filename: "partner-dead-letters.csv",
      count: 1,
      csv: "delivery_id,status\nDELIVERY-1,FAILED",
      guardrail: "Export contains failed and cancelled delivery evidence only.",
    },
  });
}

describe("PartnerIntegrationPage", () => {
  beforeEach(() => {
    mockPartnerData();
    vi.spyOn(URL, "createObjectURL").mockReturnValue("blob:partner-dead-letters");
    vi.spyOn(URL, "revokeObjectURL").mockImplementation(() => undefined);
    vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(() => undefined);
  });

  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
  });

  it("loads partner integration health, readiness, and delivery posture", async () => {
    const { container } = renderWorkspace(<PartnerIntegrationPage />);

    expect(await screen.findByRole("heading", { name: "Integration Health" })).toBeInTheDocument();
    expect(screen.getByText("FNB Rewards Partner")).toBeInTheDocument();
    expect(screen.getByText("Signed webhook callbacks")).toBeInTheDocument();
    expect(screen.getByText("Rotate legacy plaintext signing secrets.")).toBeInTheDocument();
    expect(screen.getByText("Confirm the endpoint is healthy before retrying.")).toBeInTheDocument();
    expect(panelByHeading(container, "Webhook delivery").getByText("https://partner.example/webhooks/outcomes")).toBeInTheDocument();
    expect(mockedGetPartnerIntegration).toHaveBeenCalledTimes(1);
  });

  it("creates partner-owned webhooks and exposes the one-time signing secret feedback", async () => {
    renderWorkspace(<PartnerIntegrationPage />);

    await screen.findByRole("heading", { name: "Integration Health" });
    fireEvent.change(fieldByLabel("Endpoint"), { target: { value: "https://partner.example/webhooks/new" } });
    fireEvent.click(screen.getByRole("button", { name: /^create webhook$/i }));

    await waitFor(() => {
      expect(mockedCreatePartnerWebhook).toHaveBeenCalledWith({
        eventType: "OUTCOME_COMPLETED",
        targetUrl: "https://partner.example/webhooks/new",
      });
    });
    expect(await screen.findByText("Webhook created")).toBeInTheDocument();
    expect(screen.getByText("new-webhook-secret")).toBeInTheDocument();
  });

  it("rotates webhook secrets, rotates legacy records, and retries failed deliveries", async () => {
    const { container } = renderWorkspace(<PartnerIntegrationPage />);

    await screen.findByRole("heading", { name: "Integration Health" });
    fireEvent.click(panelByHeading(container, "Webhook delivery").getByRole("button", { name: /^rotate secret$/i }));
    await waitFor(() => expect(mockedRotatePartnerWebhookSecret).toHaveBeenCalledWith("WEBHOOK-1"));
    expect(await screen.findByText("rotated-secret")).toBeInTheDocument();

    fireEvent.click(panelByHeading(container, "Secret readiness").getByRole("button", { name: /^rotate legacy$/i }));
    await waitFor(() => expect(mockedRotatePartnerLegacyWebhookSecrets).toHaveBeenCalledWith(25));
    expect(await screen.findByText("Legacy secrets rotated")).toBeInTheDocument();

    fireEvent.click(panelByHeading(container, "Delivery exceptions").getByRole("button", { name: /^retry$/i }));
    await waitFor(() => expect(mockedRetryPartnerWebhookDelivery).toHaveBeenCalledWith("DELIVERY-1"));
    expect(await screen.findByText("Delivery queued for retry")).toBeInTheDocument();
  });

  it("exports dead-letter delivery evidence as a guarded CSV", async () => {
    const { container } = renderWorkspace(<PartnerIntegrationPage />);

    await screen.findByRole("heading", { name: "Integration Health" });
    fireEvent.click(panelByHeading(container, "Delivery exceptions").getByRole("button", { name: /^export csv$/i }));

    await waitFor(() => expect(mockedExportPartnerWebhookDeadLetters).toHaveBeenCalledWith(500));
    expect(await screen.findByText("Dead-letter export prepared")).toBeInTheDocument();
    expect(screen.getByText("partner-dead-letters.csv")).toBeInTheDocument();
    expect(URL.createObjectURL).toHaveBeenCalledWith(expect.any(Blob));
  });

  it("creates tenant-scoped client credentials when the session is not already client-scoped", async () => {
    mockPartnerData({ ...partnerIntegration(), identity: { tenant_code: "FNB", client_id: "", role: "PARTNER" }, clients: [] });
    renderWorkspace(<PartnerIntegrationPage />);

    await screen.findByRole("heading", { name: "Integration Health" });
    fireEvent.change(fieldByLabel("Client name"), { target: { value: "New integration client" } });
    fireEvent.change(fieldByLabel("Scopes"), { target: { value: "events:write, referrals:read" } });
    fireEvent.click(screen.getByRole("button", { name: /^create client$/i }));

    await waitFor(() => {
      expect(mockedCreatePartnerClient).toHaveBeenCalledWith({
        clientName: "New integration client",
        scopes: ["events:write", "referrals:read"],
      });
    });
    expect(await screen.findByText("Client created")).toBeInTheDocument();
    expect(screen.getByText("new-client-secret")).toBeInTheDocument();
  });
});
