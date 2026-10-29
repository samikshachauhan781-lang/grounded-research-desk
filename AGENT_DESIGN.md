# Agent design

## Purpose

The **Research Agent** (Phase 7+) helps users investigate questions that may require **multiple retrieval steps** — for example comparing two runbooks or gathering evidence before summarizing.

It is **not** a general autonomous assistant. It is a **bounded loop** over approved tools with mandatory citations.

## Responsibilities

| Responsibility | Owner module (planned) |
| --- | --- |
| Parse user goal into subtasks | `agents/orchestrator.py` |
| Select and invoke tools | `agents/tool_runner.py` |
| Track step history | `agents/session_memory.py` |
| Enforce limits | `core/guardrails.py` |
| Produce final cited answer | `services/generation/` |

## Non-responsibilities

- Writing to documents or database (read-only corpus)
- Calling external URLs (MVP agent)
- Running shell commands
- Storing user secrets or API keys in prompts

## Agent types (single agent MVP)

**ResearchAgent** — one orchestrator class with:

- Input: `goal: str`, optional `document_ids: list[str]`, optional `conversation_id`
- Output: `AgentResult(answer, citations, steps, status)`

Future: separate **EvaluatorAgent** for offline metrics only (not user-facing).

## Boundaries vs RAG ask endpoint

| Aspect | `POST /ask` | `POST /research` |
| --- | --- | --- |
| Steps | Single retrieve → generate | Multi-tool loop |
| Latency | Lower | Higher, capped |
| Use case | Direct Q&A | Exploratory research |
| Tool calls | 0 | 1..N (bounded) |

Simple questions should use `/ask` without agent overhead ([DECISION_LOG.md](./DECISION_LOG.md) DL-008).

## Control policies

| Policy | Setting |
| --- | --- |
| Max tool calls | `AGENT_MAX_TOOL_CALLS` (default 8) |
| Wall clock | `AGENT_MAX_WALL_CLOCK_SECONDS` (default 120) |
| Feature flag | `AGENT_ENABLED` |
| Allowed tools | See [TOOL_USAGE.md](./TOOL_USAGE.md) |

## Failure modes

| Mode | User-visible behavior |
| --- | --- |
| Tool validation error | Step error in trace; retry alternate tool if planner allows |
| Retrieval empty | Stop with honest “no evidence in corpus” |
| Budget exceeded | Partial answer + note that limit reached |
| LLM timeout | 504 with retry guidance |

## Testing strategy

- Scripted goals in `tests/integration/test_agent_scripted.py`
- Assert tool call count ≤ max
- Assert every citation id appeared in a prior tool result

See [AGENT_EVALUATION.md](./AGENT_EVALUATION.md).

## Interview soundbite

“We built a **read-only research agent** with a fixed tool allowlist, hard budgets, and citation guardrails — not an open-ended AutoGPT clone.”
