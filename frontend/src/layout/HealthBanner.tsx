import { useHealthConnection } from "../api/operationalQueries";
import { StatusBadge } from "../components/StatusBadge";

export function HealthBanner({ refreshKey }: { refreshKey: number }) {
  const health = useHealthConnection(refreshKey);

  if (health.isSuccess) {
    return (
      <div className="banner success">
        <StatusBadge label="API online" tone="success" />
        <span className="muted">
          Connected to the configured Amplifi backend.
        </span>
      </div>
    );
  }

  if (health.isError) {
    return (
      <div className="banner danger">
        <StatusBadge label="API offline" tone="danger" />
        <span className="muted">
          Check that the backend is running and the base URL is correct.
        </span>
      </div>
    );
  }

  return (
    <div className="banner warning">
      <StatusBadge label="Checking" tone="warning" />
      <span className="muted">Validating backend connection.</span>
    </div>
  );
}
