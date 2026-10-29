# Observability

## Goals

Debug failed asks and agent runs without exposing private document text in production logs.

## Logging

### Format (structured)

Prefer JSON lines or key=value:

```
level=INFO request_id=abc event=ask_completed duration_ms=240 top_k=5
```

### Events

| Event | Level | Fields |
| --- | --- | --- |
| `http_request` | INFO | method, path, status, duration_ms |
| `document_ingested` | INFO | document_id, chunk_count |
| `embed_completed` | DEBUG | document_id, model, duration_ms |
| `retrieval_completed` | DEBUG | query_hash, top_scores, chunk_ids |
| `llm_call` | INFO | provider, duration_ms, timeout |
| `agent_step` | INFO | step_index, tool, duration_ms |
| `guardrail_trigger` | WARNING | rule_id |
| `error` | ERROR | code, message, stack (dev only) |

### Request correlation

- Accept `X-Request-Id` or generate UUID per request
- Propagate to all log lines and error JSON

## Metrics (optional Phase 9)

| Metric | Type | Notes |
| --- | --- | --- |
| `http_requests_total` | counter | labels: path, status |
| `ask_latency_seconds` | histogram | |
| `retrieval_chunks_count` | histogram | |
| `llm_errors_total` | counter | |
| `agent_tool_calls_total` | counter | labels: tool name |

Expose `/metrics` for Prometheus when enabled via env `METRICS_ENABLED=true`.

## Tracing (future)

OpenTelemetry spans:

- `ingest.document`
- `embed.chunks`
- `retrieve.search`
- `generate.answer`
- `agent.step`

Not required for MVP.

## Dashboards

Local: tail logs  
Production: connect to host logs (Render/Fly) — see [DEPLOYMENT.md](./DEPLOYMENT.md)

## Debugging playbook

1. Find `request_id` in API error response.
2. grep logs for that id.
3. Check `retrieval_completed` chunk_ids vs citations in response.
4. If scores low → chunking/threshold/model mismatch.
5. If LLM timeout → adjust `GENERATION_TIMEOUT_SECONDS` or use mock.

## Privacy

At `LOG_LEVEL=INFO`, log chunk ids and scores, not full chunk text.  
At `DEBUG` in dev only, optional truncated snippets (max 100 chars).

## Interview Q&A

**Q:** What do you monitor for RAG vs traditional APIs?  
**A:** Retrieval scores, empty-hit rate, citation validity failures, and LLM latency/errors — not just HTTP 500 rate.
