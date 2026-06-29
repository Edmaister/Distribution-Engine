import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
  within,
} from "@testing-library/react";
import type { ReactElement } from "react";
import { createMemoryRouter, Outlet, RouterProvider } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  getAdminOnboardingState,
  type AdminOnboardingStateResponse,
} from "../../api/endpoints/adminOnboarding";
import { createAdminOnboardingStateResponse } from "../../api/endpoints/adminOnboarding.testFixtures";
import { CampaignOpportunitySetupPage } from "./CampaignOpportunitySetupPage";

vi.mock("../../api/endpoints/adminOnboarding", () => ({
  getAdminOnboardingState: vi.fn(),
}));

const mockedGetAdminOnboardingState = vi.mocked(getAdminOnboardingState);

function onboardingStateResponse(
  overrides: Partial<AdminOnboardingStateResponse["readiness"]> = {},
): AdminOnboardingStateResponse {
  return createAdminOnboardingStateResponse({
    overall_status: "GO_LIVE_DISABLED",
    categories: [
      {
        category: "CAMPAIGN_OPPORTUNITY_SETUP",
        display_label: "Campaign / opportunity setup",
        status: "MISSING_EVIDENCE",
        safe_display_status: {
          status: "MISSING_EVIDENCE",
          label: "Missing evidence",
          action_required: true,
          go_live_enabled: false,
        },
        evidence_summary:
          "Campaign/opportunity evidence is partially available.",
        blockers: [
          "Campaign readiness remains blocked until policy and funding evidence exist.",
        ],
        next_actions: [
          "Confirm campaign_code and opportunity_ref before go-live review.",
        ],
      },
    ],
    summary: {
      ready_count: 0,
      in_progress_count: 0,
      blocked_count: 1,
      missing_evidence_count: 1,
      permission_limited_count: 0,
      go_live_disabled_count: 1,
      total_count: 1,
    },
    ...overrides,
  });
}

function renderWorkspace(ui: ReactElement) {
  const router = createMemoryRouter([
    {
      path: "/",
      element: <Outlet context={{ refreshKey: 0 }} />,
      children: [{ index: true, element: ui }],
    },
  ]);

  return render(<RouterProvider router={router} />);
}

function readinessPanel() {
  const heading = document.getElementById("campaign-readiness-heading");
  if (!heading) {
    throw new Error("Readiness review heading was not rendered");
  }
  const panel = heading.closest(".panel");
  if (!panel) {
    throw new Error("Readiness review panel was not rendered");
  }
  return within(panel as HTMLElement);
}

