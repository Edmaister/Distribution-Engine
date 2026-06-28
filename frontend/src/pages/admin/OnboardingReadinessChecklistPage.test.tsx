import { cleanup, render, screen, within } from "@testing-library/react";
import type { ReactElement } from "react";
import { createMemoryRouter, Outlet, RouterProvider } from "react-router-dom";
import { afterEach, describe, expect, it } from "vitest";
import { OnboardingReadinessChecklistPage } from "./OnboardingReadinessChecklistPage";

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

function checklistPanel() {
  const heading = document.getElementById("checklist-heading");
  if (!heading) {
    throw new Error("Checklist heading was not rendered");
  }
  const panel = heading.closest(".panel");
  if (!panel) {
    throw new Error("Checklist panel was not rendered");
  }
  return within(panel as HTMLElement);
}

function blockersPanel() {
  const heading = document.getElementById("blockers-heading");
  if (!heading) {
    throw new Error("Blockers heading was not rendered");
  }
  const panel = heading.closest(".panel");
  if (!panel) {
    throw new Error("Blockers panel was not rendered");
  }
  return within(panel as HTMLElement);
}

describe("OnboardingReadinessChecklistPage", () => {
  afterEach(() => {
    cleanup();
  });

  it("renders the onboarding readiness checklist with demo-safe statuses", () => {
    renderWorkspace(<OnboardingReadinessChecklistPage />);

    expect(
      screen.getByRole("heading", { name: "Onboarding readiness checklist" }),
    ).toBeInTheDocument();
    expect(screen.getByText("Review only")).toBeInTheDocument();
    expect(screen.getByText("Ready categories")).toBeInTheDocument();
    expect(screen.getByText("Blocked categories")).toBeInTheDocument();
    expect(screen.getByText("Internal tenant_code")).toBeInTheDocument();
    expect(checklistPanel().getByText("Organisation profile")).toBeInTheDocument();
    expect(checklistPanel().getByText("Producer / sponsor setup")).toBeInTheDocument();
    expect(checklistPanel().getByText("Distributor setup")).toBeInTheDocument();
    expect(checklistPanel().getByText("Members and roles")).toBeInTheDocument();
    expect(checklistPanel().getByText("Campaign / opportunity setup")).toBeInTheDocument();
    expect(checklistPanel().getByText("Webhook / API setup")).toBeInTheDocument();
    expect(checklistPanel().getByText("Security and permissions")).toBeInTheDocument();
    expect(checklistPanel().getByText("Go-live controls")).toBeInTheDocument();
    expect(checklistPanel().getAllByText("Ready")).toHaveLength(2);
    expect(checklistPanel().getAllByText("In progress")).toHaveLength(4);
    expect(checklistPanel().getAllByText("Blocked")).toHaveLength(2);
  });

  it("links each setup category back to the relevant onboarding shell", () => {
    renderWorkspace(<OnboardingReadinessChecklistPage />);

    expect(
      checklistPanel().getByRole("link", { name: /Organisation profile/ }),
    ).toHaveAttribute("href", "/admin/onboarding/company");
    expect(
      checklistPanel().getByRole("link", { name: /Producer \/ sponsor setup/ }),
    ).toHaveAttribute("href", "/admin/onboarding/producer-sponsor");
    expect(
      checklistPanel().getByRole("link", { name: /Distributor setup/ }),
    ).toHaveAttribute("href", "/admin/onboarding/distributor");
    expect(
      checklistPanel().getByRole("link", { name: /Members and roles/ }),
    ).toHaveAttribute("href", "/admin/onboarding/members-roles");
    expect(
      checklistPanel().getByRole("link", { name: /^Campaign \/ opportunity setup/ }),
    ).toHaveAttribute("href", "/admin/onboarding/campaign-opportunity");
    expect(
      checklistPanel().getByRole("link", { name: /Webhook \/ API setup/ }),
    ).toHaveAttribute("href", "/admin/onboarding/webhook-api");
  });

  it("shows live verification blockers and keeps go-live actions disabled", () => {
    renderWorkspace(<OnboardingReadinessChecklistPage />);

    expect(blockersPanel().getByText("TASK-027 live DB verification")).toBeInTheDocument();
    expect(blockersPanel().getByText("TASK-028 drift resolution")).toBeInTheDocument();
    expect(
      blockersPanel().getByText(/approved safe read-only runtime database access/),
    ).toBeInTheDocument();
    expect(
      blockersPanel().getByText(/verified live\/schema mismatch/),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Request go-live review later" }),
    ).toBeDisabled();
    expect(
      screen.getByRole("button", { name: "Mark ready for review later" }),
    ).toBeDisabled();
  });

  it("keeps the readiness view clear of live command and money movement behaviour", () => {
    renderWorkspace(<OnboardingReadinessChecklistPage />);

    expect(
      screen.getByText(
        "This checklist does not activate go-live, publish campaigns, create credentials, or move money.",
      ),
    ).toBeInTheDocument();
    expect(screen.getByText("No live commands")).toBeInTheDocument();
    expect(screen.getByText("Demo review only")).toBeInTheDocument();
    expect(
      screen.getByText(/wallet, funding, fulfilment, settlement, retry, and webhook delivery stay disabled/),
    ).toBeInTheDocument();
  });
});
