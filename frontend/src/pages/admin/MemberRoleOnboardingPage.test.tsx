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
import { MemberRoleOnboardingPage } from "./MemberRoleOnboardingPage";

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
        category: "MEMBERS_AND_ROLES",
        display_label: "Members and roles",
        status: "PERMISSION_LIMITED",
        safe_display_status: {
          status: "PERMISSION_LIMITED",
          label: "Permission limited",
          action_required: true,
          go_live_enabled: false,
        },
        evidence_summary:
          "Member and role evidence is permission-limited and partially available.",
        blockers: [
          "Membership source evidence is not available for this scope.",
        ],
        next_actions: [
          "Use an authorized operator/admin view before inviting or assigning roles.",
        ],
      },
    ],
    summary: {
      ready_count: 0,
      in_progress_count: 0,
      blocked_count: 0,
      missing_evidence_count: 1,
      permission_limited_count: 1,
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

describe("MemberRoleOnboardingPage", () => {
  beforeEach(() => {
    mockedGetAdminOnboardingState.mockResolvedValue(onboardingStateResponse());
  });

  afterEach(() => {
    cleanup();
    vi.clearAllMocks();
  });

  it("renders the member role setup shell with permission guardrails", async () => {
    renderWorkspace(<MemberRoleOnboardingPage />);

    expect(
      screen.getByRole("heading", { name: "User, member & role setup" }),
    ).toBeInTheDocument();
    expect(screen.getByText("Shell only")).toBeInTheDocument();
    expect(screen.getByLabelText(/organisation_ref/)).toBeInTheDocument();
    expect(screen.getByLabelText(/external_tenant_ref/)).toBeInTheDocument();
    expect(screen.getByLabelText(/User email/)).toBeInTheDocument();
    expect(screen.getByLabelText(/Display name/)).toBeInTheDocument();
    expect(screen.getByLabelText(/Role family/)).toBeInTheDocument();
    expect(screen.getByLabelText(/Participant type/)).toBeInTheDocument();
    expect(screen.getByText("External references only")).toBeInTheDocument();
    expect(screen.getByText("Auth stays unchanged")).toBeInTheDocument();
    expect(
      screen.getByText(
        "No user, invite, membership, or role records are created from this page.",
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Send invite later" }),
    ).toBeDisabled();
    expect(
      screen.getByRole("button", { name: "Assign role later" }),
    ).toBeDisabled();
    expect(
      screen.getByRole("button", { name: "Activate membership later" }),
    ).toBeDisabled();
    expect(
      screen.getByRole("button", { name: "Register identity later" }),
    ).toBeDisabled();
    expect(
      screen.getByRole("button", { name: "Change auth claims later" }),
    ).toBeDisabled();
    expect(
      screen.getByRole("button", { name: "Write audit event later" }),
    ).toBeDisabled();
    expect(
      await screen.findByText("Read-only platform state"),
    ).toBeInTheDocument();
    expect(screen.queryByText(/tenant_code/i)).not.toBeInTheDocument();
  });

  it("shows loading while fetching read-only member and role state", () => {
    mockedGetAdminOnboardingState.mockReturnValue(new Promise(() => undefined));
    renderWorkspace(<MemberRoleOnboardingPage />);

    expect(
      screen.getByText("Loading read-only member and role readiness."),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Send invite later" }),
    ).toBeDisabled();
    expect(
      screen.getByRole("button", { name: "Assign role later" }),
    ).toBeDisabled();
    expect(
      screen.getByRole("button", { name: "Activate membership later" }),
    ).toBeDisabled();
    expect(
      screen.getByRole("button", { name: "Register identity later" }),
    ).toBeDisabled();
    expect(
      screen.getByRole("button", { name: "Change auth claims later" }),
    ).toBeDisabled();
    expect(
      screen.getByRole("button", { name: "Write audit event later" }),
    ).toBeDisabled();
  });

  it("requests read-only member and role state with external references", async () => {
    renderWorkspace(<MemberRoleOnboardingPage />);

    await waitFor(() => {
      expect(mockedGetAdminOnboardingState).toHaveBeenCalledWith({
        external_tenant_ref: "demo-platform-operator",
        organisation_ref: "demo-organisation",
      });
    });
  });

  it("shows permission-limited and missing evidence without enabling access actions", async () => {
    renderWorkspace(<MemberRoleOnboardingPage />);

    expect(
      await screen.findByText(
        "Member and role evidence is permission-limited and partially available.",
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        "Membership source evidence is not available for this scope.",
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        "Use an authorized operator/admin view before inviting or assigning roles.",
      ),
    ).toBeInTheDocument();
    expect(screen.getByText("demo-platform-operator")).toBeInTheDocument();
    expect(screen.getByText("demo-organisation")).toBeInTheDocument();
    expect(screen.getByText("Permission limited")).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Send invite later" }),
    ).toBeDisabled();
    expect(
      screen.getByRole("button", { name: "Assign role later" }),
    ).toBeDisabled();
    expect(
      screen.getByRole("button", { name: "Activate membership later" }),
    ).toBeDisabled();
    expect(
      screen.getByRole("button", { name: "Register identity later" }),
    ).toBeDisabled();
    expect(
      screen.getByRole("button", { name: "Change auth claims later" }),
    ).toBeDisabled();
    expect(
      screen.getByRole("button", { name: "Write audit event later" }),
    ).toBeDisabled();
  });

  it("updates local readiness without enabling invite or role assignment actions", () => {
    renderWorkspace(<MemberRoleOnboardingPage />);

    fireEvent.change(screen.getByLabelText(/organisation_ref/), {
      target: { value: "org-acme" },
    });
    fireEvent.change(screen.getByLabelText(/external_tenant_ref/), {
      target: { value: "acme-distribution" },
    });
    fireEvent.change(screen.getByLabelText(/User email/), {
      target: { value: "admin@example.test" },
    });
    fireEvent.change(screen.getByLabelText(/Display name/), {
      target: { value: "Alex Admin" },
    });
    fireEvent.change(screen.getByLabelText(/Role family/), {
      target: { value: "Distributor / partner admin" },
    });
    fireEvent.change(screen.getByLabelText(/Participant type/), {
      target: { value: "Distributor" },
    });
    fireEvent.change(screen.getByLabelText(/Access scope/), {
      target: { value: "Distributor workspace later" },
    });
    fireEvent.change(screen.getByLabelText(/Invite status/), {
      target: { value: "Ready for future invitation API" },
    });

    expect(
      screen.getByText("Required shell fields are captured locally."),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Send invite later" }),
    ).toBeDisabled();
    expect(
      screen.getByRole("button", { name: "Assign role later" }),
    ).toBeDisabled();
    expect(
      screen.getByRole("button", { name: "Activate membership later" }),
    ).toBeDisabled();
    expect(
      screen.getByRole("button", { name: "Register identity later" }),
    ).toBeDisabled();
    expect(
      screen.getByRole("button", { name: "Change auth claims later" }),
    ).toBeDisabled();
    expect(
      screen.getByRole("button", { name: "Write audit event later" }),
    ).toBeDisabled();
    expect(readinessPanel().getByText("Profile drafted")).toBeInTheDocument();
    expect(readinessPanel().getAllByText("Ready")).toHaveLength(4);
    expect(readinessPanel().getByText("Pending")).toBeInTheDocument();
    expect(
      screen.getByText("Backend membership lifecycle"),
    ).toBeInTheDocument();
  });

  it("links role setup to onboarding and monitoring surfaces", () => {
    renderWorkspace(<MemberRoleOnboardingPage />);

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
      screen.getByRole("link", { name: /Campaign \/ opportunity setup/ }),
    ).toHaveAttribute("href", "/admin/onboarding/campaign-opportunity");
    expect(
      screen.getByRole("link", { name: /Webhook & API setup/ }),
    ).toHaveAttribute("href", "/admin/onboarding/webhook-api");
    expect(
      screen.getByRole("link", { name: /Operator monitoring/ }),
    ).toHaveAttribute("href", "/admin");
  });

  it("falls back to local shell state when read-only member and role state is unavailable", async () => {
    mockedGetAdminOnboardingState.mockRejectedValue(new Error("offline"));
    renderWorkspace(<MemberRoleOnboardingPage />);

    expect(
      await screen.findByText("Using local member and role setup fallback."),
    ).toBeInTheDocument();
    expect(
      screen.getAllByText("Invite and role intent").length,
    ).toBeGreaterThan(0);
    expect(
      screen.getByRole("button", { name: "Send invite later" }),
    ).toBeDisabled();
    expect(
      screen.getByRole("button", { name: "Assign role later" }),
    ).toBeDisabled();
    expect(
      screen.getByRole("button", { name: "Activate membership later" }),
    ).toBeDisabled();
  });
});
