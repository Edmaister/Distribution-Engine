import { useMutation, useQuery } from "@tanstack/react-query";
import { CheckCircle2, ShieldCheck, XCircle } from "lucide-react";
import { useMemo } from "react";
import { Link, useSearchParams } from "react-router-dom";

import {
  acceptReferralSaasMembershipAcceptanceToken,
  validateReferralSaasMembershipAcceptanceToken,
} from "../../api/endpoints/referralSaasAccounts";

function requestId(prefix: string) {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return `${prefix}-${crypto.randomUUID()}`;
  }
  return `${prefix}-${Date.now()}`;
}

export function ReferralSaasMembershipAcceptancePage() {
  const [searchParams] = useSearchParams();
  const token = searchParams.get("token")?.trim() || "";
  const validation = useQuery({
    queryKey: ["referral-saas-membership-acceptance", token],
    queryFn: () => validateReferralSaasMembershipAcceptanceToken({ token }),
    enabled: Boolean(token),
    retry: false,
  });
  const acceptMutation = useMutation({
    mutationFn: () =>
      acceptReferralSaasMembershipAcceptanceToken({
        token,
        correlationId: requestId("acceptance"),
        idempotencyKey: requestId("acceptance"),
        acceptanceEvidenceRef: "member-clicked-acceptance-link",
      }),
  });
  const acceptance = acceptMutation.data?.acceptance || validation.data?.acceptance;
  const tokenStatus = String(acceptance?.tokenStatus || "").toUpperCase();
  const isReady = tokenStatus === "ISSUED";
  const isAccepted =
    tokenStatus === "ACCEPTED" ||
    String(acceptance?.activation?.status || "").toUpperCase() === "MEMBERSHIP_ACTIVATED";
  const statusCopy = useMemo(() => {
    if (!token) {
      return {
        title: "Access link missing",
        copy: "Ask the sender for a fresh Referral SaaS access link.",
        tone: "danger",
      };
    }
    if (validation.isLoading) {
      return {
        title: "Checking your access link",
        copy: "We are confirming that this link is valid and still in date.",
        tone: "neutral",
      };
    }
    if (isAccepted) {
      return {
        title: "Access accepted",
        copy: "You are confirmed for this customer. Platform login, seats, and permissions are handled separately.",
        tone: "success",
      };
    }
    if (isReady) {
      return {
        title: "Review and accept access",
        copy: "Accepting confirms that you are the named person for this customer role.",
        tone: "neutral",
      };
    }
    return {
      title: "This access link cannot be used",
      copy: acceptance?.nextAction || "Ask the sender for a fresh Referral SaaS access link.",
      tone: "danger",
    };
  }, [acceptance?.nextAction, isAccepted, isReady, token, validation.isLoading]);

  return (
    <main className="workspace-shell workspace-shell--public">
      <section className={`panel panel--${statusCopy.tone}`}>
        <div className="panel__header">
          <div>
            <p className="eyebrow">Referral SaaS access</p>
            <h1>{statusCopy.title}</h1>
            <p>{statusCopy.copy}</p>
          </div>
          {isAccepted ? <CheckCircle2 aria-hidden="true" /> : isReady ? <ShieldCheck aria-hidden="true" /> : <XCircle aria-hidden="true" />}
        </div>
        {acceptance ? (
          <div className="detail-grid">
            <div>
              <span>Customer</span>
              <strong>{acceptance.account?.accountName || "Referral SaaS customer"}</strong>
            </div>
            <div>
              <span>Person</span>
              <strong>{acceptance.person?.displayName || "Named invitee"}</strong>
            </div>
            <div>
              <span>Responsibility</span>
              <strong>{acceptance.membership?.roleFamily?.replace(/_/g, " ") || "Customer access"}</strong>
            </div>
            <div>
              <span>Link expires</span>
              <strong>{acceptance.expiresAt || "Not available"}</strong>
            </div>
          </div>
        ) : null}
        {acceptMutation.isError ? (
          <div className="banner banner--error">Access could not be accepted. Ask the sender for a fresh link.</div>
        ) : null}
        <div className="safe-boundary">
          This does not create login credentials, assign a seat, change permissions, launch a campaign, bill anyone, or move money.
        </div>
        <div className="button-row">
          <button className="button button--primary" type="button" disabled={!isReady || acceptMutation.isPending} onClick={() => acceptMutation.mutate()}>
            {acceptMutation.isPending ? "Accepting..." : "Accept access"}
          </button>
          <Link className="button" to="/admin/referral-saas">
            Back to Referral SaaS
          </Link>
        </div>
      </section>
    </main>
  );
}
