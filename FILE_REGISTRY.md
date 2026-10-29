# File registry

Central index of project files: purpose, location, status, and dependencies.

**Last updated:** 2026-10-28 (completion mission)

Legend: **Done** = implemented and covered by tests or manual verification · **Partial** · **Not implemented**

## Root documentation

| File | Purpose | Status |
| --- | --- | --- |
| [README.md](./README.md) | Overview, install, usage | Done |
| [CURRENT_STATE.md](./CURRENT_STATE.md) | Implementation snapshot | Done |
| [FILE_REGISTRY.md](./FILE_REGISTRY.md) | This file | Done |

## Backend (`backend/app/`)

| Path | Purpose | Status |
| --- | --- | --- |
| `main.py` | FastAPI app, CORS, errors | Done |
| `core/config.py` | Settings | Done |
| `core/exceptions.py` | HTTP errors | Done |
| `api/routes/*.py` | Health, documents, search, ask, sessions, collections, eval, research, system | Done |
| `services/ingest/pipeline.py` | Upload + chunk + embed | Done |
| `services/retrieval/search_service.py` | Vector search | Done |
| `services/generation/ask_service.py` | RAG ask + sufficiency | Done |
| `rag/evidence_policy.py` | Lexical + provider sufficiency | Done |
| `rag/prompt_guard.py` | Untrusted context delimiters | Done |
| `agents/orchestrator.py` | Bounded agent | Done |
| `providers/embedding.py`, `providers/llm.py` | Fake/local embed, mock/Ollama LLM | Done |
| `database/models.py`, `database/session.py` | SQLite ORM | Done |

## Frontend (`frontend/src/`)

| Path | Purpose | Status |
| --- | --- | --- |
| `app/AppShell.tsx` | Shell + mobile drawer trigger | Done |
| `components/layout/MobileNavDrawer.tsx` | Responsive nav | Done |
| `components/evidence/EvidenceRail.tsx` | Source citations | Done |
| `features/workspace/WorkspacePage.tsx` | Research + sessions | Done |
| `features/library/*` | Library, inspector, collections | Done |
| `features/history/*` | History + session detail | Done |
| `features/search/SearchPage.tsx` | Semantic search | Done |
| `features/evaluation/ObservatoryPage.tsx` | Eval runs | Done |
| `features/agent/AgentPage.tsx` | Agent activity | Done |
| `features/settings/SettingsPage.tsx` | Public settings | Done |
| `styles/tokens.css`, `styles/global.css` | Design system | Done |
| `e2e/research.spec.ts` | Playwright E2E — upload, grounded ask, insufficient evidence | Done |
| `e2e/guide.spec.ts` | Playwright E2E — Research Desk Guide (2 tests) | Done |
| `e2e/demo-checklist.spec.ts` | Playwright E2E — interview smoke (5 checklist items) | Done |

## Tests (`tests/`)

| Path | Purpose | Status |
| --- | --- | --- |
| `unit/` | Config, health, chunker, vector, evidence, prompt guard | Done |
| `integration/` | Documents, ask, agent, eval, sessions, security, citations | Done |
| `fixtures/sample.md` | Golden fixture | Done |

## Ops

| Path | Purpose | Status |
| --- | --- | --- |
| `docker/Dockerfile` | API image | Done |
| `docker/docker-compose.yml` | Local stack | Done |
| `.github/workflows/ci.yml` | Backend pytest + frontend Vitest + build (no Playwright) | Done (remote run not verified here) |
| `scripts/measure_ask_latency.py` | Local latency sample | Done |

## Not implemented

| Feature | Status |
| --- | --- |
| PDF ingest | Not implemented |
| Document constellation graph | Not implemented |
| Hybrid search / reranking | Not implemented |
| Authentication | Not implemented |

## Legacy index (docs only)

The sections below remain valid references for design docs (`ARCHITECTURE.md`, `AGENT_DESIGN.md`, etc.) — all marked **Done** as documentation.

## Root documentation (extended)

