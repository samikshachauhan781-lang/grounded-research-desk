# Memory architecture

## Scope

“Memory” here means **what the system remembers across requests** — not vector embeddings (see [RAG_ARCHITECTURE.md](./RAG_ARCHITECTURE.md)).

## Memory types

| Type | Lifetime | Storage (planned) | Used by |
| --- | --- | --- | --- |
| Corpus memory | Permanent until delete | SQLite + files | RAG, agent tools |
| Session memory | Conversation / research run | SQLite table `sessions` or in-memory | `/ask` follow-ups, `/research` |
| Working memory | Single agent loop | Python list in orchestrator | Agent planner |
| Ephemeral cache | Request-scoped | LRU optional | Embedding query cache |

## Session memory (Phase 7+)

### Tables (planned)

**conversations**

| Column | Type | Notes |
| --- | --- | --- |
| id | TEXT PK | UUID |
| created_at | DATETIME | |
| updated_at | DATETIME | |

**messages**

| Column | Type | Notes |
| --- | --- | --- |
| id | TEXT PK | |
| conversation_id | TEXT FK | |
| role | TEXT | user / assistant / system |
| content | TEXT | |
| created_at | DATETIME | |

**agent_traces**

| Column | Type | Notes |
| --- | --- | --- |
| id | TEXT PK | |
| conversation_id | TEXT FK | |
| steps_json | TEXT | Serialized step list |
| created_at | DATETIME | |

## What we store in agent working memory

Each loop iteration appends:

- Planner thought (short)
- Tool name + validated input
- Observation summary (truncated)
- Retrieved chunk ids (for citation validation)

## What we do **not** store

- Full LLM weights
- Raw env secrets
- Entire uploaded files in session rows (only ids + snippets)

## Context window management

When conversation history exceeds token budget (future):

1. Keep last N user/assistant turns verbatim.
2. Summarize older turns with separate summarization call (optional).
3. Always re-retrieve fresh chunks for latest question (avoid stale RAG).

MVP `/ask` may be **single-turn only** — document in [CURRENT_STATE.md](./CURRENT_STATE.md) when implemented.

## Interview talking points

- **Short-term vs long-term memory** in agents: working trace vs persisted conversation.
- **RAG is not memory** — it is retrieval from external knowledge each turn unless you cache incorrectly.
- **Citation validation** ties “memory” claims to chunk ids in the trace.

## Privacy

Sessions containing sensitive uploads should be deletable via API (Phase 8+). See [SECURITY.md](./SECURITY.md).
