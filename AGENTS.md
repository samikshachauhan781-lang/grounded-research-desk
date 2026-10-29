# Instructions for AI coding assistants

This file guides Cursor, Copilot, and other agents working on **Grounded Research Desk** at `/Users/samiksha/Documents/Project_2`.

## Mission

Build an interview-ready **RAG platform** with optional **controlled agents**, step by step. Prefer clarity and tests over feature sprawl.

## Non-negotiables

1. **Do not modify** the user's DevOps Incident Commander project unless explicitly asked.
2. **Do not commit, push, merge, or deploy** without explicit user approval.
3. **Do not claim a feature works** until tests have been run and counts reported.
4. **Never commit secrets**, real private documents, or production databases.
5. **Use environment variables** for configuration ([CONFIGURATION.md](./CONFIGURATION.md)).
6. **Wait for user review** between milestones ([PROJECT_PLAN.md](./PROJECT_PLAN.md)).

## Teaching mode (default)

For each milestone, explain: what, why, industry use, architecture flow, implementation, how to run/test, common errors, interview Q&A, and a short exercise. Use simple English; Hinglish optional for hard concepts.

## Architecture authority

| Topic | Source of truth |
| --- | --- |
| Requirements | [REQUIREMENTS.md](./REQUIREMENTS.md) |
| System design | [ARCHITECTURE.md](./ARCHITECTURE.md) |
| RAG pipeline | [RAG_ARCHITECTURE.md](./RAG_ARCHITECTURE.md) |
| Agent behavior | [AGENT_DESIGN.md](./AGENT_DESIGN.md), [GUARDRAILS.md](./GUARDRAILS.md) |
| API shapes | [API_CONTRACT.md](./API_CONTRACT.md) |
| Database | [DATABASE_DESIGN.md](./DATABASE_DESIGN.md) |
| Decisions | [DECISION_LOG.md](./DECISION_LOG.md) |

If code and docs disagree, **fix the code or update the doc in the same change** — never leave silent drift.

## Implementation order

1. Health + config + pytest skeleton
2. Document upload and metadata
3. Chunking with overlap tests
4. Embeddings + vector search (cosine), golden retrieval test
5. Ask endpoint + mock LLM + citations
6. Evaluation harness
7. Agent tools (behind `AGENT_ENABLED`)
8. Frontend, Docker, CI, deploy docs

Do **not** add LangChain/LlamaIndex in MVP unless [DECISION_LOG.md](./DECISION_LOG.md) is updated with rationale.

## Code standards

- Python: type hints, Pydantic v2 models, explicit HTTP errors
- Modular services under `backend/app/services/`
- Providers behind interfaces (`backend/app/providers/`)
- Tests: isolated DB, fixture files in `tests/fixtures/`
- Log structured context (request id, document id) — [OBSERVABILITY.md](./OBSERVABILITY.md)

## Agent-specific coding rules

When implementing the research agent ([AGENT_WORKFLOW.md](./AGENT_WORKFLOW.md)):

- Fixed tool allowlist only ([TOOL_USAGE.md](./TOOL_USAGE.md))
- Validate every tool input before execution
- Enforce `AGENT_MAX_TOOL_CALLS` and wall-clock timeout
- Every final answer must include citations from retrieved chunks
- Refuse secrets, destructive shell, and arbitrary network fetch unless explicitly scoped in a future phase

## Session handoff

At end of each session, update:

- [CURRENT_STATE.md](./CURRENT_STATE.md)
- [TASK_TRACKER.md](./TASK_TRACKER.md)
- [NEXT_SESSION.md](./NEXT_SESSION.md)
- [CHANGELOG.md](./CHANGELOG.md) when user-facing behavior changes
- [FILE_REGISTRY.md](./FILE_REGISTRY.md) when files are added or removed

## Suggested commit message format

```
milestone(N): short imperative summary

Why: one sentence.
Tests: pytest X passed, Y failed, Z skipped.
```
