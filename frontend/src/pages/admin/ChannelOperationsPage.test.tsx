import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import type { ReactElement } from "react";
import { createMemoryRouter, Outlet, RouterProvider } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  getAdminChannelAudit,
  getAdminChannelDeliveries,
  getAdminChannelReadiness,
  retryAdminChannelDelivery,
} from "../../api/endpoints/adminChannels";
import { ChannelOperationsPage } from "./ChannelOperationsPage";

vi.mock("../../api/endpoints/adminChannels", () => ({
  getAdminChannelAudit: vi.fn(),
  getAdminChannelDeliveries: vi.fn(),
  getAdminChannelReadiness: vi.fn(),
  retryAdminChannelDelivery: vi.fn(),
}));

const mockedGetAdminChannelAudit = vi.mocked(getAdminChannelAudit);
const mockedGetAdminChannelDeliveries = vi.mocked(getAdminChannelDeliveries);
const mockedGetAdminChannelReadiness = vi.mocked(getAdminChannelReadiness);
const mockedRetryAdminChannelDelivery = vi.mocked(retryAdminChannelDelivery);

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

function mockChannelOperations() {
  mockedGetAdminChannelReadiness.mockResolvedValue({
    status: "ok",
    readiness: {
      status: "READY",
      summary: { ready_count: 2, count: 3 },
      items: [
        {
          channel_code: "WHATSAPP",
          label: "WhatsApp",
          status: "READY",
          recommended_action: "Provider connection is configured.",
        },
        {
          channel_code: "SMS",
          label: "SMS",
          status: "READY",
          recommended_action: "Provider connection is configured.",
        },
      ],
    },
  });
  mockedGetAdminChannelDeliveries.mockResolvedValue({
    status: "ok",
    deliveries: {
      summary: {
        count: 2,
        queued: 0,
        sent: 1,
        delivered: 0,
        failed: 1,
        dead_lettered: 0,
      },
      items: [
        {
          delivery_id: "CHD-RETRY",
          status: "FAILED",
          channel_code: "WHATSAPP",
          recipient_ref: "recipient:abc123",
          attempt_count: 1,
          max_attempts: 3,
          retryable: true,
          next_retry_at: 1_800_000_000,
        },
        {
          delivery_id: "CHD-SENT",
          status: "SENT",
          channel_code: "SMS",
          recipient_ref: "recipient:def456",
          attempt_count: 1,
          max_attempts: 3,
          retryable: false,
        },
      ],
    },
  });
  mockedGetAdminChannelAudit.mockResolvedValue({
    status: "ok",
    audit: {
      items: [
        {
          audit_id: "CHA-1",
          delivery_id: "CHD-RETRY",
          event_type: "FAILED",
          channel_code: "WHATSAPP",
          recipient_ref: "recipient:abc123",
        },
      ],
    },
  });
  mockedRetryAdminChannelDelivery.mockResolvedValue({
    status: "sent",
    retry: {
      status: "SENT",
      delivery: { delivery_id: "CHD-RETRY", status: "SENT" },
    },
  });
}

function panelByHeading(heading: string) {
  const headingElement = screen.getByRole("heading", { name: heading });
  const panel = headingElement.closest(".panel");
  if (!panel) {
    throw new Error(`${heading} panel was not rendered`);
  }
  return within(panel as HTMLElement);
}

describe("ChannelOperationsPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockChannelOperations();
  });

  afterEach(() => {
    cleanup();
  });

  it("loads channel readiness, deliveries, exceptions, and audit evidence", async () => {
    renderWorkspace(<ChannelOperationsPage />);

    expect(
      await screen.findByRole("heading", { name: "Channel Operations" }),
    ).toBeInTheDocument();
    expect(screen.getByText("2/3")).toBeInTheDocument();
    expect(screen.getAllByText("recipient:abc123").length).toBeGreaterThan(0);
    expect(screen.queryByText("+27123456789")).not.toBeInTheDocument();
    expect(panelByHeading("Exception queue").getByText("CHD-RETRY")).toBeInTheDocument();
    expect(panelByHeading("Audit evidence").getByText("FAILED")).toBeInTheDocument();
  });

  it("filters delivery records by lifecycle status", async () => {
    renderWorkspace(<ChannelOperationsPage />);

    await screen.findByRole("heading", { name: "Channel Operations" });
    fireEvent.click(screen.getByRole("button", { name: "Failed" }));

    await waitFor(() =>
      expect(mockedGetAdminChannelDeliveries).toHaveBeenLastCalledWith("FAILED", 50),
    );
  });

  it("retries a recoverable failed channel delivery", async () => {
    renderWorkspace(<ChannelOperationsPage />);

    await screen.findByRole("heading", { name: "Channel Operations" });
    const deliveryPanel = panelByHeading("Delivery operations");
    fireEvent.click(deliveryPanel.getAllByRole("button", { name: "Retry" })[0]);

    await waitFor(() =>
      expect(mockedRetryAdminChannelDelivery).toHaveBeenCalledWith("CHD-RETRY"),
    );
    expect(
      await screen.findByText("Retry completed with status SENT."),
    ).toBeInTheDocument();
  });
});
