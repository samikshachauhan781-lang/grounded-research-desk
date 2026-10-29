import { useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../../lib/api/client";
import { EmptyState } from "../../components/ui/EmptyState";
import { PageHeader } from "../../components/ui/PageHeader";

export function SearchPage() {
  const [query, setQuery] = useState("");
  const [topK, setTopK] = useState(5);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [results, setResults] = useState<Awaited<ReturnType<typeof api.search>> | null>(null);

  async function runSearch() {
    if (!query.trim()) return;
    setLoading(true);
    setError(null);
    try {
      setResults(await api.search(query.trim(), topK));
    } catch {
      setError("Search failed. Check your connection and try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="grd-page">
      <PageHeader
        title="Search"
        description="Semantic retrieval over indexed chunks using cosine similarity. Hybrid search and reranking are not implemented."
      />
      <label className="grd-label" htmlFor="search-query">
        Query
      </label>
      <div className="grd-toolbar">
        <input
          id="search-query"
          className="grd-input"
          style={{ maxWidth: "none", flex: 1 }}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") void runSearch();
          }}
          placeholder="Find passages in your documents…"
        />
        <label className="grd-meta">
          Top-k{" "}
          <input
            className="grd-input"
            type="number"
            min={1}
            max={20}
            value={topK}
            onChange={(e) => setTopK(Number(e.target.value))}
            style={{ width: "4.5rem", display: "inline-block" }}
          />
        </label>
        <button type="button" className="grd-btn grd-btn-primary" disabled={loading || !query.trim()} onClick={() => void runSearch()}>
          {loading ? "Searching…" : "Search"}
        </button>
      </div>
      {error ? <div className="grd-alert error">{error}</div> : null}
      {results && (
        <>
          <p className="grd-meta" style={{ marginTop: "0.5rem" }}>
            {results.duration_ms} ms · {results.model} · {results.results.length} hits
          </p>
          {results.results.length === 0 ? (
            <EmptyState title="No matches" body="Try different wording or upload more source material." />
          ) : (
            results.results.map((r) => (
              <article key={r.chunk_id} className="grd-result">
                <div style={{ display: "flex", justifyContent: "space-between", gap: "1rem" }}>
                  <strong>{r.filename}</strong>
                  <span className="grd-meta">score {r.score.toFixed(4)}</span>
                </div>
                <p style={{ fontSize: "var(--grd-text-sm)", color: "var(--grd-text-secondary)", margin: "0.5rem 0" }}>
                  {r.snippet}
                </p>
                <Link to={`/library/${r.document_id}?chunk=${encodeURIComponent(r.chunk_id)}`}>Inspect chunk</Link>
              </article>
            ))
          )}
        </>
      )}
    </div>
  );
}
