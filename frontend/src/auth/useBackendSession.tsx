import { useQuery } from "@tanstack/react-query";
import { createContext, useContext, type ReactNode } from "react";
import {
  getSession,
  type SessionIdentity,
  type SessionWorkspace,
} from "../api/endpoints/session";
import { queryKeys } from "../api/queryKeys";
import { readApiSession, roleForApiKey, roleLabelForApiKey } from "./authStore";

export type BackendSessionStatus = "loading" | "confirmed" | "fallback";

export type BackendSessionState = {
  session: SessionIdentity | null;
  status: BackendSessionStatus;
  recommendedWorkspace: SessionWorkspace | null;
  workspaces: SessionWorkspace[];
};

const fallbackSessionState: BackendSessionState = {
  session: null,
  status: "fallback",
  recommendedWorkspace: null,
  workspaces: [],
};

const BackendSessionContext =
  createContext<BackendSessionState>(fallbackSessionState);

export function BackendSessionProvider({
  children,
  refreshKey,
}: {
  children: ReactNode;
  refreshKey: number;
}) {
  const query = useQuery({
    queryKey: queryKeys.backendSession(refreshKey),
    queryFn: getSession,
    retry: 1,
  });

  const session = query.data?.session ?? null;
  const recommendedWorkspace = query.data?.recommended_workspace ?? null;
  const workspaces = query.data?.workspaces ?? [];
  const status: BackendSessionStatus = query.isLoading
    ? "loading"
    : session?.role
      ? "confirmed"
      : "fallback";

  return (
    <BackendSessionContext.Provider
      value={{ session, status, recommendedWorkspace, workspaces }}
    >
      {children}
    </BackendSessionContext.Provider>
  );
}

export function useBackendSession(_refreshKey?: number, _scopeKey = "") {
  void _refreshKey;
  void _scopeKey;
  return useContext(BackendSessionContext);
}

export function normalizeSessionRole(role?: string) {
  return role ? role.toLowerCase() : "";
}

export function activeSessionRole(
  backendSession: SessionIdentity | null,
  status: BackendSessionStatus,
) {
  if (status === "confirmed") {
    return normalizeSessionRole(backendSession?.role);
  }

  return roleForApiKey(readApiSession().apiKey);
}

export function activeSessionLabel(
  backendSession: SessionIdentity | null,
  status: BackendSessionStatus,
) {
  if (status === "confirmed" && backendSession) {
    return labelForBackendSession(backendSession);
  }

  return roleLabelForApiKey(readApiSession().apiKey);
}

export function workspaceForPath(workspaces: SessionWorkspace[], path: string) {
  return workspaces.find((workspace) => workspace.path === path);
}

export function labelForBackendSession(session: SessionIdentity) {
  const role = normalizeSessionRole(session.role);

  if (role === "admin") {
    return "Amplifi Admin";
  }

  if (role === "finance_admin") {
    return "Finance Admin";
  }

  if (role === "distribution_admin") {
    return "Distribution Admin";
  }

  if (role === "system_admin") {
    return "System Admin";
  }

  if (role === "producer") {
    return session.producer_code
      ? `Producer - ${session.producer_code}`
      : "Producer - Supply";
  }

  if (role === "distributor") {
    return session.distributor_code
      ? `Distributor - ${session.distributor_code}`
      : "Distributor - Demand";
  }

  if (role === "consumer") {
    return "Consumer Journey";
  }

  if (role === "partner") {
    return `${session.tenant_code || session.tenant || "Tenant"} Partner`;
  }

  return "Custom key";
}
