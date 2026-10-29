import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, ApiError, type DocumentItem, type PublicSettings } from "../../lib/api/client";
import { ConfirmDialog } from "../../components/ui/ConfirmDialog";
import { EmptyState } from "../../components/ui/EmptyState";
import { Icon } from "../../components/icons/Icon";
import { PageHeader } from "../../components/ui/PageHeader";
import { useToast } from "../../components/ui/Toast";

function statusTone(status: string) {
  if (status === "completed" || status === "indexed") return "success";
  if (status === "failed") return "error";
  return "warning";
}

export function LibraryPage() {
  const { notify } = useToast();
  const [docs, setDocs] = useState<DocumentItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [filter, setFilter] = useState("");
  const [dragActive, setDragActive] = useState(false);
  const [settings, setSettings] = useState<PublicSettings | null>(null);
  const [pendingDelete, setPendingDelete] = useState<DocumentItem | null>(null);
  const [deleting, setDeleting] = useState(false);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.listDocuments();
      setDocs(data.items);
      setTotal(data.total);
    } catch {
      setError("We couldn't load your documents. Check the API connection and try again.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
    api.publicSettings().then(setSettings).catch(() => setSettings(null));
  }, [refresh]);

  async function onUpload(file: File | null) {
    if (!file) return;
    setUploading(true);
    setError(null);
    try {
      await api.uploadDocument(file);
      notify(`Indexed ${file.name}`);
      await refresh();
    } catch (err) {
      if (err instanceof ApiError && err.status === 422) {
        setError("This file couldn't be uploaded. Use UTF-8 .txt or .md within the size limit.");
      } else {
        setError("Upload failed. Please try again.");
      }
    } finally {
      setUploading(false);
    }
  }

  async function confirmDelete() {
    if (!pendingDelete) return;
    setDeleting(true);
    try {
      await api.deleteDocument(pendingDelete.document_id);
      notify("Document deleted");
      setPendingDelete(null);
      await refresh();
    } catch {
      setError("Delete failed. The document may be protected in demo mode.");
    } finally {
      setDeleting(false);
    }
  }

  const filtered = docs.filter((d) => d.filename.toLowerCase().includes(filter.toLowerCase()));
  const maxMb = settings ? Math.round(settings.max_upload_bytes / 1024 / 1024) : 5;
  const exts = settings?.allowed_upload_extensions.join(", ") ?? ".md, .txt";

  return (
    <div className="grd-page grd-page-wide">
      <PageHeader
        title="Knowledge Library"
        description="Private source documents used for retrieval. Only Markdown and plain text are ingested."
        action={
          <label className="grd-btn grd-btn-primary" style={{ cursor: uploading ? "wait" : "pointer" }}>
            <Icon name="upload" size={14} />
            {uploading ? "Uploading…" : "Upload documents"}
            <input
              type="file"
              accept=".md,.txt"
              style={{ display: "none" }}
              disabled={uploading}
              onChange={(e) => void onUpload(e.target.files?.[0] ?? null)}
            />
          </label>
        }
      />

      <div
        className={`grd-dropzone${dragActive ? " active" : ""}`}
        onDragOver={(e) => {
          e.preventDefault();
          setDragActive(true);
        }}
        onDragLeave={() => setDragActive(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragActive(false);
          void onUpload(e.dataTransfer.files[0] ?? null);
        }}
      >
        <Icon name="upload" />
        <div>
          Drop a file here, or use Upload documents.
          <div className="grd-meta" style={{ marginTop: 4 }}>
            {exts} · up to {maxMb} MB
          </div>
        </div>
      </div>

      <div className="grd-toolbar" style={{ marginTop: "1.25rem" }}>
        <input
          className="grd-input"
          placeholder="Search filenames…"
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          aria-label="Filter documents"
        />
        <span className="grd-meta">{total} document{total === 1 ? "" : "s"}</span>
      </div>

      {error ? (
        <div className="grd-alert error" style={{ marginBottom: "1rem" }}>
          {error}
        </div>
      ) : null}

      {loading ? (
        <div>
          <div className="grd-skeleton" style={{ width: "60%", marginBottom: 12 }} />
          <div className="grd-skeleton" style={{ width: "40%" }} />
        </div>
      ) : null}

      {!loading && !error && filtered.length === 0 && docs.length === 0 ? (
        <EmptyState title="No documents yet" body="Upload a Markdown or text file to start researching your knowledge base." />
      ) : null}

      {!loading && !error && filtered.length === 0 && docs.length > 0 ? (
        <EmptyState title="No matches" body="Clear the filename search to see all documents." />
      ) : null}

      {!loading && filtered.length > 0 ? (
        <div className="grd-doc-list" role="table" aria-label="Documents">
          {filtered.map((d) => (
            <div className="grd-doc-row" role="row" key={d.document_id}>
              <Icon name="file" />
              <div className="grd-doc-name" role="cell">
                <Link to={`/library/${d.document_id}`}>{d.filename}</Link>
              </div>
              <span className={`grd-badge ${statusTone(d.processing_status)}`} role="cell">
                {d.processing_status}
              </span>
              <span className="grd-meta" role="cell">
                {d.chunk_count} chunks
              </span>
              <button
                type="button"
                className="grd-btn grd-btn-ghost"
                style={{ height: "32px" }}
                onClick={() => setPendingDelete(d)}
              >
                Delete
              </button>
            </div>
          ))}
        </div>
      ) : null}

      <ConfirmDialog
        open={Boolean(pendingDelete)}
        title="Delete document?"
        body={pendingDelete ? `“${pendingDelete.filename}” and its chunks will be removed from the knowledge base.` : ""}
        confirmLabel="Delete"
        busy={deleting}
        onCancel={() => setPendingDelete(null)}
        onConfirm={() => void confirmDelete()}
      />
    </div>
  );
}
