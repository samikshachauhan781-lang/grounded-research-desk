"""Bounded research agent orchestrator."""

import json
import time
import uuid

from sqlalchemy.orm import Session

from backend.app.agents.tools import (
    tool_compare_evidence,
    tool_get_chunk,
    tool_list_documents,
    tool_search_chunks,
)
from backend.app.core.config import Settings
from backend.app.core.exceptions import AgentBudgetExceededError, AgentDisabledError
from backend.app.database.models import AgentRun, utc_now_iso
from backend.app.models.schemas import AgentStep, Citation, ResearchResponse
from backend.app.providers.llm import build_citations, get_generation_provider
from backend.app.rag.evidence_policy import (
    INSUFFICIENT_EVIDENCE_MESSAGE,
    assess_retrieval_sufficiency,
)
from backend.app.services.activity import record_activity
from backend.app.services.retrieval.search_service import (
    search_chunks,
    search_results_to_citations,
)


def run_research(
    db: Session,
    settings: Settings,
    goal: str,
    request_id: str,
    document_ids: list[str] | None = None,
) -> ResearchResponse:
    if not settings.agent_enabled:
        raise AgentDisabledError("Agent is disabled. Set AGENT_ENABLED=true to enable.")

    run_id = str(uuid.uuid4())
    started = time.perf_counter()
    steps: list[AgentStep] = []
    tool_calls = 0

    run = AgentRun(
        id=run_id,
        goal=goal,
        status="running",
        created_at=utc_now_iso(),
    )
    db.add(run)
    db.commit()

    def check_budget() -> None:
        elapsed = time.perf_counter() - started
        if tool_calls >= settings.agent_max_tool_calls:
            raise AgentBudgetExceededError("Maximum tool calls exceeded")
        if elapsed > settings.agent_max_wall_clock_seconds:
            raise AgentBudgetExceededError("Agent wall-clock timeout exceeded")

    check_budget()
    docs = tool_list_documents(db, limit=20)
    tool_calls += 1
    steps.append(
        AgentStep(
            step_index=1,
            tool="list_documents",
            tool_input={"limit": 20},
            observation_summary=f"{len(docs['documents'])} documents",
        ),
    )

    check_budget()
    search = tool_search_chunks(db, settings, goal, top_k=5, document_ids=document_ids)
    tool_calls += 1
    steps.append(
        AgentStep(
            step_index=2,
            tool="search_chunks",
            tool_input={"query": goal, "top_k": 5},
            observation_summary=f"{len(search['results'])} hits",
        ),
    )

    snippets = [item["snippet"] for item in search["results"]]
    if snippets:
        check_budget()
        compare = tool_compare_evidence(snippets)
        tool_calls += 1
        steps.append(
            AgentStep(
                step_index=3,
                tool="compare_evidence",
                tool_input={"count": len(snippets)},
                observation_summary=compare["summary"][:200],
            ),
        )

    retrieval = search_chunks(db, settings, goal, top_k=5, document_ids=document_ids)
    citations = search_results_to_citations(retrieval.results)
    citation_map = {c.chunk_id: c for c in citations}

    if not retrieval.results:
        answer = INSUFFICIENT_EVIDENCE_MESSAGE
        run.status = "completed"
        run.answer = answer
        run.steps_json = json.dumps([s.model_dump() for s in steps])
        run.completed_at = utc_now_iso()
        db.commit()
        record_activity(db, "agent_run_completed", {"run_id": run_id, "status": run.status})
        return ResearchResponse(
            answer=answer,
            citations=[],
            steps=steps,
            status="completed",
            request_id=request_id,
        )

    sufficiency = assess_retrieval_sufficiency(goal, retrieval.results, settings)
    if not sufficiency.sufficient:
        answer = INSUFFICIENT_EVIDENCE_MESSAGE
        run.status = "completed"
        run.answer = answer
        run.steps_json = json.dumps([s.model_dump() for s in steps])
        run.completed_at = utc_now_iso()
        db.commit()
        record_activity(
            db,
            "agent_run_completed",
            {"run_id": run_id, "status": run.status, "reason": sufficiency.reason},
        )
        return ResearchResponse(
            answer=answer,
            citations=[],
            steps=steps,
            status="completed",
            request_id=request_id,
        )

    context_blocks: list[tuple[str, str]] = []
    for result in retrieval.results[:3]:
        chunk = tool_get_chunk(db, result.chunk_id)
        context_blocks.append((chunk["chunk_id"], chunk["text"][:2000]))
        tool_calls += 1
        check_budget()

    provider = get_generation_provider(settings)
    answer, cited_ids = provider.generate_answer(
        goal,
        context_blocks,
        settings.generation_timeout_seconds,
    )
    if not cited_ids and retrieval.results:
        cited_ids = [retrieval.results[0].chunk_id]
    final_citations = build_citations(cited_ids, citation_map)

    steps.append(
        AgentStep(
            step_index=len(steps) + 1,
            tool="assemble_cited_answer",
            tool_input={"goal": goal[:120]},
            observation_summary=f"{len(final_citations)} citations",
        ),
    )

    run.status = "completed"
    run.answer = answer
    run.citations_json = json.dumps([c.model_dump() for c in final_citations])
    run.steps_json = json.dumps([s.model_dump() for s in steps])
    run.completed_at = utc_now_iso()
    db.commit()
    record_activity(db, "agent_run_completed", {"run_id": run_id, "status": "completed"})

    return ResearchResponse(
        answer=answer,
        citations=final_citations,
        steps=steps,
        status="completed",
        request_id=request_id,
    )
