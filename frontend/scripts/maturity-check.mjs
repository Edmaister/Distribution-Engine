import { existsSync, readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { join } from "node:path";

const root = fileURLToPath(new URL("..", import.meta.url));

const requiredFiles = [
  "src/api/queryClient.ts",
  "src/api/queryKeys.ts",
  "src/api/operationalQueries.ts",
  "src/api/experienceQueries.ts",
  "src/api/partnerQueries.ts",
  "src/api/distributorQueries.ts",
  "src/pages/admin/distribution/DistributionMarketplaceView.tsx",
  "src/pages/sponsor/components/SponsorWorkspaceView.tsx",
  "src/pages/distributor/components/DistributorHubView.tsx",
  "src/pages/consumer/components/ConsumerJourneySections.tsx",
  "src/components/DataTable.tsx",
  "src/components/SegmentedFilter.tsx",
  "src/components/PanelTitle.tsx",
  "src/components/FieldLabel.tsx",
  "src/components/SummaryGrid.tsx",
  "src/components/StatusBadge.tsx",
  "src/components/ActionGuardrail.tsx",
];

const forbiddenPagePatterns = [
  { pattern: /\bfetch\s*\(/, label: "raw fetch in page/component code" },
];

function fail(message) {
  console.error(`[frontend-maturity] ${message}`);
  process.exitCode = 1;
}

for (const file of requiredFiles) {
  if (!existsSync(join(root, file))) {
    fail(`missing required maturity artifact: ${file}`);
  }
}

const pageFiles = [
  "src/pages/admin/AdminOverviewPage.tsx",
  "src/pages/admin/AdminAuditPage.tsx",
  "src/pages/admin/ChannelOperationsPage.tsx",
  "src/pages/admin/HealthPage.tsx",
  "src/pages/consumer/ConsumerPortalPage.tsx",
  "src/pages/partner/PartnerIntegrationPage.tsx",
  "src/pages/distributor/DistributorWalletPage.tsx",
];

for (const file of pageFiles) {
  const source = readFileSync(join(root, file), "utf8");
  for (const rule of forbiddenPagePatterns) {
    if (rule.pattern.test(source)) {
      fail(`${rule.label}: ${file}`);
    }
  }
}

if (!process.exitCode) {
  console.log("[frontend-maturity] query, component, primitive, and fetch guardrails passed");
}
