import { useEffect, useState } from "react";
import { api, type PublicSettings, type SystemStatus } from "../../lib/api/client";
import { useApiConnection } from "../../hooks/useApiConnection";
import { PageHeader } from "../../components/ui/PageHeader";

export function SettingsPage() {
  const connection = useApiConnection();
  const [settings, setSettings] = useState<PublicSettings | null>(null);
  const [status, setStatus] = useState<SystemStatus | null>(null);
  const [showRaw, setShowRaw] = useState(false);

  useEffect(() => {
    void Promise.all([api.publicSettings(), api.systemStatus()]).then(([s, st]) => {
      setSettings(s);
      setStatus(st);
    });
  }, []);

  return (
    <div className="grd-page">
      <PageHeader
        title="Settings"
        description="Read-only view of server configuration. Change values in .env and restart the API — this page cannot write settings."
      />
      <div className="grd-alert warning" style={{ marginBottom: "1.5rem" }}>
        <strong>No authentication.</strong> This MVP is for localhost or a trusted private network. Do not expose the API
        to the public internet without access controls, TLS, and rate limiting.
      </div>
      <div className="grd-settings-grid">
        <section className="grd-settings-row">
          <h2>General</h2>
          <div>
            <p>
              App <strong>{settings?.app_name ?? "—"}</strong> · env <strong>{settings?.app_env ?? "—"}</strong>
            </p>
            <p className="grd-meta">Version {status?.version ?? "—"}</p>
          </div>
        </section>
        <section className="grd-settings-row">
          <h2>Providers</h2>
          <div>
            <p>
              Embeddings: <strong>{settings?.embedding_provider}</strong> ({settings?.embedding_model_name}).{" "}
              <em>fake</em> is deterministic and offline; <em>local</em> uses a real sentence-transformers model.
            </p>
            <p>
              Generation: <strong>{settings?.llm_provider}</strong>. <em>mock</em> is for tests; <em>ollama</em> requires a
              running local server.
            </p>
          </div>
        </section>
        <section className="grd-settings-row">
          <h2>Retrieval</h2>
          <div>
            <p>Default top-k: {settings?.retrieval_top_k ?? "—"}</p>
            <p>
              Max upload: {settings ? Math.round(settings.max_upload_bytes / 1024 / 1024) : "—"} MB ·{" "}
              {settings?.allowed_upload_extensions.join(", ")}
            </p>
          </div>
        </section>
        <section className="grd-settings-row">
          <h2>Agent</h2>
          <div>
            <p>
              Agent{" "}
              <span className={`grd-badge ${settings?.agent_enabled ? "success" : "warning"}`}>
                {settings?.agent_enabled ? "enabled" : "disabled"}
              </span>
            </p>
            <p>Demo mode: {settings?.demo_mode ? "On (destructive ops blocked)" : "Off"}</p>
          </div>
        </section>
        <section className="grd-settings-row">
          <h2>Storage</h2>
          <div>
            <p>
              Documents {status?.document_count ?? "—"} · chunks {status?.chunk_count ?? "—"}. Database status{" "}
              {status?.database ?? "—"}.
            </p>
          </div>
        </section>
        <section className="grd-settings-row">
          <h2>Diagnostics</h2>
          <div>
            <p>
              API{" "}
              <span className={`grd-badge ${connection === "connected" ? "success" : "error"}`}>{connection}</span>
            </p>
            <button type="button" className="grd-btn grd-btn-secondary" onClick={() => setShowRaw((v) => !v)}>
              {showRaw ? "Hide" : "Show"} technical details
            </button>
            {showRaw ? (
              <pre className="grd-meta" style={{ marginTop: "1rem", whiteSpace: "pre-wrap" }}>
                {JSON.stringify({ settings, status }, null, 2)}
              </pre>
            ) : null}
          </div>
        </section>
      </div>
    </div>
  );
}
