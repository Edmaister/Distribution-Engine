import {
  ArrowUpRight,
  Banknote,
  Landmark,
  Plus,
  Search,
  Smartphone,
  Sparkles,
  Star,
  Wallet,
} from "lucide-react";
import { FormEvent, useEffect, useMemo, useState } from "react";
import {
  useDistributorOptions,
  useDistributorWalletLedger,
  useDistributorWalletWorkspace,
} from "../../api/distributorQueries";
import { ErrorPanel } from "../../components/ErrorPanel";
import { LoadingState } from "../../components/LoadingState";
import { StatusBadge } from "../../components/StatusBadge";
import {
  normalizeSessionRole,
  useBackendSession,
} from "../../auth/useBackendSession";
import {
  formatDisplay,
  getNestedValue,
  getValue,
  statusTone,
  useRefreshContext,
} from "../pageUtils";

const TENANT_KEY = "amplifi.distributorPortal.tenant";
const DISTRIBUTOR_KEY = "amplifi.distributorPortal.distributor";

export function DistributorWalletPage() {
  const { refreshKey } = useRefreshContext();
  const backend = useBackendSession(refreshKey, "distributor-workspace");
  const [tenantCode, setTenantCode] = useState(
    localStorage.getItem(TENANT_KEY) || "FNB",
  );
  const [distributorCode, setDistributorCode] = useState(
    localStorage.getItem(DISTRIBUTOR_KEY) || "",
  );
  const [submitted, setSubmitted] = useState({
    tenantCode: localStorage.getItem(TENANT_KEY) || "FNB",
    distributorCode: localStorage.getItem(DISTRIBUTOR_KEY) || "",
  });
  const [rail, setRail] = useState<"earnings" | "funding">("earnings");
  const [selectedWalletId, setSelectedWalletId] = useState("");

  const distributorSessionLocked =
    backend.status === "confirmed" &&
    normalizeSessionRole(backend.session?.role) === "distributor" &&
    Boolean(backend.session?.distributor_code);
  const distributorOptionsQuery = useDistributorOptions(tenantCode, refreshKey);
  const walletWorkspaceQuery = useDistributorWalletWorkspace(
    submitted.tenantCode,
    submitted.distributorCode,
    refreshKey,
  );
  const profile = walletWorkspaceQuery.data?.profile;
  const performance = walletWorkspaceQuery.data?.performance;
  const wallets = useMemo(
    () => walletWorkspaceQuery.data?.wallets || [],
    [walletWorkspaceQuery.data?.wallets],
  );
  const selectedWalletStillExists = wallets.some(
    (wallet) => getValue(wallet, ["wallet_id", "id"]) === selectedWalletId,
  );
  const activeWalletId = selectedWalletStillExists
    ? selectedWalletId
    : getValue(wallets[0] || {}, ["wallet_id", "id"], "");
  const walletLedgerQuery = useDistributorWalletLedger(
    submitted.tenantCode,
    submitted.distributorCode,
    activeWalletId,
    refreshKey,
  );
  const distributorOptions = distributorOptionsQuery.data || [];
  const walletLedger = walletLedgerQuery.data || [];

  useEffect(() => {
    if (!distributorSessionLocked || !backend.session?.distributor_code) {
      return;
    }

    const scopedTenant = String(
      backend.session.tenant_code || backend.session.tenant || "FNB",
    ).toUpperCase();
    const scopedDistributor = String(
      backend.session.distributor_code,
    ).toUpperCase();
    localStorage.setItem(TENANT_KEY, scopedTenant);
    localStorage.setItem(DISTRIBUTOR_KEY, scopedDistributor);
    setTenantCode(scopedTenant);
    setDistributorCode(scopedDistributor);
    setSubmitted({
      tenantCode: scopedTenant,
      distributorCode: scopedDistributor,
    });
  }, [
    distributorSessionLocked,
    backend.session?.tenant_code,
    backend.session?.tenant,
    backend.session?.distributor_code,
  ]);

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const cleanedTenant = tenantCode.trim().toUpperCase();
    const cleanedDistributor = distributorCode.trim().toUpperCase();
    localStorage.setItem(TENANT_KEY, cleanedTenant);
    localStorage.setItem(DISTRIBUTOR_KEY, cleanedDistributor);
    setTenantCode(cleanedTenant);
    setDistributorCode(cleanedDistributor);
    setSubmitted({
      tenantCode: cleanedTenant,
      distributorCode: cleanedDistributor,
    });
  }

  const selectedWallet = wallets.find(
    (wallet) => getValue(wallet, ["wallet_id", "id"]) === activeWalletId,
  );
  const available = getNestedValue(
    performance,
    ["wallet_available_balance"],
    getValue(selectedWallet || {}, ["available_balance"], "0.00"),
  );
  const pending = getNestedValue(
    performance,
    ["pending_reward_amount"],
    getNestedValue(
      performance,
      ["wallet_held_balance"],
      getValue(selectedWallet || {}, ["held_balance"], "0.00"),
    ),
  );
  const reserved = getNestedValue(
    performance,
    ["wallet_held_balance"],
    getValue(selectedWallet || {}, ["held_balance"], "0.00"),
  );
  const lifetime = getNestedValue(
    performance,
    ["total_commission_amount"],
    getValue(selectedWallet || {}, ["current_balance"], "0.00"),
  );
  const distributorName = getNestedValue(
    profile,
    ["distributor_name"],
    submitted.distributorCode || "Distributor",
  );

  return (
    <>
      <section className="earnings-command-header wallet-topbar">
        <div className="earnings-breadcrumb">
          <span>Amplifi</span>
          <span>My Wallet</span>
          <strong>Distributor view</strong>
        </div>
        <div className="earnings-search">
          <Search size={16} />
          <input
            aria-label="Search wallet transactions"
            placeholder="Search transactions, rails, settlements..."
          />
        </div>
        <div className="earnings-header-actions">
          <span className="earnings-rank-pill">
            <Wallet size={14} />
            {formatDisplay(distributorName)}
          </span>
        </div>
      </section>

      <section className="wallet-page-hero">
        <div>
          <h1>Wallet & Settlement</h1>
          <p>
            Every participant has a wallet. Earn from distributing, review
            settlement movement, and track payout readiness on one rail.
          </p>
        </div>
        <form className="wallet-scope-form" onSubmit={submit}>
          <label htmlFor="wallet-tenant">Tenant</label>
          <input
            disabled={distributorSessionLocked}
            id="wallet-tenant"
            value={tenantCode}
            onChange={(event) => setTenantCode(event.target.value)}
          />
          <select
            disabled={distributorSessionLocked}
            aria-label="Distributor"
            value={distributorCode}
            onChange={(event) => setDistributorCode(event.target.value)}
          >
            <option value="">
              {distributorOptions.length
                ? "Select distributor"
                : "Distributor code"}
            </option>
            {distributorOptions.map((option) => {
              const code = getValue(option, ["distributor_code"]);
              const name = getValue(option, ["distributor_name", "name"]);
              return (
                <option key={code} value={code}>
                  {name} - {code}
                </option>
              );
            })}
          </select>
          <button
            className="button"
            disabled={distributorSessionLocked}
            type="submit"
          >
            Load
          </button>
        </form>
      </section>

      <div className="wallet-tabs" role="tablist" aria-label="Wallet rails">
        <button
          className={rail === "earnings" ? "active" : ""}
          type="button"
          onClick={() => setRail("earnings")}
        >
          Earnings
        </button>
        <button
          className={rail === "funding" ? "active" : ""}
          type="button"
          onClick={() => setRail("funding")}
        >
          Funding
        </button>
      </div>

      {!submitted.tenantCode || !submitted.distributorCode ? (
        <div className="earnings-empty-card">
          Load a distributor to see wallet balances and settlement movement.
        </div>
      ) : walletWorkspaceQuery.isLoading ? (
        <LoadingState label="Loading wallet" />
      ) : walletWorkspaceQuery.error ? (
        <ErrorPanel error={walletWorkspaceQuery.error} />
      ) : (
        <>
          <section className="wallet-layout-grid">
            <div className="wallet-left-stack">
              <div className="wallet-balance-card">
                <div className="wallet-card-top">
                  <span>
                    {rail === "earnings"
                      ? "Available balance"
                      : "Funding balance"}
                  </span>
                  <StatusBadge
                    label={
                      selectedWallet
                        ? getValue(
                            selectedWallet,
                            ["status", "wallet_status"],
                            "Active",
                          )
                        : "No wallet"
                    }
                    tone={
                      selectedWallet
                        ? statusTone(
                            getValue(
                              selectedWallet,
                              ["status", "wallet_status"],
                              "Active",
                            ),
                          )
                        : "neutral"
                    }
                  />
                </div>
                <strong>{formatWalletMoney(available)}</strong>
                <div className="wallet-balance-grid">
                  <div>
                    <span>Pending</span>
                    <b>{formatWalletMoney(pending)}</b>
                  </div>
                  <div>
                    <span>Reserved</span>
                    <b>{formatWalletMoney(reserved)}</b>
                  </div>
                  <div>
                    <span>Lifetime</span>
                    <b>{formatWalletMoney(lifetime)}</b>
                  </div>
                </div>
                <div className="wallet-action-row">
                  <button className="button" type="button">
                    <Sparkles size={15} />
                    Instant pay
                  </button>
                  <button className="button secondary" type="button">
                    <Landmark size={15} />
                    To bank
                  </button>
                  <button className="button secondary" type="button">
                    <Smartphone size={15} />
                    Mobile money
                  </button>
                </div>
              </div>

              <div className="wallet-engine-card">
                <div>
                  <h2>Settlement engine</h2>
                  <StatusBadge
                    label={walletLedger.length ? "Reconciled" : "Waiting"}
                    tone={walletLedger.length ? "success" : "neutral"}
                  />
                </div>
                <p>
                  Every reward is matched against funding, reconciled against
                  the sponsor wallet, and settled to the distributor
                  automatically.
                  <strong>
                    {" "}
                    {walletLedger.length
                      ? "Ledger movement is visible."
                      : "No settlement movement yet."}
                  </strong>
                </p>
              </div>
            </div>

            <div className="wallet-transactions-card">
              <div className="wallet-transactions-head">
                <h2>Transactions</h2>
                <select
                  aria-label="Wallet account"
                  value={activeWalletId}
                  onChange={(event) => setSelectedWalletId(event.target.value)}
                >
                  {wallets.length ? null : <option value="">No wallets</option>}
                  {wallets.map((wallet) => {
                    const walletId = getValue(wallet, ["wallet_id", "id"], "");
                    return (
                      <option key={walletId} value={walletId}>
                        {getValue(wallet, ["currency"], "ZAR")} -{" "}
                        {getValue(wallet, ["available_balance"], "0.00")}{" "}
                        available
                      </option>
                    );
                  })}
                </select>
              </div>
              <div className="wallet-transaction-list">
                {walletLedger.length ? (
                  walletLedger
                    .slice(0, 8)
                    .map((entry, index) => (
                      <WalletTransactionRow
                        entry={entry}
                        key={`${getValue(entry, ["ledger_id", "id", "created_at"], String(index))}-${index}`}
                      />
                    ))
                ) : (
                  <div className="wallet-empty-state">
                    <Banknote size={22} />
                    <strong>No wallet transactions yet</strong>
                    <span>
                      Ledger movement will appear after rewards, holds, payouts,
                      or reversals are posted.
                    </span>
                  </div>
                )}
              </div>
            </div>
          </section>
        </>
      )}
    </>
  );
}

