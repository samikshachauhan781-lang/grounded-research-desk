"""Search API."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.core.config import Settings
from backend.app.core.dependencies import get_db, settings_dep
from backend.app.models.schemas import SearchRequest, SearchResponse
from backend.app.services.retrieval.search_service import search_chunks

router = APIRouter(prefix="/search", tags=["search"])


@router.post("", response_model=SearchResponse)
def search(
    payload: SearchRequest,
    db: Session = Depends(get_db),
    settings: Settings = Depends(settings_dep),
) -> SearchResponse:
    return search_chunks(
        db,
        settings,
        query=payload.query,
        top_k=payload.top_k,
        document_ids=payload.document_ids,
        collection_id=payload.collection_id,
        min_score=payload.min_score,
    )
