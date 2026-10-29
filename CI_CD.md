# CI/CD

**Status:** Pipeline to be added in Phase 10 — design documented here.

## Goals

- Run pytest on every push/PR
- Block merge on test failure
- No secrets in workflow files

## GitHub Actions (planned)

File: `.github/workflows/ci.yml`

### Jobs

| Job | Steps |
| --- | --- |
| `test` | checkout → setup Python 3.11 → pip install `.[dev]` → pytest |
| `lint` (optional) | ruff check |

### Pytest command

```yaml
run: pytest tests/ -v -m "not slow and not ollama" --tb=short
```

### Caching

- pip cache
- Do **not** cache downloaded embedding models in CI — use fake embedder in tests

## Branch protection (recommended)

- Require `test` job pass before merge to `main`
- Require PR review

## Release workflow (optional)

Tag `v0.x.y` → build Docker image → push to registry (manual approval).

## CD to staging

Not automated in MVP. Manual deploy per [DEPLOYMENT.md](./DEPLOYMENT.md).

## Environment secrets in CI

If later adding OpenAI key for optional provider:

- GitHub Encrypted Secrets
- Never print in logs

## Local pre-push hook (optional)

```bash
pytest tests/unit -q
```

Document in README when hook script added under `scripts/`.

## Interview Q&A

**Q:** What do you run in CI for an ML app?  
**A:** Deterministic unit/integration tests with mocked embeddings/LLM; optional nightly job for slow model tests — not blocking every PR.
