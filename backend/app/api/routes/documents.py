"""Document API routes."""

from fastapi import APIRouter, Depends, File, Query, UploadFile
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.core.config import Settings
from backend.app.core.dependencies import get_db, settings_dep
from backend.app.core.exceptions import ValidationAppError
from backend.app.database.models import Chunk, Document
from backend.app.models.schemas import (
    ChunkItem,
    ChunkListResponse,
    DocumentContentResponse,
    DocumentDetailResponse,
    DocumentListItem,
    DocumentListResponse,
    DocumentUploadResponse,
)
from backend.app.services.ingest.pipeline import (
    delete_document,
    get_chunk_count,
    ingest_upload,
    reprocess_document,
)

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("", response_model=DocumentUploadResponse, status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    settings: Settings = Depends(settings_dep),
) -> DocumentUploadResponse:
    if not file.filename:
        raise ValidationAppError("Missing filename")
    raw = await file.read()
    document = ingest_upload(db, settings, file.filename, raw)
    chunk_count = get_chunk_count(db, document.id)
    status = "indexed" if document.processing_status == "completed" else document.processing_status
    return DocumentUploadResponse(
        document_id=document.id,
        filename=document.filename,
        chunk_count=chunk_count,
        status=status,
    )


@router.get("", response_model=DocumentListResponse)
def list_documents(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> DocumentListResponse:
    total = db.scalar(select(func.count()).select_from(Document)) or 0
    docs = (
        db.query(Document)
        .order_by(Document.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    items = [
        DocumentListItem(
            document_id=d.id,
            filename=d.filename,
            created_at=d.created_at,
            chunk_count=get_chunk_count(db, d.id),
            processing_status=d.processing_status,
        )
        for d in docs
    ]
    return DocumentListResponse(items=items, total=int(total))


@router.get("/{document_id}", response_model=DocumentDetailResponse)
def get_document(document_id: str, db: Session = Depends(get_db)) -> DocumentDetailResponse:
    document = db.get(Document, document_id)
    if document is None:
        from backend.app.core.exceptions import NotFoundError

        raise NotFoundError(f"Document {document_id} not found")
    preview = document.content_text[:400] if document.content_text else None
    return DocumentDetailResponse(
        document_id=document.id,
        filename=document.filename,
        created_at=document.created_at,
        updated_at=document.updated_at,
        byte_size=document.byte_size,
        chunk_count=get_chunk_count(db, document.id),
        processing_status=document.processing_status,
        processing_error=document.processing_error,
        preview=preview,
    )


@router.get("/{document_id}/content", response_model=DocumentContentResponse)
def get_document_content(document_id: str, db: Session = Depends(get_db)) -> DocumentContentResponse:
    document = db.get(Document, document_id)
    if document is None:
        from backend.app.core.exceptions import NotFoundError

        raise NotFoundError(f"Document {document_id} not found")
    return DocumentContentResponse(
        document_id=document.id,
        filename=document.filename,
        content_text=document.content_text,
    )


@router.get("/{document_id}/chunks", response_model=ChunkListResponse)
def get_document_chunks(document_id: str, db: Session = Depends(get_db)) -> ChunkListResponse:
    document = db.get(Document, document_id)
    if document is None:
        from backend.app.core.exceptions import NotFoundError

        raise NotFoundError(f"Document {document_id} not found")
    chunks = (
        db.query(Chunk)
        .filter(Chunk.document_id == document_id)
        .order_by(Chunk.chunk_index.asc())
        .all()
    )
    items = [
        ChunkItem(
            chunk_id=c.id,
            chunk_index=c.chunk_index,
            text=c.text,
            char_start=c.char_start,
            char_end=c.char_end,
        )
        for c in chunks
    ]
    return ChunkListResponse(document_id=document_id, items=items, total=len(items))


@router.post("/{document_id}/reprocess", response_model=DocumentUploadResponse)
def reprocess(document_id: str, db: Session = Depends(get_db), settings: Settings = Depends(settings_dep)):
    document = reprocess_document(db, settings, document_id)
    return DocumentUploadResponse(
        document_id=document.id,
        filename=document.filename,
        chunk_count=get_chunk_count(db, document.id),
        status="indexed" if document.processing_status == "completed" else document.processing_status,
    )


@router.delete("/{document_id}", status_code=204)
def remove_document(
    document_id: str,
    db: Session = Depends(get_db),
    settings: Settings = Depends(settings_dep),
) -> None:
    delete_document(db, settings, document_id)
