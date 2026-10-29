# Current implementation status

**Last updated:** 2026-10-29 (portfolio doc sync)  
**Location:** `/Users/samiksha/Documents/Project_2`

## Summary

Grounded Research Desk is a **local-first RAG research MVP** with a polished Evidence Atlas UI, provider-aware evidence sufficiency, session-backed research workspace, mobile navigation, expanded regression tests, and Playwright E2E.

**Deployment posture:** suitable for **local / private-network demo** with documented lack of authentication. **Not** public production-ready.

## Default demo stack

Interview and automated tests use **`EMBEDDING_PROVIDER=fake`** (deterministic lexical retrieval, not a neural embedding model) and **`LLM_PROVIDER=mock`** (template answers from retrieved chunks, not Ollama or a hosted LLM). Optional real providers are documented in [CONFIGURATION.md](./CONFIGURATION.md).

## Verified results (local)

| Check | Result |
| --- | --- |
| Backend pytest | **33 passed**, 0 failed, 0 skipped |
| Frontend Vitest | **`npm run test:unit` — 6 passed** (guide engine) |
| Frontend build | **`npm run build` OK** |
| Playwright E2E | **`npm run test:e2e` — 4 tests** (local only; run `npx playwright install` once if browsers missing) |
| Ask latency (fake+mock, 5 samples) | Run `python scripts/measure_ask_latency.py` |
| GitHub Actions / Docker image build | **Not verified** in this workspace (workflow reviewed in repo; daemon/remote not run here) |

```bash
cd /Users/samiksha/Documents/Project_2 && source .venv/bin/activate && pytest tests/ -v
cd frontend && npm run test:unit && npm run build
cd frontend && npx playwright install   # first time only
npm run test:e2e                        # 4 tests; Playwright starts API + Vite
python scripts/measure_ask_latency.py
```

## Grounding policy

`/api/v1/ask` and the research agent share `assess_retrieval_sufficiency()`:

- **Fake embeddings:** lexical overlap ≥ `EVIDENCE_MIN_LEXICAL_OVERLAP` (default 0.15).
- **Local embeddings:** top cosine ≥ `MIN_SIMILARITY_SCORE` and lexical overlap.

Irrelevant questions return `insufficient_evidence: true`, empty citations, no LLM call. Generation prompts wrap document text in **untrusted evidence delimiters** (`backend/app/rag/prompt_guard.py`).

## UI

- Redesigned Evidence Atlas shell: grouped sidebar with icons, compact top bar, mobile drawer
- Research: editorial composer, copy answer, example prompts, desktop Evidence Rail + mobile evidence drawer
- Library: compact document rows, compact dropzone, confirm-delete dialog, toast feedback
- History, Collections, Observatory, Agent, Settings share the same page header / empty / dialog language

## Security notes

- Default `API_HOST=127.0.0.1` for safer local binding (Docker/Compose still bind `0.0.0.0` inside the container)
- Upload filename sanitization, size limits, extension allowlist
- No authentication — documented in Settings and README

## Limitations

- No PDF ingest, no document constellation graph, no hybrid search/reranking
- No multi-user auth or public internet hardening (rate limits, TLS, RBAC)
- Mock LLM summarizes retrieved text; Ollama quality depends on local model
- CI workflow reviewed locally; remote GitHub Actions not executed in this environment

## Data locations

- SQLite: `./data/grounded_research.db` (configurable via `DATABASE_URL`)
- Uploads: `./data/uploads/` (configurable via `UPLOAD_DIR`)

See [DEPLOYMENT.md](./DEPLOYMENT.md) for backup/restore guidance.
