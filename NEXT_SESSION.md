# Next session

## Suggested focus

1. **PDF ingest** — parse pipeline + tests (optional phase).
2. **Authentication** — only if targeting shared deployment; must protect API, not UI alone.
3. **Document constellation** — graph UI when relationship model exists.
4. **Hybrid retrieval / reranking** — after evaluation metrics justify complexity.

## Quick verify

```bash
cd /Users/samiksha/Documents/Project_2 && source .venv/bin/activate && pytest tests/ -q
cd frontend && npm run build && npm run test:e2e
```

## Notes

- Git is intentionally not initialized in this workspace.
- Remote GitHub Actions not verified in the completion session; workflow is locally reviewable.
