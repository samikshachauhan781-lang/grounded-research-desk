import { useEffect, useState } from "react";
import { api, type CollectionItem, type DocumentItem } from "../../lib/api/client";
import { ConfirmDialog } from "../../components/ui/ConfirmDialog";
import { EmptyState } from "../../components/ui/EmptyState";
import { PageHeader } from "../../components/ui/PageHeader";
import { useToast } from "../../components/ui/Toast";

export function CollectionsPage() {
  const { notify } = useToast();
  const [items, setItems] = useState<CollectionItem[]>([]);
  const [docs, setDocs] = useState<DocumentItem[]>([]);
  const [name, setName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [expanded, setExpanded] = useState<string | null>(null);
  const [attachId, setAttachId] = useState("");
  const [pending, setPending] = useState<CollectionItem | null>(null);
  const [busy, setBusy] = useState(false);

  async function refresh() {
    try {
      const [c, d] = await Promise.all([api.listCollections(), api.listDocuments()]);
      setItems(c);
      setDocs(d.items);
    } catch {
      setError("Could not load collections.");
    }
  }

  useEffect(() => {
    void refresh();
  }, []);

  async function create() {
    if (!name.trim()) return;
    await api.createCollection(name.trim());
    setName("");
    notify("Collection created");
    await refresh();
  }

  async function attach(collectionId: string) {
    if (!attachId) return;
    await api.addCollectionDocument(collectionId, attachId);
    notify("Document attached");
    setAttachId("");
    await refresh();
  }

  async function remove() {
    if (!pending) return;
    setBusy(true);
    try {
      await api.deleteCollection(pending.collection_id);
      notify("Collection deleted");
      setPending(null);
      await refresh();
    } catch {
      setError("Could not delete collection.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="grd-page">
      <PageHeader
        title="Collections"
        description="Group documents for organization. Membership count comes from the API; attach a library document below."
      />
      <div className="grd-toolbar">
        <input
          className="grd-input"
          placeholder="New collection name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          aria-label="Collection name"
        />
        <button type="button" className="grd-btn grd-btn-primary" onClick={() => void create()} disabled={!name.trim()}>
          Create
        </button>
      </div>
      {error ? <div className="grd-alert error">{error}</div> : null}
      {items.length === 0 ? (
        <EmptyState title="No collections" body="Create a collection, then attach documents from your library." />
      ) : (
        <div className="grd-doc-list">
          {items.map((c) => (
            <div key={c.collection_id}>
              <div className="grd-doc-row" style={{ gridTemplateColumns: "minmax(0,1fr) auto auto auto" }}>
                <button type="button" className="grd-btn grd-btn-ghost" style={{ justifyContent: "flex-start" }} onClick={() => setExpanded(expanded === c.collection_id ? null : c.collection_id)}>
                  {c.name}
                </button>
                <span className="grd-meta">{c.document_count} docs</span>
                <span className="grd-meta">{c.created_at}</span>
                <button type="button" className="grd-btn grd-btn-ghost" style={{ height: 32 }} onClick={() => setPending(c)}>
                  Delete
                </button>
              </div>
              {expanded === c.collection_id ? (
                <div style={{ padding: "0.75rem 0 1rem 0.5rem" }}>
                  {c.description ? <p style={{ fontSize: "var(--grd-text-sm)", color: "var(--grd-text-secondary)" }}>{c.description}</p> : null}
                  <p className="grd-meta" style={{ marginBottom: "0.5rem" }}>
                    The API reports {c.document_count} member document{c.document_count === 1 ? "" : "s"}. Select a library file to attach.
                  </p>
                  <div className="grd-toolbar">
                    <select className="grd-select" value={attachId} onChange={(e) => setAttachId(e.target.value)} aria-label="Document to attach">
                      <option value="">Select document…</option>
                      {docs.map((d) => (
                        <option key={d.document_id} value={d.document_id}>
                          {d.filename}
                        </option>
                      ))}
                    </select>
                    <button type="button" className="grd-btn grd-btn-secondary" disabled={!attachId} onClick={() => void attach(c.collection_id)}>
                      Attach
                    </button>
                  </div>
                </div>
              ) : null}
            </div>
          ))}
        </div>
      )}
      <ConfirmDialog
        open={Boolean(pending)}
        title="Delete collection?"
        body="Documents are not deleted — only the collection grouping."
        busy={busy}
        onCancel={() => setPending(null)}
        onConfirm={() => void remove()}
      />
    </div>
  );
}
