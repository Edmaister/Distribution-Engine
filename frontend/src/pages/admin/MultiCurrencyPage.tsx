import { ArrowRightLeft, BadgeDollarSign, Globe2, Landmark } from "lucide-react";
import { FormEvent, useEffect, useMemo, useState } from "react";
import {
  getAdminCrossBorderSettlements,
  getAdminFxRates,
  previewConversionQuote,
} from "../../api/endpoints/multiCurrency";
import { DataTable } from "../../components/DataTable";
import { ErrorPanel } from "../../components/ErrorPanel";
import { FieldLabel } from "../../components/FieldLabel";
import { ActionGuardrail, GuardrailItem, GuardrailTone } from "../../components/ActionGuardrail";
import { JourneyStep, JourneyTracker } from "../../components/JourneyTracker";
import { KpiCard } from "../../components/KpiCard";
import { LoadingState } from "../../components/LoadingState";
import { PanelTitle } from "../../components/PanelTitle";
import { StatusBadge } from "../../components/StatusBadge";
import { SummaryItem } from "../../components/SummaryItem";
import { formatDisplay, getValue, statusTone, useRefreshContext } from "../pageUtils";

const ADMIN_MULTI_CURRENCY_TENANT_KEY = "amplifi.adminMultiCurrency.tenant";

