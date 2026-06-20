import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const root = dirname(dirname(fileURLToPath(import.meta.url)));

const requiredRoutes = [
  "/admin",
  "/admin/health",
  "/admin/audit",
  "/admin/events",
  "/admin/distribution",
  "/admin/multi-currency",
  "/admin/settlements",
  "/admin/billing",
  "/sponsor",
  "/distributor",
  "/consumer",
];

const guardedPages = [
  "src/pages/admin/EnterpriseEventsPage.tsx",
  "src/pages/admin/BillingSpinePage.tsx",
  "src/pages/admin/SettlementOperationsPage.tsx",
  "src/pages/admin/DistributionCommandCentrePage.tsx",
  "src/pages/admin/MultiCurrencyPage.tsx",
  "src/pages/distributor/DistributorPortalPage.tsx",
  "src/pages/sponsor/SponsorPortalPage.tsx",
  "src/pages/consumer/ConsumerPortalPage.tsx",
];

const journeyPages = [
  "src/pages/admin/BillingSpinePage.tsx",
  "src/pages/admin/SettlementOperationsPage.tsx",
  "src/pages/admin/DistributionCommandCentrePage.tsx",
  "src/pages/admin/MultiCurrencyPage.tsx",
  "src/pages/distributor/DistributorPortalPage.tsx",
  "src/pages/sponsor/SponsorPortalPage.tsx",
  "src/pages/consumer/ConsumerPortalPage.tsx",
];

const workspaceStatePages = [
  "src/pages/sponsor/SponsorPortalPage.tsx",
  "src/pages/distributor/DistributorPortalPage.tsx",
  "src/pages/distributor/DistributorWalletPage.tsx",
  "src/pages/admin/AdminOverviewPage.tsx",
  "src/pages/admin/AdminAuditPage.tsx",
  "src/pages/admin/DistributionCommandCentrePage.tsx",
  "src/pages/admin/BillingSpinePage.tsx",
  "src/pages/admin/SettlementOperationsPage.tsx",
  "src/pages/admin/EnterpriseEventsPage.tsx",
  "src/pages/admin/MultiCurrencyPage.tsx",
  "src/pages/admin/HealthPage.tsx",
];

const checks = [];

function file(path) {
  return readFileSync(join(root, path), "utf8");
}

function pageSource(path) {
  if (path === "src/pages/consumer/ConsumerPortalPage.tsx") {
    return `${file(path)}\n${file("src/pages/consumer/components/ConsumerJourneySections.tsx")}`;
  }
  return file(path);
}

function assert(name, condition, detail = "") {
  checks.push({ name, ok: Boolean(condition), detail });
}

function uniqueMatches(source, regex) {
  return [...new Set([...source.matchAll(regex)].map((match) => match[1]))];
}

const app = file("src/app/App.tsx");
const shell = file("src/layout/AppShell.tsx");
const sidebar = file("src/layout/Sidebar.tsx");
const guardrail = file("src/components/ActionGuardrail.tsx");
const sessionPanel = file("src/auth/ApiKeySessionPanel.tsx");
const sessionBanner = file("src/auth/SessionRoleBanner.tsx");
const sessionEndpoint = file("src/api/endpoints/session.ts");
const sessionHook = file("src/auth/useBackendSession.tsx");
const authStore = file("src/auth/authStore.ts");
const healthBanner = file("src/layout/HealthBanner.tsx");
const css = file("src/styles/base.css");
const adminAuditPage = file("src/pages/admin/AdminAuditPage.tsx");
const healthPage = file("src/pages/admin/HealthPage.tsx");
const operationalQueries = file("src/api/operationalQueries.ts");
const partnerIntegrationPage = file(
  "src/pages/partner/PartnerIntegrationPage.tsx",
);
const partnerQueries = file("src/api/partnerQueries.ts");
const distributorWalletPage = file(
  "src/pages/distributor/DistributorWalletPage.tsx",
);
const distributorQueries = file("src/api/distributorQueries.ts");

for (const route of requiredRoutes) {
  assert(`route registered: ${route}`, app.includes(`path="${route}"`));
  assert(`topbar title registered: ${route}`, shell.includes(`"${route}"`));
  assert(
    `sidebar link registered: ${route}`,
    sidebar.includes(`to: "${route}"`),
  );
}

