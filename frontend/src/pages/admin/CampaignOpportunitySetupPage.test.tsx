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
import { CampaignOpportunitySetupPage } from "./CampaignOpportunitySetupPage";

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
  const heading = document.getElementById("campaign-readiness-heading");
  if (!heading) {
    throw new Error("Readiness review heading was not rendered");
  }
  const panel = heading.closest(".panel");
  if (!panel) {
    throw new Error("Readiness review panel was not rendered");
  }
  return within(panel as HTMLElement);
}

describe("CampaignOpportunitySetupPage", () => {
  afterEach(() => {
    cleanup();
  });

  it("renders the campaign opportunity wizard shell with safe launch guardrails", () => {
    renderWorkspace(<CampaignOpportunitySetupPage />);

    expect(
      screen.getByRole("heading", { name: "Campaign & opportunity setup wizard" }),
    ).toBeInTheDocument();
    expect(screen.getByText("Shell only")).toBeInTheDocument();
    expect(screen.getByLabelText(/organisation_ref/)).toBeInTheDocument();
    expect(screen.getByLabelText(/campaign_code/)).toBeInTheDocument();
    expect(screen.getByLabelText(/opportunity_ref/)).toBeInTheDocument();
    expect(screen.getByText("External setup identifiers")).toBeInTheDocument();
    expect(screen.getByText("Lifecycle commands are unavailable")).toBeInTheDocument();
    expect(screen.getByText("Money setup is intent only")).toBeInTheDocument();
    expect(
      screen.getByText(
        "No campaign, opportunity, route, link, code, reward, or funding records are created from this page.",
      ),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Save campaign later" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Publish opportunity later" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Generate links later" })).toBeDisabled();
  });

  it("walks wizard steps and updates local readiness without enabling launch actions", () => {
    renderWorkspace(<CampaignOpportunitySetupPage />);

    fireEvent.change(screen.getByLabelText(/organisation_ref/), {
      target: { value: "org-acme" },
    });
    fireEvent.change(screen.getByLabelText(/campaign_code/), {
      target: { value: "ACME-INSURANCE-2026" },
    });
    fireEvent.change(screen.getByLabelText(/opportunity_ref/), {
      target: { value: "opp-acme-insurance-2026" },
    });
    fireEvent.change(screen.getByLabelText(/Campaign name/), {
      target: { value: "Acme insurance launch" },
    });
    fireEvent.change(screen.getByLabelText(/Market \/ country/), {
      target: { value: "South Africa" },
    });

    fireEvent.click(screen.getByRole("button", { name: /2\. Participants/ }));
    fireEvent.change(screen.getByLabelText(/producer_ref \/ sponsor_ref/), {
      target: { value: "prod-acme-insurance" },
    });
    fireEvent.change(screen.getByLabelText(/Eligible distributor type/), {
      target: { value: "Advisor network" },
    });

    fireEvent.click(screen.getByRole("button", { name: /3\. Distribution model/ }));
    fireEvent.change(screen.getByLabelText(/Channel \/ distribution model/), {
      target: { value: "QR/link distribution" },
    });
    fireEvent.change(screen.getByLabelText(/Link\/code intent/), {
      target: { value: "Future distributor route link" },
    });

    fireEvent.click(screen.getByRole("button", { name: /4\. Outcome and reward intention/ }));
    fireEvent.change(screen.getByLabelText(/Intended outcome event/), {
      target: { value: "POLICY_ACTIVATED" },
    });
    fireEvent.change(screen.getByLabelText(/Reward \/ commission policy intention/), {
      target: { value: "Reward plus distributor commission" },
    });

    fireEvent.click(screen.getByRole("button", { name: /5\. Funding intention/ }));
    fireEvent.change(screen.getByLabelText(/Funding model intention/), {
      target: { value: "Prefunded campaign later" },
    });

    fireEvent.click(screen.getByRole("button", { name: /6\. Readiness review/ }));
    fireEvent.change(screen.getByLabelText(/Go-live target \/ status/), {
      target: { value: "Ready for future readiness API" },
    });

    expect(
      screen.getByText("Required wizard fields are captured locally."),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Save campaign later" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Publish opportunity later" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Generate links later" })).toBeDisabled();
    expect(readinessPanel().getByText("Draft complete")).toBeInTheDocument();
    expect(readinessPanel().getAllByText("Ready")).toHaveLength(5);
    expect(readinessPanel().getByText("Pending")).toBeInTheDocument();
    expect(screen.getByText("Backend launch lifecycle")).toBeInTheDocument();
  });

  it("links campaign setup to onboarding and monitoring surfaces", () => {
    renderWorkspace(<CampaignOpportunitySetupPage />);

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
      screen.getByRole("link", { name: /Demand marketplace/ }),
    ).toHaveAttribute("href", "/admin/distribution");
  });
});
