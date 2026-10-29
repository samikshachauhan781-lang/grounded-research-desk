# Testing strategy

## Goals

- Prove retrieval works before trusting LLM output.
- Keep CI fast with mock providers.
- Isolate tests from developer uploads in `data/uploads/`.

## Test pyramid

| Layer | Location | Focus |
| --- | --- | --- |
| Unit | `tests/unit/` | Chunker, cosine math, prompt builder, tool validation |
| Integration | `tests/integration/` | API + SQLite + ingest + ask |
| Golden / eval | `tests/golden/`, `tests/eval/` | recall@k, citation validity |
| E2E (optional) | Playwright Phase 8 | Upload UI happy path |

## Fixtures

| Path | Purpose |
| --- | --- |
| `tests/fixtures/sample.md` | Known facts for retrieval |
| `tests/fixtures/sample.txt` | Plain text variant |
| `tests/golden/qa_pairs.json` | question → expected_chunk_substring |

## Conventions

- Use `tmp_path` or `:memory:` SQLite per test
- Never depend on Ollama in default pytest run
- Mark slow tests: `@pytest.mark.slow` (embedding model download)
- Mark ollama: `@pytest.mark.ollama` skipped in CI

## Critical test cases (implement by Phase 5)

| ID | Test | Phase |
| --- | --- | --- |
| T-1 | Health 200 | 1 |
| T-2 | Upload rejects .exe | 2 |
| T-3 | Chunk overlap contains boundary sentence | 3 |
| T-4 | Golden question retrieves correct chunk | 4 |
| T-5 | Ask response citations ⊆ retrieved ids | 5 |
| T-6 | Model mismatch blocks search | 4 |
| T-7 | Agent exceeds tool budget → structured stop | 7 |
| T-8 | Empty retrieval → no hallucination path | 5 |

## Running tests

```bash
cd /Users/samiksha/Documents/Project_2
pytest tests/ -v
pytest tests/ -v -m "not slow and not ollama"
pytest tests/eval/ -v  # golden metrics
```

## Coverage

Target: **critical path ≥ 80%** line coverage on `services/`, `rag/`, `agents/` when implemented.

```bash
pytest --cov=backend/app --cov-report=term-missing
```

## CI

See [CI_CD.md](./CI_CD.md) — run unit + integration on every push.

## Reporting rule (mentoring)

After each milestone, report exact:

```
passed: N, failed: M, skipped: K
```

## Fake embedder for speed

Test double returns fixed vectors for known strings — enables deterministic similarity in unit tests without downloading MiniLM.

## Interview Q&A

**Q:** Why mock the LLM but not retrieval?  
**A:** Retrieval is our code + math we must verify; LLM is non-deterministic and external — we test provider wiring separately.
