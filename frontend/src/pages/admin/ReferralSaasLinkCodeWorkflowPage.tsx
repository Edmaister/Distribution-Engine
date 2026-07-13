import { CheckCircle2, KeyRound, Link as LinkIcon, ShieldCheck, UserCheck } from "lucide-react";
import { useState } from "react";
import type { ReactNode } from "react";
import { Link } from "react-router-dom";
import { useMutation } from "@tanstack/react-query";

import {
  captureConsumerRefereeUcn,
  issueConsumerReferralCode,
  validateConsumerReferralCode,
  type ConsumerPortalRecord,
} from "../../api/endpoints/consumerPortal";
import { ErrorPanel } from "../../components/ErrorPanel";
import { KpiCard } from "../../components/KpiCard";
import { StatusBadge } from "../../components/StatusBadge";
import { SummaryItem } from "../../components/SummaryItem";
import { asRecord, formatDisplay, getNestedValue, getValue, statusTone } from "../pageUtils";

const defaultTenantCode = "FNB";
const defaultReferrerUcn = "5555555555";
const defaultSticker = "QR001";
const defaultSegment = "PERSONAL";

function resultValue(result: ConsumerPortalRecord | undefined, keys: string[], fallback = "-") {
  return result ? getValue(result, keys, fallback) : fallback;
}

function issuedReferralCode(result: ConsumerPortalRecord | undefined) {
  return resultValue(result, ["referral_code", "referralCode", "code"], "");
}

function validationTrackId(result: ConsumerPortalRecord | undefined) {
  return resultValue(result, ["referral_track_id", "referralTrackId", "track_id"], "");
}

