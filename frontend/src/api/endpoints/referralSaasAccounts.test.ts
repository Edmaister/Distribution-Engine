import { beforeEach, describe, expect, it, vi } from "vitest";

import { apiRequest } from "../client";
import { resolveReferralSaasAccount } from "./referralSaasAccounts";

vi.mock("../client", () => ({
  apiRequest: vi.fn(),
}));

const mockedApiRequest = vi.mocked(apiRequest);

describe("referralSaasAccounts endpoint client", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("resolves a Referral SaaS account through the product account wrapper", async () => {
    mockedApiRequest.mockResolvedValue({
      status: "ok",
      context: "setup",
      account: {
        accountCode: "FNB_REFERRAL_SAAS",
        accountName: "FNB Referral SaaS",
        accountStatus: "ACTIVE",
      },
      guardrail: "Read-only Referral SaaS account resolver.",
    });

    await expect(
      resolveReferralSaasAccount({
        refType: "external_tenant_ref",
        externalRef: " demo-platform-operator ",
        context: "setup",
      }),
    ).resolves.toMatchObject({
      status: "ok",
      account: {
        accountCode: "FNB_REFERRAL_SAAS",
      },
    });

    expect(mockedApiRequest).toHaveBeenCalledWith("v1/referral-saas/accounts/resolve", {
      query: {
        ref_type: "external_tenant_ref",
        external_ref: "demo-platform-operator",
        context: "setup",
      },
    });
    expect(JSON.stringify(mockedApiRequest.mock.calls).toLowerCase()).not.toMatch(
      /tenant_code|client_secret|wallet|settlement|money/,
    );
  });
});
