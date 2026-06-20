import { afterEach, describe, expect, it, vi } from "vitest";

import { getConsumerExperience } from "./consumerPortal";

describe("consumer portal api", () => {
  afterEach(() => {
    vi.restoreAllMocks();
    localStorage.clear();
  });

  it("requests the consumer experience aggregate with the expected query", async () => {
    localStorage.setItem("amplifi.apiBaseUrl", "https://api.example.test");
    localStorage.setItem("amplifi.apiKey", "consumer-key");
    const fetchMock = vi.fn(async () => {
      return new Response(JSON.stringify({ status: "ok" }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
    });
    vi.stubGlobal("fetch", fetchMock);

    await getConsumerExperience({
      tenantCode: "FNB",
      referrerUcn: "UCN-123",
      referralTrackId: "TRACK-1",
      leaderboardCode: "GLOBAL_MONTHLY",
      includeInsuranceProof: true,
    });

    expect(fetchMock).toHaveBeenCalledTimes(1);
    const firstCall = fetchMock.mock.calls[0] as unknown as [string, RequestInit];
    const [url, options] = firstCall;
    const requestUrl = new URL(url);

    expect(requestUrl.origin).toBe("https://api.example.test");
    expect(requestUrl.pathname).toBe("/v1/experience/consumer");
    expect(requestUrl.searchParams.get("tenant_code")).toBe("FNB");
    expect(requestUrl.searchParams.get("referrer_ucn")).toBe("UCN-123");
    expect(requestUrl.searchParams.get("referral_track_id")).toBe("TRACK-1");
    expect(requestUrl.searchParams.get("leaderboard_code")).toBe("GLOBAL_MONTHLY");
    expect(requestUrl.searchParams.get("include_insurance_proof")).toBe("true");
    expect(options.headers).toMatchObject({ "x-api-key": "consumer-key" });
  });
});
