"""Shared retrieval-to-synthesis context for Ask and Agent paths."""

from sqlalchemy.orm import Session

from backend.app.database.models import Chunk
from backend.app.models.schemas import SearchResultItem
from backend.app.rag.evidence_answer import clip_chunk_text_for_synthesis


def build_synthesis_context_blocks(
    db: Session,
    results: list[SearchResultItem],
) -> list[tuple[str, str]]:
    """Pass full chunk text (clipped) to synthesis; same set and order as retrieval hits."""
    blocks: list[tuple[str, str]] = []
    for item in results:
        chunk = db.get(Chunk, item.chunk_id)
        raw = chunk.text if chunk is not None else item.snippet
        blocks.append((item.chunk_id, clip_chunk_text_for_synthesis(raw)))
    return blocks