describe("CampaignOpportunitySetupPage", () => {
  beforeEach(() => {
    mockedGetAdminOnboardingState.mockResolvedValue(onboardingStateResponse());
  });

  afterEach(() => {
    cleanup();
    vi.clearAllMocks();
  });

  it("renders the campaign opportunity wizard shell with safe launch guardrails", async () => {
    renderWorkspace(<CampaignOpportunitySetupPage />);

    expect(
      screen.getByRole("heading", {
        name: "Campaign & opportunity setup wizard",
      }),
    ).toBeInTheDocument();
    expect(screen.getByText("Shell only")).toBeInTheDocument();
    expect(screen.getByLabelText(/organisation_ref/)).toBeInTheDocument();
    expect(screen.getByLabelText(/campaign_code/)).toBeInTheDocument();
    expect(screen.getByLabelText(/opportunity_ref/)).toBeInTheDocument();
    expect(screen.getByText("External setup identifiers")).toBeInTheDocument();
    expect(
      screen.getByText("Lifecycle commands are unavailable"),
    ).toBeInTheDocument();
    expect(screen.getByText("Money setup is intent only")).toBeInTheDocument();
    expect(
      screen.getByText(
        "No campaign, opportunity, route, link, code, reward, or funding records are created from this page.",
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Save campaign later" }),
    ).toBeDisabled();
    expect(
      screen.getByRole("button", { name: "Publish opportunity later" }),
    ).toBeDisabled();
    expect(
      screen.getByRole("button", { name: "Generate links later" }),
    ).toBeDisabled();
    expect(
      screen.getByRole("button", { name: "Activate route later" }),
    ).toBeDisabled();
    expect(
      screen.getByRole("button", { name: "Write reward policy later" }),
    ).toBeDisabled();
    expect(
      screen.getByRole("button", { name: "Configure funding later" }),
    ).toBeDisabled();
    expect(
      screen.getByRole("button", { name: "Trigger fulfilment later" }),
    ).toBeDisabled();
    expect(
      screen.getByRole("button", { name: "Run settlement later" }),
    ).toBeDisabled();
    expect(
      screen.getByRole("button", { name: "Retry lifecycle later" }),
    ).toBeDisabled();
    expect(
      screen.getByRole("button", { name: "Activate go-live later" }),
    ).toBeDisabled();
    expect(
      screen.getByRole("button", { name: "Move money later" }),
    ).toBeDisabled();
    expect(
      await screen.findByText("Read-only platform state"),
    ).toBeInTheDocument();
    expect(screen.queryByText(/tenant_code/i)).not.toBeInTheDocument();
  });

  it("shows loading while fetching read-only campaign state", () => {
    mockedGetAdminOnboardingState.mockReturnValue(new Promise(() => undefined));
    renderWorkspace(<CampaignOpportunitySetupPage />);

    expect(
      screen.getByText("Loading read-only campaign readiness."),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Publish opportunity later" }),
    ).toBeDisabled();
    expect(
      screen.getByRole("button", { name: "Activate go-live later" }),
    ).toBeDisabled();
    expect(
      screen.getByRole("button", { name: "Move money later" }),
    ).toBeDisabled();
  });

  it("requests read-only campaign state with external references", async () => {
    renderWorkspace(<CampaignOpportunitySetupPage />);

    await waitFor(() => {
      expect(mockedGetAdminOnboardingState).toHaveBeenCalledWith({
        external_tenant_ref: "demo-platform-operator",
        organisation_ref: "demo-organisation",
        producer_ref: "demo-producer",
        sponsor_ref: "demo-sponsor",
        campaign_code: "DEMO-CAMPAIGN",
        opportunity_ref: "demo-opportunity",
      });
    });
  });

  it("shows read-only missing evidence and blockers without enabling launch actions", async () => {
    renderWorkspace(<CampaignOpportunitySetupPage />);

    expect(
      await screen.findByText(
        "Campaign/opportunity evidence is partially available.",
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        "Campaign readiness remains blocked until policy and funding evidence exist.",
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        "Confirm campaign_code and opportunity_ref before go-live review.",
      ),
    ).toBeInTheDocument();
    expect(screen.getByText("DEMO-CAMPAIGN")).toBeInTheDocument();
    expect(screen.getByText("demo-opportunity")).toBeInTheDocument();
    expect(screen.getByText("demo-producer")).toBeInTheDocument();
    expect(screen.getByText("demo-sponsor")).toBeInTheDocument();
    expect(screen.getByText("demo-organisation")).toBeInTheDocument();
    expect(screen.getByText("Missing evidence")).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Publish opportunity later" }),
    ).toBeDisabled();
    expect(
      screen.getByRole("button", { name: "Generate links later" }),
    ).toBeDisabled();
    expect(
      screen.getByRole("button", { name: "Activate route later" }),
    ).toBeDisabled();
    expect(
      screen.getByRole("button", { name: "Write reward policy later" }),
    ).toBeDisabled();
    expect(
      screen.getByRole("button", { name: "Configure funding later" }),
    ).toBeDisabled();
    expect(
      screen.getByRole("button", { name: "Trigger fulfilment later" }),
    ).toBeDisabled();
    expect(
      screen.getByRole("button", { name: "Run settlement later" }),
    ).toBeDisabled();
    expect(
      screen.getByRole("button", { name: "Retry lifecycle later" }),
    ).toBeDisabled();
    expect(
      screen.getByRole("button", { name: "Activate go-live later" }),
    ).toBeDisabled();
    expect(
      screen.getByRole("button", { name: "Move money later" }),
    ).toBeDisabled();
  });

  it("walks wizard steps and updates local readiness without enabling launch actions", () => {
    renderWorkspace(<CampaignOpportunitySetupPage />);

    fireEvent.change(screen.getByLabelText(/organisation_ref/), {
      target: { value: "org-acme" },
    });
    fireEvent.change(screen.getByLabelText(/campaign_code/), {
      target: { value: "ACME-INSURANCE-2026" },
    });
    fireEvent.change(screen.getByLabelText(/opportunity_ref/), {
      target: { value: "opp-acme-insurance-2026" },
    });
    fireEvent.change(screen.getByLabelText(/Campaign name/), {
      target: { value: "Acme insurance launch" },
    });
    fireEvent.change(screen.getByLabelText(/Market \/ country/), {
      target: { value: "South Africa" },
    });

    fireEvent.click(screen.getByRole("button", { name: /2\. Participants/ }));
    fireEvent.change(screen.getByLabelText(/producer_ref \/ sponsor_ref/), {
      target: { value: "prod-acme-insurance" },
    });
    fireEvent.change(screen.getByLabelText(/Eligible distributor type/), {
      target: { value: "Advisor network" },
    });

    fireEvent.click(
      screen.getByRole("button", { name: /3\. Distribution model/ }),
    );
    fireEvent.change(screen.getByLabelText(/Channel \/ distribution model/), {
      target: { value: "QR/link distribution" },
    });
    fireEvent.change(screen.getByLabelText(/Link\/code intent/), {
      target: { value: "Future distributor route link" },
    });

    fireEvent.click(
      screen.getByRole("button", { name: /4\. Outcome and reward intention/ }),
    );
    fireEvent.change(screen.getByLabelText(/Intended outcome event/), {
      target: { value: "POLICY_ACTIVATED" },
    });
    fireEvent.change(
      screen.getByLabelText(/Reward \/ commission policy intention/),
      {
        target: { value: "Reward plus distributor commission" },
      },
    );

    fireEvent.click(
      screen.getByRole("button", { name: /5\. Funding intention/ }),
    );
    fireEvent.change(screen.getByLabelText(/Funding model intention/), {
      target: { value: "Prefunded campaign later" },
    });

    fireEvent.click(
      screen.getByRole("button", { name: /6\. Readiness review/ }),
    );
    fireEvent.change(screen.getByLabelText(/Go-live target \/ status/), {
      target: { value: "Ready for future readiness API" },
    });

    expect(
      screen.getByText("Required wizard fields are captured locally."),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Save campaign later" }),
    ).toBeDisabled();
    expect(
      screen.getByRole("button", { name: "Publish opportunity later" }),
    ).toBeDisabled();
    expect(
      screen.getByRole("button", { name: "Generate links later" }),
    ).toBeDisabled();
    expect(
      screen.getByRole("button", { name: "Activate route later" }),
    ).toBeDisabled();
    expect(
      screen.getByRole("button", { name: "Write reward policy later" }),
    ).toBeDisabled();
    expect(
      screen.getByRole("button", { name: "Configure funding later" }),
    ).toBeDisabled();
    expect(
      screen.getByRole("button", { name: "Trigger fulfilment later" }),
    ).toBeDisabled();
    expect(
      screen.getByRole("button", { name: "Run settlement later" }),
    ).toBeDisabled();
    expect(
      screen.getByRole("button", { name: "Retry lifecycle later" }),
    ).toBeDisabled();
    expect(
      screen.getByRole("button", { name: "Activate go-live later" }),
    ).toBeDisabled();
    expect(
      screen.getByRole("button", { name: "Move money later" }),
    ).toBeDisabled();
    expect(readinessPanel().getByText("Draft complete")).toBeInTheDocument();
    expect(readinessPanel().getAllByText("Ready")).toHaveLength(5);
    expect(readinessPanel().getByText("Pending")).toBeInTheDocument();
    expect(screen.getByText("Backend launch lifecycle")).toBeInTheDocument();
  });

  it("links campaign setup to onboarding and monitoring surfaces", () => {
    renderWorkspace(<CampaignOpportunitySetupPage />);

    expect(
      screen.getByRole("link", { name: /Company onboarding/ }),
    ).toHaveAttribute("href", "/admin/onboarding/company");
    expect(
      screen.getByRole("link", { name: /Producer \/ sponsor onboarding/ }),
    ).toHaveAttribute("href", "/admin/onboarding/producer-sponsor");
    expect(
      screen.getByRole("link", { name: /Distributor onboarding/ }),
    ).toHaveAttribute("href", "/admin/onboarding/distributor");
    expect(
      screen.getByRole("link", { name: /User & role setup/ }),
    ).toHaveAttribute("href", "/admin/onboarding/members-roles");
    expect(
      screen.getByRole("link", { name: /Webhook & API setup/ }),
    ).toHaveAttribute("href", "/admin/onboarding/webhook-api");
    expect(
      screen.getByRole("link", { name: /Demand marketplace/ }),
    ).toHaveAttribute("href", "/admin/distribution");
  });

  it("falls back to local shell state when read-only campaign state is unavailable", async () => {
    mockedGetAdminOnboardingState.mockRejectedValue(new Error("offline"));
    renderWorkspace(<CampaignOpportunitySetupPage />);

    expect(
      await screen.findByText("Using local campaign setup fallback."),
    ).toBeInTheDocument();
    expect(screen.getAllByText("Wizard steps").length).toBeGreaterThan(0);
    expect(
      screen.getByRole("button", { name: "Save campaign later" }),
    ).toBeDisabled();
    expect(
      screen.getByRole("button", { name: "Publish opportunity later" }),
    ).toBeDisabled();
    expect(
      screen.getByRole("button", { name: "Activate go-live later" }),
    ).toBeDisabled();
  });
});
