"""Agent tool implementations."""

from sqlalchemy.orm import Session

from backend.app.core.config import Settings
from backend.app.core.exceptions import NotFoundError
from backend.app.database.models import Chunk, Document
from backend.app.services.retrieval.search_service import search_chunks


def tool_list_documents(db: Session, limit: int = 50) -> dict:
    rows = db.query(Document).order_by(Document.created_at.desc()).limit(limit).all()
    return {
        "documents": [
            {"id": d.id, "filename": d.filename, "created_at": d.created_at}
            for d in rows
        ],
    }


def tool_search_chunks(
    db: Session,
    settings: Settings,
    query: str,
    top_k: int = 5,
    document_ids: list[str] | None = None,
) -> dict:
    response = search_chunks(
        db,
        settings,
        query=query,
        top_k=top_k,
        document_ids=document_ids,
    )
    return {
        "results": [
            {
                "chunk_id": r.chunk_id,
                "document_id": r.document_id,
                "score": r.score,
                "snippet": r.snippet,
            }
            for r in response.results
        ],
    }


def tool_get_chunk(db: Session, chunk_id: str) -> dict:
    chunk = db.get(Chunk, chunk_id)
    if chunk is None:
        raise NotFoundError(f"Chunk {chunk_id} not found")
    return {
        "chunk_id": chunk.id,
        "document_id": chunk.document_id,
        "index": chunk.chunk_index,
        "text": chunk.text,
    }


def tool_compare_evidence(snippets: list[str]) -> dict:
    unique = list(dict.fromkeys(snippets))
    return {
        "unique_count": len(unique),
        "summary": " | ".join(s[:120] for s in unique[:3]),
    }
