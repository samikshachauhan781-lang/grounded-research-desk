# Project overview

## Name

**Grounded Research Desk** (working product name)  
**AI Knowledge & Research Intelligence Platform** (descriptive title)

## One-sentence pitch

A local-first application that lets teams upload documents, ask questions, and receive **cited answers** from retrieved passages — with an optional **controlled research agent** for multi-step investigation.

## Goals

1. **Learn by building** — embeddings, chunking, RAG, evaluation, and agents with visible code paths.
2. **Interview readiness** — explain trade-offs, failure modes, and metrics without hand-waving.
3. **Production habits** — tests, config, logging, security basics, and deployment docs.
4. **Cost discipline** — mock and local models by default; no required paid API for MVP.

## Target users

| User | Need |
| --- | --- |
| AI/ML job candidate | Portfolio project with measurable retrieval quality |
| Student / analyst | Private Q&A over notes without pasting full PDFs into chat |
| Small engineering team | Inspectable internal “ask the docs” prototype |

## In scope (full vision)

- Document upload, parse, clean, chunk
- Embeddings and vector search (hybrid + rerank later)
- RAG Q&A with citations
- Conversation history (later)
- Retrieval and answer evaluation
- Controlled agent with tools, guardrails, retries
- FastAPI backend + React frontend
- Docker, CI, deployment documentation

## Out of scope (initial releases)

- Multi-tenant SaaS billing
- Real-time web crawling as core product
- Replacing Datadog / PagerDuty / enterprise search
- Unrestricted autonomous agents with shell access

## Relationship to prior work

The author completed **DevOps Incident Commander** (incident CRUD, template-guided AI investigation, demo mode). This project reuses **patterns** (FastAPI, SQLite, mock/Ollama providers, pytest discipline) but **different domain**: knowledge retrieval and grounded answers, not incident lifecycle.

## Success criteria (project-level)

| Metric | Target |
| --- | --- |
| Golden retrieval | Top-3 contains correct chunk ≥ 90% on fixture set |
| Groundedness | 100% citation ids ∈ retrieved set in automated tests |
| MVP API | Upload + ask + cite working with mock LLM |
| Agent phase | Completes scripted multi-step task without exceeding tool budget |
| Documentation | All registry files accurate to repo state |

## Document map

Start with [README.md](./README.md) → [PROJECT_PLAN.md](./PROJECT_PLAN.md) → [ARCHITECTURE.md](./ARCHITECTURE.md).
