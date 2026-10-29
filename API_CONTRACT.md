# API contract

Base URL: `http://127.0.0.1:8000`  
API prefix: `/api/v1` (see [DECISION_LOG.md](./DECISION_LOG.md) DL-010)

**Status:** Implemented for health, documents, search, ask, collections, sessions, evaluations, agent research, and system routes. See OpenAPI at `/docs` in development.

## Common

### Headers

| Header | Required | Notes |
| --- | --- | --- |
| `X-Request-Id` | Optional | Client-supplied; server generates if absent |
| `Content-Type` | JSON routes | `application/json` |

### Error envelope

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Human readable",
    "details": [],
    "request_id": "uuid"
  }
}
```

## Endpoints

### `GET /health`

**Response 200**

```json
{
  "status": "ok",
  "app": "grounded-research-desk",
  "version": "0.1.0"
}
```

---

### `POST /api/v1/documents`

Upload a document (multipart).

**Request:** `multipart/form-data` field `file`

**Response 201**

```json
{
  "document_id": "uuid",
  "filename": "notes.md",
  "chunk_count": 12,
  "status": "indexed"
}
```

**Errors:** 413, 422

---

### `GET /api/v1/documents`

**Query:** `limit`, `offset`

**Response 200**

```json
{
  "items": [
    {
      "document_id": "uuid",
      "filename": "notes.md",
      "created_at": "2026-10-28T10:00:00Z",
      "chunk_count": 12
    }
  ],
  "total": 1
}
```

---

### `GET /api/v1/documents/{document_id}`

**Response 200:** metadata + optional preview snippet  
**404** if missing

---

### `DELETE /api/v1/documents/{document_id}`

**Response 204**  
Blocked when `DEMO_MODE=true` (403)

---

### `POST /api/v1/ask`

RAG question answering.

**Request**

```json
{
  "question": "What is the rollback step?",
  "document_ids": ["optional-filter"],
  "top_k": 5,
  "conversation_id": "optional-phase7"
}
```

**Response 200**

```json
{
  "answer": "Rollback requires ... [chunk_id]",
  "citations": [
    {
      "chunk_id": "uuid",
      "document_id": "uuid",
      "filename": "runbook.md",
      "snippet": "...",
      "score": 0.81
    }
  ],
  "retrieval": {
    "model": "sentence-transformers/all-MiniLM-L6-v2",
    "top_k": 5
  },
  "request_id": "uuid"
}
```

**Errors:** 422, 503, 504

---

### `POST /api/v1/research`

Agent research (Phase 7). Requires `AGENT_ENABLED=true`.

**Request**

```json
{
  "goal": "Compare rollback steps in two runbooks",
  "document_ids": [],
  "conversation_id": "optional"
}
```

**Response 200**

```json
{
  "answer": "...",
  "citations": [],
  "steps": [
    {
      "step_index": 1,
      "tool": "search_chunks",
      "tool_input": {},
      "observation_summary": "3 hits"
    }
  ],
  "status": "completed",
  "request_id": "uuid"
}
```

**403** if agent disabled  
**504** on budget/timeout

---

### `GET /api/v1/metrics/eval` (optional)

Run internal golden eval (dev only, protect in production).

## Pydantic models (planned location)

`backend/app/models/schemas.py`

## OpenAPI

FastAPI auto-docs at `/docs` when `APP_ENV=development` only (disable in production — [SECURITY.md](./SECURITY.md)).

## Versioning policy

Breaking changes → `/api/v2`; v1 supported until documented sunset.