export function ReferralSaasLinkCodeWorkflowPage() {
  const [tenantCode, setTenantCode] = useState(defaultTenantCode);
  const [referrerUcn, setReferrerUcn] = useState(defaultReferrerUcn);
  const [sticker, setSticker] = useState(defaultSticker);
  const [segment, setSegment] = useState(defaultSegment);
  const [preferredHandle, setPreferredHandle] = useState("");
  const [acceptedTerms, setAcceptedTerms] = useState(true);
  const [referralCode, setReferralCode] = useState("");
  const [alias, setAlias] = useState("customer-alias");
  const [refereeUcn, setRefereeUcn] = useState("");

  const issueMutation = useMutation({
    mutationFn: () =>
      issueConsumerReferralCode({
        referrerUcn,
        tenantCode,
        sticker,
        segment,
        preferredHandle,
        acceptedTerms,
      }),
    onSuccess: (result) => {
      const nextReferralCode = issuedReferralCode(result);
      if (nextReferralCode) {
        setReferralCode(nextReferralCode);
      }
    },
  });

  const validateMutation = useMutation({
    mutationFn: () =>
      validateConsumerReferralCode({
        tenantCode,
        referralCode: referralCode || issuedReferralCode(issueMutation.data),
        acceptedTerms,
        alias,
      }),
  });

  const captureMutation = useMutation({
    mutationFn: () =>
      captureConsumerRefereeUcn(
        validationTrackId(validateMutation.data),
        refereeUcn,
      ),
  });

  const issueResult = issueMutation.data;
  const validationResult = validateMutation.data;
  const captureResult = captureMutation.data;
  const activeReferralCode = referralCode || issuedReferralCode(issueResult);
  const activeTrackId = validationTrackId(validationResult);
  const validationAttributes = asRecord(getNestedValue(validationResult, ["attributes"], {}));
  const canIssueOrValidate = acceptedTerms && tenantCode.trim() !== "";
  const canValidate = canIssueOrValidate && activeReferralCode.trim() !== "";
  const canCapture = activeTrackId.trim() !== "" && refereeUcn.trim() !== "";

  return (
    <>
      <section className="page-header">
        <div>
          <div className="page-kicker">Referral SaaS - Links & Codes</div>
          <h1 className="page-title">Link and code workflow</h1>
          <p className="page-copy">
            Run the existing issue, validation, and identity-capture primitives
            from one bounded product workflow with safe result display.
          </p>
        </div>
        <StatusBadge label="Bounded workflow" tone="info" />
      </section>

      <section className="panel">
        <div className="panel-header">
          <div>
            <h2 className="panel-title">Transitional tenant/code bridge</h2>
            <div className="panel-subtitle">
              Product account and participant references remain future work; this page uses the current tenant and UCN bridge.
            </div>
          </div>
        </div>
        <div className="panel-body referral-link-code-controls">
          <label className="field">
            <span>Tenant code bridge</span>
            <input
              className="input"
              onChange={(event) => setTenantCode(event.target.value.toUpperCase())}
              value={tenantCode}
            />
          </label>
          <label className="field">
            <span>Referrer UCN bridge</span>
            <input
              className="input"
              onChange={(event) => setReferrerUcn(event.target.value)}
              value={referrerUcn}
            />
          </label>
          <label className="field">
            <span>Sticker</span>
            <input
              className="input"
              onChange={(event) => setSticker(event.target.value.toUpperCase())}
              value={sticker}
            />
          </label>
          <label className="field">
            <span>Segment</span>
            <input
              className="input"
              onChange={(event) => setSegment(event.target.value.toUpperCase())}
              value={segment}
            />
          </label>
          <label className="field">
            <span>Preferred handle</span>
            <input
              className="input"
              onChange={(event) => setPreferredHandle(event.target.value)}
              placeholder="Optional"
              value={preferredHandle}
            />
          </label>
          <label className="field">
            <span>Referral code</span>
            <input
              className="input"
              onChange={(event) => setReferralCode(event.target.value.toUpperCase())}
              placeholder="Filled after issue"
              value={referralCode}
            />
          </label>
          <label className="field">
            <span>Validation alias</span>
            <input
              className="input"
              onChange={(event) => setAlias(event.target.value)}
              value={alias}
            />
          </label>
          <label className="field">
            <span>Referee UCN bridge</span>
            <input
              className="input"
              onChange={(event) => setRefereeUcn(event.target.value)}
              placeholder="Required for identity capture"
              value={refereeUcn}
            />
          </label>
          <label className="checkbox-row referral-link-code-terms">
            <input
              checked={acceptedTerms}
              onChange={(event) => setAcceptedTerms(event.target.checked)}
              type="checkbox"
            />
            <span>Accepted terms checked for issue and validation requests</span>
          </label>
        </div>
      </section>

      <section className="grid-4">
        <KpiCard label="Issue" value={issueResult ? "Ready" : "Pending"} footnote="Get-or-create code" icon={KeyRound} />
        <KpiCard label="Validate" value={validationResult ? "Checked" : "Pending"} footnote="Public validation" icon={ShieldCheck} />
        <KpiCard label="Identity" value={captureResult ? "Captured" : "Pending"} footnote="Track-bound UCN capture" icon={UserCheck} />
        <KpiCard label="Guardrail" value="No money" footnote="No rewards, funding, or settlement" icon={CheckCircle2} />
      </section>

      <section className="grid-3">
        <WorkflowPanel
          title="Issue or reuse code"
          subtitle="Calls the existing referral code issue primitive."
          actionLabel={issueMutation.isPending ? "Issuing" : "Issue code"}
          disabled={!canIssueOrValidate || issueMutation.isPending}
          icon={<KeyRound size={16} />}
          onAction={() => issueMutation.mutate()}
          status={resultValue(issueResult, ["created"], "") === "true" ? "Created" : issueResult ? "Existing" : "Waiting"}
          tone={issueResult ? "success" : "neutral"}
        >
          {issueMutation.error ? <ErrorPanel error={issueMutation.error} /> : null}
          <div className="summary-grid">
            <SummaryItem label="Referral code" value={resultValue(issueResult, ["referral_code", "referralCode", "code"])} />
            <SummaryItem label="Handle" value={resultValue(issueResult, ["gaming_handle", "preferred_handle", "handle"])} />
            <SummaryItem label="Message" value={resultValue(issueResult, ["message", "detail"])} />
            <SummaryItem label="Error code" value={resultValue(issueResult, ["error_code", "code"])} />
          </div>
        </WorkflowPanel>

        <WorkflowPanel
          title="Validate code"
          subtitle="Checks the public validation path using accepted terms."
          actionLabel={validateMutation.isPending ? "Validating" : "Validate code"}
          disabled={!canValidate || validateMutation.isPending}
          icon={<ShieldCheck size={16} />}
          onAction={() => validateMutation.mutate()}
          status={resultValue(validationResult, ["validation_outcome", "valid"], "Waiting")}
          tone={validationResult ? statusTone(resultValue(validationResult, ["validation_outcome", "valid"])) : "neutral"}
        >
          {validateMutation.error ? <ErrorPanel error={validateMutation.error} /> : null}
          <div className="summary-grid">
            <SummaryItem label="Outcome" value={resultValue(validationResult, ["validation_outcome", "valid"])} />
            <SummaryItem label="Track ID" value={resultValue(validationResult, ["referral_track_id", "referralTrackId", "track_id"])} />
            <SummaryItem label="Alias" value={resultValue(validationResult, ["alias"])} />
            <SummaryItem label="Message" value={resultValue(validationResult, ["message", "detail"])} />
          </div>
          {Object.keys(validationAttributes).length ? (
            <div className="route-item">
              <div>
                <div className="route-name">Internal attributes redacted</div>
                <div className="route-path">Validation attributes are present but not rendered in this product surface.</div>
              </div>
              <StatusBadge label="Redacted" tone="info" />
            </div>
          ) : null}
        </WorkflowPanel>

        <WorkflowPanel
          title="Capture identity"
          subtitle="Binds referee identity to the validated track."
          actionLabel={captureMutation.isPending ? "Capturing" : "Capture identity"}
          disabled={!canCapture || captureMutation.isPending}
          icon={<UserCheck size={16} />}
          onAction={() => captureMutation.mutate()}
          status={resultValue(captureResult, ["status"], "Waiting")}
          tone={captureResult ? statusTone(resultValue(captureResult, ["status"])) : "neutral"}
        >
          {captureMutation.error ? <ErrorPanel error={captureMutation.error} /> : null}
          <div className="summary-grid">
            <SummaryItem label="Status" value={resultValue(captureResult, ["status"])} />
            <SummaryItem label="Message" value={resultValue(captureResult, ["message", "detail"])} />
            <SummaryItem label="Error code" value={resultValue(captureResult, ["error_code", "code"])} />
          </div>
        </WorkflowPanel>
      </section>

      <section className="grid-2">
        <div className="panel">
          <div className="panel-header">
            <div>
              <h2 className="panel-title">Workflow guardrails</h2>
              <div className="panel-subtitle">
                This surface wraps existing primitives only.
              </div>
            </div>
          </div>
          <div className="panel-body route-list">
            <div className="route-item">
              <div>
                <div className="route-name">No link lifecycle mutation</div>
                <div className="route-path">
                  Reissue, revoke, expire, repair, replay, and manual reward actions are not available here.
                </div>
              </div>
              <StatusBadge label="Deferred" tone="warning" />
            </div>
            <div className="route-item">
              <div>
                <div className="route-name">Safe result display</div>
                <div className="route-path">
                  Response UCNs, hashes, raw attributes, reward, funding, settlement, and wallet evidence are not rendered.
                </div>
              </div>
              <StatusBadge label="Whitelisted" tone="success" />
            </div>
          </div>
        </div>

        <div className="panel">
          <div className="panel-header">
            <div>
              <h2 className="panel-title">Adjacent Referral SaaS surfaces</h2>
              <div className="panel-subtitle">
                Continue through the focused product workflow without forking source code.
              </div>
            </div>
          </div>
          <div className="panel-body route-list">
            <SetupLink to="/admin/referral-saas/account-setup" title="Account setup readiness" copy="Confirm account and membership guardrails." />
            <SetupLink to="/admin/referral-saas/campaigns" title="Campaign readiness" copy="Confirm launch gates before codes are promised." />
            <SetupLink to="/admin/referral-saas/reports" title="Referral SaaS reports" copy="Review link/code and attribution reporting." />
          </div>
        </div>
      </section>
    </>
  );
}

function WorkflowPanel({
  title,
  subtitle,
  actionLabel,
  disabled,
  icon,
  onAction,
  status,
  tone,
  children,
}: {
  title: string;
  subtitle: string;
  actionLabel: string;
  disabled: boolean;
  icon: ReactNode;
  onAction: () => void;
  status: string;
  tone: "success" | "warning" | "danger" | "info" | "neutral";
  children: ReactNode;
}) {
  return (
    <div className="panel">
      <div className="panel-header">
        <div>
          <h2 className="panel-title">{title}</h2>
          <div className="panel-subtitle">{subtitle}</div>
        </div>
        <StatusBadge label={formatDisplay(status)} tone={tone} />
      </div>
      <div className="panel-body route-list">
        <button className="button" disabled={disabled} onClick={onAction} type="button">
          {icon}
          {actionLabel}
        </button>
        {children}
      </div>
    </div>
  );
}

function SetupLink({ to, title, copy }: { to: string; title: string; copy: string }) {
  return (
    <Link className="route-item route-link" to={to}>
      <div>
        <div className="route-name">{title}</div>
        <div className="route-path">{copy}</div>
      </div>
      <LinkIcon size={16} />
    </Link>
  );
}
