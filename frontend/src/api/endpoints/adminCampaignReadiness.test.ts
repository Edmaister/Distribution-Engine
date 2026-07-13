import { beforeEach, describe, expect, it, vi } from "vitest";

import { apiRequest } from "../client";
import { getAdminCampaignReadiness } from "./adminCampaignReadiness";

vi.mock("../client", () => ({
  apiRequest: vi.fn(),
}));

const mockedApiRequest = vi.mocked(apiRequest);

describe("adminCampaignReadiness endpoint", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockedApiRequest.mockResolvedValue({ status: "ok" });
  });

  it("maps campaign readiness requests to the existing read-only admin route", async () => {
    await getAdminCampaignReadiness({
      campaignCode: "camp 001",
      tenantCode: "FNB",
      operation: "GENERATE_LINKS",
      opportunityId: "opp-1",
      includeEvidence: false,
    });

    expect(mockedApiRequest).toHaveBeenCalledWith(
      "admin/campaigns/camp%20001/readiness",
      {
        query: {
          tenant_code: "FNB",
          operation: "GENERATE_LINKS",
          opportunity_id: "opp-1",
          include_evidence: false,
        },
      },
    );
  });

  it("does not accept product account references as caller-supplied scope", async () => {
    await getAdminCampaignReadiness({
      campaignCode: "CAMP001",
      tenantCode: "FNB",
    });

    expect(JSON.stringify(mockedApiRequest.mock.calls)).not.toMatch(
      /account_ref|external_tenant_ref/i,
    );
  });
});