export function MultiCurrencyPage() {
  const { refreshKey } = useRefreshContext();
  const [tenantCode, setTenantCode] = useState(localStorage.getItem(ADMIN_MULTI_CURRENCY_TENANT_KEY) || "FNB");
  const [submittedTenant, setSubmittedTenant] = useState(
    localStorage.getItem(ADMIN_MULTI_CURRENCY_TENANT_KEY) || "FNB",
  );
  const [fxRates, setFxRates] = useState<Record<string, unknown>[]>([]);
  const [settlements, setSettlements] = useState<Record<string, unknown>[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<unknown>(null);
  const [quoteSource, setQuoteSource] = useState("ZAR");
  const [quoteTarget, setQuoteTarget] = useState("USD");
  const [quoteAmount, setQuoteAmount] = useState("1000");
  const [quote, setQuote] = useState<Record<string, unknown> | null>(null);
  const [quoteError, setQuoteError] = useState<unknown>(null);
  const [quoteLoading, setQuoteLoading] = useState(false);

  useEffect(() => {
    if (!submittedTenant) {
      return;
    }

    let alive = true;
    setLoading(true);
    setError(null);
    Promise.all([getAdminFxRates(submittedTenant), getAdminCrossBorderSettlements(submittedTenant)])
      .then(([ratePayload, settlementPayload]) => {
        if (alive) {
          setFxRates(ratePayload);
          setSettlements(settlementPayload);
          const firstRate = ratePayload[0];
          if (firstRate) {
            setQuoteSource(getValue(firstRate, ["base_currency"], quoteSource));
            setQuoteTarget(getValue(firstRate, ["quote_currency"], quoteTarget));
          }
        }
      })
      .catch((requestError) => alive && setError(requestError))
      .finally(() => alive && setLoading(false));
    return () => {
      alive = false;
    };
  }, [submittedTenant, refreshKey]);

  const currencyPairs = useMemo(
    () =>
      new Set(
        fxRates.map((rate) => `${getValue(rate, ["base_currency"])}-${getValue(rate, ["quote_currency"])}`),
      ).size,
    [fxRates],
  );
  const pendingSettlements = useMemo(() => countPendingSettlements(settlements), [settlements]);
  const treasuryGuidance = getTreasuryGuidance({ fxRates, settlements, currencyPairs, quote });
  const quoteGuard = getQuoteGuardrail({ quoteSource, quoteTarget, quoteAmount, quoteLoading, fxRates });

  function submitTenant(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const cleanedTenant = tenantCode.trim().toUpperCase();
    localStorage.setItem(ADMIN_MULTI_CURRENCY_TENANT_KEY, cleanedTenant);
    setTenantCode(cleanedTenant);
    setSubmittedTenant(cleanedTenant);
    setQuote(null);
    setQuoteError(null);
  }

  function submitQuote(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setQuoteLoading(true);
    setQuote(null);
    setQuoteError(null);
    previewConversionQuote({
      tenant_code: submittedTenant,
      source_currency: quoteSource.trim().toUpperCase(),
      target_currency: quoteTarget.trim().toUpperCase(),
      source_amount: quoteAmount,
      persist_quote: false,
    })
      .then((payload) => setQuote(payload))
      .catch((requestError) => setQuoteError(requestError))
      .finally(() => setQuoteLoading(false));
  }

  if (loading) {
    return <LoadingState label="Loading multi-currency controls" />;
  }

  if (error) {
    return <ErrorPanel error={error} />;
  }

  return (
    <>
      <section className="page-header">
        <div>
          <div className="page-kicker">Producer - Supply</div>
          <h1 className="page-title">Treasury Rail</h1>
          <p className="page-copy">
            FX rates, quote previewing, currency corridors, and cross-border settlement visibility
            for producer-funded distribution flows.
          </p>
        </div>
        <StatusBadge label={pendingSettlements ? "Exposure watch" : "FX control"} tone={pendingSettlements ? "warning" : "success"} />
      </section>

      <section className="treasury-rail-grid">
        <div className="treasury-rail-card primary">
          <div className="treasury-rail-card-top">
            <div>
              <div className="treasury-rail-kicker">Treasury posture</div>
              <h2>Keep producer-funded rewards currency-safe.</h2>
              <p>
                Treasury Rail is where Amplifi validates rate availability, previews conversion
                value, and monitors cross-border settlement exposure before money movement becomes
                operational risk.
              </p>
            </div>
            <StatusBadge label={pendingSettlements ? "Watch" : "Ready"} tone={pendingSettlements ? "warning" : "success"} />
          </div>
          <div className="treasury-rail-metrics">
            <SummaryItem label="FX rates" value={fxRates.length} />
            <SummaryItem label="Corridors" value={currencyPairs} />
            <SummaryItem label="Settlements" value={settlements.length} />
            <SummaryItem label="Pending" value={pendingSettlements} />
          </div>
        </div>

        <div className="treasury-rail-card">
          <div className="panel-header compact">
            <div>
              <PanelTitle
                help="Shows the page areas a treasury operator should move through, in the order that reduces risk."
                title="Operator action map"
              />
              <div className="panel-subtitle">Each action points to the place where the work happens.</div>
            </div>
          </div>
          <div className="treasury-action-map">
            <TreasuryActionMapRow
              label="Load treasury context"
              value="Set the tenant before checking rates or settlements."
              target="Treasury scope"
              tone={submittedTenant ? "success" : "warning"}
            />
            <TreasuryActionMapRow
              label="Preview FX quote"
              value="Run a non-saved conversion preview."
              target="Quote preview"
              tone={quote ? "success" : "info"}
            />
            <TreasuryActionMapRow
              label="Review rate coverage"
              value="Confirm the active rate table and currency pairs."
              target="FX rates"
              tone={fxRates.length ? "success" : "warning"}
            />
            <TreasuryActionMapRow
              label="Monitor settlement exposure"
              value="Check provider, compliance, and settlement status."
              target="Cross-border settlements"
              tone={pendingSettlements ? "warning" : "success"}
            />
          </div>
        </div>
      </section>

      <section className="panel" id="treasury-scope">
        <div className="panel-header">
          <div>
            <PanelTitle
              help="Sets the tenant context for FX rates, quote previews, and settlement records."
              title="Treasury scope"
            />
            <div className="panel-subtitle">Required by the multi-currency admin APIs.</div>
          </div>
        </div>
        <div className="panel-body">
          <form className="form-row treasury-scope-row" onSubmit={submitTenant}>
            <div className="field">
              <FieldLabel
                help="The tenant whose treasury data should be loaded, for example FNB."
                htmlFor="multi-currency-tenant"
                label="Tenant code"
              />
              <input
                className="input"
                id="multi-currency-tenant"
                value={tenantCode}
                onChange={(event) => setTenantCode(event.target.value)}
              />
            </div>
            <button className="button" type="submit">
              Load treasury
            </button>
          </form>
        </div>
      </section>

      <section className="grid-3">
        <KpiCard label="FX rates" value={fxRates.length} footnote="Returned active rates" icon={BadgeDollarSign} />
        <KpiCard label="Currency pairs" value={currencyPairs} footnote="Available conversion corridors" icon={Globe2} />
        <KpiCard
          label="Settlements"
          value={settlements.length}
          footnote="Cross-border settlement records"
          icon={Landmark}
        />
      </section>

      <JourneyTracker
        badge={treasuryGuidance.badge}
        currentCopy={treasuryGuidance.copy}
        currentTitle={treasuryGuidance.title}
        steps={treasuryGuidance.steps}
        subtitle="Step-by-step path from FX readiness through quote preview and cross-border settlement review."
        title="Treasury journey"
        tone={treasuryGuidance.tone}
      />

      <section className="grid-2">
        <div className="panel" id="treasury-quote-preview">
          <div className="panel-header">
            <div>
              <PanelTitle
                help="Calculates a currency conversion using the current FX table without saving a quote."
                title="Quote preview"
              />
              <div className="panel-subtitle">Runs as a non-persisted preview against the current FX table.</div>
            </div>
            <StatusBadge label="Preview only" tone="info" />
          </div>
          <div className="panel-body">
            <form className="form-row quote-form" onSubmit={submitQuote}>
              <div className="field">
                <FieldLabel
                  help="The currency you are converting from."
                  htmlFor="quote-source"
                  label="From"
                />
                <input
                  className="input"
                  id="quote-source"
                  value={quoteSource}
                  onChange={(event) => setQuoteSource(event.target.value)}
                />
              </div>
              <div className="field">
                <FieldLabel
                  help="The currency you are converting into."
                  htmlFor="quote-target"
                  label="To"
                />
                <input
                  className="input"
                  id="quote-target"
                  value={quoteTarget}
                  onChange={(event) => setQuoteTarget(event.target.value)}
                />
              </div>
              <div className="field">
                <FieldLabel
                  help="The source amount to convert in preview mode."
                  htmlFor="quote-amount"
                  label="Amount"
                />
                <input
                  className="input"
                  id="quote-amount"
                  value={quoteAmount}
                  onChange={(event) => setQuoteAmount(event.target.value)}
                />
              </div>
              <button className="button" disabled={quoteLoading} type="submit">
                <ArrowRightLeft size={16} />
                {quoteLoading ? "Previewing" : "Preview"}
              </button>
            </form>
            {quoteError ? <div className="quote-result"><ErrorPanel error={quoteError} /></div> : null}
            {quote ? (
              <div className="summary-grid quote-result">
                <SummaryItem
                  label="Source"
                  value={`${getValue(quote, ["source_amount"])} ${getValue(quote, ["source_currency"])}`}
                />
                <SummaryItem
                  label="Target"
                  value={`${getValue(quote, ["target_amount"])} ${getValue(quote, ["target_currency"])}`}
                />
                <SummaryItem label="Rate" value={getValue(quote, ["rate"])} />
              </div>
            ) : null}
            <ActionGuardrail
              badge={quoteGuard.badge}
              tone={quoteGuard.tone}
              title={quoteGuard.title}
              copy={quoteGuard.copy}
              items={quoteGuard.items}
            />
          </div>
        </div>
        <div className="panel" id="treasury-posture">
          <div className="panel-header">
            <div>
              <PanelTitle
                help="A quick view of rates, corridors, and settlement exposure."
                title="Treasury posture"
              />
              <div className="panel-subtitle">Current operational shape from the returned records.</div>
            </div>
          </div>
          <div className="panel-body route-list">
            <SignalRow label="Active FX rates" value={fxRates.length} tone="success" />
            <SignalRow label="Settlement exposure" value={settlements.length} tone="warning" />
            <SignalRow label="Default corridor" value={fxRates[0] ? pairLabel(fxRates[0]) : "-"} tone="info" />
          </div>
        </div>
      </section>

      <section className="panel" id="treasury-fx-rates">
        <div className="panel-header">
          <div>
            <PanelTitle
              help="Conversion rates available to the platform for a currency pair and rate date."
              title="FX rates"
            />
            <div className="panel-subtitle">Active conversion rates available to the platform.</div>
          </div>
        </div>
        <DataTable
          emptyText="No FX rates returned for this tenant."
          rows={fxRates}
          columns={[
            { key: "pair", header: "Pair", render: (row) => <span className="mono">{pairLabel(row)}</span> },
            { key: "rate", header: "Rate", render: (row) => getValue(row, ["rate"]) },
            { key: "rate_date", header: "Rate date", render: (row) => getValue(row, ["rate_date"]) },
            {
              key: "source",
              header: "Source",
              render: (row) => (
                <div>
                  <div>{getValue(row, ["source_system"])}</div>
                  <div className="table-subtext">{getValue(row, ["source_reference"])}</div>
                </div>
              ),
            },
            {
              key: "status",
              header: "Status",
              render: (row) => {
                const status = getValue(row, ["rate_status", "status"]);
                return <StatusBadge label={status} tone={statusTone(status)} />;
              },
            },
          ]}
        />
      </section>

      <section className="panel" id="treasury-cross-border-settlements">
        <div className="panel-header">
          <div>
            <PanelTitle
              help="Settlements where source and target currencies differ, including provider and compliance status."
              title="Cross-border settlements"
            />
            <div className="panel-subtitle">Settlement, provider, and compliance state by corridor.</div>
          </div>
        </div>
        <DataTable
          emptyText="No cross-border settlements returned for this tenant."
          rows={settlements}
          columns={[
            {
              key: "settlement",
              header: "Settlement",
              render: (row) => (
                <div>
                  <div className="mono">{getValue(row, ["provider_reference", "settlement_id"])}</div>
                  <div className="table-subtext">{getValue(row, ["cross_border_settlement_id"])}</div>
                </div>
              ),
            },
            { key: "sponsor", header: "Sponsor", render: (row) => getValue(row, ["sponsor_code"]) },
            { key: "corridor", header: "Corridor", render: (row) => getValue(row, ["corridor"]) },
            {
              key: "amount",
              header: "Amount",
              render: (row) =>
                `${getValue(row, ["source_amount"])} ${getValue(row, ["source_currency"])} -> ${getValue(
                  row,
                  ["target_amount"],
                )} ${getValue(row, ["target_currency"])}`,
            },
            { key: "provider", header: "Provider", render: (row) => getValue(row, ["provider_key"]) },
            {
              key: "compliance",
              header: "Compliance",
              render: (row) => {
                const status = getValue(row, ["compliance_status"]);
                return <StatusBadge label={status} tone={statusTone(status)} />;
              },
            },
            {
              key: "status",
              header: "Settlement",
              render: (row) => {
                const status = getValue(row, ["settlement_status"]);
                return <StatusBadge label={status} tone={statusTone(status)} />;
              },
            },
          ]}
        />
      </section>
    </>
  );
}

function SignalRow({
  label,
  value,
  tone,
}: {
  label: string;
  value: string | number;
  tone: "success" | "warning" | "danger" | "info" | "neutral";
}) {
  return (
    <div className="route-item">
      <div>
        <div className="route-name">{label}</div>
        <div className="route-path">{formatDisplay(value)}</div>
      </div>
      <StatusBadge label={tone === "warning" ? "Watch" : tone} tone={tone} />
    </div>
  );
}

function TreasuryActionMapRow({
  label,
  value,
  target,
  tone,
}: {
  label: string;
  value: string;
  target: string;
  tone: "success" | "warning" | "danger" | "info" | "neutral";
}) {
  return (
    <div className="admin-attention-row">
      <div>
        <div className="admin-attention-title">{label}</div>
        <div className="admin-attention-copy">{value}</div>
      </div>
      <StatusBadge label={target} tone={tone} />
    </div>
  );
}

function pairLabel(row: Record<string, unknown>): string {
  return `${getValue(row, ["base_currency"])} -> ${getValue(row, ["quote_currency"])}`;
}

function countPendingSettlements(settlements: Record<string, unknown>[]): number {
  return settlements.filter((settlement) => {
    const settlementStatus = String(getValue(settlement, ["settlement_status"], "")).toUpperCase();
    const complianceStatus = String(getValue(settlement, ["compliance_status"], "")).toUpperCase();
    return ["PENDING", "QUEUED", "PROCESSING", "REVIEW"].includes(settlementStatus) ||
      ["PENDING", "REVIEW", "HELD"].includes(complianceStatus);
  }).length;
}

type BadgeTone = GuardrailTone;

type Guardrail = {
  badge: string;
  tone: BadgeTone;
  title: string;
  copy: string;
  items: GuardrailItem[];
};

function getQuoteGuardrail({
  quoteSource,
  quoteTarget,
  quoteAmount,
  quoteLoading,
  fxRates,
}: {
  quoteSource: string;
  quoteTarget: string;
  quoteAmount: string;
  quoteLoading: boolean;
  fxRates: Record<string, unknown>[];
}): Guardrail {
  const source = quoteSource.trim().toUpperCase();
  const target = quoteTarget.trim().toUpperCase();
  const amount = Number(quoteAmount);
  const hasRate = fxRates.some(
    (rate) =>
      getValue(rate, ["base_currency"]) === source &&
      getValue(rate, ["quote_currency"]) === target,
  );
  const amountValid = Number.isFinite(amount) && amount > 0;
  const ready = Boolean(source && target && amountValid && hasRate);

  if (quoteLoading) {
    return {
      badge: "Previewing",
      tone: "info",
      title: "Quote preview is running",
      copy: "Wait for the preview result before changing the currency pair or amount.",
      items: [
        { label: "Currency pair", value: `${source || "-"} -> ${target || "-"}`, tone: hasRate ? "success" : "warning" },
        { label: "Amount", value: quoteAmount || "Required", tone: amountValid ? "success" : "warning" },
        { label: "System change", value: "None", tone: "success" },
      ],
    };
  }

  return {
    badge: ready ? "Ready" : "Check inputs",
    tone: ready ? "success" : "warning",
    title: ready ? "Preview is safe to run" : "Confirm the quote inputs",
    copy: "This action calculates a conversion preview only. It does not save a quote, move money, or settle a cross-border item.",
    items: [
      { label: "Currency pair", value: `${source || "-"} -> ${target || "-"}`, tone: hasRate ? "success" : "warning" },
      { label: "Amount", value: quoteAmount || "Required", tone: amountValid ? "success" : "warning" },
      { label: "System change", value: "None", tone: "success" },
    ],
  };
}

function getTreasuryGuidance({
  fxRates,
  settlements,
  currencyPairs,
  quote,
}: {
  fxRates: Record<string, unknown>[];
  settlements: Record<string, unknown>[];
  currencyPairs: number;
  quote: Record<string, unknown> | null;
}): {
  badge: string;
  tone: BadgeTone;
  title: string;
  copy: string;
  steps: JourneyStep[];
} {
  const pendingSettlements = countPendingSettlements(settlements);

  if (!fxRates.length) {
    return {
      badge: "Rates",
      tone: "warning",
      title: "Load active FX rates",
      copy: "No active FX rates were returned. Treasury users need at least one rate before quotes or cross-border settlement review are useful.",
      steps: treasurySteps("current", "waiting", "waiting", "waiting", "waiting"),
    };
  }

  if (!currencyPairs) {
    return {
      badge: "Corridor",
      tone: "warning",
      title: "Confirm currency corridors",
      copy: "Rates are present, but no usable currency corridor is visible. Confirm the base and quote currency setup.",
      steps: treasurySteps("done", "current", "waiting", "waiting", "waiting"),
    };
  }

  if (!quote) {
    return {
      badge: "Preview",
      tone: "info",
      title: "Preview a conversion quote",
      copy: "FX rates and corridors are available. Preview a conversion before relying on the corridor for settlement planning.",
      steps: treasurySteps("done", "done", "current", settlements.length ? "review" : "waiting", "waiting"),
    };
  }

  if (pendingSettlements > 0) {
    return {
      badge: "Settlement",
      tone: "warning",
      title: "Review cross-border settlement exposure",
      copy: "A quote has been previewed and cross-border settlement records need attention. Review compliance and settlement statuses by corridor.",
      steps: treasurySteps("done", "done", "done", "current", "waiting"),
    };
  }

  return {
    badge: "Stable",
    tone: "success",
    title: "Treasury position is ready",
    copy: "FX rates, currency corridors, and quote preview are available. Keep monitoring settlement exposure and provider status.",
    steps: treasurySteps("done", "done", "done", settlements.length ? "done" : "waiting", "current"),
  };
}

function treasurySteps(
  rates: JourneyStep["state"],
  corridors: JourneyStep["state"],
  quote: JourneyStep["state"],
  settlements: JourneyStep["state"],
  monitor: JourneyStep["state"],
): JourneyStep[] {
  return [
    {
      label: "Load FX rates",
      description: "Confirm active exchange rates for the tenant.",
      workArea: "Treasury scope and FX rates",
      targetId: "treasury-fx-rates",
      state: rates,
    },
    {
      label: "Check corridors",
      description: "Confirm available source and target currency pairs.",
      workArea: "Currency pairs KPI and FX rates",
      targetId: "treasury-fx-rates",
      state: corridors,
    },
    {
      label: "Preview quote",
      description: "Run a non-saved conversion quote against the rate table.",
      workArea: "Quote preview",
      targetId: "treasury-quote-preview",
      state: quote,
    },
    {
      label: "Review settlements",
      description: "Inspect cross-border settlement and compliance status.",
      workArea: "Cross-border settlements",
      targetId: "treasury-cross-border-settlements",
      state: settlements,
    },
    {
      label: "Monitor treasury",
      description: "Watch rate freshness, exposure, provider, and corridor movement.",
      workArea: "Treasury posture",
      targetId: "treasury-posture",
      state: monitor,
    },
  ];
}
