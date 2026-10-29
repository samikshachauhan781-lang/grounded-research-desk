import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, type SessionItem } from "../../lib/api/client";
import { ConfirmDialog } from "../../components/ui/ConfirmDialog";
import { EmptyState } from "../../components/ui/EmptyState";
import { PageHeader } from "../../components/ui/PageHeader";
import { useToast } from "../../components/ui/Toast";

export function HistoryPage() {
  const { notify } = useToast();
  const [sessions, setSessions] = useState<SessionItem[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [pending, setPending] = useState<SessionItem | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    api
      .listSessions()
      .then(setSessions)
      .catch(() => setError("Could not load research sessions."))
      .finally(() => setLoading(false));
  }, []);

  async function remove() {
    if (!pending) return;
    setBusy(true);
    try {
      await api.deleteSession(pending.session_id);
      setSessions((s) => s.filter((x) => x.session_id !== pending.session_id));
      notify("Session deleted");
      setPending(null);
    } catch {
      setError("Could not delete session.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="grd-page">
      <PageHeader
        title="Research History"
        description="Sessions created from the Research workspace. Entries appear only after a question is submitted."
      />
      {error ? <div className="grd-alert error">{error}</div> : null}
      {loading ? <div className="grd-skeleton" style={{ width: "40%" }} /> : null}
      {!loading && sessions.length === 0 ? (
        <EmptyState
          title="No saved sessions"
          body="Ask a question on the Research page to create your first saved session."
          action={
            <Link to="/" className="grd-btn grd-btn-primary">
              Open Research
            </Link>
          }
        />
      ) : null}
      {!loading && sessions.length > 0 ? (
        <div className="grd-doc-list">
          {sessions.map((s) => (
            <div className="grd-doc-row" key={s.session_id} style={{ gridTemplateColumns: "minmax(0,1fr) auto auto auto" }}>
              <div className="grd-doc-name">
                <Link to={`/history/${s.session_id}`}>{s.title}</Link>
              </div>
              <span className="grd-meta">{s.message_count} messages</span>
              <span className="grd-meta">{s.updated_at}</span>
              <button type="button" className="grd-btn grd-btn-ghost" style={{ height: 32 }} onClick={() => setPending(s)}>
                Delete
              </button>
            </div>
          ))}
        </div>
      ) : null}
      <ConfirmDialog
        open={Boolean(pending)}
        title="Delete session?"
        body="This removes the saved questions and answers for this session."
        busy={busy}
        onCancel={() => setPending(null)}
        onConfirm={() => void remove()}
      />
    </div>
  );
}
