"""Ask / RAG answer orchestration."""

import json
import uuid

from sqlalchemy.orm import Session

from backend.app.core.config import Settings
from backend.app.database.models import ResearchSession, SessionMessage, utc_now_iso
from backend.app.models.schemas import AskResponse
from backend.app.providers.llm import (
    build_citations,
    get_generation_provider,
    synthesis_failed,
)
from backend.app.rag.evidence_policy import (
    INSUFFICIENT_EVIDENCE_MESSAGE,
    assess_retrieval_sufficiency,
)
from backend.app.services.activity import record_activity
from backend.app.services.retrieval.search_service import (
    search_chunks,
    search_results_to_citations,
)


def ask_question(
    db: Session,
    settings: Settings,
    question: str,
    request_id: str,
    document_ids: list[str] | None = None,
    top_k: int | None = None,
    session_id: str | None = None,
) -> AskResponse:
    retrieval = search_chunks(
        db,
        settings,
        query=question,
        top_k=top_k,
        document_ids=document_ids,
    )

    retrieval_meta = {
        "model": retrieval.model,
        "top_k": retrieval.top_k,
        "duration_ms": retrieval.duration_ms,
    }

    if not retrieval.results:
        response = AskResponse(
            answer=INSUFFICIENT_EVIDENCE_MESSAGE,
            citations=[],
            insufficient_evidence=True,
            retrieval=retrieval_meta,
            request_id=request_id,
            session_id=session_id,
        )
        _maybe_persist_session(db, session_id, question, response)
        record_activity(db, "answer_generated", {"request_id": request_id, "grounded": False})
        return response

    sufficiency = assess_retrieval_sufficiency(question, retrieval.results, settings)
    if not sufficiency.sufficient:
        response = AskResponse(
            answer=INSUFFICIENT_EVIDENCE_MESSAGE,
            citations=[],
            insufficient_evidence=True,
            retrieval={
                **retrieval_meta,
                "sufficiency_reason": sufficiency.reason,
                "lexical_overlap": sufficiency.lexical_overlap,
                "top_score": sufficiency.top_score,
            },
            request_id=request_id,
            session_id=session_id,
        )
        _maybe_persist_session(db, session_id, question, response)
        record_activity(
            db,
            "answer_generated",
            {"request_id": request_id, "grounded": False, "reason": sufficiency.reason},
        )
        return response

    citations = search_results_to_citations(retrieval.results)
    citation_map = {c.chunk_id: c for c in citations}

    context_blocks = [(r.chunk_id, r.snippet) for r in retrieval.results]
    provider = get_generation_provider(settings)
    synthesis = provider.generate_answer(
        question,
        context_blocks,
        settings.generation_timeout_seconds,
    )

    if synthesis_failed(synthesis) or not synthesis.source_chunk_id:
        response = AskResponse(
            answer=INSUFFICIENT_EVIDENCE_MESSAGE,
            citations=[],
            insufficient_evidence=True,
            retrieval={
                **retrieval_meta,
                "synthesis_reason": synthesis.reason,
            },
            request_id=request_id,
            session_id=session_id,
        )
        _maybe_persist_session(db, session_id, question, response)
        record_activity(
            db,
            "answer_generated",
            {
                "request_id": request_id,
                "grounded": False,
                "reason": synthesis.reason,
            },
        )
        return response

    answer_text = synthesis.answer
    valid_ids = [synthesis.source_chunk_id]
    final_citations = build_citations(valid_ids, citation_map)

    response = AskResponse(
        answer=answer_text,
        citations=final_citations,
        insufficient_evidence=False,
        retrieval=retrieval_meta,
        request_id=request_id,
        session_id=session_id,
    )
    _maybe_persist_session(db, session_id, question, response)
    record_activity(
        db,
        "answer_generated",
        {"request_id": request_id, "citation_count": len(final_citations)},
    )
    return response


def _maybe_persist_session(
    db: Session,
    session_id: str | None,
    question: str,
    response: AskResponse,
) -> None:
    if not session_id:
        return
    session = db.get(ResearchSession, session_id)
    if session is None:
        return
    message = SessionMessage(
        id=str(uuid.uuid4()),
        session_id=session_id,
        role="user",
        question=question,
        answer=response.answer,
        citations_json=json.dumps([c.model_dump() for c in response.citations]),
        created_at=utc_now_iso(),
    )
    session.updated_at = utc_now_iso()
    db.add(message)
    db.commit()
