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
import { DistributorOnboardingPage } from "./DistributorOnboardingPage";

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
  afterEach(() => {
    cleanup();
  });

  it("renders the distributor onboarding shell with safe reference guardrails", () => {
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
    expect(screen.getByText("External distributor identity")).toBeInTheDocument();
    expect(screen.getByText("Routes are not active")).toBeInTheDocument();
    expect(screen.getByText("Wallets are not created")).toBeInTheDocument();
    expect(
      screen.getByText("No distributor or marketplace records are created from this page."),
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
    fireEvent.change(screen.getByLabelText(/Campaign \/ opportunity participation/), {
      target: { value: "Opportunity candidate" },
    });

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
    expect(screen.getByText("Backend distributor onboarding")).toBeInTheDocument();
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
});
