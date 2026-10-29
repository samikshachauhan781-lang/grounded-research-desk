# Agent and RAG evaluation

## Objectives

Measure whether the system **finds the right evidence** and **answers from it** — not whether the LLM sounds fluent.

## Metrics

### Retrieval

| Metric | Definition | MVP target (fixture set) |
| --- | --- | --- |
| recall@1 | % queries where rank-1 chunk contains answer span | Document baseline |
| recall@3 | % where answer span in top 3 | ≥ 90% on fixtures |
| MRR | Mean of 1/rank of first correct chunk | Track trend |

### Answer quality

| Metric | Definition | Method |
| --- | --- | --- |
| Citation validity | All cited chunk ids were retrieved | Automated |
| Abstention rate | “Don’t know” when no context | Automated scenarios |
| Groundedness | Claims supported by cited text | Manual or LLM-judge (optional) |
| Agent task success | Scripted goal completed within budget | Integration tests |

## Golden dataset format

`tests/golden/qa_pairs.json`:

```json
[
  {
    "id": "rollback-01",
    "document_fixture": "sample.md",
    "question": "What command rolls back the database?",
    "expected_substring": "flyway rollback",
    "notes": "Fact in chunk 2"
  }
]
```

## Evaluation runs

### Retrieval-only

1. Ingest fixture doc
2. Embed (real or fake embedder)
3. Search question
4. Assert expected_substring in top-k chunk texts

### End-to-end (mock LLM)

Mock returns canned answer including correct chunk id — validates orchestration and citation mapping.

### Agent scripted tasks

Example goal: “List documents, search for X, summarize with citations.”  
Assert: `len(steps) <= AGENT_MAX_TOOL_CALLS` and citation guardrail pass.

## LLM-as-judge (optional, Phase 9)

Use local model with rubric:

- Score 1-5 grounded in citations
- Fail if judge cites chunk not in context

Not used as sole gate in CI (variance).

## Reporting

Print table after eval:

```
recall@3: 92% (11/12)
citation_validity: 100% (20/20)
```

Store results in CI artifact or `tests/eval/last_run.txt` (gitignored).

## Regression policy

Prompt or chunk size change → re-run golden before merge.

## Interview talking points

- Difference between **offline eval** (golden set) and **online monitoring** (latency, errors)
- Why recall@k matters more than BLEU for RAG
