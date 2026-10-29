import { Link } from "react-router-dom";
import type { Citation } from "../../lib/api/client";

type Props = {
  citations: Citation[];
  selected: Citation | null;
  onSelect: (citation: Citation) => void;
  onOpenDocument: (documentId: string, chunkId?: string) => void;
  insufficient?: boolean;
  className?: string;
};

export function EvidenceRail({
  citations,
  selected,
  onSelect,
  onOpenDocument,
  insufficient,
  className = "",
}: Props) {
  return (
    <aside className={`grd-inspector ${className}`} aria-label="Evidence rail">
      <h2 style={{ margin: "0 0 0.35rem", fontSize: "var(--grd-text-sm)", fontWeight: 650 }}>Evidence</h2>
      <p className="grd-meta" style={{ margin: "0 0 1rem" }}>
        Retrieved passages — not a proof of correctness.
      </p>
      {insufficient ? (
        <div className="grd-alert warning">
          No supporting sources met the evidence threshold. Upload a relevant document or narrow the question.{" "}
          <Link to="/library">Open library</Link>
        </div>
      ) : null}
      {!citations.length && !insufficient ? (
        <p style={{ color: "var(--grd-text-secondary)", fontSize: "var(--grd-text-sm)" }}>
          Sources appear here after a grounded answer.
        </p>
      ) : null}
      {citations.map((c) => (
        <div
          key={c.citation_id}
          className={`grd-evidence-card${selected?.citation_id === c.citation_id ? " selected" : ""}`}
        >
          <button type="button" className="grd-btn grd-btn-ghost" style={{ display: "block", width: "100%", height: "auto", textAlign: "left", padding: 0 }} onClick={() => onSelect(c)}>
            <div style={{ fontWeight: 600, fontSize: "var(--grd-text-sm)", marginBottom: "0.35rem" }}>{c.filename}</div>
            <p style={{ margin: "0 0 0.5rem", fontSize: "var(--grd-text-sm)", color: "var(--grd-text-secondary)" }}>
              {c.snippet}
            </p>
            <div className="grd-meta">
              {c.citation_id} · chunk {c.chunk_id.slice(0, 8)}
              {typeof c.score === "number" ? ` · ${c.score.toFixed(3)}` : ""}
            </div>
          </button>
          <button
            type="button"
            className="grd-btn grd-btn-secondary"
            style={{ marginTop: "0.75rem", height: "30px", fontSize: "var(--grd-text-xs)" }}
            onClick={() => onOpenDocument(c.document_id, c.chunk_id)}
          >
            Open source
          </button>
        </div>
      ))}
    </aside>
  );
}
