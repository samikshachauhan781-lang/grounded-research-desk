import { useEffect, useState } from "react";
import { api, ApiError, type PublicSettings, type ResearchResponse } from "../../lib/api/client";
import { PageHeader } from "../../components/ui/PageHeader";
import { Prose } from "../../components/ui/Prose";

export function AgentPage() {
  const [settings, setSettings] = useState<PublicSettings | null>(null);
  const [goal, setGoal] = useState("");
  const [result, setResult] = useState<ResearchResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [running, setRunning] = useState(false);

  useEffect(() => {
    api.publicSettings().then(setSettings).catch(() => setSettings(null));
  }, []);

  async function run() {
    setError(null);
    setResult(null);
    setRunning(true);
    try {
      setResult(await api.research(goal));
    } catch (err) {
      if (err instanceof ApiError && err.status === 403) {
        setError("The research agent is disabled. Set AGENT_ENABLED=true in the server environment and restart the API.");
      } else {
        setError("Agent run failed.");
      }
    } finally {
      setRunning(false);
    }
  }

  const enabled = Boolean(settings?.agent_enabled);

  return (
    <div className="grd-page">
      <PageHeader
        title="Agent Activity"
        description="Bounded research agent with a fixed tool allowlist, tool-call cap, and wall-clock timeout. It cannot run arbitrary shell commands."
      />
      <p>
        Status:{" "}
        <span className={`grd-badge ${enabled ? "success" : "warning"}`}>{enabled ? "Enabled" : "Disabled"}</span>
      </p>
      {!enabled ? (
        <div className="grd-alert warning" style={{ margin: "1rem 0" }}>
          Agent routes are protected while disabled. Enabling requires a server restart with AGENT_ENABLED=true.
        </div>
      ) : null}
      <label className="grd-label" htmlFor="agent-goal">
        Research goal
      </label>
      <textarea
        id="agent-goal"
        className="grd-textarea"
        rows={3}
        value={goal}
        onChange={(e) => setGoal(e.target.value)}
        disabled={!enabled}
      />
      <button
        type="button"
        className="grd-btn grd-btn-primary"
        style={{ marginTop: "0.75rem" }}
        disabled={!enabled || !goal.trim() || running}
        onClick={() => void run()}
      >
        {running ? "Running…" : "Run agent"}
      </button>
      {error ? (
        <div className="grd-alert warning" style={{ marginTop: "1rem" }}>
          {error}
        </div>
      ) : null}
      {result ? (
        <div style={{ marginTop: "1.5rem" }}>
          <p className="grd-meta">{result.status}</p>
          <Prose text={result.answer} />
          {result.steps?.length ? (
            <ol style={{ paddingLeft: "1.25rem", fontSize: "var(--grd-text-sm)", color: "var(--grd-text-secondary)" }}>
              {result.steps.map((s) => (
                <li key={s.step_index}>
                  <strong>{s.tool}</strong> — {s.observation_summary}
                </li>
              ))}
            </ol>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}
