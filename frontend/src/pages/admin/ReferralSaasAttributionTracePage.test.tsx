import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import type { ReactElement } from "react";
import { createMemoryRouter, Outlet, RouterProvider } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { inspectReferralSaasOperatorAttributionTrace } from "../../api/endpoints/referralSaasLinks";
import { ReferralSaasAttributionTracePage } from "./ReferralSaasAttributionTracePage";

vi.mock("../../api/endpoints/referralSaasLinks", () => ({
  inspectReferralSaasOperatorAttributionTrace: vi.fn(),
}));

const mockedInspectReferralSaasOperatorAttributionTrace = vi.mocked(
  inspectReferralSaasOperatorAttributionTrace,
);

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

function panelByHeading(heading: string) {
  const headingElement = screen.getByRole("heading", { name: heading });
  const panel = headingElement.closest(".panel");
  if (!panel) {
    throw new Error(`${heading} panel was not rendered`);
  }
  return within(panel as HTMLElement);
}

describe("ReferralSaasAttributionTracePage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockedInspectReferralSaasOperatorAttributionTrace.mockResolvedValue({
      status: "ok",
      attributionTrace: {
        traceStatus: "PARTIAL",
        traceId: "outcome:referral_track_id:11111111-1111-4111-8111-111111111111",
        lookup: {
          type: "REFERRAL_TRACK_ID",
          value: "11111111-1111-4111-8111-111111111111",
        },
        tenantCode: "FNB",
        generatedAt: "2026-07-14T00:00:00Z",
        sections: {
          outcome: {
            referral_track_id: "11111111-1111-4111-8111-111111111111",
            status: "ACCOUNT_OPENED",
          },
          attribution: {
            campaign_links: [
              {
                campaign_code: "CAMP001",
                campaign_track_id: "campaign-track-1",
                referral_track_id: "11111111-1111-4111-8111-111111111111",
              },
            ],
            route_links: [
              {
                route_id: "route-1",
                route_referral_link_id: "route-link-1",
              },
            ],
          },
          participants: {
            items: [
              {
                participant_type: "REFERRER",
                safe_display_ref: "safe-referrer",
              },
            ],
          },
          events: {
            items: [
              {
                event_type: "ACCOUNT_OPENED",
                source_event_id: "event-1",
              },
            ],
          },
          audit: {
            items: [
              {
                action_type: "TRACE_READ",
                audit_id: "audit-1",
              },
            ],
          },
          reward: {
            items: [{ amount: "999.00", wallet_ref: "wallet-secret" }],
          },
          funding: {
            items: [{ amount: "999.00", funding_ref: "funding-secret" }],
          },
          webhooks: {
            items: [{ payload: "raw-provider-payload" }],
          },
        },
        missingEvidence: [
          {
            code: "ATTRIBUTION_EVENT_MISSING",
            message: "Expected attribution event evidence was not found.",
          },
        ],
        sourceWarnings: [
          {
            code: "SOURCE_DELAYED",
            message: "One evidence source was delayed.",
          },
        ],
        redactions: [{ field: "referrer_ucn", reason: "sensitive" }],
        nextDiagnostics: [
          {
            type: "CAMPAIGN_READINESS",
            label: "Inspect campaign readiness",
            targetRef: "CAMP001",
          },
        ],
      },
      operator_scope: {
        tenant_code: "FNB",
      },
      guardrail: "Read-only operator attribution trace wrapper.",
    });
  });

  afterEach(() => {
    cleanup();
  });

  it("calls the product attribution trace wrapper and renders safe trace evidence", async () => {
    renderWorkspace(<ReferralSaasAttributionTracePage />);

    expect(screen.getByRole("heading", { name: "Operator attribution trace" })).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Inspect trace" }));

    await waitFor(() =>
      expect(mockedInspectReferralSaasOperatorAttributionTrace).toHaveBeenCalledWith({
        tenantCode: "FNB",
        referralTrackId: "11111111-1111-4111-8111-111111111111",
        includeSections: ["attribution", "participants", "events", "audit"],
      }),
    );

    expect(await screen.findAllByText("PARTIAL")).not.toHaveLength(0);
    expect(screen.getAllByText("ACCOUNT_OPENED").length).toBeGreaterThan(0);
    expect(screen.getAllByText("CAMP001").length).toBeGreaterThan(0);
    expect(screen.getByText("route-1")).toBeInTheDocument();
    expect(screen.getAllByText("ACCOUNT_OPENED").length).toBeGreaterThan(0);
    expect(screen.getByText("TRACE_READ")).toBeInTheDocument();
    expect(screen.getByText("ATTRIBUTION_EVENT_MISSING")).toBeInTheDocument();
    expect(screen.getByText("SOURCE_DELAYED")).toBeInTheDocument();

    expect(screen.queryByText("999.00")).not.toBeInTheDocument();
    expect(screen.queryByText("wallet-secret")).not.toBeInTheDocument();
    expect(screen.queryByText("funding-secret")).not.toBeInTheDocument();
    expect(screen.queryByText("raw-provider-payload")).not.toBeInTheDocument();
  });

  it("lets operators narrow safe first-launch sections without adding money sections", async () => {
    renderWorkspace(<ReferralSaasAttributionTracePage />);

    fireEvent.click(screen.getByLabelText("Participants"));
    fireEvent.click(screen.getByLabelText("Events"));
    fireEvent.click(screen.getByRole("button", { name: "Inspect trace" }));

    await waitFor(() =>
      expect(mockedInspectReferralSaasOperatorAttributionTrace).toHaveBeenCalledWith({
        tenantCode: "FNB",
        referralTrackId: "11111111-1111-4111-8111-111111111111",
        includeSections: ["attribution", "audit"],
      }),
    );

    expect(screen.queryByLabelText(/reward/i)).not.toBeInTheDocument();
    expect(screen.queryByLabelText(/funding/i)).not.toBeInTheDocument();
    expect(screen.queryByLabelText(/settlement/i)).not.toBeInTheDocument();
    expect(screen.queryByLabelText(/webhook/i)).not.toBeInTheDocument();
  });

  it("keeps mutation, replay, support-case, and money actions absent", () => {
    renderWorkspace(<ReferralSaasAttributionTracePage />);

    expect(screen.queryByRole("button", { name: /override/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /repair/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /retry/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /replay/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /support case/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /reward/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /settle/i })).not.toBeInTheDocument();
  });

  it("links to adjacent read-only Referral SaaS support surfaces", () => {
    renderWorkspace(<ReferralSaasAttributionTracePage />);

    expect(screen.getByRole("link", { name: /Support workflow hub/ })).toHaveAttribute(
      "href",
      "/admin/referral-saas/support",
    );
    expect(screen.getByRole("link", { name: /Link\/code inspection/ })).toHaveAttribute(
      "href",
      "/admin/referral-saas/operator-links",
    );
    expect(screen.getByRole("link", { name: /Progress\/status/ })).toHaveAttribute(
      "href",
      "/admin/referral-saas/progress-status",
    );
    expect(screen.getByRole("link", { name: /Campaign readiness/ })).toHaveAttribute(
      "href",
      "/admin/referral-saas/campaigns",
    );
    expect(screen.getByRole("link", { name: /Referral SaaS reports/ })).toHaveAttribute(
      "href",
      "/admin/referral-saas/reports",
    );
  });

  it("does not render hidden money sections in the attribution link panel", async () => {
    renderWorkspace(<ReferralSaasAttributionTracePage />);

    fireEvent.click(screen.getByRole("button", { name: "Inspect trace" }));

    const attributionPanel = await waitFor(() => panelByHeading("Attribution links"));
    expect(attributionPanel.queryByText("reward")).not.toBeInTheDocument();
    expect(attributionPanel.queryByText("funding")).not.toBeInTheDocument();
    expect(attributionPanel.queryByText("webhooks")).not.toBeInTheDocument();
  });
});
