import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { createMemoryRouter, RouterProvider, useLocation } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import { useReferralSaasCustomerPortfolio } from "../../api/referralSaasAccountQueries";
import { ReferralSaasCustomerPortfolioPage } from "./ReferralSaasCustomerPortfolioPage";

vi.mock("../../api/referralSaasAccountQueries", () => ({ useReferralSaasCustomerPortfolio: vi.fn() }));
const mockPortfolio = vi.mocked(useReferralSaasCustomerPortfolio);
const response = {
  status: "ok" as const, operatorScope: { role: "AMPLIFI_ADMIN", jurisdictions: ["BW", "ZA"] },
  portfolio: {
    customers: [{ accountRef: "account-1", accountCode: "ACC-1", accountName: "Northstar Financial", accountType: "ENTERPRISE", accountStatus: "ACTIVE" as const, onboardingStatus: "COMPLETE", jurisdiction: "ZA", customerReference: "northstar", organisationReference: "northstar-org", updatedAt: null, attention: { needsAttention: true, openCaseCount: 2, criticalCaseCount: 1, highestPriority: "CRITICAL" as const, reasons: ["1 critical operational case"] }, destination: "/admin/referral-saas/account-maintenance/account-1" }],
    nextCursor: "25", filters: {}, summary: { visibleCustomers: 1, needingAttention: 1, criticalAttention: 1 }, guardrails: [], redactions: [],
  }, noCrossJurisdictionAccessConfirmed: true, noSyntheticFrontendMetricsConfirmed: true,
};
function Location() { return <output data-testid="location">{useLocation().search}</output>; }
function renderPage(initial = "/admin/referral-saas/operations/customer-portfolio") {
  const router = createMemoryRouter([{ path: "/admin/referral-saas/operations/customer-portfolio", element: <><ReferralSaasCustomerPortfolioPage /><Location /></> }], { initialEntries: [initial] });
  return render(<RouterProvider router={router} />);
}

describe("ReferralSaasCustomerPortfolioPage", () => {
  afterEach(() => cleanup());
  it("shows labelled customer context and opens the persisted destination", () => {
    mockPortfolio.mockReturnValue({ data: response, isLoading: false, error: null } as unknown as ReturnType<typeof useReferralSaasCustomerPortfolio>);
    renderPage("/admin/referral-saas/operations/customer-portfolio?jurisdiction=ZA&attention=NEEDS_ATTENTION");
    expect(mockPortfolio).toHaveBeenCalledWith(expect.objectContaining({ jurisdiction: "ZA", attention: "NEEDS_ATTENTION" }), 0);
    expect(screen.getAllByText("Jurisdiction")).toHaveLength(2);
    expect(screen.getByRole("link", { name: /Open customer/ })).toHaveAttribute("href", "/admin/referral-saas/account-maintenance/account-1");
  });
  it("stores search in the URL", async () => {
    mockPortfolio.mockReturnValue({ data: response, isLoading: false, error: null } as unknown as ReturnType<typeof useReferralSaasCustomerPortfolio>);
    renderPage();
    fireEvent.change(screen.getByLabelText("Customer"), { target: { value: "Northstar" } });
    await waitFor(() => expect(screen.getByTestId("location")).toHaveTextContent("search=Northstar"));
  });
  it("opens programme governance only after a permitted customer is selected", () => {
    mockPortfolio.mockReturnValue({ data: response, isLoading: false, error: null } as unknown as ReturnType<typeof useReferralSaasCustomerPortfolio>);
    renderPage("/admin/referral-saas/operations/customer-portfolio?destination=programmes");
    expect(screen.getByRole("heading", { name: "Select a customer for programme governance" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Open programmes/ })).toHaveAttribute("href", "/admin/referral-saas/account-maintenance/account-1/programmes");
  });
  it("opens commercial governance only after a permitted customer is selected", () => {
    mockPortfolio.mockReturnValue({ data: response, isLoading: false, error: null } as unknown as ReturnType<typeof useReferralSaasCustomerPortfolio>);
    renderPage("/admin/referral-saas/operations/customer-portfolio?destination=commercial");
    expect(screen.getByRole("heading", { name: "Select a customer for commercial governance" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Open commercial governance/ })).toHaveAttribute("href", "/admin/referral-saas/account-maintenance/account-1/commercial");
  });
});
