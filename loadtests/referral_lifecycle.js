import http from "k6/http";
import { check, sleep } from "k6";

export const options = {
  scenarios: {
    lifecycle_smoke: {
      executor: "constant-vus",
      vus: 10,
      duration: "2m",
    },
  },
  thresholds: {
    http_req_failed: ["rate<0.05"],
    http_req_duration: ["p(95)<1000"],

    "http_req_duration{endpoint:issue_code}": ["p(95)<1000"],
    "http_req_duration{endpoint:validate}": ["p(95)<1000"],
    "http_req_duration{endpoint:capture_ucn}": ["p(95)<1000"],
    "http_req_duration{endpoint:progress}": ["p(95)<1000"],
    "http_req_duration{endpoint:leaderboard}": ["p(95)<1000"],
  },
};

const BASE_URL = __ENV.BASE_URL || "http://127.0.0.1:8000";
const API_KEY = __ENV.API_KEY || "dev-fnb-key-123";

const authHeaders = {
  "Content-Type": "application/json",
  "x-api-key": API_KEY,
};

const publicHeaders = {
  "Content-Type": "application/json",
};

function uniqueId() {
  return `${Date.now()}-${__VU}-${__ITER}`;
}

function logFailure(label, res) {
  if (res.status < 200 || res.status >= 300) {
    console.log(`${label} FAILED status=${res.status} body=${res.body}`);
  }
}

export default function () {
  const id = uniqueId();
  const referrerUcn = `2026${__VU}${__ITER}${Date.now()}`;
  const refereeUcn = `3000${__VU}${__ITER}${Date.now()}`;
  const accountNumber = `123456${__VU}${__ITER}${Date.now()}`.slice(0, 12);

  const issueRes = http.post(
    `${BASE_URL}/referrals/codes`,
    JSON.stringify({
      referrer_ucn: referrerUcn,
      sticker: "Easy",
      tenant: "FNB",
      segment: "PERSONAL",
      preferred_handle: `Player${__VU}_${__ITER}`,
      acceptedTerms: true,
    }),
    {
      headers: authHeaders,
      tags: { endpoint: "issue_code" },
    }
  );

  logFailure("ISSUE", issueRes);

  check(issueRes, {
    "issue code ok": (r) => r.status === 200 || r.status === 201,
  });

  const referralCode = issueRes.json("referral_code");
  if (!referralCode) return;

  const validateRes = http.post(
    `${BASE_URL}/public/referrals/validate`,
    JSON.stringify({
      tenantCode: "FNB",
      referralCode: referralCode,
      acceptedTerms: true,
      alias: `Alias_${__VU}_${__ITER}`,
      deviceFingerprint: `device-${id}`,
      ipAddress: "127.0.0.1",
      qrCode: `qr-${id}`,
    }),
    {
      headers: publicHeaders,
      tags: { endpoint: "validate" },
    }
  );

  logFailure("VALIDATE", validateRes);

  check(validateRes, {
    "validate ok": (r) => r.status === 200,
    "validate valid": (r) => r.json("valid") === true,
  });

  const trackId = validateRes.json("referralTrackId");
  if (!trackId) return;

  const captureRes = http.post(
    `${BASE_URL}/referrals/referees/ucn`,
    JSON.stringify({
      referral_track_id: trackId,
      referee_ucn: refereeUcn,
    }),
    {
      headers: authHeaders,
      tags: { endpoint: "capture_ucn" },
    }
  );

  logFailure("CAPTURE_UCN", captureRes);

  check(captureRes, {
    "capture ucn ok": (r) => r.status === 200,
  });

  const events = [
    "ACCOUNT_OPENED",
    "ACCOUNT_ACTIVATED",
    "FUNDED",
    "SALARY_SWITCHED",
    "DEBIT_ORDER_SWITCHED",
    "FIRST_TRANSACTION_COMPLETED",
  ];

  for (const eventType of events) {
    const body = {
      referralTrackId: trackId,
      product: "Transactional",
      subProduct: "DDA13",
      eventType: eventType,
      refereeUCN: refereeUcn,
      sourceSystem: "K6_LOAD_TEST",
      sourceEventId: `${eventType}-${id}`,
      meta: {
        test: "k6_referral_lifecycle",
      },
    };

    if (eventType === "ACCOUNT_OPENED") {
      body.accountNumber = accountNumber;
    }

    const progressRes = http.post(
      `${BASE_URL}/v1/progress`,
      JSON.stringify(body),
      {
        headers: authHeaders,
        tags: {
          endpoint: "progress",
          progress_event: eventType,
        },
      }
    );

    logFailure(eventType, progressRes);

    check(progressRes, {
      [`${eventType} ok`]: (r) => r.status === 200 || r.status === 201,
    });
  }

  const leaderboardRes = http.get(
    `${BASE_URL}/v1/tenants/FNB/leaderboards/GLOBAL_OVERALL?limit=10&offset=0`,
    {
      headers: authHeaders,
      tags: { endpoint: "leaderboard" },
    }
  );

  logFailure("LEADERBOARD", leaderboardRes);

  check(leaderboardRes, {
    "leaderboard ok": (r) => r.status === 200,
    "leaderboard has items": (r) => Array.isArray(r.json("items")),
  });

  sleep(1);
}