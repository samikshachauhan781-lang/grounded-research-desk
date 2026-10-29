# Database design

**Engine:** SQLite (MVP)  
**File:** `data/grounded_research.db` (from `DATABASE_URL`)

## ER diagram

```mermaid
erDiagram
  documents ||--o{ chunks : contains
  chunks ||--|| chunk_embeddings : has
  conversations ||--o{ messages : has
  conversations ||--o{ agent_traces : has

  documents {
    text id PK
    text filename
    text content_text
    text storage_path
    datetime created_at
    datetime updated_at
  }

  chunks {
    text id PK
    text document_id FK
    int chunk_index
    text text
    datetime created_at
  }

  chunk_embeddings {
    text chunk_id PK FK
    text model_name
    blob vector
    datetime created_at
  }

  conversations {
    text id PK
    datetime created_at
  }

  messages {
    text id PK
    text conversation_id FK
    text role
    text content
    datetime created_at
  }

  agent_traces {
    text id PK
    text conversation_id FK
    text steps_json
    datetime created_at
  }
```

## Table definitions

### `documents`

| Column | Type | Constraints |
| --- | --- | --- |
| id | TEXT | PK, UUID |
| filename | TEXT | NOT NULL |
| content_text | TEXT | NOT NULL |
| storage_path | TEXT | NOT NULL |
| byte_size | INTEGER | NOT NULL |
| created_at | TEXT | ISO8601 UTC |
| updated_at | TEXT | ISO8601 UTC |

Index: `idx_documents_created_at`

### `chunks`

| Column | Type | Constraints |
| --- | --- | --- |
| id | TEXT | PK |
| document_id | TEXT | FK → documents(id) ON DELETE CASCADE |
| chunk_index | INTEGER | NOT NULL |
| text | TEXT | NOT NULL |
| char_start | INTEGER | optional |
| char_end | INTEGER | optional |
| created_at | TEXT | |

Unique: `(document_id, chunk_index)`  
Index: `idx_chunks_document_id`

### `chunk_embeddings`

| Column | Type | Constraints |
| --- | --- | --- |
| chunk_id | TEXT | PK, FK → chunks(id) ON DELETE CASCADE |
| model_name | TEXT | NOT NULL |
| dimension | INTEGER | NOT NULL |
| vector | BLOB | NOT NULL (float32 array) |
| created_at | TEXT | |

Index: `idx_embeddings_model`

### Conversation tables (Phase 7)

See [MEMORY_ARCHITECTURE.md](./MEMORY_ARCHITECTURE.md).

## Migrations strategy

MVP: SQLAlchemy `create_all` on startup for dev; Alembic when schema stabilizes (Phase 9).

## Vector storage format

- Serialize `numpy.float32` array to bytes
- Deserialize on search
- Document endianness: little-endian native

## Sample queries

**Top chunks for document**

```sql
SELECT id, chunk_index FROM chunks WHERE document_id = ? ORDER BY chunk_index;
```

**Delete document cascade**

Deletes chunks and embeddings via FK CASCADE.

## Backup

Copy `data/grounded_research.db` and `data/uploads/` together — paths referenced in rows.

## Future: Postgres + pgvector

If migration needed: dual-write period; re-embed only if model changes.

## Testing

- Use in-memory SQLite `:memory:` or temp file per test session
- Fixture factory in `tests/conftest.py` (planned)
