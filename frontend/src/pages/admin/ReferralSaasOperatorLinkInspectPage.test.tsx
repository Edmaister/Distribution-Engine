import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import type { ReactElement } from "react";
import { createMemoryRouter, Outlet, RouterProvider } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { inspectReferralSaasOperatorLink } from "../../api/endpoints/referralSaasLinks";
import { ReferralSaasOperatorLinkInspectPage } from "./ReferralSaasOperatorLinkInspectPage";

vi.mock("../../api/endpoints/referralSaasLinks", () => ({
  inspectReferralSaasOperatorLink: vi.fn(),
}));

const mockedInspectReferralSaasOperatorLink = vi.mocked(inspectReferralSaasOperatorLink);

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

describe("ReferralSaasOperatorLinkInspectPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockedInspectReferralSaasOperatorLink.mockResolvedValue({
      status: "ok",
      inspection: {
        inspectionStatus: "LINKED",
        linkCode: {
          link_code_id: "campaign-track-1/referral-track-1",
          source_type: "CAMPAIGN_REFERRAL_LINK",
          source: "campaign_referral_links",
          tenant_code: "FNB",
          status: "LINKED",
          code: "REF123",
          campaign: {
            campaign_code: "CAMP001",
            campaign_track_id: "campaign-track-1",
          },
          participant: {
            participant_type: "REFERRER",
            participant_ref: "safe-referrer",
          },
          attribution: {
            referral_track_id: "referral-track-1",
            route_id: "route-1",
          },
          evidence: {
            raw_ucn: "9999999999",
            provider_payload: "raw-provider-payload",
          },
          missing_evidence: [{ code: "SOURCE_NOT_FOUND", message: "Source missing" }],
          source_warnings: [{ code: "COMPATIBILITY_SOURCE_ONLY", message: "Compatibility only" }],
          redactions: [{ field: "raw_ucn", reason: "sensitive" }],
          inspected_at: "2026-07-13T20:00:00Z",
        },
        nextDiagnostics: [
          {
            type: "CAMPAIGN_READINESS",
            label: "Inspect campaign readiness",
            targetRef: "CAMP001",
          },
          {
            type: "ATTRIBUTION_TRACE",
            label: "Inspect attribution trace",
            targetRef: "referral-track-1",
          },
        ],
      },
      operator_scope: {
        tenant_code: "FNB",
      },
      guardrail: "Read-only operator wrapper.",
    });
  });

  afterEach(() => {
    cleanup();
  });

  it("inspects referral codes through the product operator wrapper and renders safe fields", async () => {
    renderWorkspace(<ReferralSaasOperatorLinkInspectPage />);

    expect(screen.getByRole("heading", { name: "Operator link/code inspection" })).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Inspect link/code" }));

    await waitFor(() =>
      expect(mockedInspectReferralSaasOperatorLink).toHaveBeenCalledWith({
        tenantCode: "FNB",
        sourceType: "REFERRAL_CODE",
        linkCodeId: undefined,
        codeOrRef: "REF123",
        includeEvidence: false,
      }),
    );

    expect(await screen.findAllByText("LINKED")).not.toHaveLength(0);
    expect(screen.getByText("campaign_referral_links")).toBeInTheDocument();
    expect(screen.getAllByText("CAMP001").length).toBeGreaterThan(0);
    expect(screen.getAllByText("referral-track-1").length).toBeGreaterThan(0);
    expect(screen.getByText("Inspect attribution trace")).toBeInTheDocument();

    expect(screen.queryByText("9999999999")).not.toBeInTheDocument();
    expect(screen.queryByText("raw-provider-payload")).not.toBeInTheDocument();
  });

  it("uses linkCodeId when the operator selects a link-backed source", async () => {
    renderWorkspace(<ReferralSaasOperatorLinkInspectPage />);

    fireEvent.change(screen.getByLabelText("Source type"), {
      target: { value: "CAMPAIGN_REFERRAL_LINK" },
    });
    fireEvent.change(screen.getByLabelText("Link/code ID"), {
      target: { value: "campaign-track-1/referral-track-1" },
    });
    fireEvent.click(screen.getByLabelText(/Request source evidence/i));
    fireEvent.click(screen.getByRole("button", { name: "Inspect link/code" }));

    await waitFor(() =>
      expect(mockedInspectReferralSaasOperatorLink).toHaveBeenCalledWith({
        tenantCode: "FNB",
        sourceType: "CAMPAIGN_REFERRAL_LINK",
        linkCodeId: "campaign-track-1/referral-track-1",
        codeOrRef: undefined,
        includeEvidence: true,
      }),
    );
  });

  it("renders missing evidence, warnings, redactions, and next diagnostics", async () => {
    renderWorkspace(<ReferralSaasOperatorLinkInspectPage />);

    fireEvent.click(screen.getByRole("button", { name: "Inspect link/code" }));

    expect(await screen.findByText("SOURCE_NOT_FOUND")).toBeInTheDocument();
    expect(screen.getByText("COMPATIBILITY_SOURCE_ONLY")).toBeInTheDocument();
    expect(screen.getByText("raw_ucn")).toBeInTheDocument();
    expect(screen.getByText("CAMPAIGN_READINESS")).toBeInTheDocument();

    const summaryPanel = panelByHeading("Source summary");
    expect(summaryPanel.queryByText("provider_payload")).not.toBeInTheDocument();
  });

  it("keeps mutation, replay, support-case, and money actions absent", () => {
    renderWorkspace(<ReferralSaasOperatorLinkInspectPage />);

    expect(screen.queryByRole("button", { name: /reissue/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /revoke/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /expire/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /repair/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /retry/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /replay/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /support case/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /reward/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /settle/i })).not.toBeInTheDocument();
  });

  it("links to adjacent read-only Referral SaaS support surfaces", () => {
    renderWorkspace(<ReferralSaasOperatorLinkInspectPage />);

    expect(screen.getByRole("link", { name: /Support workflow hub/ })).toHaveAttribute(
      "href",
      "/admin/referral-saas/support",
    );
    expect(screen.getByRole("link", { name: /Campaign readiness/ })).toHaveAttribute(
      "href",
      "/admin/referral-saas/campaigns",
    );
    expect(screen.getByRole("link", { name: /Attribution trace/ })).toHaveAttribute(
      "href",
      "/admin/referral-saas/attribution-trace",
    );
    expect(screen.getByRole("link", { name: /Progress\/status/ })).toHaveAttribute(
      "href",
      "/admin/referral-saas/progress-status",
    );
    expect(screen.getByRole("link", { name: /Link\/code workflow/ })).toHaveAttribute(
      "href",
      "/admin/referral-saas/link-codes",
    );
    expect(screen.getByRole("link", { name: /Referral SaaS reports/ })).toHaveAttribute(
      "href",
      "/admin/referral-saas/reports",
    );
  });
});
