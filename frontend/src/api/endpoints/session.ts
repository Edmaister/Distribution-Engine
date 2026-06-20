import { apiRequest } from "../client";

export type SessionIdentity = {
  authenticated?: boolean;
  role?: string;
  tenant_code?: string;
  tenant?: string;
  producer_code?: string;
  distributor_code?: string;
  auth_source?: string;
  subject?: string;
};

export type SessionWorkspace = {
  code: string;
  label: string;
  path: string;
  summary?: string;
  access: "allowed" | "blocked";
  guidance?: string;
  scope?: {
    tenant_code?: string;
    tenant?: string;
    producer_code?: string;
    distributor_code?: string;
  };
};

export type SessionResponse = {
  status?: string;
  session?: SessionIdentity;
  recommended_workspace?: SessionWorkspace;
  workspaces?: SessionWorkspace[];
};

export function getSession(): Promise<SessionResponse> {
  return apiRequest<SessionResponse>("auth/session");
}
