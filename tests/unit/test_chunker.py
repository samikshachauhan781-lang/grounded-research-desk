"""Chunker unit tests."""

from backend.app.rag.chunker import chunk_text


def test_chunk_overlap_preserves_boundary_sentence() -> None:
    text = "A" * 700 + " BOUNDARY_FACT " + "B" * 700
    chunks = chunk_text(text, chunk_size=800, overlap=120)
    assert len(chunks) >= 2
    joined = " ".join(c.text for c in chunks)
    assert "BOUNDARY_FACT" in joined


def test_short_document_single_chunk() -> None:
    chunks = chunk_text("short doc", chunk_size=800, overlap=120)
    assert len(chunks) == 1
    assert chunks[0].text == "short doc"
