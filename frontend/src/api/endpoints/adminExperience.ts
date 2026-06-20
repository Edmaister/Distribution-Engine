import { apiRequest } from "../client";

export type AdminExperienceSection = {
  status: string;
  data?: unknown;
  error?: string | null;
  degraded: boolean;
};

export type AdminCommandCentreExperience = {
  status: string;
  tenantCode: string;
  sections: Record<string, AdminExperienceSection | undefined>;
  unavailableSections: string[];
  guardrail: string;
};

export function getAdminCommandCentreExperience(
  tenantCode: string,
  outcomeLimit = 25,
): Promise<AdminCommandCentreExperience> {
  return apiRequest<AdminCommandCentreExperience>("v1/experience/admin-command-centre", {
    query: {
      tenant_code: tenantCode,
      outcome_limit: outcomeLimit,
    },
  });
}
