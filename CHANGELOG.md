# Changelog

All notable changes to **Grounded Research Desk** will be documented here.

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Changed

- Documentation: Playwright E2E count (**4 tests**), browser install prerequisite, default fake/mock demo stack; CI frontend job runs Vitest.

### Added

- Mobile navigation drawer, session-backed research workspace, copy answer, library drag-and-drop.
- Prompt guard delimiters for untrusted document context; agent uses same evidence sufficiency as `/ask`.
- Regression tests: sessions, citations, upload security, prompt-injection fixture, agent irrelevant goal.
- Expanded Playwright E2E (Evidence Rail, API error, upload cleanup).
- Docker non-root user + healthcheck; CI frontend build job; `scripts/measure_ask_latency.py`.
- Safer default `API_HOST=127.0.0.1` for local development.

### Fixed

- **Insufficient evidence:** lexical + provider-aware sufficiency gate skips LLM on weak matches.
- Retrieval with fake embeddings no longer drops all hits via uncalibrated similarity cutoff alone.

### Previously shipped (RAG MVP)

- Full RAG backend, SQLite schema, mock/Ollama LLM, fake/local embeddings, agent, UI, Docker, CI.

### Added (Milestone 1)

- Project scaffold at `/Users/samiksha/Documents/Project_2`
- Full documentation registry (architecture, RAG, agent, API, security, testing, deploy)
- Directory layout for backend, frontend, tests, data, docker, deploy
- `.env.example` and `.gitignore`
- Test fixtures: `tests/fixtures/sample.md`, `tests/golden/qa_pairs.json`

### Changed

- N/A

### Fixed

- N/A

## [0.0.1] - 2026-10-28

### Added

- Phase 0 planning documentation only — no runnable application yet

---

## Versioning plan

| Version | Milestone |
| --- | --- |
| 0.1.0 | Phase 1 health + pytest |
| 0.2.0 | Document upload API |
| 0.3.0 | Chunk + embed + search |
| 0.4.0 | Ask + citations |
| 0.5.0 | Evaluation harness |
| 0.6.0 | Agent `/research` |
| 1.0.0 | Frontend + Docker + demo deploy verified by maintainer |
