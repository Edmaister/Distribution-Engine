import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { createMemoryRouter, RouterProvider } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import {
  useReferralSaasCustomerPortfolio,
  useReferralSaasOperationsOverview,
} from "../../api/referralSaasAccountQueries";
import {
  expectNamedInteractiveElements,
  expectNoPositiveTabIndex,
  expectValidAriaReferences,
} from "../../test/accessibility";
import { ReferralSaasCustomerPortfolioPage } from "./ReferralSaasCustomerPortfolioPage";
import { ReferralSaasWorkspacePage } from "./ReferralSaasWorkspacePage";

vi.mock("../../api/referralSaasAccountQueries", () => ({
  useReferralSaasCustomerPortfolio: vi.fn(),
  useReferralSaasOperationsOverview: vi.fn(),
}));

const mockOverview = vi.mocked(useReferralSaasOperationsOverview);
const mockPortfolio = vi.mocked(useReferralSaasCustomerPortfolio);

const operationsResponse = {
  status: "ok" as const,
  operatorScope: { role: "AMPLIFI_ADMIN", jurisdictions: ["BW", "ZA"] },
  operations: {
    metrics: {
      awaitingYourAction: 1,
      customersNeedingAttention: 1,
      withinServiceTargetPercent: null,
      serviceTargetStatus: "UNAVAILABLE" as const,
      productionIncidents: 0,
    },
    workItems: [],
    nextCursor: null,
    filters: {
      jurisdictions: ["BW", "ZA"],
      priority: null,
      customer: null,
      category: null,
      status: null,
      owner: null,
      workType: null,
      serviceTarget: null,
      sort: "PRIORITY",
      limit: 8,
    },
    metricDefinitions: {},
    guardrails: ["PERMITTED_JURISDICTION_INTERSECTION"],
    redactions: ["internal_tenant_identifier"],
  },
  noCrossJurisdictionAccessConfirmed: true,
  noSyntheticFrontendMetricsConfirmed: true,
};

const portfolioResponse = {
  status: "ok" as const,
  operatorScope: { role: "AMPLIFI_ADMIN", jurisdictions: ["BW", "ZA"] },
  portfolio: {
    customers: [
      {
        accountRef: "account-1",
        accountCode: "ACC-100",
        accountName: "Northstar Financial",
        accountType: "ENTERPRISE",
        accountStatus: "ACTIVE" as const,
        onboardingStatus: "COMPLETE",
        jurisdiction: "ZA",
        customerReference: "northstar",
        organisationReference: "northstar-org",
        updatedAt: "2026-08-19T08:00:00Z",
        attention: {
          needsAttention: true,
          openCaseCount: 1,
          criticalCaseCount: 0,
          highestPriority: "HIGH" as const,
          reasons: ["1 high-priority operational case"],
        },
        destination: "/admin/referral-saas/account-maintenance/account-1",
      },
    ],
    nextCursor: null,
    filters: {},
    summary: { visibleCustomers: 1, needingAttention: 1, criticalAttention: 0 },
    guardrails: ["ACCOUNT_REGISTRY_SOURCE"],
    redactions: ["internal_tenant_identifier"],
  },
  noCrossJurisdictionAccessConfirmed: true,
  noSyntheticFrontendMetricsConfirmed: true,
};

function renderJourney() {
  const router = createMemoryRouter(
    [
      { path: "/admin/referral-saas", element: <ReferralSaasWorkspacePage /> },
      {
        path: "/admin/referral-saas/operations/customer-portfolio",
        element: <ReferralSaasCustomerPortfolioPage />,
      },
      {
        path: "/admin/referral-saas/account-maintenance/:accountId/:module",
        element: <h1>Authoritative customer workflow</h1>,
      },
    ],
    { initialEntries: ["/admin/referral-saas"] },
  );
  return render(<RouterProvider router={router} />);
}

function expectAccessibleSurface(container: HTMLElement) {
  expectNamedInteractiveElements(container);
  expectValidAriaReferences(container);
  expectNoPositiveTabIndex(container);
}

describe("Referral SaaS Operations Workspace journey", () => {
  afterEach(() => cleanup());

  it.each([
    ["programme governance", "programmes", "Open programmes"],
    ["commercial governance", "commercial", "Open commercial governance"],
  ])(
    "keeps %s behind permission-safe customer selection",
    async (_label, destination, action) => {
      mockOverview.mockReturnValue({
        data: operationsResponse,
        isLoading: false,
        error: null,
      } as unknown as ReturnType<typeof useReferralSaasOperationsOverview>);
      mockPortfolio.mockReturnValue({
        data: portfolioResponse,
        isLoading: false,
        error: null,
      } as unknown as ReturnType<typeof useReferralSaasCustomerPortfolio>);
      const view = renderJourney();

      expectAccessibleSurface(view.container);
      fireEvent.click(
        screen.getByRole("link", { name: "Find or create customer" }),
      );
      await screen.findByRole("heading", { name: "Customer portfolio" });
      expectAccessibleSurface(view.container);

      const destinationLink = screen.getByRole("link", {
        name: "Open customer",
      });
      expect(destinationLink).toHaveAttribute(
        "href",
        "/admin/referral-saas/account-maintenance/account-1",
      );

      const router = createMemoryRouter(
        [
          {
            path: "/admin/referral-saas/operations/customer-portfolio",
            element: <ReferralSaasCustomerPortfolioPage />,
          },
          {
            path: "/admin/referral-saas/account-maintenance/:accountId/:module",
            element: <h1>Authoritative customer workflow</h1>,
          },
        ],
        {
          initialEntries: [
            `/admin/referral-saas/operations/customer-portfolio?destination=${destination}`,
          ],
        },
      );
      view.unmount();
      const governedView = render(<RouterProvider router={router} />);

      expectAccessibleSurface(governedView.container);
      fireEvent.click(screen.getByRole("link", { name: action }));
      await waitFor(() =>
        expect(
          screen.getByRole("heading", {
            name: "Authoritative customer workflow",
          }),
        ).toBeInTheDocument(),
      );
    },
  );
});
