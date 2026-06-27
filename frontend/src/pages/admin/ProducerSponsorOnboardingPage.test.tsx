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
import { ProducerSponsorOnboardingPage } from "./ProducerSponsorOnboardingPage";

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
  afterEach(() => {
    cleanup();
  });

  it("renders the producer sponsor onboarding shell with safe identifier guardrails", () => {
    renderWorkspace(<ProducerSponsorOnboardingPage />);

    expect(
      screen.getByRole("heading", {
        name: "Producer & sponsor onboarding",
      }),
    ).toBeInTheDocument();
    expect(screen.getByText("Shell only")).toBeInTheDocument();
    expect(screen.getByLabelText(/Producer \/ sponsor name/)).toBeInTheDocument();
    expect(screen.getByLabelText(/external_tenant_ref/)).toBeInTheDocument();
    expect(screen.getByLabelText(/producer_ref/)).toBeInTheDocument();
    expect(screen.getByLabelText(/sponsor_ref/)).toBeInTheDocument();
    expect(screen.getByLabelText(/organisation_ref/)).toBeInTheDocument();
    expect(screen.getByText("External sponsor identity")).toBeInTheDocument();
    expect(screen.getByText("Funding is not active")).toBeInTheDocument();
    expect(
      screen.getByText("No money or sponsor records are created from this page."),
    ).toBeInTheDocument();
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
    ).toHaveAttribute("href", "/distributor");
    expect(
      screen.getByRole("link", { name: /Producer workspace/ }),
    ).toHaveAttribute("href", "/sponsor");
  });
});
