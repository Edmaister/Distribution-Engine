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
import { CompanyOnboardingPage } from "./CompanyOnboardingPage";

vi.mock("../../api/endpoints/adminOnboarding", () => ({
  getAdminOnboardingState: vi.fn(),
}));

const mockedGetAdminOnboardingState = vi.mocked(getAdminOnboardingState);

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
          status: "MISSING_EVIDENCE",
          safe_display_status: {
            status: "MISSING_EVIDENCE",
            label: "Missing evidence",
            action_required: true,
            go_live_enabled: false,
          },
          evidence_summary: "Organisation evidence is partially available.",
          blockers: ["Company onboarding remains shell-only."],
          next_actions: ["Confirm external references before go-live review."],
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
    },
  };
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

describe("CompanyOnboardingPage", () => {
  beforeEach(() => {
    mockedGetAdminOnboardingState.mockResolvedValue(onboardingStateResponse());
  });

  afterEach(() => {
    cleanup();
    vi.clearAllMocks();
  });

  it("renders the company onboarding shell with external identifier guardrails", async () => {
    renderWorkspace(<CompanyOnboardingPage />);

    expect(
      screen.getByRole("heading", {
        name: "Company & organisation onboarding",
      }),
    ).toBeInTheDocument();
    expect(screen.getByText("Shell only")).toBeInTheDocument();
    expect(screen.getByLabelText(/Organisation name/)).toBeInTheDocument();
    expect(screen.getByLabelText(/external_tenant_ref/)).toBeInTheDocument();
    expect(screen.getByLabelText(/organisation_ref/)).toBeInTheDocument();
    expect(
      screen.getByText("Internal tenant identifier stays hidden"),
    ).toBeInTheDocument();
    expect(
      screen.getByText("No records are created from this page."),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Create account later" }),
    ).toBeDisabled();
    expect(
      await screen.findByText("Read-only platform state"),
    ).toBeInTheDocument();
    expect(screen.queryByText(/tenant_code/i)).not.toBeInTheDocument();
  });

  it("requests read-only company state with external references", async () => {
    renderWorkspace(<CompanyOnboardingPage />);

    await waitFor(() => {
      expect(mockedGetAdminOnboardingState).toHaveBeenCalledWith({
        external_tenant_ref: "demo-platform-operator",
        organisation_ref: "demo-organisation",
      });
    });
  });

  it("shows read-only partial evidence without enabling account creation", async () => {
    renderWorkspace(<CompanyOnboardingPage />);

    expect(
      await screen.findByText("Organisation evidence is partially available."),
    ).toBeInTheDocument();
    expect(
      screen.getByText("Company onboarding remains shell-only."),
    ).toBeInTheDocument();
    expect(
      screen.getByText("Confirm external references before go-live review."),
    ).toBeInTheDocument();
    expect(screen.getByText("demo-platform-operator")).toBeInTheDocument();
    expect(screen.getByText("demo-organisation")).toBeInTheDocument();
    expect(screen.getByText("Missing evidence")).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Create account later" }),
    ).toBeDisabled();
  });

  it("updates local readiness state without enabling account creation", () => {
    renderWorkspace(<CompanyOnboardingPage />);

    fireEvent.change(screen.getByLabelText(/Organisation name/), {
      target: { value: "Acme Distribution Ltd" },
    });
    fireEvent.change(screen.getByLabelText(/external_tenant_ref/), {
      target: { value: "acme-distribution" },
    });
    fireEvent.change(screen.getByLabelText(/organisation_ref/), {
      target: { value: "org-acme" },
    });
    fireEvent.change(screen.getByLabelText(/Country/), {
      target: { value: "South Africa" },
    });
    fireEvent.change(screen.getByLabelText(/Industry/), {
      target: { value: "Insurance" },
    });
    fireEvent.change(screen.getByLabelText(/Admin contact/), {
      target: { value: "ops@example.test" },
    });
    fireEvent.change(screen.getByLabelText(/Intended role/), {
      target: { value: "Producer admin" },
    });

    expect(
      screen.getByText("Required shell fields are captured locally."),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Create account later" }),
    ).toBeDisabled();
    expect(readinessPanel().getByText("Profile drafted")).toBeInTheDocument();
    expect(readinessPanel().getAllByText("Ready")).toHaveLength(3);
    expect(readinessPanel().getByText("Pending")).toBeInTheDocument();
    expect(screen.getByText("Backend account lifecycle")).toBeInTheDocument();
  });

  it("links the company setup journey to future onboarding and monitoring surfaces", () => {
    renderWorkspace(<CompanyOnboardingPage />);

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
      screen.getByRole("link", { name: /Campaign \/ opportunity setup/ }),
    ).toHaveAttribute("href", "/admin/onboarding/campaign-opportunity");
    expect(
      screen.getByRole("link", { name: /Webhook & API setup/ }),
    ).toHaveAttribute("href", "/admin/onboarding/webhook-api");
    expect(
      screen.getByRole("link", { name: /Operator monitoring/ }),
    ).toHaveAttribute("href", "/admin");
  });

  it("falls back to local shell state when read-only company state is unavailable", async () => {
    mockedGetAdminOnboardingState.mockRejectedValue(new Error("offline"));
    renderWorkspace(<CompanyOnboardingPage />);

    expect(
      await screen.findByText("Using local company setup fallback."),
    ).toBeInTheDocument();
    expect(screen.getAllByText("Company profile").length).toBeGreaterThan(0);
    expect(
      screen.getByRole("button", { name: "Create account later" }),
    ).toBeDisabled();
  });
});
