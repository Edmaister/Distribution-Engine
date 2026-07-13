import { beforeEach, describe, expect, it, vi } from "vitest";

import { apiRequest } from "../client";
import {
  captureReferralSaasRefereeUcn,
  issueReferralSaasCode,
  inspectReferralSaasOperatorLink,
  inspectReferralSaasOperatorAttributionTrace,
  validateReferralSaasCode,
} from "./referralSaasLinks";

vi.mock("../client", () => ({
  apiRequest: vi.fn(),
}));

const mockedApiRequest = vi.mocked(apiRequest);

describe("referralSaasLinks endpoint client", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockedApiRequest.mockResolvedValue({ status: "ok" });
  });

  it("issues Referral SaaS codes through the product wrapper", async () => {
    await issueReferralSaasCode({
      referrerUcn: "5555555555",
      sticker: "QR001",
      segment: "PERSONAL",
      preferredHandle: "edwin",
      acceptedTerms: true,
    });

    expect(mockedApiRequest).toHaveBeenCalledWith("v1/referral-saas/referral-codes", {
      method: "POST",
      body: {
        referrerUcn: "5555555555",
        sticker: "QR001",
        segment: "PERSONAL",
        preferredHandle: "edwin",
        acceptedTerms: true,
      },
    });
  });

  it("validates Referral SaaS codes through the product wrapper", async () => {
    await validateReferralSaasCode({
      tenantCode: "FNB",
      referralCode: "REF123",
      acceptedTerms: true,
      alias: "customer-alias",
    });

    expect(mockedApiRequest).toHaveBeenCalledWith(
      "v1/referral-saas/public/referrals/validate",
      {
        method: "POST",
        body: {
          tenantCode: "FNB",
          referralCode: "REF123",
          acceptedTerms: true,
          alias: "customer-alias",
        },
      },
    );
  });

  it("captures referee UCNs through the product wrapper", async () => {
    await captureReferralSaasRefereeUcn("track-1", "7777777777");

    expect(mockedApiRequest).toHaveBeenCalledWith(
      "v1/referral-saas/referrals/track-1/referee-ucn",
      {
        method: "POST",
        body: {
          refereeUcn: "7777777777",
        },
      },
    );
  });

  it("inspects operator link/code evidence through the product wrapper", async () => {
    await inspectReferralSaasOperatorLink({
      tenantCode: "FNB",
      sourceType: "CAMPAIGN_REFERRAL_LINK",
      linkCodeId: "campaign-track-1/referral-track-1",
      includeEvidence: false,
    });

    expect(mockedApiRequest).toHaveBeenCalledWith("v1/referral-saas/operator/links/inspect", {
      query: {
        tenant_code: "FNB",
        source_type: "CAMPAIGN_REFERRAL_LINK",
        link_code_id: "campaign-track-1/referral-track-1",
        code_or_ref: undefined,
        include_evidence: false,
      },
    });
  });

  it("inspects operator attribution traces through the product wrapper", async () => {
    await inspectReferralSaasOperatorAttributionTrace({
      tenantCode: "FNB",
      referralTrackId: "11111111-1111-4111-8111-111111111111",
      includeSections: ["attribution", "events", "audit"],
    });

    expect(mockedApiRequest).toHaveBeenCalledWith(
      "v1/referral-saas/operator/outcomes/11111111-1111-4111-8111-111111111111/trace",
      {
        query: {
          tenant_code: "FNB",
          include_sections: ["attribution", "events", "audit"],
        },
      },
    );
  });
});
