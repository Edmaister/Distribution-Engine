import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";
import { CommercialEntitlementJourney } from "./ReferralSaasAccountMaintenancePage";
import { recordReferralSaasCommercialEntitlement, type ReferralSaasCommercialEntitlementResponse } from "../../api/endpoints/referralSaasAccounts";
import { solutionModuleAllowed } from "../../api/solutionPackageAccess";
vi.mock("../../api/endpoints/referralSaasAccounts", async (original) => ({ ...await original<object>(), recordReferralSaasCommercialEntitlement: vi.fn() }));
afterEach(() => { cleanup(); vi.clearAllMocks(); });
const packages = [
  { code: "REFERRAL_MANAGEMENT", name: "Referral Management", description: "Referral workflows", solutions: ["REFERRAL_MANAGEMENT"], recommended: false },
  { code: "CAMPAIGN_ATTRIBUTION", name: "Campaign Attribution", description: "Registered campaign evidence", solutions: ["CAMPAIGN_ATTRIBUTION"], recommended: false },
  { code: "REFERRAL_MANAGEMENT_AND_ATTRIBUTION", name: "Referral Management + Campaign Attribution", description: "Both solutions", solutions: ["REFERRAL_MANAGEMENT", "CAMPAIGN_ATTRIBUTION"], recommended: true },
];
const response = { commercialEntitlement: { overallStatus: "COMMERCIAL_SETUP_REQUIRED", plan: { planCode: "REFERRAL_SAAS_H1_REFERENCE", planName: "Solution package not selected", contractSource: "NOT_CONFIGURED" }, entitlementEvidence: {}, solutionPackages: packages, limits: {} } } as unknown as ReferralSaasCommercialEntitlementResponse;
function show(owners: Record<string, unknown>[] = [{ membershipRef: "owner-1", displayName: "Carla" }]) {
  return render(<QueryClientProvider client={new QueryClient({ defaultOptions: { mutations: { retry: false } } })}><MemoryRouter><CommercialEntitlementJourney owners={owners} accountRef="a" entitlement={response} error={null} externalTenantRef="customer" isLoading={false} productionActivationError={null} isProductionActivationLoading={false} selectedCustomerPath="/customer" onRefresh={async () => {}} /></MemoryRouter></QueryClientProvider>);
}
describe("commercial solution approval", () => {
  it.each(packages)("records $name using the server catalogue", async (pkg) => {
    vi.mocked(recordReferralSaasCommercialEntitlement).mockResolvedValue(response);
    show();
    expect(screen.getAllByRole("radio")).toHaveLength(3);
    expect(screen.getAllByRole("button", { name: "Record commercial approval evidence" })).toHaveLength(1);
    fireEvent.click(screen.getByRole("radio", { name: pkg.name }));
    fireEvent.change(screen.getByLabelText(/Approval reference/), { target: { value: "ORDER-464" } });
    fireEvent.change(screen.getByLabelText(/Responsible Account owner/), { target: { value: "owner-1" } });
    fireEvent.click(screen.getByRole("button", { name: "Record commercial approval evidence" }));
    await waitFor(() => expect(recordReferralSaasCommercialEntitlement).toHaveBeenCalled());
    expect(vi.mocked(recordReferralSaasCommercialEntitlement).mock.calls[0][0].entitlement).toMatchObject({ planCode: pkg.code, planName: pkg.name, responsibleOwner: "owner-1" });
  });
  it("requires an owner and presents no invented quotas", () => {
    show([]);
    expect(screen.getByRole("button", { name: "Record commercial approval evidence" })).toBeDisabled();
    fireEvent.click(screen.getByRole("button", { name: /Limits/ }));
    expect(screen.getByText(/No package limits configured/)).toBeInTheDocument();
  });
  it("blocks navigation outside an attribution package", () => {
    const commercial = { ...response.commercialEntitlement, plan: { ...response.commercialEntitlement.plan, planCode: "CAMPAIGN_ATTRIBUTION" }, enabledModules: ["attribution"] };
    expect(solutionModuleAllowed(commercial, "campaigns")).toBe(false);
    expect(solutionModuleAllowed(commercial, "attribution")).toBe(true);
    expect(solutionModuleAllowed(commercial, "commercial")).toBe(true);
  });
});
