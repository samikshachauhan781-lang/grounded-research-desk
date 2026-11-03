"""Agent and Ask synthesis context alignment (Phase 5.4)."""

from backend.app.core.config import Settings
from backend.app.models.schemas import SearchResultItem
from backend.app.providers.llm import build_citations
from backend.app.rag.evidence_answer import synthesize_answer_from_evidence
from backend.app.rag.evidence_policy import assess_retrieval_sufficiency
from backend.app.rag.synthesis_result import SynthesisStatus
from backend.app.services.generation.synthesis_context import build_synthesis_context_blocks


def _result(
    chunk_id: str,
    snippet: str,
    score: float = 0.1,
) -> SearchResultItem:
    return SearchResultItem(
        chunk_id=chunk_id,
        document_id="doc-1",
        filename="inventory.md",
        snippet=snippet,
        score=score,
    )


class _ChunkRow:
    def __init__(self, chunk_id: str, text: str) -> None:
        self.chunk_id = chunk_id
        self.text = text


class _FakeSession:
    def __init__(self, chunks: dict[str, str]) -> None:
        self._chunks = chunks

    def get(self, _model: object, chunk_id: str) -> _ChunkRow | None:
        text = self._chunks.get(chunk_id)
        if text is None:
            return None
        return _ChunkRow(chunk_id, text)


def _five_hit_ranking(*, rank4_text: str, rank5_text: str = "Unrelated filler about caches and virtual environments.") -> list[SearchResultItem]:
    ids = [f"rank-{i}-chunk-id-000000000000000{i}" for i in range(1, 6)]
    filler = "Unrelated metadata about virtual environments and cache directories."
    return [
        _result(ids[0], filler, score=0.9),
        _result(ids[1], filler, score=0.8),
        _result(ids[2], filler, score=0.7),
        _result(ids[3], rank4_text, score=0.6),
        _result(ids[4], rank5_text, score=0.5),
    ]


STATUS_TEXT = (
    "The project appears to be at Day 7 with the timeline and audit trail "
    "feature already implemented."
)
STATUS_QUESTION = "What is the reported development status of the project?"


def test_build_synthesis_context_includes_all_retrieval_ranks() -> None:
    results = _five_hit_ranking(rank4_text=STATUS_TEXT)
    db = _FakeSession({r.chunk_id: r.snippet for r in results})
    blocks = build_synthesis_context_blocks(db, results)
    assert [cid for cid, _ in blocks] == [r.chunk_id for r in results]
    assert len(blocks) == 5


def test_rank4_supporting_hit_reaches_synthesis_after_sufficiency() -> None:
    """Old Agent bug: retrieval.results[:3] dropped rank-4 evidence that passed sufficiency."""
    settings = Settings(EMBEDDING_PROVIDER="fake", EVIDENCE_MIN_LEXICAL_OVERLAP=0.15)
    results = _five_hit_ranking(rank4_text=STATUS_TEXT)
    suff = assess_retrieval_sufficiency(STATUS_QUESTION, results, settings)
    assert suff.sufficient is True

    db = _FakeSession({r.chunk_id: r.snippet for r in results})
    full_blocks = build_synthesis_context_blocks(db, results)
    old_agent_blocks = full_blocks[:3]

    old_syn = synthesize_answer_from_evidence(STATUS_QUESTION, old_agent_blocks, settings)
    new_syn = synthesize_answer_from_evidence(STATUS_QUESTION, full_blocks, settings)

    assert old_syn.status != SynthesisStatus.SUCCESS or "day 7" not in old_syn.answer.lower()
    assert new_syn.status == SynthesisStatus.SUCCESS
    assert "day 7" in new_syn.answer.lower()
    assert new_syn.source_chunk_id == results[3].chunk_id


def test_rank5_supporting_hit_reaches_synthesis_after_sufficiency() -> None:
    settings = Settings(EMBEDDING_PROVIDER="fake", EVIDENCE_MIN_LEXICAL_OVERLAP=0.15)
    results = _five_hit_ranking(
        rank4_text="Still unrelated but mentions project planning notes only.",
        rank5_text=STATUS_TEXT,
    )
    suff = assess_retrieval_sufficiency(STATUS_QUESTION, results, settings)
    assert suff.sufficient is True

    db = _FakeSession({r.chunk_id: r.snippet for r in results})
    full_blocks = build_synthesis_context_blocks(db, results)
    old_agent_blocks = full_blocks[:3]

    old_syn = synthesize_answer_from_evidence(STATUS_QUESTION, old_agent_blocks, settings)
    new_syn = synthesize_answer_from_evidence(STATUS_QUESTION, full_blocks, settings)

    assert old_syn.status != SynthesisStatus.SUCCESS or "day 7" not in old_syn.answer.lower()
    assert new_syn.status == SynthesisStatus.SUCCESS
    assert new_syn.source_chunk_id == results[4].chunk_id


def test_rank1_evidence_still_available_to_synthesis() -> None:
    settings = Settings(EMBEDDING_PROVIDER="fake", EVIDENCE_MIN_LEXICAL_OVERLAP=0.15)
    rank1_id = "rank-1-chunk-id-0000000000000001"
    inventory = (
        "This directory contains the DevOps Incident Commander project with the following files."
    )
    results = [
        _result(rank1_id, inventory, score=0.9),
        _result("rank-2-chunk-id-0000000000000002", STATUS_TEXT, score=0.5),
    ]
    question = "What is the DevOps Incident Commander project directory about?"
    db = _FakeSession({r.chunk_id: r.snippet for r in results})
    blocks = build_synthesis_context_blocks(db, results)
    syn = synthesize_answer_from_evidence(question, blocks, settings)
    assert syn.status == SynthesisStatus.SUCCESS
    assert syn.source_chunk_id == rank1_id


def test_agent_citation_uses_synthesis_source_chunk() -> None:
    settings = Settings(EMBEDDING_PROVIDER="fake", EVIDENCE_MIN_LEXICAL_OVERLAP=0.15)
    results = _five_hit_ranking(rank4_text=STATUS_TEXT)
    db = _FakeSession({r.chunk_id: r.snippet for r in results})
    blocks = build_synthesis_context_blocks(db, results)
    syn = synthesize_answer_from_evidence(STATUS_QUESTION, blocks, settings)
    assert syn.status == SynthesisStatus.SUCCESS
    from backend.app.models.schemas import Citation

    citation_map = {
        r.chunk_id: Citation(
            citation_id="cite-x",
            chunk_id=r.chunk_id,
            document_id=r.document_id,
            filename=r.filename,
            snippet=r.snippet,
            score=r.score,
        )
        for r in results
    }
    cites = build_citations([syn.source_chunk_id], citation_map)
    assert len(cites) == 1
    assert cites[0].chunk_id == results[3].chunk_id


def test_insufficient_evidence_skips_synthesis_context_use() -> None:
    settings = Settings(EMBEDDING_PROVIDER="fake", EVIDENCE_MIN_LEXICAL_OVERLAP=0.15)
    results = [_result("only-chunk", "flyway rollback database migration", score=0.9)]
    question = "What is the capital of Mars colony Zephyr-9?"
    suff = assess_retrieval_sufficiency(question, results, settings)
    assert suff.sufficient is False


def test_ask_and_agent_share_same_context_builder() -> None:
    import backend.app.agents.orchestrator as agent_mod
    import backend.app.services.generation.ask_service as ask_mod

    assert ask_mod.build_synthesis_context_blocks is agent_mod.build_synthesis_context_blocks
