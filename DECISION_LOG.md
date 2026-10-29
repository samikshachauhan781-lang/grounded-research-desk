# Decision log

Record of significant technical decisions. Update when choices change.

## DL-001 — Project location and isolation

| Field | Value |
| --- | --- |
| Date | 2026-10-28 |
| Decision | New repo at `/Users/samiksha/Documents/Project_2`, separate from DevOps Incident Commander |
| Alternatives | Extend incident project; monorepo |
| Rationale | Clean interview narrative; avoid cross-contamination of domains |
| Status | Accepted |

## DL-002 — Product name

| Field | Value |
| --- | --- |
| Date | 2026-10-28 |
| Decision | **Grounded Research Desk** |
| Alternatives | DocMind, ResearchIQ, AskCorpus |
| Rationale | Emphasizes grounded/cited answers for interviews |
| Status | Proposed — confirm with user |

## DL-003 — Database for MVP

| Field | Value |
| --- | --- |
| Date | 2026-10-28 |
| Decision | SQLite file at `data/grounded_research.db` |
| Alternatives | Postgres; Chroma-only |
| Rationale | Matches prior project skill; zero infra; easy tests |
| Status | Accepted |

## DL-004 — Vector search implementation (MVP)

| Field | Value |
| --- | --- |
| Date | 2026-10-28 |
| Decision | Store embeddings in SQLite BLOB; cosine similarity in Python |
| Alternatives | FAISS; pgvector; dedicated vector DB |
| Rationale | Transparent for learning; optimize when measured slow |
| Status | Accepted |

## DL-005 — Embedding model

| Field | Value |
| --- | --- |
| Date | 2026-10-28 |
| Decision | `sentence-transformers/all-MiniLM-L6-v2` (384-dim) on CPU |
| Alternatives | OpenAI embeddings; larger models |
| Rationale | Free, local, common interview reference |
| Status | Accepted |

## DL-006 — LLM providers

| Field | Value |
| --- | --- |
| Date | 2026-10-28 |
| Decision | Interface with `mock` (tests) and `ollama` (optional local) |
| Alternatives | OpenAI API only |
| Rationale | No mandatory cost; deterministic CI |
| Status | Accepted |

## DL-007 — No LangChain in MVP

| Field | Value |
| --- | --- |
| Date | 2026-10-28 |
| Decision | Hand-roll chunk → embed → retrieve → prompt |
| Alternatives | LangChain, LlamaIndex |
| Rationale | Interviewers ask about steps hidden by frameworks |
| Status | Accepted — revisit if maintenance burden grows |

## DL-008 — Agent scope

| Field | Value |
| --- | --- |
| Date | 2026-10-28 |
| Decision | Read-only tools over corpus; no shell; no open web |
| Alternatives | Full ReAct with bash |
| Rationale | Safety and demo reliability |
| Status | Accepted |

## DL-009 — Chunking strategy

| Field | Value |
| --- | --- |
| Date | 2026-10-28 |
| Decision | Character-based sliding window with overlap (defaults in `.env.example`) |
| Alternatives | Token-based via tiktoken; semantic chunking |
| Rationale | Simple, testable; upgrade to token-based in Phase 9 if needed |
| Status | Accepted |

## DL-010 — API versioning

| Field | Value |
| --- | --- |
| Date | 2026-10-28 |
| Decision | Prefix `/api/v1` |
| Alternatives | Unversioned |
| Rationale | Room for breaking changes without surprise |
| Status | Accepted |

## Template for new entries

```
## DL-XXX — Title
| Field | Value |
| Date | YYYY-MM-DD |
| Decision | |
| Alternatives | |
| Rationale | |
| Status | Proposed / Accepted / Superseded by DL-YYY |
```
