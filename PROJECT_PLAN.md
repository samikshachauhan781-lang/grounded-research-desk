# Project plan — phases and roadmap

## Workflow rules

- Small milestones; user review between milestones.
- Report pytest pass/fail/skip counts after each milestone.
- No commit/push without explicit approval.
- Update [CURRENT_STATE.md](./CURRENT_STATE.md), [TASK_TRACKER.md](./TASK_TRACKER.md), [NEXT_SESSION.md](./NEXT_SESSION.md).

## Phase 0 — Planning (current)

**Deliverables:** Documentation set, folder scaffold, `.env.example`, `.gitignore`.

**Acceptance:** All files in [FILE_REGISTRY.md](./FILE_REGISTRY.md) exist; user approved plan.

## Phase 1 — Foundation

**Build:** `pyproject.toml`, settings module, FastAPI app, `GET /health`, logging bootstrap, first pytest.

**Acceptance:**

- `curl /health` → `{"status":"ok"}`
- `pytest` runs with ≥ 1 passing test
- Config loads from env with defaults

## Phase 2 — Document ingest (MVP slice)

**Build:** Upload endpoint, document metadata in SQLite, list/get/delete (delete optional in demo).

**Acceptance:**

- Upload `.md`/`.txt` under size limit
- List returns id, filename, created_at
- Invalid type → 422; oversize → 413

## Phase 3 — Chunking

**Build:** Text cleaner, sliding-window chunker with overlap, persist chunks.

**Acceptance:**

- Unit tests: overlap, stable ordering, boundary fixture
- Re-ingest replaces or versions chunks (document decision in [DECISION_LOG.md](./DECISION_LOG.md))

## Phase 4 — Embeddings and retrieval

**Build:** Embedding provider interface, local MiniLM, store vectors, cosine top-k search.

**Acceptance:**

- Golden test: planted question retrieves chunk containing answer
- Model name stored; mismatch blocks search

## Phase 5 — RAG answers with citations

**Build:** Ask endpoint, prompt builder, mock + Ollama providers, response schema with sources.

**Acceptance:**

- Integration test with mock LLM
- Citations reference real chunk ids from retrieval step

## Phase 6 — Evaluation harness

**Build:** JSON golden set in `tests/golden/`, script or pytest parametrize for recall@k and groundedness checks.

**Acceptance:**

- Printed or asserted metrics on CI-local run
- Document baseline in [AGENT_EVALUATION.md](./AGENT_EVALUATION.md)

## Phase 7 — Agent layer

**Build:** Research agent orchestrator, tool registry, guardrails, memory session store.

**Acceptance:**

- `AGENT_ENABLED=true` runs scripted multi-tool flow on fixture
- Exceeding tool budget → graceful stop with partial result

## Phase 8 — Frontend

**Build:** React + Vite UI: upload, document list, ask panel, citation sidebar.

**Acceptance:**

- Manual test path documented in README
- Playwright smoke (optional) for happy path

## Phase 9 — Hardening

**Build:** Hybrid search, reranker (if measured benefit), rate limits, observability, performance notes.

**Acceptance:**

- [PERFORMANCE.md](./PERFORMANCE.md) has measured latencies on sample hardware
- [SECURITY.md](./SECURITY.md) checklist reviewed

## Phase 10 — Packaging and deploy

**Build:** Dockerfile, compose, CI workflow, [DEPLOYMENT.md](./DEPLOYMENT.md).

**Acceptance:**

- `docker compose up` brings API + optional Ollama profile
- CI runs pytest on push

## Phase 11 — Interview package

**Deliverables:** Architecture diagram in docs, resume bullets, mock interview in `docs/interview-notebook/`.

**Acceptance:** User can demo upload → ask → cite in < 5 minutes.

## Milestone numbering for git commits

Use `milestone(1): ...` through `milestone(11): ...` aligned with phases above.

## Adjustments

Phases may merge (e.g. 2+3) if architecture stays testable. Any reorder requires a [DECISION_LOG.md](./DECISION_LOG.md) entry.
