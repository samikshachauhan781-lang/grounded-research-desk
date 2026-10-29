# Configuration

All configuration via **environment variables**. Copy `.env.example` → `.env` for local dev.

## Loading pattern

`backend/app/core/config.py` using `pydantic-settings`:

- Read from environment
- Optional `.env` file (not committed)
- Singleton `get_settings()` cached with `lru_cache`

## Variable reference

| Variable | Default | Description |
| --- | --- | --- |
| `APP_NAME` | `grounded-research-desk` | Service name in health |
| `APP_ENV` | `development` | `development` \| `production` |
| `LOG_LEVEL` | `INFO` | Python log level |
| `API_HOST` | `127.0.0.1` | Bind host (use `0.0.0.0` in Docker) |
| `API_PORT` | `8000` | Bind port |
| `API_PREFIX` | `/api/v1` | Router prefix |
| `DATABASE_URL` | `sqlite:///./data/grounded_research.db` | SQLAlchemy URL |
| `MAX_UPLOAD_BYTES` | `5242880` | 5 MB |
| `ALLOWED_UPLOAD_EXTENSIONS` | `.txt,.md` | Comma-separated |
| `EMBEDDING_MODEL_NAME` | `all-MiniLM-L6-v2` | HuggingFace id |
| `EMBEDDING_DIMENSION` | `384` | Must match model |
| `EMBEDDING_DEVICE` | `cpu` | `cpu` or `cuda` |
| `CHUNK_SIZE_CHARS` | `800` | Chunk window |
| `CHUNK_OVERLAP_CHARS` | `120` | Overlap |
| `RETRIEVAL_TOP_K` | `5` | Chunks to LLM |
| `MIN_SIMILARITY_SCORE` | `0.25` | Filter threshold |
| `EVIDENCE_MIN_LEXICAL_OVERLAP` | `0.15` | Min share of question content tokens found in top passage before LLM |
| `LLM_PROVIDER` | `mock` | `mock` \| `ollama` |
| `OLLAMA_BASE_URL` | `http://127.0.0.1:11434` | Ollama API |
| `OLLAMA_MODEL` | `llama3.2` | Model tag |
| `GENERATION_TIMEOUT_SECONDS` | `60` | LLM timeout |
| `AGENT_ENABLED` | `false` | Enable `/research` |
| `AGENT_MAX_TOOL_CALLS` | `8` | Agent budget |
| `AGENT_MAX_WALL_CLOCK_SECONDS` | `120` | Agent timeout |
| `DEMO_MODE` | `false` | Read-only destructive ops |

## Production overrides

| Variable | Recommended |
| --- | --- |
| `APP_ENV` | `production` |
| `LOG_LEVEL` | `WARNING` |
| `LLM_PROVIDER` | `ollama` or hosted (if added later) |

## Secrets

No secrets required for MVP. If API keys added later:

- Store in host secret manager
- Never in `.env.example`

## Validation rules

- `CHUNK_OVERLAP_CHARS < CHUNK_SIZE_CHARS`
- `RETRIEVAL_TOP_K >= 1`
- `EMBEDDING_DIMENSION` matches model or startup fails fast

## Interview Q&A

**Q:** Why pydantic-settings?  
**A:** Typed config with validation at startup — fail fast before serving traffic.
