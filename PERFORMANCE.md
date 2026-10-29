# Performance

## Policy

We **measure** before optimizing. Numbers below marked **TARGET** until benchmark script exists.

## Latency components (ask path)

| Stage | TARGET (small corpus, CPU, mock LLM) | Notes |
| --- | --- | --- |
| Query embed | 20–80 ms | MiniLM batch 1 |
| Vector search (brute force, N<5k chunks) | 10–200 ms | Grows linearly |
| LLM mock | < 5 ms | |
| LLM Ollama | 1–15 s | Model/hardware dependent |
| Measured `/ask` (mock, sample.md, fake embed) | **~5 ms p50** (5 samples, local) | `python scripts/measure_ask_latency.py` |
| Total `/ask` (mock) | **< 500 ms** | Met on sample corpus |

## Throughput

| Scenario | TARGET |
| --- | --- |
| Concurrent asks on SQLite | Low — single writer; use queue later |
| Ingest 1 MB text | **TARGET** < 30 s including embed |

## Resource usage

| Resource | Typical |
| --- | --- |
| RAM (API without model) | < 200 MB |
| RAM (sentence-transformers loaded) | +300–600 MB |
| Disk | DB + uploads + model cache |

## Optimization roadmap

| Optimization | When |
| --- | --- |
| Batch embedding on ingest | Phase 4 if slow |
| numpy vectorized cosine matrix | Phase 4 |
| FAISS / hnswlib index | When N chunks > 10k **measured** |
| Async ingest worker | Phase 9 |
| Cache query embeddings (LRU) | If repeated queries |

## Benchmark script (planned)

`scripts/bench_retrieval.py`:

- Ingest fixture
- Run 100 searches
- Report p50/p95 latency

Output appended to this doc after first run.

## Frontend perf (Phase 8)

- TanStack Query caching for document list
- Debounce ask input

## Interview Q&A

**Q:** Why not FAISS on day one?  
**A:** Brute force is O(n) but simple and fine for small n; premature ANN adds ops burden without measured pain.

**Q:** Bottleneck in RAG?  
**A:** Often LLM generation, then embedding; retrieval math is cheap until corpus scales.
