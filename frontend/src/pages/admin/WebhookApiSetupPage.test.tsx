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
import { WebhookApiSetupPage } from "./WebhookApiSetupPage";

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
          category: "WEBHOOK_API_SETUP",
          display_label: "Webhook / API setup",
          status: "MISSING_EVIDENCE",
          safe_display_status: {
            status: "MISSING_EVIDENCE",
            label: "Missing evidence",
            action_required: true,
            go_live_enabled: false,
          },
          evidence_summary:
            "Webhook/API setup is read-only and missing credential lifecycle evidence.",
          blockers: [
            "Credential lifecycle, callback registration, signing, queueing, delivery, and retry evidence remain unavailable.",
          ],
          next_actions: [
            "Confirm external_tenant_ref and organisation_ref before any future integration review.",
          ],
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

function readinessPanel() {
  const heading = document.getElementById("webhook-readiness-heading");
  if (!heading) {
    throw new Error("Readiness review heading was not rendered");
  }
  const panel = heading.closest(".panel");
  if (!panel) {
    throw new Error("Readiness review panel was not rendered");
  }
  return within(panel as HTMLElement);
}

describe("WebhookApiSetupPage", () => {
  beforeEach(() => {
    mockedGetAdminOnboardingState.mockResolvedValue(onboardingStateResponse());
  });

  afterEach(() => {
    cleanup();
    vi.clearAllMocks();
  });

  it("renders the webhook and API setup shell with credential guardrails", async () => {
    renderWorkspace(<WebhookApiSetupPage />);

    expect(
      screen.getByRole("heading", { name: "Webhook & API credential setup" }),
    ).toBeInTheDocument();
    expect(screen.getByText("Shell only")).toBeInTheDocument();
    expect(screen.getByLabelText(/organisation_ref/)).toBeInTheDocument();
    expect(screen.getByLabelText(/external_tenant_ref/)).toBeInTheDocument();
    expect(screen.getByText("Webhook event categories")).toBeInTheDocument();
    expect(
      screen.getByText("Non-delivering payload preview"),
    ).toBeInTheDocument();
    expect(screen.getByText("Secrets stay unavailable")).toBeInTheDocument();
    expect(screen.getByText("No webhook side effects")).toBeInTheDocument();
    expect(
      screen.getByText(/the internal tenant identifier stays hidden/i),
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        "No API keys, webhook subscriptions, signing material, callback registrations, or deliveries are created from this page.",
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Create API key later" }),
    ).toBeDisabled();
    expect(
      screen.getByRole("button", { name: "Rotate key later" }),
    ).toBeDisabled();
    expect(
      screen.getByRole("button", { name: "Create secret later" }),
    ).toBeDisabled();
    expect(
      screen.getByRole("button", { name: "Send test webhook later" }),
    ).toBeDisabled();
    expect(
      screen.getByRole("button", { name: "Subscribe later" }),
    ).toBeDisabled();
    expect(
      screen.getByRole("button", { name: "Register callback later" }),
    ).toBeDisabled();
    expect(
      screen.getByRole("button", { name: "Sign payload later" }),
    ).toBeDisabled();
    expect(
      screen.getByRole("button", { name: "Queue delivery later" }),
    ).toBeDisabled();
    expect(
      screen.getByRole("button", { name: "Retry delivery later" }),
    ).toBeDisabled();
    expect(
      screen.getByRole("button", { name: "Activate live credentials later" }),
    ).toBeDisabled();
    expect(
      screen.getByRole("button", { name: "Move money later" }),
    ).toBeDisabled();
    expect(await screen.findByText("Read-only")).toBeInTheDocument();
    expect(screen.queryByText(/tenant_code/i)).not.toBeInTheDocument();
  });

  it("shows loading while fetching read-only webhook and API state", () => {
    mockedGetAdminOnboardingState.mockReturnValue(new Promise(() => undefined));
    renderWorkspace(<WebhookApiSetupPage />);

    expect(
      screen.getByText("Loading read-only webhook and API readiness."),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Create API key later" }),
    ).toBeDisabled();
    expect(
      screen.getByRole("button", { name: "Subscribe later" }),
    ).toBeDisabled();
    expect(
      screen.getByRole("button", { name: "Retry delivery later" }),
    ).toBeDisabled();
  });

  it("requests read-only webhook/API state with external references", async () => {
    renderWorkspace(<WebhookApiSetupPage />);

    await waitFor(() => {
      expect(mockedGetAdminOnboardingState).toHaveBeenCalledWith({
        external_tenant_ref: "demo-platform-operator",
        organisation_ref: "demo-organisation",
      });
    });
  });

  it("shows read-only missing evidence without enabling credential or delivery actions", async () => {
    renderWorkspace(<WebhookApiSetupPage />);

    expect(
      await screen.findByText(
        "Webhook/API setup is read-only and missing credential lifecycle evidence.",
      ),
    ).toBeInTheDocument();
    expect(screen.getByText("demo-platform-operator")).toBeInTheDocument();
    expect(screen.getByText("demo-organisation")).toBeInTheDocument();
    expect(screen.getByText("Missing evidence")).toBeInTheDocument();
    expect(
      screen.getByText(
        "Credential lifecycle, callback registration, signing, queueing, delivery, and retry evidence remain unavailable.",
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        "Confirm external_tenant_ref and organisation_ref before any future integration review.",
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Create API key later" }),
    ).toBeDisabled();
    expect(
      screen.getByRole("button", { name: "Create secret later" }),
    ).toBeDisabled();
    expect(
      screen.getByRole("button", { name: "Register callback later" }),
    ).toBeDisabled();
    expect(
      screen.getByRole("button", { name: "Sign payload later" }),
    ).toBeDisabled();
    expect(
      screen.getByRole("button", { name: "Queue delivery later" }),
    ).toBeDisabled();
    expect(
      screen.getByRole("button", { name: "Retry delivery later" }),
    ).toBeDisabled();
    expect(
      screen.getByRole("button", { name: "Move money later" }),
    ).toBeDisabled();
  });

  it("updates local readiness and catalog preview without enabling credential actions", async () => {
    renderWorkspace(<WebhookApiSetupPage />);

    await screen.findByText("Read-only");
    fireEvent.change(screen.getByLabelText(/organisation_ref/), {
      target: { value: "org-acme" },
    });
    fireEvent.change(screen.getByLabelText(/external_tenant_ref/), {
      target: { value: "acme-distribution" },
    });
    fireEvent.change(screen.getByLabelText(/Integration owner \/ contact/), {
      target: { value: "integration-owner@example.test" },
    });
    fireEvent.change(screen.getByLabelText(/API environment intention/), {
      target: { value: "Sandbox then live review" },
    });
    fireEvent.change(screen.getByLabelText(/Callback URL placeholder/), {
      target: { value: "https://hooks.example.test/dlaas/events" },
    });
    fireEvent.change(screen.getByLabelText(/Intended authentication method/), {
      target: { value: "Signed webhook secret later" },
    });
    fireEvent.change(screen.getByLabelText(/IP allowlist notes/), {
      target: { value: "Partner network ranges to confirm later" },
    });
    fireEvent.change(screen.getByLabelText(/Payload format \/ version/), {
      target: { value: "Safe diagnostics preview" },
    });
    fireEvent.change(screen.getByLabelText(/Go-live readiness status/), {
      target: { value: "Ready for future credential API" },
    });
    fireEvent.click(screen.getByLabelText(/Fulfilment events/));
    fireEvent.click(screen.getByLabelText(/Settlement events/));

    expect(
      screen.getByText(
        "Required integration setup fields are captured locally.",
      ),
    ).toBeInTheDocument();
    expect(screen.getByText("acme-distribution")).toBeInTheDocument();
    expect(
      screen.getByText(
        /Campaign events, Outcome events, Fulfilment events, Settlement events/,
      ),
    ).toBeInTheDocument();
    expect(
      screen.getAllByText("Safe diagnostics preview").length,
    ).toBeGreaterThanOrEqual(1);
    expect(readinessPanel().getByText("Draft complete")).toBeInTheDocument();
    expect(readinessPanel().getAllByText("Ready")).toHaveLength(5);
    expect(readinessPanel().getByText("Pending")).toBeInTheDocument();
    expect(
      screen.getByText("Backend credential lifecycle"),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Create API key later" }),
    ).toBeDisabled();
    expect(
      screen.getByRole("button", { name: "Create secret later" }),
    ).toBeDisabled();
    expect(
      screen.getByRole("button", { name: "Subscribe later" }),
    ).toBeDisabled();
    expect(
      screen.getByRole("button", { name: "Register callback later" }),
    ).toBeDisabled();
    expect(
      screen.getByRole("button", { name: "Sign payload later" }),
    ).toBeDisabled();
    expect(
      screen.getByRole("button", { name: "Queue delivery later" }),
    ).toBeDisabled();
    expect(
      screen.getByRole("button", { name: "Retry delivery later" }),
    ).toBeDisabled();
  });

  it("falls back to local shell state when read-only webhook/API state is unavailable", async () => {
    mockedGetAdminOnboardingState.mockRejectedValue(new Error("offline"));
    renderWorkspace(<WebhookApiSetupPage />);

    expect(
      await screen.findByText("Using local webhook/API setup fallback."),
    ).toBeInTheDocument();
    expect(
      screen.getByText("Non-delivering payload preview"),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Create API key later" }),
    ).toBeDisabled();
    expect(
      screen.getByRole("button", { name: "Send test webhook later" }),
    ).toBeDisabled();
    expect(
      screen.getByRole("button", { name: "Activate live credentials later" }),
    ).toBeDisabled();
  });

  it("keeps secret material redacted and does not show real credential examples", async () => {
    renderWorkspace(<WebhookApiSetupPage />);

    await screen.findByText("Read-only");
    expect(
      screen.getByText(
        "Never generated, stored, displayed, signed, or delivered in this shell.",
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        "No API key, token, signing material, client secret, certificate, or credential value is created or displayed.",
      ),
    ).toBeInTheDocument();
    expect(document.body.textContent).not.toMatch(
      /sk_live|sk_test|secret_[A-Za-z0-9]|Bearer\s+[A-Za-z0-9]|-----BEGIN|client_secret_[A-Za-z0-9]|signing_secret_[A-Za-z0-9]|queue_id|retry_attempt|delivery_id/i,
    );
    expect(document.body.textContent).not.toMatch(/tenant_code/i);
  });

  it("links integration setup to the onboarding journey", async () => {
    renderWorkspace(<WebhookApiSetupPage />);

    await screen.findByText("Read-only");
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
      screen.getByRole("link", { name: /Campaign \/ opportunity setup/ }),
    ).toHaveAttribute("href", "/admin/onboarding/campaign-opportunity");
  });
});
