import { cleanup, render, screen, within } from "@testing-library/react";
import type { ReactElement } from "react";
import { createMemoryRouter, Outlet, RouterProvider } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  getAdminOnboardingState,
  type AdminOnboardingStateResponse,
} from "../../api/endpoints/adminOnboarding";
import { OperatorDemoHomePage } from "./OperatorDemoHomePage";

vi.mock("../../api/endpoints/adminOnboarding", () => ({
  getAdminOnboardingState: vi.fn(),
}));

const mockedGetAdminOnboardingState = vi.mocked(getAdminOnboardingState);

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

function panelByHeading(name: string) {
  const heading = screen.getByRole("heading", { name });
  const panel = heading.closest(".panel");
  if (!panel) {
    throw new Error(`${name} panel was not rendered`);
  }
  return within(panel as HTMLElement);
}

function onboardingStateResponse(
  overrides: Partial<AdminOnboardingStateResponse["readiness"]> = {},
): AdminOnboardingStateResponse {
  return {
    status: "ok",
    guardrail: "Read-only admin onboarding state.",
    readiness: {
      contract_version: "onboarding.v1",
      overall_status: "GO_LIVE_DISABLED",
      categories: [
        {
          category: "ORGANISATION_PROFILE",
          display_label: "Organisation profile",
          status: "READY",
          safe_display_status: {
            status: "READY",
            label: "Ready",
            action_required: false,
            go_live_enabled: false,
          },
          evidence_summary: "Required read-only evidence is present.",
          blockers: [],
          next_actions: ["Review this section before go-live."],
        },
        {
          category: "WEBHOOK_API_SETUP",
          display_label: "Webhook / API setup",
          status: "MISSING_EVIDENCE",
          safe_display_status: {
            status: "MISSING_EVIDENCE",
            label: "Missing evidence",
            action_required: true,
            go_live_enabled: false,
          },
          evidence_summary: "Required evidence is unavailable or shell-only.",
          blockers: ["Webhook/API setup is currently shell-only."],
          next_actions: [
            "Capture webhook/API setup when a safe source is available.",
          ],
        },
        {
          category: "GO_LIVE_CONTROLS",
          display_label: "Go-live controls",
          status: "GO_LIVE_DISABLED",
          safe_display_status: {
            status: "GO_LIVE_DISABLED",
            label: "Go-live disabled",
            action_required: true,
            go_live_enabled: false,
          },
          evidence_summary: "GO_LIVE_DISABLED",
          blockers: ["Go-live activation and money movement are disabled."],
          next_actions: ["Use this readiness output for review only."],
        },
      ],
      summary: {
        ready_count: 1,
        in_progress_count: 0,
        blocked_count: 0,
        missing_evidence_count: 1,
        permission_limited_count: 0,
        go_live_disabled_count: 1,
        total_count: 3,
      },
      ...overrides,
    },
  };
}

function expectLiveActionsDisabled() {
  expect(
    screen.getByRole("button", { name: "Start live demo later" }),
  ).toBeDisabled();
  expect(
    screen.getByRole("button", { name: "Run live smoke check later" }),
  ).toBeDisabled();
  expect(
    screen.getByRole("button", { name: "Publish campaign later" }),
  ).toBeDisabled();
  expect(
    screen.getByRole("button", { name: "Deliver webhook later" }),
  ).toBeDisabled();
}

