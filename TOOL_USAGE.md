# Tool usage

## Design principles

- **Allowlist only** — unknown tool names rejected before execution.
- **Read-only** — tools never mutate corpus or database content.
- **Structured I/O** — JSON schemas validated with Pydantic.
- **Deterministic tests** — mock tool backend in unit tests.

## Tool catalog (MVP agent)

### `list_documents`

| Field | Value |
| --- | --- |
| Purpose | Discover available document ids and titles |
| Input | `{ "limit": int optional, default 50 }` |
| Output | `{ "documents": [{"id","filename","created_at"}] }` |
| Errors | None fatal; empty list valid |

### `search_chunks`

| Field | Value |
| --- | --- |
| Purpose | Semantic search over embedded chunks |
| Input | `{ "query": str, "top_k": int optional, "document_ids": [str] optional }` |
| Output | `{ "results": [{"chunk_id","document_id","score","snippet"}] }` |
| Errors | `ModelMismatchError`, `EmbeddingError` |

### `get_chunk`

| Field | Value |
| --- | --- |
| Purpose | Fetch full chunk text for citation |
| Input | `{ "chunk_id": str }` |
| Output | `{ "chunk_id","document_id","index","text" }` |
| Errors | `NotFoundError` if id invalid |

## Planned tools (post-MVP)

| Tool | Phase | Notes |
| --- | --- | --- |
| `keyword_search` | 9 | BM25 or SQLite FTS |
| `compare_chunks` | 9 | Side-by-side diff summary |
| `fetch_url` | Not planned MVP | Would need SSRF guardrails |

## Registration pattern (planned code)

```python
TOOL_REGISTRY: dict[str, ToolSpec] = {
    "search_chunks": ToolSpec(schema=SearchChunksInput, handler=search_chunks_handler),
    ...
}
```

## Validation flow

1. Parse LLM tool call JSON.
2. Pydantic validate against input schema.
3. Check tool name ∈ registry.
4. Run handler inside timeout wrapper.
5. Truncate observation if > max chars (configurable).

## Output size limits

| Setting | Default (proposed) |
| --- | --- |
| Max snippet in search results | 500 chars |
| Max full chunk in observation | 4000 chars |
| Max steps returned to client | 20 |

## Interview questions

**Q:** Why not give the agent SQL?  
**A:** SQL is flexible but high risk; narrow tools enforce read-only scope and easier testing.

**Q:** How do you prevent tool injection from user content?  
**A:** User text is data, not instructions; system prompt fixed; tool args schema-validated; no shell.
