# Error handling, retries, and recovery

## Error taxonomy

| Category | HTTP | Examples |
| --- | --- | --- |
| Client validation | 422 | Bad JSON, wrong file type |
| Not found | 404 | Unknown document/chunk id |
| Payload too large | 413 | Upload over limit |
| Conflict | 409 | Duplicate ingest job (future) |
| Dependency unavailable | 503 | Ollama down |
| Timeout | 504 | LLM or agent exceeded deadline |
| Internal | 500 | Unexpected exception (logged with stack) |

## Exception hierarchy (planned)

```
AppError (base)
├── ValidationError
├── NotFoundError
├── ModelMismatchError
├── EmbeddingError
├── LLMProviderError
├── LLMTimeoutError
├── AgentBudgetExceededError
└── AgentDisabledError
```

Map to HTTP in `backend/app/core/exceptions.py` handlers.

## Retry policy

| Operation | Retry? | Notes |
| --- | --- | --- |
| Embed single chunk | Yes, 2x with backoff | Idempotent write same vector |
| LLM generate | Yes, 1x on timeout | Only if no partial streamed response |
| SQLite read | No | Fail fast |
| Tool call | No automatic retry | Orchestrator may replan once |
| File upload save | No | Client must re-upload |

Use exponential backoff: 0.5s, 1s (jitter optional).

## Timeouts

| Component | Env var | Default |
| --- | --- | --- |
| LLM generation | `GENERATION_TIMEOUT_SECONDS` | 60 |
| Agent session | `AGENT_MAX_WALL_CLOCK_SECONDS` | 120 |
| Ollama HTTP client | same as generation | 60 |

## User-facing error body

```json
{
  "error": {
    "code": "LLM_TIMEOUT",
    "message": "Generation timed out after 60s.",
    "request_id": "uuid"
  }
}
```

## Logging on errors

Always log: `request_id`, `error_code`, `duration_ms`.  
Never log: full document text at ERROR level (use DEBUG with redaction).

## Recovery flows

### Ollama unavailable

1. Detect connection error.
2. Return 503 with hint to set `LLM_PROVIDER=mock` for dev.
3. Metrics counter `llm_provider_errors`.

### Empty retrieval

1. Do not call LLM with empty context.
2. Return 200 with answer: “No relevant passages found in your documents.” and empty citations.

### Agent loop detected

1. If same tool+args repeated twice, inject observation: “Loop detected.”
2. Force finalize or fail with `AgentBudgetExceededError`.

## Testing

- `tests/unit/test_error_mapping.py`
- Mock Ollama connection failure → 503

See [OBSERVABILITY.md](./OBSERVABILITY.md) for correlation ids.
