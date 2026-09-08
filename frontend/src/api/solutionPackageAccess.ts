import type { ReferralSaasCommercialEntitlement } from "./endpoints/referralSaasAccounts";

// Shared setup/support remain accessible while an operator repairs approval evidence.
const packagedModules = new Set(["campaigns", "referrals", "referrers", "links", "progress", "attribution", "journeys", "products", "programmes"]);
export function solutionModuleAllowed(commercial: ReferralSaasCommercialEntitlement | undefined, module: string) {
  if (!packagedModules.has(module)) return true;
  if (!commercial || commercial.plan.planCode === "REFERRAL_SAAS_H1_REFERENCE") return true;
  return commercial.enabledModules?.includes(module) ?? false;
}
export function solutionIncluded(commercial: ReferralSaasCommercialEntitlement | undefined, solution: string) {
  if (!commercial || commercial.plan.planCode === "REFERRAL_SAAS_H1_REFERENCE") return true;
  return commercial.overallStatus === "COMMERCIAL_READY" && (commercial.solutionPackage?.solutions.includes(solution) ?? false);
}
