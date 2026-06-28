import {
  cleanup,
  fireEvent,
  render,
  screen,
  within,
} from "@testing-library/react";
import type { ReactElement } from "react";
import { createMemoryRouter, Outlet, RouterProvider } from "react-router-dom";
import { afterEach, describe, expect, it } from "vitest";
import { WebhookApiSetupPage } from "./WebhookApiSetupPage";

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
  afterEach(() => {
    cleanup();
  });

  it("renders the webhook and API setup shell with credential guardrails", () => {
    renderWorkspace(<WebhookApiSetupPage />);

    expect(
      screen.getByRole("heading", { name: "Webhook & API credential setup" }),
    ).toBeInTheDocument();
    expect(screen.getByText("Shell only")).toBeInTheDocument();
    expect(screen.getByLabelText(/organisation_ref/)).toBeInTheDocument();
    expect(screen.getByLabelText(/external_tenant_ref/)).toBeInTheDocument();
    expect(screen.getByText("Webhook event categories")).toBeInTheDocument();
    expect(screen.getByText("Non-delivering payload preview")).toBeInTheDocument();
    expect(screen.getByText("Secrets stay unavailable")).toBeInTheDocument();
    expect(screen.getByText("No webhook side effects")).toBeInTheDocument();
    expect(
      screen.getByText(
        "No API keys, webhook subscriptions, signing material, callback registrations, or deliveries are created from this page.",
      ),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Create API key later" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Rotate key later" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Create secret later" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Send test webhook later" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Subscribe later" })).toBeDisabled();
    expect(
      screen.getByRole("button", { name: "Activate live credentials later" }),
    ).toBeDisabled();
  });

  it("updates local readiness and catalog preview without enabling credential actions", () => {
    renderWorkspace(<WebhookApiSetupPage />);

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
      screen.getByText("Required integration setup fields are captured locally."),
    ).toBeInTheDocument();
    expect(screen.getByText("acme-distribution")).toBeInTheDocument();
    expect(
      screen.getByText(/Campaign events, Outcome events, Fulfilment events, Settlement events/),
    ).toBeInTheDocument();
    expect(screen.getAllByText("Safe diagnostics preview").length).toBeGreaterThanOrEqual(1);
    expect(readinessPanel().getByText("Draft complete")).toBeInTheDocument();
    expect(readinessPanel().getAllByText("Ready")).toHaveLength(5);
    expect(readinessPanel().getByText("Pending")).toBeInTheDocument();
    expect(screen.getByText("Backend credential lifecycle")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Create API key later" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Create secret later" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Subscribe later" })).toBeDisabled();
  });

  it("keeps secret material redacted and does not show real credential examples", () => {
    renderWorkspace(<WebhookApiSetupPage />);

    expect(
      screen.getByText(
        "Never generated, stored, displayed, signed, or delivered in this shell.",
      ),
    ).toBeInTheDocument();
    expect(screen.getByText("No API key, token, signing material, client secret, certificate, or credential value is created or displayed.")).toBeInTheDocument();
    expect(document.body.textContent).not.toMatch(/sk_live|sk_test|secret_[A-Za-z0-9]|Bearer\s+[A-Za-z0-9]/);
  });

  it("links integration setup to the onboarding journey", () => {
    renderWorkspace(<WebhookApiSetupPage />);

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
