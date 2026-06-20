import { Link, useLocation } from "react-router-dom";
import { StatusBadge } from "../components/StatusBadge";
import { activeSessionLabel, useBackendSession, workspaceForPath } from "./useBackendSession";

export function SessionRoleBanner() {
  const location = useLocation();
  const backend = useBackendSession();
  const workspace = workspaceForPath(backend.workspaces, location.pathname);

  if (!workspace) {
    return null;
  }

  const activeLabel = activeSessionLabel(backend.session, backend.status);
  const confirmation =
    backend.status === "confirmed"
      ? "Session confirmed by backend."
      : "Session role could not be confirmed; using selected key.";
  const recommendedWorkspace = backend.recommendedWorkspace;
  const guidance = workspace.guidance || workspace.summary || `Access is aligned to ${workspace.label}.`;
  const recommendation =
    recommendedWorkspace && recommendedWorkspace.code !== workspace.code
      ? ` Recommended start: ${recommendedWorkspace.label}.`
      : recommendedWorkspace?.code === workspace.code
        ? " This is the recommended starting point."
        : "";
  const showRecommendedLink =
    recommendedWorkspace && recommendedWorkspace.code !== workspace.code && recommendedWorkspace.path;

  if (workspace.access === "allowed") {
    return (
      <div className="banner success session-role-banner">
        <StatusBadge label={activeLabel} tone="success" />
        <span className="muted">
          {confirmation} {guidance}{recommendation}
        </span>
        {showRecommendedLink && recommendedWorkspace ? (
          <Link className="session-role-link" to={recommendedWorkspace.path}>
            Go to start
          </Link>
        ) : null}
      </div>
    );
  }

  return (
    <div className="banner warning session-role-banner">
      <StatusBadge label={activeLabel} tone="warning" />
      <span className="muted">
        {confirmation} {guidance}{recommendation}
      </span>
      {showRecommendedLink && recommendedWorkspace ? (
        <Link className="session-role-link" to={recommendedWorkspace.path}>
          Go to start
        </Link>
      ) : null}
    </div>
  );
}
