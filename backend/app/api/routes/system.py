"""Public settings and system status."""

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.core.config import Settings
from backend.app.core.dependencies import get_db, settings_dep
from backend.app.database.models import ActivityEvent, Chunk, Document
from backend.app.models.schemas import PublicSettingsResponse, SystemStatusResponse

router = APIRouter(tags=["system"])


@router.get("/settings/public", response_model=PublicSettingsResponse)
def public_settings(settings: Settings = Depends(settings_dep)) -> PublicSettingsResponse:
    return PublicSettingsResponse(
        app_name=settings.app_name,
        app_env=settings.app_env,
        embedding_provider=settings.embedding_provider,
        embedding_model_name=settings.embedding_model_name,
        llm_provider=settings.llm_provider,
        retrieval_top_k=settings.retrieval_top_k,
        max_upload_bytes=settings.max_upload_bytes,
        allowed_upload_extensions=settings.allowed_extensions_list,
        demo_mode=settings.demo_mode,
        agent_enabled=settings.agent_enabled,
    )


@router.get("/system/status", response_model=SystemStatusResponse)
def system_status(
    db: Session = Depends(get_db),
    settings: Settings = Depends(settings_dep),
) -> SystemStatusResponse:
    doc_count = int(db.scalar(select(func.count()).select_from(Document)) or 0)
    chunk_count = int(db.scalar(select(func.count()).select_from(Chunk)) or 0)
    return SystemStatusResponse(
        status="ok",
        database="ok",
        document_count=doc_count,
        chunk_count=chunk_count,
        embedding_model=settings.embedding_model_name,
        llm_provider=settings.llm_provider,
        version=settings.app_version,
    )


@router.get("/activity")
def list_activity(db: Session = Depends(get_db), limit: int = 50) -> dict:
    import json

    events = (
        db.query(ActivityEvent)
        .order_by(ActivityEvent.created_at.desc())
        .limit(limit)
        .all()
    )
    return {
        "items": [
            {
                "id": e.id,
                "event_type": e.event_type,
                "payload": json.loads(e.payload_json),
                "created_at": e.created_at,
            }
            for e in events
        ],
    }