function WalletTransactionRow({ entry }: { entry: Record<string, unknown> }) {
  const type = getValue(entry, ["transaction_type", "type"], "Movement");
  const amount = getValue(entry, ["amount"], "0.00");
  const numericAmount = Number(String(amount).replace(/[^0-9.-]/g, ""));
  const isDebit =
    ["PAYOUT", "REVERSE", "DEBIT"].includes(type.toUpperCase()) ||
    numericAmount < 0;
  const Icon = isDebit
    ? ArrowUpRight
    : type.toUpperCase().includes("BONUS")
      ? Star
      : Plus;

  return (
    <div className="wallet-transaction-row">
      <span
        className={
          isDebit ? "wallet-transaction-icon debit" : "wallet-transaction-icon"
        }
      >
        <Icon size={16} />
      </span>
      <div>
        <strong>{walletTransactionTitle(type)}</strong>
        <p>
          {getValue(
            entry,
            ["description", "reference", "correlation_id"],
            "Wallet ledger",
          )}{" "}
          - {formatDisplay(getValue(entry, ["created_at"], "recent"))}
        </p>
      </div>
      <b className={isDebit ? "debit" : ""}>
        {isDebit ? "-" : "+"}
        {formatWalletMoney(Math.abs(numericAmount || 0))}
      </b>
    </div>
  );
}

function walletTransactionTitle(type: string): string {
  const normalised = type.replace(/_/g, " ").toLowerCase();
  return normalised.charAt(0).toUpperCase() + normalised.slice(1);
}

function formatWalletMoney(value: unknown): string {
  const numeric = Number(String(value ?? "0").replace(/[^0-9.-]/g, ""));
  if (!Number.isFinite(numeric)) {
    return "R0.00";
  }
  return `R${numeric.toLocaleString("en-ZA", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}