assert(
  "unknown routes redirect to admin",
  app.includes('path="*"') && app.includes('to="/admin"'),
);
assert(
  "decision guide default label exists",
  guardrail.includes('label = "Decision guide"'),
);
assert("decision guide uses status badge", guardrail.includes("<StatusBadge"));
assert(
  "decision guide styles exist",
  css.includes(".action-guardrail") && css.includes(".action-guardrail-list"),
);
assert(
  "decision guide responsive stacking exists",
  css.includes("@media") && css.includes(".action-guardrail-list"),
);
assert(
  "session role selector exists",
  sessionPanel.includes("Session role") &&
    sessionPanel.includes("ROLE_PRESETS"),
);
assert(
  "session role presets include target users",
  authStore.includes("Producer - Supply") &&
    authStore.includes("Distributor - Demand") &&
    authStore.includes("Consumer Journey") &&
    authStore.includes("Finance Admin") &&
    authStore.includes("Distribution Admin") &&
    authStore.includes("System Admin"),
);
assert(
  "session role banner exists",
  sessionBanner.includes("SessionRoleBanner") &&
    sessionBanner.includes("workspace.guidance"),
);
assert(
  "session banner is backend-confirmed",
  sessionBanner.includes("useBackendSession") &&
    sessionBanner.includes("Session confirmed by backend"),
);
assert(
  "session endpoint exists",
  sessionEndpoint.includes("auth/session") &&
    sessionEndpoint.includes("SessionIdentity"),
);
assert(
  "session endpoint exposes workspace access",
  sessionEndpoint.includes("SessionWorkspace") &&
    sessionEndpoint.includes("recommended_workspace") &&
    sessionEndpoint.includes("workspaces") &&
    sessionEndpoint.includes("guidance") &&
    sessionEndpoint.includes("summary"),
);
assert(
  "session hook centralises backend session role",
  sessionHook.includes("useBackendSession") &&
    sessionHook.includes("BackendSessionProvider") &&
    sessionHook.includes("useQuery") &&
    !sessionHook.includes("useEffect(") &&
    sessionHook.includes("labelForBackendSession") &&
    sessionHook.includes("recommendedWorkspace") &&
    sessionHook.includes("Finance Admin") &&
    sessionHook.includes("Distribution Admin") &&
    sessionHook.includes("System Admin") &&
    sessionHook.includes("workspaceForPath"),
);
assert(
  "app shell owns backend session provider",
  shell.includes("BackendSessionProvider") &&
    shell.includes("<Sidebar />") &&
    shell.includes("<SessionRoleBanner />"),
);
assert(
  "session banner uses backend workspace access",
  sessionBanner.includes("workspaceForPath") &&
    sessionBanner.includes("workspace.access") &&
    sessionBanner.includes("workspace.guidance") &&
    sessionBanner.includes("recommendedWorkspace") &&
    sessionBanner.includes("recommendedWorkspace.path") &&
    sessionBanner.includes("session-role-link") &&
    sessionBanner.includes("<Link") &&
    !sessionBanner.includes("pageRoles"),
);
assert(
  "sidebar uses backend workspace access",
  sidebar.includes("useBackendSession") &&
    sidebar.includes("workspaceForPath") &&
    sidebar.includes("nav-sub-start") &&
    sidebar.includes("nav-sub-allowed") &&
    !sidebar.includes("refreshKey"),
);
assert(
  "producer workspace uses backend session scope",
  file("src/pages/sponsor/SponsorPortalPage.tsx").includes(
    "producerSessionLocked",
  ) &&
    file("src/pages/sponsor/SponsorPortalPage.tsx").includes(
      "Backend-confirmed producer scope",
    ),
);
assert(
  "distributor workspace uses backend session scope",
  file("src/pages/distributor/DistributorPortalPage.tsx").includes(
    "distributorSessionLocked",
  ) &&
    file("src/pages/distributor/DistributorPortalPage.tsx").includes(
      "Backend-confirmed distributor scope",
    ),
);
assert(
  "session role layout styles exist",
  css.includes(".form-row.api-session-row") &&
    css.includes(".session-role-banner") &&
    css.includes(".session-role-link") &&
    css.includes(".nav-sub-start") &&
    css.includes(".nav-sub-allowed") &&
    css.includes(".nav-sub-blocked"),
);
assert(
  "admin outcome money settlement repair is wired",
  file("src/api/endpoints/finance.ts").includes(
    "createOutcomeSettlementEvidence",
  ) &&
    file("src/pages/admin/AdminOverviewPage.tsx").includes(
      "CREATE_SETTLEMENT_EVIDENCE",
    ) &&
    file("src/pages/admin/AdminOverviewPage.tsx").includes("Create settlement"),
);
assert(
  "admin outcome money ledger repairs are wired",
  file("src/api/endpoints/finance.ts").includes(
    "createOutcomeRewardEvidence",
  ) &&
    file("src/api/endpoints/finance.ts").includes(
      "createOutcomeCommissionEvidence",
    ) &&
    file("src/api/endpoints/finance.ts").includes(
      "createOutcomeWalletEvidence",
    ) &&
    file("src/pages/admin/AdminOverviewPage.tsx").includes(
      "CREATE_REWARD_EVIDENCE",
    ) &&
    file("src/pages/admin/AdminOverviewPage.tsx").includes(
      "CREATE_COMMISSION_EVIDENCE",
    ) &&
    file("src/pages/admin/AdminOverviewPage.tsx").includes(
      "CREATE_WALLET_EVIDENCE",
    ) &&
    file("src/pages/admin/AdminOverviewPage.tsx").includes("Create reward") &&
    file("src/pages/admin/AdminOverviewPage.tsx").includes(
      "Create commission",
    ) &&
    file("src/pages/admin/AdminOverviewPage.tsx").includes("Create wallet"),
);
assert(
  "runtime health reads use shared query hook",
  healthPage.includes("useHealthReadiness") &&
    !healthPage.includes("useEffect(") &&
    operationalQueries.includes("getHealth"),
);
assert(
  "layout health banner uses shared query hook",
  healthBanner.includes("useHealthConnection") &&
    !healthBanner.includes("useEffect(") &&
    operationalQueries.includes("useHealthConnection"),
);
assert(
  "admin audit reads use shared query hook",
  adminAuditPage.includes("useAdminAudit") &&
    !adminAuditPage.includes("useEffect(") &&
    operationalQueries.includes("getAdminAuditSummary"),
);
assert(
  "operational query keys are centralised",
  file("src/api/queryKeys.ts").includes("adminAudit") &&
    file("src/api/queryKeys.ts").includes("backendSession") &&
    file("src/api/queryKeys.ts").includes("healthReadiness") &&
    file("src/api/queryKeys.ts").includes("healthConnection"),
);
assert(
  "partner integration reads use shared query hook",
  partnerIntegrationPage.includes("usePartnerIntegrationWorkspace") &&
    !partnerIntegrationPage.includes("useEffect(") &&
    partnerQueries.includes("getPartnerIntegration") &&
    partnerQueries.includes("loadAdminPartnerIntegration"),
);
assert(
  "distributor wallet reads use shared query hooks",
  distributorWalletPage.includes("useDistributorWalletWorkspace") &&
    distributorWalletPage.includes("useDistributorWalletLedger") &&
    distributorWalletPage.includes("useDistributorOptions") &&
    !distributorWalletPage.includes("getDistributorPortalWallets") &&
    distributorQueries.includes("getDistributorPortalWalletLedger"),
);

