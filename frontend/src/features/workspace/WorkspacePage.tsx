import { useEffect, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api, type AskResponse, type Citation } from "../../lib/api/client";
import { EvidenceRail } from "../../components/evidence/EvidenceRail";
import { Icon } from "../../components/icons/Icon";
import { Prose } from "../../components/ui/Prose";
import { useToast } from "../../components/ui/Toast";

const EXAMPLE_QUESTIONS = [
  "What command rolls back the database migration?",
  "When should we scale API replicas for checkout latency?",
];

export function WorkspacePage() {
  const navigate = useNavigate();
  const { notify } = useToast();
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [response, setResponse] = useState<AskResponse | null>(null);
  const [selected, setSelected] = useState<Citation | null>(null);
  const [docCount, setDocCount] = useState<number | null>(null);
  const [copyLabel, setCopyLabel] = useState("Copy answer");
  const [evidenceOpen, setEvidenceOpen] = useState(false);
  const sessionIdRef = useRef<string | null>(null);

  useEffect(() => {
    api
      .listDocuments()
      .then((d) => setDocCount(d.total))
      .catch(() => setDocCount(null));
  }, [response]);

  async function ensureSession() {
    if (sessionIdRef.current) return sessionIdRef.current;
    const session = await api.createSession(question.trim().slice(0, 80) || "Research session");
    sessionIdRef.current = session.session_id;
    return session.session_id;
  }

  async function submit() {
    const q = question.trim();
    if (!q) return;
    setLoading(true);
    setError(null);
    try {
      const sessionId = await ensureSession();
      const result = await api.ask(q, { session_id: sessionId });
      setResponse(result);
      setSelected(result.citations[0] ?? null);
      setEvidenceOpen(true);
    } catch {
      setError("We couldn't complete your research request. Check the API connection and try again.");
    } finally {
      setLoading(false);
    }
  }

  async function copyAnswer() {
    if (!response?.answer) return;
    try {
      await navigator.clipboard.writeText(response.answer);
      setCopyLabel("Copied");
      notify("Answer copied");
      window.setTimeout(() => setCopyLabel("Copy answer"), 2000);
    } catch {
      setCopyLabel("Copy failed");
    }
  }

  function openSource(id: string, chunkId?: string) {
    const q = chunkId ? `?chunk=${encodeURIComponent(chunkId)}` : "";
    navigate(`/library/${id}${q}`);
  }

  const showInspector = Boolean(response && (response.citations.length || response.insufficient_evidence));

  const rail = (
    <EvidenceRail
      citations={response?.citations ?? []}
      selected={selected}
      onSelect={setSelected}
      insufficient={response?.insufficient_evidence ?? false}
      onOpenDocument={openSource}
      className={showInspector ? "desktop-only" : ""}
    />
  );

  return (
    <div className={`grd-workspace-layout${showInspector ? "" : " no-inspector"}`}>
      <div className="grd-page">
        {!response ? (
          <div style={{ maxWidth: "var(--grd-content-max)" }}>
            <p className="grd-meta" style={{ marginBottom: "0.75rem" }}>
              RESEARCH
            </p>
            <h1 style={{ margin: "0 0 0.5rem", fontSize: "var(--grd-text-xl)", letterSpacing: "-0.03em", fontWeight: 650 }}>
              Ask with your sources in view
            </h1>
            <p style={{ margin: "0 0 1.5rem", color: "var(--grd-text-secondary)" }}>
              Grounded Research Desk answers from your uploaded documents and shows the passages it used.
            </p>
            {docCount === 0 ? (
              <div className="grd-alert info" style={{ marginBottom: "1.25rem" }}>
                No documents yet.{" "}
                <Link to="/library">Upload Markdown or text</Link> before you ask — answers are not invented from the
                open web.
              </div>
            ) : null}
            {docCount != null && docCount > 0 ? (
              <div style={{ marginBottom: "1rem", display: "flex", flexWrap: "wrap", gap: "0.4rem" }}>
                {EXAMPLE_QUESTIONS.map((ex) => (
                  <button key={ex} type="button" className="grd-chip" onClick={() => setQuestion(ex)}>
                    {ex.length > 52 ? `${ex.slice(0, 52)}…` : ex}
                  </button>
                ))}
              </div>
            ) : null}
            <Composer
              id="research-question"
              label="Research question"
              value={question}
              onChange={setQuestion}
              loading={loading}
              onSubmit={() => void submit()}
              meta={docCount != null ? `${docCount} documents indexed` : undefined}
            />
            {error ? <p style={{ color: "var(--grd-error)", marginTop: "1rem" }}>{error}</p> : null}
          </div>
        ) : (
          <div style={{ maxWidth: "var(--grd-content-max)" }}>
            <p className="grd-meta" style={{ marginBottom: "0.5rem" }}>
              Question
            </p>
            <p style={{ margin: "0 0 1.5rem", fontWeight: 600, fontSize: "var(--grd-text-lg)", letterSpacing: "-0.02em" }}>
              {question}
            </p>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: "1rem" }}>
              <h2 style={{ margin: 0, fontSize: "var(--grd-text-sm)", letterSpacing: "0.04em" }}>ANSWER</h2>
              <div style={{ display: "flex", gap: "0.5rem" }}>
                {showInspector ? (
                  <button
                    type="button"
                    className="grd-btn grd-btn-secondary grd-evidence-toggle"
                    style={{ height: "32px" }}
                    onClick={() => setEvidenceOpen(true)}
                  >
                    Evidence
                  </button>
                ) : null}
                {!response.insufficient_evidence ? (
                  <button type="button" className="grd-btn grd-btn-secondary" style={{ height: "32px" }} onClick={() => void copyAnswer()}>
                    <Icon name="copy" size={14} />
                    {copyLabel}
                  </button>
                ) : null}
              </div>
            </div>
            {response.insufficient_evidence ? (
              <div className="grd-alert warning" role="status" style={{ marginTop: "1rem" }}>
                <strong>Insufficient evidence</strong>
                <p style={{ margin: "0.5rem 0 0" }}>{response.answer}</p>
                <p style={{ margin: "0.75rem 0 0", fontSize: "var(--grd-text-sm)" }}>
                  <Link to="/library">Upload a relevant source</Link>
                </p>
              </div>
            ) : (
              <div style={{ marginTop: "1rem" }}>
                <Prose text={response.answer} />
              </div>
            )}
            {!response.insufficient_evidence && response.retrieval?.duration_ms != null ? (
              <p className="grd-meta" style={{ marginTop: "1rem" }}>
                Retrieved in {String(response.retrieval.duration_ms)} ms
              </p>
            ) : null}
            <div style={{ marginTop: "2rem", paddingTop: "1.25rem", borderTop: "1px solid var(--grd-border-subtle)" }}>
              <Composer
                id="followup-question"
                label="Ask another question"
                value={question}
                onChange={setQuestion}
                loading={loading}
                onSubmit={() => void submit()}
              />
              <div style={{ marginTop: "0.75rem", display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
                <button
                  type="button"
                  className="grd-btn grd-btn-ghost"
                  onClick={() => {
                    setResponse(null);
                    setSelected(null);
                    setQuestion("");
                    sessionIdRef.current = null;
                  }}
                >
                  Start over
                </button>
                {sessionIdRef.current ? (
                  <Link to={`/history/${sessionIdRef.current}`} className="grd-btn grd-btn-secondary">
                    View session
                  </Link>
                ) : null}
              </div>
            </div>
            {error ? <p style={{ color: "var(--grd-error)" }}>{error}</p> : null}
          </div>
        )}
      </div>
      {showInspector ? rail : null}
      {showInspector && evidenceOpen ? (
        <div className="grd-drawer-root grd-mobile-only" role="presentation">
          <button type="button" className="grd-dialog-backdrop" aria-label="Close evidence" onClick={() => setEvidenceOpen(false)} />
          <div className="grd-drawer-panel grd-inspector-mobile">
            <EvidenceRail
              citations={response?.citations ?? []}
              selected={selected}
              onSelect={setSelected}
              insufficient={response?.insufficient_evidence ?? false}
              onOpenDocument={openSource}
            />
          </div>
        </div>
      ) : null}
    </div>
  );
}

function Composer({
  id,
  label,
  value,
  onChange,
  loading,
  onSubmit,
  meta,
}: {
  id: string;
  label: string;
  value: string;
  onChange: (v: string) => void;
  loading: boolean;
  onSubmit: () => void;
  meta?: string;
}) {
  return (
    <>
      <label className="grd-label" htmlFor={id}>
        {label}
      </label>
      <div className="grd-composer">
        <textarea
          id={id}
          className="grd-textarea"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder="Ask about content in your uploaded documents…"
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey && (e.metaKey || e.ctrlKey)) {
              e.preventDefault();
              onSubmit();
            }
          }}
        />
        <div className="grd-composer-bar">
          <span className="grd-meta">{meta ?? "⌘/Ctrl + Enter to submit"}</span>
          <button className="grd-btn grd-btn-primary" type="button" disabled={loading || !value.trim()} onClick={onSubmit}>
            {loading ? "Searching documents…" : "Submit question"}
          </button>
        </div>
      </div>
    </>
  );
}
