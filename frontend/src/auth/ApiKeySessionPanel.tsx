import { Save } from "lucide-react";
import { FormEvent, useState } from "react";
import { ROLE_PRESETS, readApiSession, roleForApiKey, writeApiSession } from "./authStore";

type Props = {
  onSave: () => void;
};

export function ApiKeySessionPanel({ onSave }: Props) {
  const [session, setSession] = useState(readApiSession);
  const [selectedRole, setSelectedRole] = useState(() => roleForApiKey(readApiSession().apiKey));

  function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    writeApiSession(session);
    onSave();
  }

  return (
    <form className="form-row api-session-row" onSubmit={save}>
      <div className="field">
        <label htmlFor="api-role">Session role</label>
        <select
          className="input"
          id="api-role"
          value={selectedRole}
          onChange={(event) => {
            const nextRole = event.target.value;
            setSelectedRole(nextRole);
            const preset = ROLE_PRESETS.find((item) => item.value === nextRole);
            if (preset) {
              setSession({ ...session, apiKey: preset.apiKey, authToken: "" });
            }
          }}
        >
          {ROLE_PRESETS.map((preset) => (
            <option key={preset.value} value={preset.value}>
              {preset.label}
            </option>
          ))}
          <option value="custom">Custom key</option>
        </select>
      </div>
      <div className="field">
        <label htmlFor="api-base">API base URL</label>
        <input
          className="input"
          id="api-base"
          value={session.apiBaseUrl}
          onChange={(event) => setSession({ ...session, apiBaseUrl: event.target.value })}
        />
      </div>
      <div className="field">
        <label htmlFor="api-key">Local API key</label>
        <input
          className="input"
          id="api-key"
          value={session.apiKey}
          onChange={(event) => {
            setSelectedRole(roleForApiKey(event.target.value));
            setSession({ ...session, apiKey: event.target.value });
          }}
        />
      </div>
      <div className="field">
        <label htmlFor="auth-token">Bearer token</label>
        <input
          className="input"
          id="auth-token"
          placeholder="JWT bearer token overrides local key"
          value={session.authToken}
          onChange={(event) => setSession({ ...session, authToken: event.target.value })}
        />
      </div>
      <button className="button" type="submit" title="Save API session">
        <Save size={16} />
        Save
      </button>
    </form>
  );
}
