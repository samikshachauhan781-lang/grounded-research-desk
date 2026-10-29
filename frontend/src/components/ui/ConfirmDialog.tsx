type Props = {
  open: boolean;
  title: string;
  body: string;
  confirmLabel?: string;
  onConfirm: () => void;
  onCancel: () => void;
  busy?: boolean;
};

export function ConfirmDialog({ open, title, body, confirmLabel = "Delete", onConfirm, onCancel, busy }: Props) {
  if (!open) return null;
  return (
    <div className="grd-dialog-root" role="presentation">
      <button type="button" className="grd-dialog-backdrop" aria-label="Dismiss" onClick={onCancel} />
      <div className="grd-dialog" role="dialog" aria-modal="true" aria-labelledby="confirm-title">
        <h2 id="confirm-title" style={{ margin: 0, fontSize: "var(--grd-text-lg)" }}>
          {title}
        </h2>
        <p style={{ color: "var(--grd-text-secondary)", margin: "0.75rem 0 1.25rem" }}>{body}</p>
        <div style={{ display: "flex", justifyContent: "flex-end", gap: "0.5rem" }}>
          <button type="button" className="grd-btn grd-btn-secondary" onClick={onCancel} disabled={busy}>
            Cancel
          </button>
          <button type="button" className="grd-btn grd-btn-danger" onClick={onConfirm} disabled={busy}>
            {busy ? "Working…" : confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}
