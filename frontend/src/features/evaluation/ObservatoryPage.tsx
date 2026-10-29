import { useEffect, useState } from "react";
import { api } from "../../lib/api/client";
import { EmptyState } from "../../components/ui/EmptyState";
import { PageHeader } from "../../components/ui/PageHeader";

type Run = {
  run_id: string;
  dataset_name?: string;
  metrics: Record<string, number>;
  created_at: string;
};

export function ObservatoryPage() {
  const [runs, setRuns] = useState<Run[]>([]);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .listEvalRuns()
      .then((r) => setRuns(r))
      .catch(() => setError("Could not load evaluation history."))
      .finally(() => setLoading(false));
  }, []);

  async function runEval() {
    setRunning(true);
    setError(null);
    try {
      const result = await api.runEvaluation();
      setRuns((prev) => [{ run_id: result.run_id, metrics: result.metrics, created_at: result.created_at, dataset_name: "golden" }, ...prev]);
    } catch {
      setError("Evaluation run failed.");
    } finally {
      setRunning(false);
    }
  }

  return (
    <div className="grd-page">
      <PageHeader
        title="Evaluation Observatory"
        description="Retrieval metrics on the committed golden fixture. Recall@k / Precision@k / MRR measure ranking quality, not factual truth. Runs are started only when you click the button."
        action={
          <button type="button" className="grd-btn grd-btn-primary" disabled={running} onClick={() => void runEval()}>
            {running ? "Running evaluation…" : "Run golden evaluation"}
          </button>
        }
      />
      {error ? <div className="grd-alert error">{error}</div> : null}
      {loading ? <div className="grd-skeleton" style={{ width: "50%" }} /> : null}
      {!loading && runs.length === 0 ? (
        <EmptyState title="No evaluation runs yet" body="Run an evaluation to measure retrieval against the golden Q&A set." />
      ) : null}
      {runs.map((run) => (
        <article key={run.run_id} className="grd-result">
          <div className="grd-meta">
            {run.created_at} · {run.dataset_name ?? "golden"} · {run.run_id.slice(0, 8)}
          </div>
          <div className="grd-metric-row" style={{ marginTop: "0.75rem" }}>
            <div className="grd-metric">
              <span>Recall@k</span>
              <strong>{formatMetric(run.metrics.recall_at_k)}</strong>
            </div>
            <div className="grd-metric">
              <span>Precision@k</span>
              <strong>{formatMetric(run.metrics.precision_at_k)}</strong>
            </div>
            <div className="grd-metric">
              <span>MRR</span>
              <strong>{formatMetric(run.metrics.mrr)}</strong>
            </div>
          </div>
        </article>
      ))}
    </div>
  );
}

function formatMetric(value: number | undefined) {
  if (value == null || Number.isNaN(value)) return "—";
  return value.toFixed(3);
}
