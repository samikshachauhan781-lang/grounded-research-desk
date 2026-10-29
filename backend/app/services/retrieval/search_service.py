"""Semantic retrieval service."""

import time
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.core.config import Settings
from backend.app.core.exceptions import ModelMismatchError
from backend.app.database.models import Chunk, ChunkEmbedding, CollectionDocument, Document
from backend.app.models.schemas import Citation, SearchResponse, SearchResultItem
from backend.app.providers.embedding import EmbeddingProvider, get_embedding_provider
import numpy as np

from backend.app.rag.vector_search import bytes_to_vector, rank_vectors
from backend.app.services.activity import record_activity


def search_chunks(
    db: Session,
    settings: Settings,
    query: str,
    top_k: int | None = None,
    document_ids: list[str] | None = None,
    collection_id: str | None = None,
    min_score: float | None = None,
    provider: EmbeddingProvider | None = None,
) -> SearchResponse:
    started = time.perf_counter()
    k = top_k or settings.retrieval_top_k
    if min_score is not None:
        threshold: float | None = min_score
    elif settings.embedding_provider == "fake":
        # Fake vectors are not calibrated to semantic similarity cutoffs.
        threshold = None
    else:
        threshold = settings.min_similarity_score
    embedder = provider or get_embedding_provider(settings)

    stmt = (
        select(Chunk, ChunkEmbedding, Document)
        .join(ChunkEmbedding, ChunkEmbedding.chunk_id == Chunk.id)
        .join(Document, Document.id == Chunk.document_id)
        .where(Document.processing_status == "completed")
    )
    if document_ids:
        stmt = stmt.where(Document.id.in_(document_ids))
    if collection_id:
        stmt = stmt.join(
            CollectionDocument,
            CollectionDocument.document_id == Document.id,
        ).where(CollectionDocument.collection_id == collection_id)

    rows = db.execute(stmt).all()
    if not rows:
        duration_ms = (time.perf_counter() - started) * 1000
        return SearchResponse(
            query=query,
            results=[],
            model=embedder.model_name,
            top_k=k,
            duration_ms=round(duration_ms, 2),
        )

    expected_model = embedder.model_name
    candidates: list[tuple[str, np.ndarray]] = []
    meta: dict[str, tuple[Chunk, Document]] = {}
    for chunk, embedding, document in rows:
        if embedding.model_name != expected_model:
            raise ModelMismatchError(
                f"Stored embeddings use {embedding.model_name}; active model is {expected_model}",
            )
        vec = bytes_to_vector(embedding.vector, embedding.dimension)
        candidates.append((chunk.id, vec))
        meta[chunk.id] = (chunk, document)

    query_vec = embedder.embed_texts([query])[0]
    ranked = rank_vectors(query_vec, candidates, top_k=k, min_score=threshold)

    results: list[SearchResultItem] = []
    for chunk_id, score in ranked:
        chunk, document = meta[chunk_id]
        snippet = chunk.text[:500]
        results.append(
            SearchResultItem(
                chunk_id=chunk.id,
                document_id=document.id,
                filename=document.filename,
                snippet=snippet,
                score=round(score, 4),
                char_start=chunk.char_start,
                char_end=chunk.char_end,
            ),
        )

    duration_ms = (time.perf_counter() - started) * 1000
    record_activity(
        db,
        "retrieval_executed",
        {
            "query_id": str(uuid.uuid4()),
            "result_count": len(results),
            "duration_ms": round(duration_ms, 2),
        },
    )
    return SearchResponse(
        query=query,
        results=results,
        model=embedder.model_name,
        top_k=k,
        duration_ms=round(duration_ms, 2),
    )


def search_results_to_citations(results: list[SearchResultItem]) -> list[Citation]:
    citations: list[Citation] = []
    for idx, item in enumerate(results, start=1):
        citations.append(
            Citation(
                citation_id=f"cite-{idx}",
                chunk_id=item.chunk_id,
                document_id=item.document_id,
                filename=item.filename,
                snippet=item.snippet,
                score=item.score,
                char_start=item.char_start,
                char_end=item.char_end,
            ),
        )
    return citations
