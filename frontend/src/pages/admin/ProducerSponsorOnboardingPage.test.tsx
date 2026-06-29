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
import { ProducerSponsorOnboardingPage } from "./ProducerSponsorOnboardingPage";

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
        category: "PRODUCER_SPONSOR_SETUP",
        display_label: "Producer / sponsor setup",
        status: "MISSING_EVIDENCE",
        safe_display_status: {
          status: "MISSING_EVIDENCE",
          label: "Missing evidence",
          action_required: true,
          go_live_enabled: false,
        },
        evidence_summary: "Producer/sponsor evidence is partially available.",
        blockers: ["Producer/sponsor onboarding remains shell-only."],
        next_actions: ["Confirm producer_ref and sponsor_ref before review."],
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

describe("ProducerSponsorOnboardingPage", () => {
  beforeEach(() => {
    mockedGetAdminOnboardingState.mockResolvedValue(onboardingStateResponse());
  });

  afterEach(() => {
    cleanup();
    vi.clearAllMocks();
  });

  it("renders the producer sponsor onboarding shell with safe identifier guardrails", async () => {
    renderWorkspace(<ProducerSponsorOnboardingPage />);

    expect(
      screen.getByRole("heading", {
        name: "Producer & sponsor onboarding",
      }),
    ).toBeInTheDocument();
    expect(screen.getByText("Shell only")).toBeInTheDocument();
    expect(
      screen.getByLabelText(/Producer \/ sponsor name/),
    ).toBeInTheDocument();
    expect(screen.getByLabelText(/external_tenant_ref/)).toBeInTheDocument();
    expect(screen.getByLabelText(/producer_ref/)).toBeInTheDocument();
    expect(screen.getByLabelText(/sponsor_ref/)).toBeInTheDocument();
    expect(screen.getByLabelText(/organisation_ref/)).toBeInTheDocument();
    expect(screen.getByText("External sponsor identity")).toBeInTheDocument();
    expect(screen.getByText("Funding is not active")).toBeInTheDocument();
    expect(
      screen.getByText(
        "No money or sponsor records are created from this page.",
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Create sponsor later" }),
    ).toBeDisabled();
    expect(
      screen.getByRole("button", { name: "Configure funding later" }),
    ).toBeDisabled();
    expect(
      await screen.findByText("Read-only platform state"),
    ).toBeInTheDocument();
    expect(screen.queryByText(/tenant_code/i)).not.toBeInTheDocument();
  });

  it("shows loading while fetching read-only producer state", () => {
    mockedGetAdminOnboardingState.mockReturnValue(new Promise(() => undefined));
    renderWorkspace(<ProducerSponsorOnboardingPage />);

    expect(
      screen.getByText("Loading read-only producer readiness."),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Create sponsor later" }),
    ).toBeDisabled();
    expect(
      screen.getByRole("button", { name: "Configure funding later" }),
    ).toBeDisabled();
  });

  it("requests read-only producer state with external references", async () => {
    renderWorkspace(<ProducerSponsorOnboardingPage />);

    await waitFor(() => {
      expect(mockedGetAdminOnboardingState).toHaveBeenCalledWith({
        external_tenant_ref: "demo-platform-operator",
        organisation_ref: "demo-organisation",
        producer_ref: "demo-producer",
        sponsor_ref: "demo-sponsor",
      });
    });
  });

  it("shows read-only partial evidence without enabling sponsor or funding actions", async () => {
    renderWorkspace(<ProducerSponsorOnboardingPage />);

    expect(
      await screen.findByText(
        "Producer/sponsor evidence is partially available.",
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByText("Producer/sponsor onboarding remains shell-only."),
    ).toBeInTheDocument();
    expect(
      screen.getByText("Confirm producer_ref and sponsor_ref before review."),
    ).toBeInTheDocument();
    expect(screen.getByText("demo-producer")).toBeInTheDocument();
    expect(screen.getByText("demo-sponsor")).toBeInTheDocument();
    expect(screen.getByText("Missing evidence")).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Create sponsor later" }),
    ).toBeDisabled();
    expect(
      screen.getByRole("button", { name: "Configure funding later" }),
    ).toBeDisabled();
  });

  it("updates local readiness without enabling sponsor or funding actions", () => {
    renderWorkspace(<ProducerSponsorOnboardingPage />);

    fireEvent.change(screen.getByLabelText(/Producer \/ sponsor name/), {
      target: { value: "Acme Insurance Sponsors" },
    });
    fireEvent.change(screen.getByLabelText(/external_tenant_ref/), {
      target: { value: "acme-insurance" },
    });
    fireEvent.change(screen.getByLabelText(/producer_ref/), {
      target: { value: "prod-acme-insurance" },
    });
    fireEvent.change(screen.getByLabelText(/sponsor_ref/), {
      target: { value: "spon-acme-insurance" },
    });
    fireEvent.change(screen.getByLabelText(/organisation_ref/), {
      target: { value: "org-acme" },
    });
    fireEvent.change(screen.getByLabelText(/Industry \/ vertical/), {
      target: { value: "Insurance" },
    });
    fireEvent.change(screen.getByLabelText(/Producer admin contact/), {
      target: { value: "producer-admin@example.test" },
    });
    fireEvent.change(screen.getByLabelText(/Campaign \/ opportunity role/), {
      target: { value: "Opportunity sponsor" },
    });

    expect(
      screen.getByText("Required shell fields are captured locally."),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Create sponsor later" }),
    ).toBeDisabled();
    expect(
      screen.getByRole("button", { name: "Configure funding later" }),
    ).toBeDisabled();
    expect(readinessPanel().getByText("Profile drafted")).toBeInTheDocument();
    expect(readinessPanel().getAllByText("Ready")).toHaveLength(4);
    expect(readinessPanel().getByText("Pending")).toBeInTheDocument();
    expect(screen.getByText("Backend sponsor onboarding")).toBeInTheDocument();
  });

  it("links producer setup to company, distributor, and producer workspace surfaces", () => {
    renderWorkspace(<ProducerSponsorOnboardingPage />);

    expect(
      screen.getByRole("link", { name: /Company onboarding/ }),
    ).toHaveAttribute("href", "/admin/onboarding/company");
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
      screen.getByRole("link", { name: /Producer workspace/ }),
    ).toHaveAttribute("href", "/sponsor");
  });

  it("falls back to local shell state when read-only producer state is unavailable", async () => {
    mockedGetAdminOnboardingState.mockRejectedValue(new Error("offline"));
    renderWorkspace(<ProducerSponsorOnboardingPage />);

    expect(
      await screen.findByText("Using local producer setup fallback."),
    ).toBeInTheDocument();
    expect(screen.getAllByText("Producer profile").length).toBeGreaterThan(0);
    expect(
      screen.getByRole("button", { name: "Create sponsor later" }),
    ).toBeDisabled();
    expect(
      screen.getByRole("button", { name: "Configure funding later" }),
    ).toBeDisabled();
  });
});
