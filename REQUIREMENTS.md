# Requirements

## Functional requirements

### FR-1 Document management

| ID | Requirement | Priority | Phase |
| --- | --- | --- | --- |
| FR-1.1 | Upload text/Markdown files via API | Must | 2 |
| FR-1.2 | Reject unsupported extensions | Must | 2 |
| FR-1.3 | Enforce max upload size | Must | 2 |
| FR-1.4 | List and fetch document metadata | Must | 2 |
| FR-1.5 | Store raw text for re-chunking | Must | 2 |
| FR-1.6 | PDF upload and parse | Should | 9 |

### FR-2 Ingest pipeline

| ID | Requirement | Priority | Phase |
| --- | --- | --- | --- |
| FR-2.1 | Clean whitespace and normalize line breaks | Must | 3 |
| FR-2.2 | Chunk with configurable size and overlap | Must | 3 |
| FR-2.3 | Persist chunk order index | Must | 3 |
| FR-2.4 | Trigger embed on ingest completion | Must | 4 |

### FR-3 Retrieval

| ID | Requirement | Priority | Phase |
| --- | --- | --- | --- |
| FR-3.1 | Embed query with same model as corpus | Must | 4 |
| FR-3.2 | Return top-k chunks by cosine similarity | Must | 4 |
| FR-3.3 | Optional minimum similarity threshold | Should | 4 |
| FR-3.4 | Hybrid keyword + vector search | Could | 9 |
| FR-3.5 | Rerank top candidates | Could | 9 |

### FR-4 Question answering

| ID | Requirement | Priority | Phase |
| --- | --- | --- | --- |
| FR-4.1 | Accept natural language question | Must | 5 |
| FR-4.2 | Answer using retrieved context only (prompt contract) | Must | 5 |
| FR-4.3 | Return citations (document, chunk id, snippet) | Must | 5 |
| FR-4.4 | Support mock LLM for tests | Must | 5 |
| FR-4.5 | Support Ollama when configured | Should | 5 |
| FR-4.6 | Multi-turn conversation with history | Could | 7 |

### FR-5 Research agent

| ID | Requirement | Priority | Phase |
| --- | --- | --- | --- |
| FR-5.1 | Agent uses fixed tool allowlist | Must | 7 |
| FR-5.2 | Tool inputs validated before execution | Must | 7 |
| FR-5.3 | Max tool calls and wall-clock limits | Must | 7 |
| FR-5.4 | Final response includes citations | Must | 7 |
| FR-5.5 | User can disable agent (`AGENT_ENABLED=false`) | Must | 7 |

### FR-6 Evaluation

| ID | Requirement | Priority | Phase |
| --- | --- | --- | --- |
| FR-6.1 | Golden Q/A dataset for retrieval | Must | 6 |
| FR-6.2 | Metrics: recall@k, citation validity | Must | 6 |
| FR-6.3 | Optional LLM-judge for relevance (local) | Could | 9 |

## Non-functional requirements

### NFR-1 Performance

| ID | Requirement | Target |
| --- | --- | --- |
| NFR-1.1 | Ask latency (mock LLM, small corpus) | Measure and document; no unsubstantiated claims |
| NFR-1.2 | Ingest of 1 MB text | Complete locally without timeout under default settings |

### NFR-2 Reliability

| ID | Requirement |
| --- | --- |
| NFR-2.1 | Explicit timeouts on LLM and agent runs |
| NFR-2.2 | Retries only for idempotent read operations ([ERROR_HANDLING.md](./ERROR_HANDLING.md)) |
| NFR-2.3 | Graceful degradation when Ollama unavailable |

### NFR-3 Security

| ID | Requirement |
| --- | --- |
| NFR-3.1 | No secrets in repo |
| NFR-3.2 | Upload validation (type, size, content scanning basic) |
| NFR-3.3 | Agent cannot execute arbitrary shell ([GUARDRAILS.md](./GUARDRAILS.md)) |
| NFR-3.4 | Demo mode read-only for destructive ops (optional, Phase 9) |

### NFR-4 Observability

| ID | Requirement |
| --- | --- |
| NFR-4.1 | Structured logs with correlation id |
| NFR-4.2 | Log retrieval scores and chunk ids at debug level |
| NFR-4.3 | Metrics hooks for later Prometheus (optional) |

### NFR-5 Maintainability

| ID | Requirement |
| --- | --- |
| NFR-5.1 | ≥ 80% critical path covered by tests (ingest, retrieve, ask) |
| NFR-5.2 | All public API documented in [API_CONTRACT.md](./API_CONTRACT.md) |
| NFR-5.3 | [FILE_REGISTRY.md](./FILE_REGISTRY.md) updated when structure changes |

### NFR-6 Operability

| ID | Requirement |
| --- | --- |
| NFR-6.1 | Single-command local run documented |
| NFR-6.2 | Docker compose for reproducible demo |
| NFR-6.3 | [INCIDENT_RESPONSE.md](./INCIDENT_RESPONSE.md) for production issues |

## Constraints

- Python 3.11+ backend
- SQLite for MVP (Postgres migration optional future)
- No mandatory paid third-party API for core features
