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
import { MemberRoleOnboardingPage } from "./MemberRoleOnboardingPage";

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
  afterEach(() => {
    cleanup();
  });

  it("renders the member role setup shell with permission guardrails", () => {
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
      screen.getByText("No user, invite, membership, or role records are created from this page."),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Send invite later" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Assign role later" })).toBeDisabled();
    expect(
      screen.getByRole("button", { name: "Activate membership later" }),
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
    expect(screen.getByRole("button", { name: "Send invite later" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Assign role later" })).toBeDisabled();
    expect(
      screen.getByRole("button", { name: "Activate membership later" }),
    ).toBeDisabled();
    expect(readinessPanel().getByText("Profile drafted")).toBeInTheDocument();
    expect(readinessPanel().getAllByText("Ready")).toHaveLength(4);
    expect(readinessPanel().getByText("Pending")).toBeInTheDocument();
    expect(screen.getByText("Backend membership lifecycle")).toBeInTheDocument();
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
      screen.getByRole("link", { name: /Operator monitoring/ }),
    ).toHaveAttribute("href", "/admin");
  });
});
