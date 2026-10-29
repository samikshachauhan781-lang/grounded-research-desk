# Deployment

**Status:** Documented target process — containers and scripts land in Phase 10.

## Deployment models

| Model | Use case |
| --- | --- |
| Local dev | `uvicorn` + optional local Ollama |
| Docker Compose | Demo / interview machine |
| PaaS (Render/Fly/Railway) | Public portfolio demo |

## Local (MVP)

```bash
cd /Users/samiksha/Documents/Project_2
source .venv/bin/activate
export $(grep -v '^#' .env | xargs)  # or use direnv
uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

Optional Ollama on same machine:

```bash
ollama serve
ollama pull llama3.2
```

Set `LLM_PROVIDER=ollama`.

## Docker Compose

`docker/docker-compose.yml`:

- Service `api`: build from `docker/Dockerfile` (non-root user, healthcheck)
- Volume: `./data:/app/data`
- Binds `0.0.0.0:8000` inside the container

```bash
docker compose -f docker/docker-compose.yml up --build
```

## Backup and restore

**Backup**

1. Stop the API / containers.
2. Copy `data/grounded_research.db` and the `data/uploads/` directory.

**Restore**

1. Stop the API.
2. Replace the database file and uploads folder.
3. Start the API and verify `GET /health/ready`.

Never run test cleanup scripts against your primary `data/` directory.

## Production checklist

- [ ] `APP_ENV=production`
- [ ] Disable OpenAPI `/docs`
- [ ] TLS termination at reverse proxy
- [ ] Persistent volume for `data/`
- [ ] Backups for SQLite + uploads
- [ ] Resource limits (CPU/RAM) for embedding model
- [ ] Health check: `GET /health`

## Render example (future)

Similar to Incident Commander pattern:

- Web service for API
- Static site or combined for frontend
- Env: `DATABASE_URL`, `LLM_PROVIDER=mock` for public demo

Document live URL only after you verify — do not claim unverified uptime.

## Rollback

- Redeploy previous container image
- Restore DB snapshot if migration failed

## Scaling limits (honest)

SQLite single-writer — suitable for demo/small team. For multi-user prod, plan Postgres migration ([DATABASE_DESIGN.md](./DATABASE_DESIGN.md)).

## Interview Q&A

**Q:** How would you deploy RAG differently from a CRUD app?  
**A:** Account for embedding model memory, cold start download, and optional GPU sidecar for Ollama; persistent volumes for vectors and uploads.
