import { cleanup, render, screen, within } from "@testing-library/react";
import type { ReactElement } from "react";
import { createMemoryRouter, Outlet, RouterProvider } from "react-router-dom";
import { afterEach, describe, expect, it } from "vitest";
import { OperatorDemoHomePage } from "./OperatorDemoHomePage";

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

function panelByHeading(name: string) {
  const heading = screen.getByRole("heading", { name });
  const panel = heading.closest(".panel");
  if (!panel) {
    throw new Error(`${name} panel was not rendered`);
  }
  return within(panel as HTMLElement);
}

describe("OperatorDemoHomePage", () => {
  afterEach(() => {
    cleanup();
  });

  it("renders the operator demo home with journey sections", () => {
    renderWorkspace(<OperatorDemoHomePage />);

    expect(screen.getByRole("heading", { name: "Operator demo home" })).toBeInTheDocument();
    expect(screen.getByText("Demo shell")).toBeInTheDocument();
    expect(screen.getByText("Demo journey links")).toBeInTheDocument();
    expect(screen.getByText("Diagnostics UI pending")).toBeInTheDocument();
    expect(screen.getByText("Internal tenant_code")).toBeInTheDocument();

    expect(screen.getByRole("heading", { name: "Setup journey" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Readiness review" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Operational monitoring" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Diagnostics and support" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Persona paths" })).toBeInTheDocument();
  });

  it("links onboarding and readiness steps to their existing shell routes", () => {
    renderWorkspace(<OperatorDemoHomePage />);

    const setup = panelByHeading("Setup journey");
    const readiness = panelByHeading("Readiness review");

    expect(
      setup.getByRole("link", { name: /Company \/ organisation onboarding/ }),
    ).toHaveAttribute("href", "/admin/onboarding/company");
    expect(
      setup.getByRole("link", { name: /Producer \/ sponsor onboarding/ }),
    ).toHaveAttribute("href", "/admin/onboarding/producer-sponsor");
    expect(
      setup.getByRole("link", { name: /Distributor onboarding/ }),
    ).toHaveAttribute("href", "/admin/onboarding/distributor");
    expect(
      setup.getByRole("link", { name: /User \/ member role setup/ }),
    ).toHaveAttribute("href", "/admin/onboarding/members-roles");
    expect(
      readiness.getByRole("link", { name: /Campaign \/ opportunity setup/ }),
    ).toHaveAttribute("href", "/admin/onboarding/campaign-opportunity");
    expect(
      readiness.getByRole("link", { name: /Webhook \/ API setup/ }),
    ).toHaveAttribute("href", "/admin/onboarding/webhook-api");
    expect(
      readiness.getByRole("link", { name: /Onboarding readiness checklist/ }),
    ).toHaveAttribute("href", "/admin/onboarding/readiness");
  });

  it("links read-only monitoring views that already have frontend routes", () => {
    renderWorkspace(<OperatorDemoHomePage />);

    const monitoring = panelByHeading("Operational monitoring");

    expect(
      monitoring.getByRole("link", { name: /Demand marketplace/ }),
    ).toHaveAttribute("href", "/admin/distribution");
    expect(
      monitoring.getByRole("link", { name: /Demand operations/ }),
    ).toHaveAttribute("href", "/admin/distribution/operations");
    expect(
      monitoring.getByRole("link", { name: /Channel operations/ }),
    ).toHaveAttribute("href", "/admin/channels");
    expect(
      monitoring.getByRole("link", { name: /Event fabric/ }),
    ).toHaveAttribute("href", "/admin/events");
    expect(
      monitoring.getByRole("link", { name: /Runtime health/ }),
    ).toHaveAttribute("href", "/admin/health");
    expect(
      monitoring.getByRole("link", { name: /Distributor safe status/ }),
    ).toHaveAttribute("href", "/distributor");
  });

  it("keeps backend-ready diagnostics visible without pretending a frontend exists", () => {
    renderWorkspace(<OperatorDemoHomePage />);

    const diagnostics = panelByHeading("Diagnostics and support");

    expect(diagnostics.getByText("Operator control-plane BFF")).toBeInTheDocument();
    expect(diagnostics.getByText("Outcome trace")).toBeInTheDocument();
    expect(diagnostics.getByText("Liability projection")).toBeInTheDocument();
    expect(diagnostics.getByText("Campaign readiness")).toBeInTheDocument();
    expect(diagnostics.getByText("Link/code diagnostics")).toBeInTheDocument();
    expect(diagnostics.getByText("Tenant-safe analytics")).toBeInTheDocument();
    expect(diagnostics.getByText("Webhook catalog and payload preview")).toBeInTheDocument();
    expect(diagnostics.getAllByText("UI pending")).toHaveLength(7);
    expect(diagnostics.queryByRole("link", { name: /Outcome trace/ })).not.toBeInTheDocument();
  });

  it("shows persona paths, live blockers, and disabled command actions", () => {
    renderWorkspace(<OperatorDemoHomePage />);

    expect(screen.getByText("Platform operator")).toBeInTheDocument();
    expect(screen.getByText("Producer / sponsor / company admin")).toBeInTheDocument();
    expect(screen.getByText("Distributor / partner admin")).toBeInTheDocument();
    expect(screen.getByText("TASK-027 live DB verification")).toBeInTheDocument();
    expect(screen.getByText("TASK-028 drift resolution")).toBeInTheDocument();
    expect(screen.getByText("No live command path")).toBeInTheDocument();

    expect(screen.getByRole("button", { name: "Start live demo later" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Run live smoke check later" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Publish campaign later" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Deliver webhook later" })).toBeDisabled();
    expect(
      screen.getByText("This page does not execute live platform actions."),
    ).toBeInTheDocument();
  });
});
