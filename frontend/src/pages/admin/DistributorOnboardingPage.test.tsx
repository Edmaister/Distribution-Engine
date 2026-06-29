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
import { DistributorOnboardingPage } from "./DistributorOnboardingPage";

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
        category: "DISTRIBUTOR_SETUP",
        display_label: "Distributor setup",
        status: "MISSING_EVIDENCE",
        safe_display_status: {
          status: "MISSING_EVIDENCE",
          label: "Missing evidence",
          action_required: true,
          go_live_enabled: false,
        },
        evidence_summary: "Distributor evidence is partially available.",
        blockers: ["Distributor onboarding remains shell-only."],
        next_actions: ["Confirm distributor_ref before route review."],
      },
    ],
    summary: {
      ready_count: 0,
      in_progress_count: 0,
      blocked_count: 0,
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
  const heading = screen.getByRole("heading", { name: "Setup readiness" });
  const panel = heading.closest(".panel");
  if (!panel) {
    throw new Error("Setup readiness panel was not rendered");
  }
  return within(panel as HTMLElement);
}

describe("DistributorOnboardingPage", () => {
  beforeEach(() => {
    mockedGetAdminOnboardingState.mockResolvedValue(onboardingStateResponse());
  });

  afterEach(() => {
    cleanup();
    vi.clearAllMocks();
  });

  it("renders the distributor onboarding shell with safe reference guardrails", async () => {
    renderWorkspace(<DistributorOnboardingPage />);

    expect(
      screen.getByRole("heading", { name: "Distributor onboarding" }),
    ).toBeInTheDocument();
    expect(screen.getByText("Shell only")).toBeInTheDocument();
    expect(screen.getByLabelText(/Distributor name/)).toBeInTheDocument();
    expect(screen.getByLabelText(/external_tenant_ref/)).toBeInTheDocument();
    expect(screen.getByLabelText(/distributor_ref/)).toBeInTheDocument();
    expect(screen.getByLabelText(/organisation_ref/)).toBeInTheDocument();
    expect(screen.getByLabelText(/Channel type/)).toBeInTheDocument();
    expect(screen.getByLabelText(/Market \/ country/)).toBeInTheDocument();
    expect(
      screen.getByText("External distributor identity"),
    ).toBeInTheDocument();
    expect(screen.getByText("Routes are not active")).toBeInTheDocument();
    expect(screen.getByText("Wallets are not created")).toBeInTheDocument();
    expect(
      screen.getByText(
        "No distributor or marketplace records are created from this page.",
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Create distributor later" }),
    ).toBeDisabled();
    expect(
      screen.getByRole("button", { name: "Activate route later" }),
    ).toBeDisabled();
    expect(
      screen.getByRole("button", { name: "Create wallet later" }),
    ).toBeDisabled();
    expect(
      await screen.findByText("Read-only platform state"),
    ).toBeInTheDocument();
    expect(screen.queryByText(/tenant_code/i)).not.toBeInTheDocument();
  });

  it("shows loading while fetching read-only distributor state", () => {
    mockedGetAdminOnboardingState.mockReturnValue(new Promise(() => undefined));
    renderWorkspace(<DistributorOnboardingPage />);

    expect(
      screen.getByText("Loading read-only distributor readiness."),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Create distributor later" }),
    ).toBeDisabled();
    expect(
      screen.getByRole("button", { name: "Activate route later" }),
    ).toBeDisabled();
    expect(
      screen.getByRole("button", { name: "Create wallet later" }),
    ).toBeDisabled();
  });

  it("requests read-only distributor state with external references", async () => {
    renderWorkspace(<DistributorOnboardingPage />);

    await waitFor(() => {
      expect(mockedGetAdminOnboardingState).toHaveBeenCalledWith({
        external_tenant_ref: "demo-platform-operator",
        organisation_ref: "demo-organisation",
        distributor_ref: "demo-distributor",
      });
    });
  });

  it("shows read-only partial evidence without enabling distributor lifecycle actions", async () => {
    renderWorkspace(<DistributorOnboardingPage />);

    expect(
      await screen.findByText("Distributor evidence is partially available."),
    ).toBeInTheDocument();
    expect(
      screen.getByText("Distributor onboarding remains shell-only."),
    ).toBeInTheDocument();
    expect(
      screen.getByText("Confirm distributor_ref before route review."),
    ).toBeInTheDocument();
    expect(screen.getByText("demo-distributor")).toBeInTheDocument();
    expect(screen.getByText("demo-organisation")).toBeInTheDocument();
    expect(screen.getByText("Missing evidence")).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Create distributor later" }),
    ).toBeDisabled();
    expect(
      screen.getByRole("button", { name: "Activate route later" }),
    ).toBeDisabled();
    expect(
      screen.getByRole("button", { name: "Create wallet later" }),
    ).toBeDisabled();
  });

  it("updates local readiness without enabling distributor lifecycle actions", () => {
    renderWorkspace(<DistributorOnboardingPage />);

    fireEvent.change(screen.getByLabelText(/Distributor name/), {
      target: { value: "Acme Advisor Network" },
    });
    fireEvent.change(screen.getByLabelText(/external_tenant_ref/), {
      target: { value: "acme-advisors" },
    });
    fireEvent.change(screen.getByLabelText(/distributor_ref/), {
      target: { value: "dist-acme-advisors" },
    });
    fireEvent.change(screen.getByLabelText(/organisation_ref/), {
      target: { value: "org-acme-advisors" },
    });
    fireEvent.change(screen.getByLabelText(/Market \/ country/), {
      target: { value: "South Africa" },
    });
    fireEvent.change(screen.getByLabelText(/Distributor admin contact/), {
      target: { value: "distributor-admin@example.test" },
    });
    fireEvent.change(screen.getByLabelText(/Distribution model/), {
      target: { value: "QR/link distribution" },
    });
    fireEvent.change(
      screen.getByLabelText(/Campaign \/ opportunity participation/),
      {
        target: { value: "Opportunity candidate" },
      },
    );

    expect(
      screen.getByText("Required shell fields are captured locally."),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Create distributor later" }),
    ).toBeDisabled();
    expect(
      screen.getByRole("button", { name: "Activate route later" }),
    ).toBeDisabled();
    expect(
      screen.getByRole("button", { name: "Create wallet later" }),
    ).toBeDisabled();
    expect(readinessPanel().getByText("Profile drafted")).toBeInTheDocument();
    expect(readinessPanel().getAllByText("Ready")).toHaveLength(4);
    expect(readinessPanel().getByText("Pending")).toBeInTheDocument();
    expect(
      screen.getByText("Backend distributor onboarding"),
    ).toBeInTheDocument();
  });

  it("links distributor setup to company, producer, and portal surfaces", () => {
    renderWorkspace(<DistributorOnboardingPage />);

    expect(
      screen.getByRole("link", { name: /Company onboarding/ }),
    ).toHaveAttribute("href", "/admin/onboarding/company");
    expect(
      screen.getByRole("link", { name: /Producer \/ sponsor onboarding/ }),
    ).toHaveAttribute("href", "/admin/onboarding/producer-sponsor");
    expect(
      screen.getByRole("link", { name: /User & role setup/ }),
    ).toHaveAttribute("href", "/admin/onboarding/members-roles");
    expect(
      screen.getByRole("link", { name: /Campaign \/ opportunity setup/ }),
    ).toHaveAttribute("href", "/admin/onboarding/campaign-opportunity");
    expect(
      screen.getByRole("link", { name: /Webhook & API setup/ }),
    ).toHaveAttribute("href", "/admin/onboarding/webhook-api");
    expect(
      screen.getByRole("link", { name: /Distributor portal/ }),
    ).toHaveAttribute("href", "/distributor");
  });

  it("falls back to local shell state when read-only distributor state is unavailable", async () => {
    mockedGetAdminOnboardingState.mockRejectedValue(new Error("offline"));
    renderWorkspace(<DistributorOnboardingPage />);

    expect(
      await screen.findByText("Using local distributor setup fallback."),
    ).toBeInTheDocument();
    expect(screen.getAllByText("Distributor profile").length).toBeGreaterThan(
      0,
    );
    expect(
      screen.getByRole("button", { name: "Create distributor later" }),
    ).toBeDisabled();
    expect(
      screen.getByRole("button", { name: "Activate route later" }),
    ).toBeDisabled();
    expect(
      screen.getByRole("button", { name: "Create wallet later" }),
    ).toBeDisabled();
  });
});