for (const pagePath of guardedPages) {
  const source = pageSource(pagePath);
  assert(
    `${pagePath} imports ActionGuardrail`,
    source.includes("ActionGuardrail"),
  );
  assert(
    `${pagePath} renders decision guide`,
    source.includes("<ActionGuardrail"),
  );
  assert(
    `${pagePath} uses user-facing system-change wording`,
    source.includes("System change"),
  );
}

for (const pagePath of journeyPages) {
  const source = pageSource(pagePath);
  const targetIds = uniqueMatches(source, /targetId:\s*"([^"]+)"/g);
  const missingIds = targetIds.filter((id) => !source.includes(`id="${id}"`));
  assert(
    `${pagePath} journey targets resolve`,
    missingIds.length === 0,
    missingIds.join(", "),
  );
}

for (const pagePath of workspaceStatePages) {
  const source = file(pagePath);
  assert(`${pagePath} has loading state`, source.includes("LoadingState"));
  assert(`${pagePath} has error state`, source.includes("ErrorPanel"));
  assert(
    `${pagePath} has empty state`,
    source.includes("EmptyState") ||
      source.includes("emptyText") ||
      source.includes("empty-state"),
  );
  assert(
    `${pagePath} has review/partial state language`,
    source.includes("Needs review") ||
      source.includes("Review needed") ||
      source.includes("No ") ||
      source.includes("Waiting") ||
      source.includes("warning"),
  );
}

assert(
  "keyboard focus is visible across controls",
  css.includes(":focus-visible") &&
    css.includes("outline: 3px solid var(--color-signal)") &&
    css.includes("outline-offset: 3px") &&
    css.includes('[role="button"]') &&
    css.includes('[role="tab"]'),
);
assert(
  "tablet layouts collapse dense workspaces",
  css.includes("@media (max-width: 920px)") &&
    css.includes(".app-shell") &&
    css.includes(".topbar") &&
    css.includes(".page-header") &&
    css.includes(".form-row") &&
    css.includes("grid-template-columns: 1fr") &&
    css.includes("flex-direction: column"),
);
assert(
  "mobile data tables stay readable",
  css.includes(".data-table") &&
    css.includes("table-layout: fixed") &&
    css.includes("overflow-wrap: anywhere") &&
    css.includes("white-space: normal"),
);
assert(
  "compact mobile controls stretch predictably",
  css.includes("@media (max-width: 520px)") &&
    css.includes(".wallet-tabs") &&
    css.includes("width: 100%"),
);
assert(
  "typography avoids viewport-scaled font sizes",
  !/font-size:\s*[^;]*vw/.test(css),
);
assert(
  "typography avoids negative letter spacing",
  !/letter-spacing:\s*-\d/.test(css),
);

const failures = checks.filter((check) => !check.ok);

if (failures.length) {
  console.error("Frontend smoke check failed:");
  for (const failure of failures) {
    console.error(
      `- ${failure.name}${failure.detail ? ` (${failure.detail})` : ""}`,
    );
  }
  process.exit(1);
}

console.log(`Frontend smoke check passed (${checks.length} checks).`);
