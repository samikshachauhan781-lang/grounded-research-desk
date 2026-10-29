# Grounded Research Desk

**AI Knowledge & Research Intelligence Platform** — upload documents, ask questions, get answers with source citations. Built for learning, interviews, and local-first deployment without mandatory paid APIs.

## What it is

1. Ingests **text and Markdown** documents.
2. Chunks and embeds content for semantic search.
3. Retrieves relevant passages for each question (RAG).
4. Generates answers constrained to retrieved text, with citations — or returns **insufficient evidence** when support is weak.
5. Optional **bounded research agent** with explicit tools and guardrails.

Core promise: **Research with evidence. Every answer traceable to its source.**

## Status

| Area | State |
| --- | --- |
| Backend RAG MVP | **33 pytest tests** (fake embeddings + mock LLM in tests) |
| Evidence Atlas UI | **Production build**; **4 Playwright E2E tests** (local; browsers required) |
| Docker / CI | Compose file + GitHub Actions (backend pytest, frontend unit tests + build). **Remote CI and Docker builds not verified in this workspace.** |
| Public production | **Not ready** — no authentication |

See [CURRENT_STATE.md](./CURRENT_STATE.md).

## Prerequisites

- Python 3.11+
- Node 20+ (frontend)
- (Optional) [Ollama](https://ollama.com) for local LLM answers

## Installation

```bash
cd /Users/samiksha/Documents/Project_2
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env

cd frontend && npm ci
```

## Run locally

**Default interview demo:** use **`EMBEDDING_PROVIDER=fake`** and **`LLM_PROVIDER=mock`** (same as pytest and Playwright). Fake embeddings use lexical overlap for retrieval — **not** live neural embedding inference. The mock LLM formats answers from retrieved chunks — **not** Ollama or a cloud LLM. Switch to real providers via [CONFIGURATION.md](./CONFIGURATION.md) when you have models installed.

**Terminal 1 — API**

```bash
source .venv/bin/activate
EMBEDDING_PROVIDER=fake LLM_PROVIDER=mock uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

**Terminal 2 — UI**

```bash
cd frontend && npm run dev
```

Open http://127.0.0.1:5173 — top bar should show **API Connected** (green). If not, start Terminal 1 first and refresh.

## Demo checklist (interview)

| Step | What to do | Pass criteria |
| --- | --- | --- |
| 1 | Terminal 1: `uvicorn … --port 8000` | `curl http://127.0.0.1:8000/health` → `"status":"ok"` |
| 2 | Terminal 2: `npm run dev` → open `http://127.0.0.1:5173` | **API Connected** in top bar |
| 3 | **Library** → upload `tests/fixtures/sample.md` | Status **completed**, chunk count ≥ 1 |
| 4 | **Research** → *What command rolls back the database migration?* | Answer + Evidence with **flyway rollback**; **Open source** works |
| 5 | Ask *What is the capital of Mars colony Zephyr-9?* | **Insufficient evidence**, **no citations** |
| 6 | Save & prep | Copy `data/` for backup; read [ARCHITECTURE.md](./ARCHITECTURE.md) + pitch below |

**30-second pitch:** Local-first RAG app — ingest Markdown/text, retrieve with embeddings, answer only with citations; refuses when evidence is weak (`assess_retrieval_sufficiency`); optional bounded agent behind `AGENT_ENABLED`.

**Verified on 2026-10-28:** API health OK, UI Connected, upload `completed`, grounded ask with 1 citation, safety ask `insufficient_evidence: true`, citations `0`.

## Example workflow

1. **Library** — upload `tests/fixtures/sample.md`.
2. **Research** — ask *What command rolls back the database migration?*
3. Review **Answer** and **Evidence Rail** (flyway rollback).
4. Ask an off-topic question — see **Insufficient evidence** with no false citations.
5. **Research History** — open the auto-saved session.

## Docker

```bash
docker compose -f docker/docker-compose.yml up --build
```

API on port 8000; persist `./data` via compose volume. Compose uses fake embeddings and mock LLM by default. **Image build not verified** unless you run the command locally with Docker running.

## Testing

```bash
pytest tests/ -v
cd frontend && npm run test:unit && npm run build
cd frontend && npx playwright install   # once per machine / after @playwright/test upgrade
npm run test:e2e                        # 4 tests; Playwright starts API + Vite (see playwright.config.ts)
python scripts/measure_ask_latency.py
```

Playwright needs browser binaries (`npx playwright install`). A missing browser is an **environment setup** issue, not an application failure.

## Configuration

Environment variables — [CONFIGURATION.md](./CONFIGURATION.md). Defaults use **fake embeddings** and **mock LLM** for offline deterministic tests.

## Security limitations

- **No login or API keys** — intended for localhost or a trusted private network.
- Do not expose destructive endpoints to the public internet without auth, TLS, and rate limiting.
- Uploaded documents are **untrusted**; prompts treat them as evidence only ([PROMPT_ENGINEERING.md](./PROMPT_ENGINEERING.md)).

## Backup and restore

- Stop the API.
- Copy `data/grounded_research.db` and `data/uploads/`.
- Restore by placing files back and restarting.

Details: [DEPLOYMENT.md](./DEPLOYMENT.md).

## Documentation map

| Document | Purpose |
| --- | --- |
| [ARCHITECTURE.md](./ARCHITECTURE.md) | Components and data flow |
| [RAG_ARCHITECTURE.md](./RAG_ARCHITECTURE.md) | Ingest → retrieve → generate |
| [API_CONTRACT.md](./API_CONTRACT.md) | HTTP API |
| [FILE_REGISTRY.md](./FILE_REGISTRY.md) | File index |

## Save your work

This project is version-controlled with **Git** (`main`). Clone or pull from your remote for portfolio copies; **runtime data is not in Git** — your uploaded docs and SQLite DB stay local in:

- `data/grounded_research.db`
- `data/uploads/`

To back up before an interview: copy the whole `data/` folder elsewhere. Do not delete `data/` during demos.