describe("OperatorDemoHomePage", () => {
  beforeEach(() => {
    mockedGetAdminOnboardingState.mockResolvedValue(onboardingStateResponse());
  });

  afterEach(() => {
    cleanup();
    vi.clearAllMocks();
  });

  it("renders the operator demo home with journey sections", () => {
    renderWorkspace(<OperatorDemoHomePage />);

    expect(
      screen.getByRole("heading", { name: "Operator demo home" }),
    ).toBeInTheDocument();
    expect(screen.getByText("Demo shell")).toBeInTheDocument();
    expect(screen.getByText("Demo journey links")).toBeInTheDocument();
    expect(screen.getByText("Diagnostics UI pending")).toBeInTheDocument();
    expect(screen.getByText("Internal tenant identifier")).toBeInTheDocument();

    expect(
      screen.getByRole("heading", { name: "Setup journey" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "Read-only onboarding readiness" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "Readiness review" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "Operational monitoring" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "Diagnostics and support" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "Persona paths" }),
    ).toBeInTheDocument();
  });

  it("shows loading while fetching read-only onboarding readiness", () => {
    mockedGetAdminOnboardingState.mockReturnValue(new Promise(() => undefined));

    renderWorkspace(<OperatorDemoHomePage />);

    expect(
      screen.getByText("Loading read-only readiness state."),
    ).toBeInTheDocument();
    expect(screen.getByText("Loading")).toBeInTheDocument();
  });

  it("requests read-only onboarding readiness with external references", async () => {
    renderWorkspace(<OperatorDemoHomePage />);

    await screen.findByText("Read-only state");

    expect(mockedGetAdminOnboardingState).toHaveBeenCalledWith({
      external_tenant_ref: "demo-platform-operator",
      organisation_ref: "org-demo",
      producer_ref: "producer-demo",
      sponsor_ref: "sponsor-demo",
      distributor_ref: "distributor-demo",
      campaign_code: "DEMO-CAMPAIGN",
      opportunity_ref: "opportunity-demo",
    });
  });

  it("renders successful read-only readiness categories from the endpoint", async () => {
    renderWorkspace(<OperatorDemoHomePage />);

    expect(await screen.findByText("Read-only state")).toBeInTheDocument();
    expect(screen.getByText("Overall readiness")).toBeInTheDocument();
    expect(screen.getAllByText("GO_LIVE_DISABLED").length).toBeGreaterThan(0);
    expect(screen.getByText("Organisation profile")).toBeInTheDocument();
    expect(
      screen.getByText("Required read-only evidence is present."),
    ).toBeInTheDocument();
    expect(screen.getAllByText("Ready").length).toBeGreaterThan(0);
  });

  it("renders partial and missing evidence explicitly", async () => {
    renderWorkspace(<OperatorDemoHomePage />);

    expect(await screen.findByText("Webhook / API setup")).toBeInTheDocument();
    expect(screen.getAllByText("Missing evidence").length).toBeGreaterThan(0);
    expect(
      screen.getByText("Webhook/API setup is currently shell-only."),
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        "Capture webhook/API setup when a safe source is available.",
      ),
    ).toBeInTheDocument();
  });

  it("falls back safely when read-only onboarding state is unavailable", async () => {
    mockedGetAdminOnboardingState.mockRejectedValue(new Error("offline"));

    renderWorkspace(<OperatorDemoHomePage />);

    expect(await screen.findByText("Demo fallback")).toBeInTheDocument();
    expect(screen.getByText("Using local demo fallback.")).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "Setup journey" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: /Company \/ organisation onboarding/ }),
    ).toHaveAttribute("href", "/admin/onboarding/company");
  });

  it("links onboarding and readiness steps to their existing shell routes", () => {
    renderWorkspace(<OperatorDemoHomePage />);

    const setup = panelByHeading("Setup journey");
    const readiness = panelByHeading("Readiness review");

    expect(
      setup.getByRole("link", { name: /Company \/ organisation onboarding/ }),
    ).toHaveAttribute("href", "/admin/onboarding/company");
    expect(
      setup.getByRole("link", { name: /Producer \/ sponsor onboarding/ }),
    ).toHaveAttribute("href", "/admin/onboarding/producer-sponsor");
    expect(
      setup.getByRole("link", { name: /Distributor onboarding/ }),
    ).toHaveAttribute("href", "/admin/onboarding/distributor");
    expect(
      setup.getByRole("link", { name: /User \/ member role setup/ }),
    ).toHaveAttribute("href", "/admin/onboarding/members-roles");
    expect(
      readiness.getByRole("link", { name: /Campaign \/ opportunity setup/ }),
    ).toHaveAttribute("href", "/admin/onboarding/campaign-opportunity");
    expect(
      readiness.getByRole("link", { name: /Webhook \/ API setup/ }),
    ).toHaveAttribute("href", "/admin/onboarding/webhook-api");
    expect(
      readiness.getByRole("link", { name: /Onboarding readiness checklist/ }),
    ).toHaveAttribute("href", "/admin/onboarding/readiness");
  });

  it("links read-only monitoring views that already have frontend routes", () => {
    renderWorkspace(<OperatorDemoHomePage />);

    const monitoring = panelByHeading("Operational monitoring");

    expect(
      monitoring.getByRole("link", { name: /Demand marketplace/ }),
    ).toHaveAttribute("href", "/admin/distribution");
    expect(
      monitoring.getByRole("link", { name: /Demand operations/ }),
    ).toHaveAttribute("href", "/admin/distribution/operations");
    expect(
      monitoring.getByRole("link", { name: /Channel operations/ }),
    ).toHaveAttribute("href", "/admin/channels");
    expect(
      monitoring.getByRole("link", { name: /Event fabric/ }),
    ).toHaveAttribute("href", "/admin/events");
    expect(
      monitoring.getByRole("link", { name: /Runtime health/ }),
    ).toHaveAttribute("href", "/admin/health");
    expect(
      monitoring.getByRole("link", { name: /Distributor safe status/ }),
    ).toHaveAttribute("href", "/distributor");
  });

  it("keeps backend-ready diagnostics visible without pretending a frontend exists", () => {
    renderWorkspace(<OperatorDemoHomePage />);

    const diagnostics = panelByHeading("Diagnostics and support");

    expect(
      diagnostics.getByText("Operator control-plane BFF"),
    ).toBeInTheDocument();
    expect(diagnostics.getByText("Outcome trace")).toBeInTheDocument();
    expect(diagnostics.getByText("Liability projection")).toBeInTheDocument();
    expect(diagnostics.getByText("Campaign readiness")).toBeInTheDocument();
    expect(diagnostics.getByText("Link/code diagnostics")).toBeInTheDocument();
    expect(diagnostics.getByText("Tenant-safe analytics")).toBeInTheDocument();
    expect(
      diagnostics.getByText("Webhook catalog and payload preview"),
    ).toBeInTheDocument();
    expect(diagnostics.getAllByText("UI pending")).toHaveLength(7);
    expect(
      diagnostics.queryByRole("link", { name: /Outcome trace/ }),
    ).not.toBeInTheDocument();
  });

  it("shows persona paths, live blockers, and disabled command actions", () => {
    renderWorkspace(<OperatorDemoHomePage />);

    expect(screen.getByText("Platform operator")).toBeInTheDocument();
    expect(
      screen.getByText("Producer / sponsor / company admin"),
    ).toBeInTheDocument();
    expect(screen.getByText("Distributor / partner admin")).toBeInTheDocument();
    expect(
      screen.getByText("TASK-027 live DB verification"),
    ).toBeInTheDocument();
    expect(screen.getByText("TASK-028 drift resolution")).toBeInTheDocument();
    expect(screen.getByText("No live command path")).toBeInTheDocument();

    expectLiveActionsDisabled();
    expect(
      screen.getByText("This page does not execute live platform actions."),
    ).toBeInTheDocument();
  });

  it("does not expose tenant_code as a user-facing identifier", async () => {
    mockedGetAdminOnboardingState.mockResolvedValue({
      ...onboardingStateResponse(),
      onboarding_state: {
        scope: {
          resolved_tenant: {
            tenant_code: "INTERNAL-TENANT",
          },
        },
      },
    } as unknown as AdminOnboardingStateResponse);

    renderWorkspace(<OperatorDemoHomePage />);

    await screen.findByText("Read-only state");

    expect(screen.queryByText(/tenant_code/i)).not.toBeInTheDocument();
    expect(screen.queryByText("INTERNAL-TENANT")).not.toBeInTheDocument();
    expect(screen.getByText("Internal tenant identifier")).toBeInTheDocument();
    expect(screen.getByText("Hidden")).toBeInTheDocument();
  });

  it("keeps live actions disabled after successful readiness hydration", async () => {
    renderWorkspace(<OperatorDemoHomePage />);

    await screen.findByText("Read-only state");

    expectLiveActionsDisabled();
  });
});
