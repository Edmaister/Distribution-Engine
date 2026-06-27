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
import { CompanyOnboardingPage } from "./CompanyOnboardingPage";

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
  afterEach(() => {
    cleanup();
  });

  it("renders the company onboarding shell with external identifier guardrails", () => {
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
    expect(screen.getByText("tenant_code stays internal")).toBeInTheDocument();
    expect(
      screen.getByText("No records are created from this page."),
    ).toBeInTheDocument();
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
    ).toHaveAttribute("href", "/sponsor");
    expect(
      screen.getByRole("link", { name: /Distributor onboarding/ }),
    ).toHaveAttribute("href", "/distributor");
    expect(
      screen.getByRole("link", { name: /Operator monitoring/ }),
    ).toHaveAttribute("href", "/admin");
  });
});
