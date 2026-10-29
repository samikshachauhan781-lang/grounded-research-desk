import { useEffect, useState } from "react";
import { Link, useNavigate, useParams, useSearchParams } from "react-router-dom";
import { api, type DocumentDetail } from "../../lib/api/client";
import { ConfirmDialog } from "../../components/ui/ConfirmDialog";
import { EmptyState } from "../../components/ui/EmptyState";
import { useToast } from "../../components/ui/Toast";

export function DocumentInspectorPage() {
  const { documentId } = useParams<{ documentId: string }>();
  const [searchParams] = useSearchParams();
  const chunkFromQuery = searchParams.get("chunk");
  const navigate = useNavigate();
  const { notify } = useToast();
  const [doc, setDoc] = useState<DocumentDetail | null>(null);
  const [chunks, setChunks] = useState<Array<{ chunk_id: string; chunk_index: number; text: string }>>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeChunk, setActiveChunk] = useState<string | null>(null);
  const [confirm, setConfirm] = useState(false);
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    if (!documentId) return;
    setError(null);
    setLoading(true);
    Promise.all([api.getDocument(documentId), api.getChunks(documentId)])
      .then(([detail, chunkData]) => {
        setDoc(detail);
        setChunks(chunkData.items);
        const preferred =
          chunkFromQuery && chunkData.items.some((c) => c.chunk_id === chunkFromQuery)
            ? chunkFromQuery
            : chunkData.items[0]?.chunk_id ?? null;
        setActiveChunk(preferred);
      })
      .catch(() => setError("Document not found or unavailable."))
      .finally(() => setLoading(false));
  }, [documentId, chunkFromQuery]);

  async function onDelete() {
    if (!documentId) return;
    setDeleting(true);
    try {
      await api.deleteDocument(documentId);
      notify("Document deleted");
      navigate("/library");
    } catch {
      setError("Delete failed.");
    } finally {
      setDeleting(false);
      setConfirm(false);
    }
  }

  if (!documentId) {
    return (
      <div className="grd-page">
        <EmptyState title="Select a document" body="Open a document from the Library." action={<Link to="/library">Library</Link>} />
      </div>
    );
  }

  const active = chunks.find((c) => c.chunk_id === activeChunk);

  return (
    <div className="grd-page grd-page-wide">
      <p className="grd-meta" style={{ marginBottom: "0.75rem" }}>
        <Link to="/library">Library</Link>
        <span className="grd-crumb"> / {doc?.filename ?? "Document"}</span>
      </p>
      {error ? <div className="grd-alert warning">{error}</div> : null}
      {loading ? <div className="grd-skeleton" style={{ width: "50%" }} /> : null}
      {!loading && !error && doc ? (
        <div className="grd-inspector-grid" style={{ display: "grid", gridTemplateColumns: "minmax(180px, 240px) 1fr", gap: "1.5rem" }}>
          <aside>
            <h1 style={{ fontSize: "var(--grd-text-lg)", margin: "0 0 0.5rem", letterSpacing: "-0.02em" }}>{doc.filename}</h1>
            <span className={`grd-badge ${doc.processing_status === "completed" ? "success" : "warning"}`}>
              {doc.processing_status}
            </span>
            <p className="grd-meta" style={{ marginTop: "0.75rem" }}>
              {doc.chunk_count} chunks · {doc.byte_size} bytes
            </p>
            <p className="grd-meta">Updated {doc.updated_at}</p>
            <button type="button" className="grd-btn grd-btn-danger" style={{ marginTop: "1rem", height: 32 }} onClick={() => setConfirm(true)}>
              Delete
            </button>
            <nav aria-label="Chunks" style={{ marginTop: "1.25rem" }}>
              {chunks.map((c) => (
                <button
                  key={c.chunk_id}
                  type="button"
                  className={`grd-nav-link${activeChunk === c.chunk_id ? " active" : ""}`}
                  style={{ width: "100%", border: "none", background: "transparent", cursor: "pointer" }}
                  onClick={() => setActiveChunk(c.chunk_id)}
                >
                  Chunk {c.chunk_index}
                </button>
              ))}
            </nav>
          </aside>
          <section>
            <h2 style={{ marginTop: 0, fontSize: "var(--grd-text-sm)", letterSpacing: "0.04em" }}>SOURCE TEXT</h2>
            {active ? (
              <pre
                id={`chunk-${active.chunk_id}`}
                className={chunkFromQuery === active.chunk_id ? "grd-chunk-highlight" : undefined}
                style={{
                  whiteSpace: "pre-wrap",
                  fontFamily: "var(--grd-font-mono)",
                  fontSize: "var(--grd-text-sm)",
                  lineHeight: 1.65,
                  margin: 0,
                  padding: "var(--grd-space-4)",
                  background: "var(--grd-bg-muted)",
                  borderRadius: "var(--grd-radius-md)",
                  border: "1px solid var(--grd-border-subtle)",
                }}
              >
                {active.text}
              </pre>
            ) : (
              <p className="grd-meta">No chunks available.</p>
            )}
            {doc.preview ? (
              <details style={{ marginTop: "1.5rem" }}>
                <summary className="grd-meta">Technical metadata</summary>
                <p className="grd-meta" style={{ marginTop: "0.5rem" }}>
                  ID {doc.document_id}
                </p>
              </details>
            ) : (
              <p className="grd-meta" style={{ marginTop: "1rem" }}>
                ID {doc.document_id}
              </p>
            )}
          </section>
        </div>
      ) : null}
      <ConfirmDialog
        open={confirm}
        title="Delete document?"
        body="This removes the file and all indexed chunks."
        busy={deleting}
        onCancel={() => setConfirm(false)}
        onConfirm={() => void onDelete()}
      />
    </div>
  );
}
