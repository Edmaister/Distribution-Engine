import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import type { ReactElement } from "react";
import { createMemoryRouter, Outlet, RouterProvider } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  captureConsumerRefereeUcn,
  issueConsumerReferralCode,
  validateConsumerReferralCode,
} from "../../api/endpoints/consumerPortal";
import { ReferralSaasLinkCodeWorkflowPage } from "./ReferralSaasLinkCodeWorkflowPage";

vi.mock("../../api/endpoints/consumerPortal", () => ({
  issueConsumerReferralCode: vi.fn(),
  validateConsumerReferralCode: vi.fn(),
  captureConsumerRefereeUcn: vi.fn(),
}));

const mockedIssueConsumerReferralCode = vi.mocked(issueConsumerReferralCode);
const mockedValidateConsumerReferralCode = vi.mocked(validateConsumerReferralCode);
const mockedCaptureConsumerRefereeUcn = vi.mocked(captureConsumerRefereeUcn);

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

describe("ReferralSaasLinkCodeWorkflowPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockedIssueConsumerReferralCode.mockResolvedValue({
      referral_code: "REF123",
      gaming_handle: "edwin",
      created: true,
      message: "Referral code created",
      referrer_ucn: "9999999999",
      referrer_ucn_hash: "raw-response-hash",
    });
    mockedValidateConsumerReferralCode.mockResolvedValue({
      valid: true,
      validation_outcome: "VALIDATED",
      referral_track_id: "track-1",
      alias: "customer-alias",
      message: "Referral code validated",
      attributes: {
        tenant_code: "FNB",
        referrer_ucn: "9999999999",
      },
    });
    mockedCaptureConsumerRefereeUcn.mockResolvedValue({
      status: "ok",
      message: "Referee UCN captured",
    });
  });

  afterEach(() => {
    cleanup();
  });

  it("issues a referral code through the existing primitive and renders safe result fields", async () => {
    renderWorkspace(<ReferralSaasLinkCodeWorkflowPage />);

    expect(screen.getByRole("heading", { name: "Link and code workflow" })).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText("Preferred handle"), { target: { value: "edwin" } });
    fireEvent.click(screen.getByRole("button", { name: "Issue code" }));

    await waitFor(() =>
      expect(mockedIssueConsumerReferralCode).toHaveBeenCalledWith({
        referrerUcn: "5555555555",
        tenantCode: "FNB",
        sticker: "QR001",
        segment: "PERSONAL",
        preferredHandle: "edwin",
        acceptedTerms: true,
      }),
    );
    expect(await screen.findByText("REF123")).toBeInTheDocument();
    expect(screen.getByText("edwin")).toBeInTheDocument();
    expect(screen.getByText("Referral code created")).toBeInTheDocument();

    const issuePanel = panelByHeading("Issue or reuse code");
    expect(issuePanel.queryByText("9999999999")).not.toBeInTheDocument();
    expect(issuePanel.queryByText("raw-response-hash")).not.toBeInTheDocument();
  });

  it("validates the issued referral code and redacts internal validation attributes", async () => {
    renderWorkspace(<ReferralSaasLinkCodeWorkflowPage />);

    fireEvent.click(screen.getByRole("button", { name: "Issue code" }));
    await screen.findByText("REF123");
    fireEvent.click(screen.getByRole("button", { name: "Validate code" }));

    await waitFor(() =>
      expect(mockedValidateConsumerReferralCode).toHaveBeenCalledWith({
        tenantCode: "FNB",
        referralCode: "REF123",
        acceptedTerms: true,
        alias: "customer-alias",
      }),
    );
    expect(await screen.findAllByText("VALIDATED")).not.toHaveLength(0);
    expect(screen.getByText("track-1")).toBeInTheDocument();
    expect(screen.getByText("Internal attributes redacted")).toBeInTheDocument();

    const validatePanel = panelByHeading("Validate code");
    expect(validatePanel.queryByText("tenant_code")).not.toBeInTheDocument();
    expect(validatePanel.queryByText("9999999999")).not.toBeInTheDocument();
  });

  it("captures referee identity against the validated track", async () => {
    renderWorkspace(<ReferralSaasLinkCodeWorkflowPage />);

    fireEvent.click(screen.getByRole("button", { name: "Issue code" }));
    await screen.findByText("REF123");
    fireEvent.click(screen.getByRole("button", { name: "Validate code" }));
    await screen.findByText("track-1");
    fireEvent.change(screen.getByLabelText("Referee UCN bridge"), { target: { value: "7777777777" } });
    fireEvent.click(screen.getByRole("button", { name: "Capture identity" }));

    await waitFor(() =>
      expect(mockedCaptureConsumerRefereeUcn).toHaveBeenCalledWith("track-1", "7777777777"),
    );
    expect(await screen.findByText("Referee UCN captured")).toBeInTheDocument();
  });

  it("keeps terms as a visible gate for issue and validation actions", () => {
    renderWorkspace(<ReferralSaasLinkCodeWorkflowPage />);

    fireEvent.click(screen.getByLabelText(/Accepted terms checked/i));

    expect(screen.getByRole("button", { name: "Issue code" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Validate code" })).toBeDisabled();
    expect(mockedIssueConsumerReferralCode).not.toHaveBeenCalled();
    expect(mockedValidateConsumerReferralCode).not.toHaveBeenCalled();
  });

  it("does not expose unsupported lifecycle, support replay, or money actions", () => {
    renderWorkspace(<ReferralSaasLinkCodeWorkflowPage />);

    expect(screen.queryByRole("button", { name: /reissue/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /revoke/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /expire/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /repair/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /replay/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /reward/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /settle/i })).not.toBeInTheDocument();
  });

  it("links to adjacent Referral SaaS setup surfaces", () => {
    renderWorkspace(<ReferralSaasLinkCodeWorkflowPage />);

    expect(screen.getByRole("link", { name: /Account setup readiness/ })).toHaveAttribute(
      "href",
      "/admin/referral-saas/account-setup",
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
});