| File | Purpose | Status | Depends on |
| --- | --- | --- | --- |
| [AGENTS.md](./AGENTS.md) | AI assistant instructions | Done | PROJECT_PLAN |
| [PROJECT_OVERVIEW.md](./PROJECT_OVERVIEW.md) | Goals, scope, users | Done | — |
| [PROJECT_PLAN.md](./PROJECT_PLAN.md) | Phases, acceptance criteria | Done | REQUIREMENTS |
| [REQUIREMENTS.md](./REQUIREMENTS.md) | FR/NFR | Done | — |
| [ARCHITECTURE.md](./ARCHITECTURE.md) | System design | Done | RAG_ARCHITECTURE, AGENT_DESIGN |
| [TASK_TRACKER.md](./TASK_TRACKER.md) | Task status | Done | PROJECT_PLAN |
| [NEXT_SESSION.md](./NEXT_SESSION.md) | Handoff for next session | Done | TASK_TRACKER |
| [DECISION_LOG.md](./DECISION_LOG.md) | ADR-style decisions | Done | — |
| [CHANGELOG.md](./CHANGELOG.md) | Version history | Done | — |

## Agent and RAG docs

| File | Purpose | Status |
| --- | --- | --- |
| [AGENT_DESIGN.md](./AGENT_DESIGN.md) | Agent scope and boundaries | Done |
| [AGENT_WORKFLOW.md](./AGENT_WORKFLOW.md) | Plan-act-observe loop | Done |
| [TOOL_USAGE.md](./TOOL_USAGE.md) | Tool schemas | Done |
| [GUARDRAILS.md](./GUARDRAILS.md) | Safety rules | Done |
| [MEMORY_ARCHITECTURE.md](./MEMORY_ARCHITECTURE.md) | Session vs corpus memory | Done |
| [RAG_ARCHITECTURE.md](./RAG_ARCHITECTURE.md) | Ingest → retrieve → generate | Done |
| [PROMPT_ENGINEERING.md](./PROMPT_ENGINEERING.md) | Prompt templates | Done |
| [AGENT_EVALUATION.md](./AGENT_EVALUATION.md) | Metrics and golden sets | Done |

## Engineering docs

| File | Purpose | Status |
| --- | --- | --- |
| [API_CONTRACT.md](./API_CONTRACT.md) | HTTP API | Done |
| [DATABASE_DESIGN.md](./DATABASE_DESIGN.md) | SQLite schema | Done |
| [ERROR_HANDLING.md](./ERROR_HANDLING.md) | Errors and retries | Done |
| [SECURITY.md](./SECURITY.md) | Security practices | Done |
| [TESTING_STRATEGY.md](./TESTING_STRATEGY.md) | Test layers | Done |
| [OBSERVABILITY.md](./OBSERVABILITY.md) | Logs and metrics | Done |
| [CONFIGURATION.md](./CONFIGURATION.md) | Env vars | Done |
| [PERFORMANCE.md](./PERFORMANCE.md) | Latency notes | Done |
| [DEPLOYMENT.md](./DEPLOYMENT.md) | Deploy process | Done |
| [CI_CD.md](./CI_CD.md) | GitHub Actions | Done |
| [INCIDENT_RESPONSE.md](./INCIDENT_RESPONSE.md) | Ops runbook | Done |

## Config and ignore

| File | Purpose | Status |
| --- | --- | --- |
| [.env.example](./.env.example) | Env template | Done |
| [.gitignore](./.gitignore) | Git ignore rules | Done |
| `.env` | Local secrets (user) | User-local (gitignored) |

<!-- Removed stale "Planned" backend table — see Backend section above. -->

## Maintenance rule

When adding or removing files, update this registry in the **same PR/commit** as the change.

## Dependency graph (high level)

```
README → PROJECT_PLAN → implementation files
API_CONTRACT ↔ backend/app/api/routes/*
DATABASE_DESIGN ↔ backend/app/models/*
RAG_ARCHITECTURE ↔ backend/app/rag/* + services/*
AGENT_* ↔ backend/app/agents/*
TESTING_STRATEGY ↔ tests/*
```
