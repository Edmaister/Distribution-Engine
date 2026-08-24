import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { createMemoryRouter, RouterProvider, useLocation } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import { useReferralSaasCustomerPortfolio } from "../../api/referralSaasAccountQueries";
import { ReferralSaasCustomerAccountsPage } from "./ReferralSaasCustomerAccountsPage";

vi.mock("../../api/referralSaasAccountQueries", () => ({ useReferralSaasCustomerPortfolio: vi.fn() }));
vi.mock("./ReferralSaasAccountSetupPage", () => ({ ReferralSaasAccountSetupPage: ({ embedded, compact }: { embedded?: boolean; compact?: boolean }) => <div data-compact={compact ? "true" : "false"} data-testid="account-setup">{embedded ? "Embedded account setup" : "Account setup"}</div> }));
const mockDirectory = vi.mocked(useReferralSaasCustomerPortfolio);
const response = {
  status: "ok" as const,
  operatorScope: { role: "AMPLIFI_ADMIN", jurisdictions: ["BW", "ZA"] },
  portfolio: {
    customers: [{ accountRef: "account-1", accountCode: "ACC-NSF-008", accountName: "Northstar Financial", accountType: "ENTERPRISE", accountStatus: "ACTIVE" as const, onboardingStatus: "COMPLETE", jurisdiction: "ZA", customerReference: "northstar", organisationReference: "northstar-org", updatedAt: null, attention: { needsAttention: false, openCaseCount: 0, criticalCaseCount: 0, highestPriority: null, reasons: [] }, destination: "/admin/referral-saas/account-maintenance/account-1" }],
    nextCursor: null, filters: {}, summary: { visibleCustomers: 1, needingAttention: 0, criticalAttention: 0 }, guardrails: [], redactions: [],
  }, noCrossJurisdictionAccessConfirmed: true, noSyntheticFrontendMetricsConfirmed: true,
};
function Location() { return <output data-testid="location">{useLocation().search}</output>; }
function renderPage() {
  const router = createMemoryRouter([{ path: "/admin/referral-saas/operations/customer-accounts", element: <><ReferralSaasCustomerAccountsPage /><Location /></> }], { initialEntries: ["/admin/referral-saas/operations/customer-accounts"] });
  return render(<RouterProvider router={router} />);
}

describe("ReferralSaasCustomerAccountsPage", () => {
  afterEach(cleanup);
  it("separates permission-scoped discovery from governed creation", () => {
    mockDirectory.mockReturnValue({ data: response, isLoading: false, error: null } as unknown as ReturnType<typeof useReferralSaasCustomerPortfolio>);
    renderPage();
    expect(screen.getByRole("heading", { name: "Customer accounts" })).toBeInTheDocument();
    expect(screen.getByText("Results are permission-scoped")).toBeInTheDocument();
    expect(screen.getByLabelText("Jurisdiction")).toBeInTheDocument();
    expect(screen.getByLabelText("Account status")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Find customer" })).toHaveAttribute("aria-current", "page");
    expect(screen.getAllByRole("link", { name: /Create customer|Create new customer/ })[0]).toHaveAttribute("href", "/admin/referral-saas/operations/customer-accounts?mode=create");
    expect(screen.getByRole("link", { name: "Open Northstar Financial profile" })).toHaveAttribute("href", "/admin/referral-saas/account-maintenance/account-1");
    expect(mockDirectory).toHaveBeenCalledWith(expect.objectContaining({ sort: "NAME_ASC", limit: 50 }), 0);
  });
  it("keeps governed customer creation inside the Customer Accounts workspace", () => {
    mockDirectory.mockReturnValue({ data: response, isLoading: false, error: null } as unknown as ReturnType<typeof useReferralSaasCustomerPortfolio>);
    const router = createMemoryRouter([{ path: "/admin/referral-saas/operations/customer-accounts", element: <ReferralSaasCustomerAccountsPage /> }], { initialEntries: ["/admin/referral-saas/operations/customer-accounts?mode=create"] });
    render(<RouterProvider router={router} />);
    expect(screen.getByTestId("account-setup")).toHaveTextContent("Embedded account setup");
    expect(screen.getByTestId("account-setup")).toHaveAttribute("data-compact", "true");
    expect(screen.getByRole("complementary", { name: "What happens next" })).toHaveTextContent("Duplicate check");
    expect(screen.getByRole("complementary", { name: "What happens next" })).toHaveTextContent("checked automatically");
    expect(screen.getByRole("complementary", { name: "What happens next" })).toHaveTextContent("Jurisdiction check");
    expect(screen.getByRole("link", { name: "Create customer" })).toHaveAttribute("aria-current", "page");
    expect(screen.getByRole("link", { name: "Back to customer search" })).toHaveAttribute("href", "/admin/referral-saas/operations/customer-accounts?mode=find");
    expect(screen.getByRole("link", { name: "Find customer" })).toHaveAttribute("href", "/admin/referral-saas/operations/customer-accounts?mode=find");
    expect(screen.queryByText("Create a governed customer")).not.toBeInTheDocument();
    expect(screen.queryByText("Results are permission-scoped")).not.toBeInTheDocument();
  });
  it("keeps customer search in the URL", async () => {
    mockDirectory.mockReturnValue({ data: response, isLoading: false, error: null } as unknown as ReturnType<typeof useReferralSaasCustomerPortfolio>);
    renderPage();
    fireEvent.change(screen.getByLabelText("Customer name or number"), { target: { value: "Northstar" } });
    fireEvent.click(screen.getByRole("button", { name: "Search" }));
    await waitFor(() => expect(screen.getByTestId("location")).toHaveTextContent("search=Northstar"));
  });
});
