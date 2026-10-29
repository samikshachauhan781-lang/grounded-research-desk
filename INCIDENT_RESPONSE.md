# Incident response (production)

Lightweight runbook for when **Grounded Research Desk** is deployed beyond local dev.

## Severity levels

| Level | Example | Response time |
| --- | --- | --- |
| SEV-1 | Service down, all asks fail | Immediate |
| SEV-2 | Ollama errors, mock fallback needed | Same day |
| SEV-3 | Slow retrieval, elevated latency | Next business day |
| SEV-4 | Doc typo, non-critical UI glitch | Backlog |

## On-call checklist (SEV-1)

1. Confirm scope: `GET /health` — API up?
2. Check recent deploy / config change
3. Inspect logs for `request_id` spikes (`error`, `llm_call` timeouts)
4. Verify disk space on `data/` volume (SQLite + uploads)
5. If Ollama: check sidecar health and model pull
6. Communicate status to users/stakeholders
7. Mitigate: rollback deploy or set `LLM_PROVIDER=mock` temporarily for read-only demo

## Common failures

| Symptom | Likely cause | Mitigation |
| --- | --- | --- |
| 503 on ask | Ollama unreachable | Restart Ollama; increase timeout |
| Empty answers | Retrieval threshold too high | Lower `MIN_SIMILARITY_SCORE` temporarily |
| Wrong answers | Model change without re-embed | Block search; re-ingest ([ERROR_HANDLING.md](./ERROR_HANDLING.md)) |
| DB locked | SQLite write contention | Reduce concurrency; migrate Postgres |
| Disk full | Large uploads | Purge test uploads; expand volume |

## Post-incident

1. Timeline document (start, detect, mitigate, resolve)
2. Root cause — 5 whys
3. Action items: test, alert, doc update
4. Update [DECISION_LOG.md](./DECISION_LOG.md) if architecture change

## Security incidents

Data leak suspicion:

1. Rotate API keys if auth enabled
2. Review access logs
3. Follow [SECURITY.md](./SECURITY.md)

## Communication template

```
Incident: [title]
Impact: [who/what]
Status: investigating | mitigated | resolved
Workaround: [if any]
Next update: [time]
```

## Interview Q&A

**Q:** How is incident response different for RAG apps?  
**A:** You debug three layers: infra, retrieval quality regressions, and LLM provider failures — not just HTTP availability.
