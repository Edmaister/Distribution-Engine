import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import type { ReactElement } from "react";
import { createMemoryRouter, Outlet, RouterProvider } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { inspectReferralSaasOperatorProgressStatus } from "../../api/endpoints/referralSaasLinks";
import { ReferralSaasProgressStatusPage } from "./ReferralSaasProgressStatusPage";

vi.mock("../../api/endpoints/referralSaasLinks", () => ({
  inspectReferralSaasOperatorProgressStatus: vi.fn(),
}));

const mockedInspectReferralSaasOperatorProgressStatus = vi.mocked(
  inspectReferralSaasOperatorProgressStatus,
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

describe("ReferralSaasProgressStatusPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockedInspectReferralSaasOperatorProgressStatus.mockResolvedValue({
      status: "ok",
      progressStatus: {
        lookup: {
          type: "REFERRAL_TRACK_ID",
          value: "11111111-1111-4111-8111-111111111111",
        },
        tenantCode: "FNB",
        viewerRole: "referrer",
        progress: {
          referralTrackId: "11111111-1111-4111-8111-111111111111",
          status: "ACCOUNT_OPENED",
          isComplete: false,
          progressPercent: 60,
          progressBand: "ACTIVE",
          displayStatus: "Account opened",
          nextMilestone: "ACCOUNT_ACTIVATED",
          referrerUcn: "900010",
        },
        safeStatus: {
          product_status: "IN_PROGRESS",
          product_label: "In progress",
          summary: "Your referral is in progress.",
          what_happened: "The referral was validated and progress evidence was received.",
          what_happens_next: "The next milestone will update this status.",
          action_required: false,
          action_category: "NONE",
          terminal: false,
          source_confidence: "HIGH",
        },
        missingEvidence: [
          {
            code: "PROGRESS_EVENT_DELAYED",
            message: "Expected progress evidence has not arrived yet.",
          },
        ],
        redactions: [{ field: "referrer_ucn", reason: "sensitive" }],
        nextDiagnostics: [
          {
            type: "NEXT_MILESTONE",
            label: "Review next progress milestone",
            targetRef: "ACCOUNT_ACTIVATED",
          },
          {
            type: "ATTRIBUTION_TRACE",
            label: "Inspect attribution trace",
            targetRef: "11111111-1111-4111-8111-111111111111",
          },
        ],
      },
      operator_scope: {
        tenant_code: "FNB",
      },
      guardrail: "Read-only operator progress/status wrapper.",
    });
  });

  afterEach(() => {
    cleanup();
  });

  it("calls the product progress/status wrapper and renders safe evidence", async () => {
    renderWorkspace(<ReferralSaasProgressStatusPage />);

    expect(screen.getByRole("heading", { name: "Operator progress/status" })).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Inspect progress" }));

    await waitFor(() =>
      expect(mockedInspectReferralSaasOperatorProgressStatus).toHaveBeenCalledWith({
        tenantCode: "FNB",
        referralTrackId: "11111111-1111-4111-8111-111111111111",
        viewerRole: "referrer",
      }),
    );

    expect(await screen.findAllByText("IN_PROGRESS")).not.toHaveLength(0);
    expect(screen.getAllByText("ACCOUNT_OPENED").length).toBeGreaterThan(0);
    expect(screen.getAllByText("ACCOUNT_ACTIVATED").length).toBeGreaterThan(0);
    expect(screen.getByText("Your referral is in progress.")).toBeInTheDocument();
    expect(screen.getByText("PROGRESS_EVENT_DELAYED")).toBeInTheDocument();
    expect(screen.getByText("NEXT_MILESTONE")).toBeInTheDocument();
    expect(screen.getByText("ATTRIBUTION_TRACE")).toBeInTheDocument();

    expect(screen.queryByText("900010")).not.toBeInTheDocument();
    expect(screen.queryByText("wallet-secret")).not.toBeInTheDocument();
    expect(screen.queryByText("funding-secret")).not.toBeInTheDocument();
  });

  it("lets operators choose the safe viewer projection", async () => {
    renderWorkspace(<ReferralSaasProgressStatusPage />);

    fireEvent.change(screen.getByLabelText("Viewer projection"), {
      target: { value: "operator" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Inspect progress" }));

    await waitFor(() =>
      expect(mockedInspectReferralSaasOperatorProgressStatus).toHaveBeenCalledWith({
        tenantCode: "FNB",
        referralTrackId: "11111111-1111-4111-8111-111111111111",
        viewerRole: "operator",
      }),
    );
  });

  it("keeps progress mutation, replay, support-case, and money actions absent", () => {
    renderWorkspace(<ReferralSaasProgressStatusPage />);

    expect(screen.queryByRole("button", { name: /ingest/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /correct/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /repair/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /retry/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /replay/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /support case/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /reward/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /settle/i })).not.toBeInTheDocument();
  });

  it("links to adjacent read-only Referral SaaS support surfaces", () => {
    renderWorkspace(<ReferralSaasProgressStatusPage />);

    expect(screen.getByRole("link", { name: /Attribution trace/ })).toHaveAttribute(
      "href",
      "/admin/referral-saas/attribution-trace",
    );
    expect(screen.getByRole("link", { name: /Link\/code inspection/ })).toHaveAttribute(
      "href",
      "/admin/referral-saas/operator-links",
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

  it("keeps sensitive fields confined to the redaction panel", async () => {
    renderWorkspace(<ReferralSaasProgressStatusPage />);

    fireEvent.click(screen.getByRole("button", { name: "Inspect progress" }));

    const redactionPanel = await waitFor(() => panelByHeading("Redactions"));
    expect(redactionPanel.getByText("referrer_ucn")).toBeInTheDocument();
    expect(screen.queryByText("900010")).not.toBeInTheDocument();
  });
});
