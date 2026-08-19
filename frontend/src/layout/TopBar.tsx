import { RefreshCw } from "lucide-react";
import { useLocation } from "react-router-dom";
import { ApiKeySessionPanel } from "../auth/ApiKeySessionPanel";

type Props = {
  title: string;
  subtitle: string;
  onRefresh: () => void;
};

export function TopBar({ title, subtitle, onRefresh }: Props) {
  const location = useLocation();
  const role = getRoleLabel(location.pathname);
  const isReferralSaas = location.pathname.startsWith("/admin/referral-saas");
  const isSelectedCustomer = /^\/admin\/referral-saas\/account-maintenance\/[^/]+/.test(
    location.pathname,
  );

  return (
    <header className="topbar">
      <div>
        {isReferralSaas ? (
          <div className="topbar-context">
            {isSelectedCustomer ? "Selected customer" : "Amplifi Global"}
          </div>
        ) : null}
        <div className="topbar-title-row">
          <div className="topbar-title">{title}</div>
          <span className="role-pill">{role}</span>
        </div>
        <div className="topbar-meta">{subtitle}</div>
      </div>
      <div className="topbar-actions">
        <ApiKeySessionPanel onSave={onRefresh} />
        <button className="icon-button" type="button" title="Refresh current view" onClick={onRefresh}>
          <RefreshCw size={16} />
        </button>
      </div>
    </header>
  );
}

function getRoleLabel(pathname: string) {
  if (pathname.startsWith("/admin")) {
    return "Amplifi Admin";
  }
  if (pathname.startsWith("/distributor") || pathname === "/consumer" || pathname === "/admin/distribution") {
    return "Distributor - Demand";
  }
  if (pathname.startsWith("/sponsor") || pathname === "/partner") {
    return "Producer - Supply";
  }
  return "Amplifi Admin";
}
