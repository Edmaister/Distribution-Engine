import {
  cleanup,
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
import { OnboardingReadinessChecklistPage } from "./OnboardingReadinessChecklistPage";

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
        category: "ORGANISATION_PROFILE",
        display_label: "Organisation profile",
        status: "READY",
        safe_display_status: {
          status: "READY",
          label: "Ready",
          action_required: false,
          go_live_enabled: false,
        },
        evidence_summary: "Read-only organisation evidence is present.",
        blockers: [],
        next_actions: ["Review organisation profile before go-live."],
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
        evidence_summary: "Webhook/API evidence is unavailable.",
        blockers: ["Webhook/API setup is currently shell-only."],
        next_actions: [
          "Capture webhook/API setup when a safe source is available.",
        ],
      },
    ],
    summary: {
      ready_count: 1,
      in_progress_count: 0,
      blocked_count: 0,
      missing_evidence_count: 1,
      permission_limited_count: 0,
      go_live_disabled_count: 1,
      total_count: 2,
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

function checklistPanel() {
  const heading = document.getElementById("checklist-heading");
  if (!heading) {
    throw new Error("Checklist heading was not rendered");
  }
  const panel = heading.closest(".panel");
  if (!panel) {
    throw new Error("Checklist panel was not rendered");
  }
  return within(panel as HTMLElement);
}

function blockersPanel() {
  const heading = document.getElementById("blockers-heading");
  if (!heading) {
    throw new Error("Blockers heading was not rendered");
  }
  const panel = heading.closest(".panel");
  if (!panel) {
    throw new Error("Blockers panel was not rendered");
  }
  return within(panel as HTMLElement);
}

describe("OnboardingReadinessChecklistPage", () => {
  beforeEach(() => {
    mockedGetAdminOnboardingState.mockResolvedValue(onboardingStateResponse());
  });

  afterEach(() => {
    cleanup();
    vi.clearAllMocks();
  });

  it("renders the onboarding readiness checklist with demo-safe statuses", async () => {
    renderWorkspace(<OnboardingReadinessChecklistPage />);

    expect(
      screen.getByRole("heading", { name: "Onboarding readiness checklist" }),
    ).toBeInTheDocument();
    expect(screen.getByText("Review only")).toBeInTheDocument();
    expect(screen.getByText("Ready categories")).toBeInTheDocument();
    expect(screen.getByText("Blocked categories")).toBeInTheDocument();
    expect(screen.getByText("Internal tenant identifier")).toBeInTheDocument();
    expect(await screen.findByText("Overall readiness")).toBeInTheDocument();
    expect(screen.getByText("demo-platform-operator")).toBeInTheDocument();
    expect(
      checklistPanel().getByText("Organisation profile"),
    ).toBeInTheDocument();
    expect(
      checklistPanel().getByText("Webhook / API setup"),
    ).toBeInTheDocument();
    expect(checklistPanel().getByText("Missing evidence")).toBeInTheDocument();
    expect(
      checklistPanel().getByText("Webhook/API setup is currently shell-only."),
    ).toBeInTheDocument();
    expect(screen.queryByText(/tenant_code/i)).not.toBeInTheDocument();
  });

  it("requests read-only onboarding state using external references", async () => {
    renderWorkspace(<OnboardingReadinessChecklistPage />);

    await waitFor(() => {
      expect(mockedGetAdminOnboardingState).toHaveBeenCalledWith({
        external_tenant_ref: "demo-platform-operator",
        organisation_ref: "demo-organisation",
        producer_ref: "demo-producer",
        distributor_ref: "demo-distributor",
        campaign_code: "DEMO-CAMPAIGN",
        opportunity_ref: "demo-opportunity",
      });
    });
  });

  it("links hydrated categories back to relevant onboarding shells", async () => {
    renderWorkspace(<OnboardingReadinessChecklistPage />);

    await screen.findByText(/Read-only organisation evidence is present/);

    expect(
      checklistPanel().getByRole("link", { name: /Organisation profile/ }),
    ).toHaveAttribute("href", "/admin/onboarding/company");
    expect(
      checklistPanel().getByRole("link", { name: /Webhook \/ API setup/ }),
    ).toHaveAttribute("href", "/admin/onboarding/webhook-api");
  });

  it("shows live verification blockers and keeps go-live actions disabled", () => {
    mockedGetAdminOnboardingState.mockRejectedValue(new Error("offline"));
    renderWorkspace(<OnboardingReadinessChecklistPage />);

    expect(
      blockersPanel().getByText("TASK-027 live DB verification"),
    ).toBeInTheDocument();
    expect(
      blockersPanel().getByText("TASK-028 drift resolution"),
    ).toBeInTheDocument();
    expect(
      blockersPanel().getByText(
        /approved safe read-only runtime database access/,
      ),
    ).toBeInTheDocument();
    expect(
      blockersPanel().getByText(/verified live\/schema mismatch/),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Request go-live review later" }),
    ).toBeDisabled();
    expect(
      screen.getByRole("button", { name: "Mark ready for review later" }),
    ).toBeDisabled();
  });

  it("keeps the readiness view clear of live command and money movement behaviour", () => {
    renderWorkspace(<OnboardingReadinessChecklistPage />);

    expect(
      screen.getByText(
        "This checklist does not activate go-live, publish campaigns, create credentials, or move money.",
      ),
    ).toBeInTheDocument();
    expect(screen.getByText("No live commands")).toBeInTheDocument();
    expect(screen.getByText("Demo review only")).toBeInTheDocument();
    expect(
      screen.getByText(
        /wallet, funding, fulfilment, settlement, retry, and webhook delivery stay disabled/,
      ),
    ).toBeInTheDocument();
  });

  it("falls back to local demo readiness when the endpoint is unavailable", async () => {
    mockedGetAdminOnboardingState.mockRejectedValue(new Error("offline"));
    renderWorkspace(<OnboardingReadinessChecklistPage />);

    expect(
      await screen.findByText("Using local demo fallback."),
    ).toBeInTheDocument();
    expect(
      checklistPanel().getByText("Producer / sponsor setup"),
    ).toBeInTheDocument();
    expect(checklistPanel().getByText("Distributor setup")).toBeInTheDocument();
    expect(
      checklistPanel().getByText("Security and permissions"),
    ).toBeInTheDocument();
  });
});
