"""Document ingest orchestration."""

import uuid
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.core.config import Settings
from backend.app.core.exceptions import (
    DemoModeError,
    NotFoundError,
    PayloadTooLargeError,
    ValidationAppError,
)
from backend.app.database.models import Chunk, ChunkEmbedding, Document, utc_now_iso
from backend.app.providers.embedding import EmbeddingProvider, get_embedding_provider
from backend.app.rag.chunker import chunk_text
from backend.app.rag.text_cleaner import clean_text
from backend.app.rag.vector_search import vector_to_bytes
from backend.app.services.activity import record_activity


def _safe_filename(name: str) -> str:
    base = Path(name).name
    if not base or base in {".", ".."}:
        raise ValidationAppError("Invalid filename")
    return base


def _validate_extension(filename: str, settings: Settings) -> None:
    ext = Path(filename).suffix.lower()
    if ext not in settings.allowed_extensions_list:
        raise ValidationAppError(
            f"Unsupported file type '{ext}'. Allowed: {settings.allowed_extensions_list}",
        )


def ingest_upload(
    db: Session,
    settings: Settings,
    filename: str,
    raw_bytes: bytes,
    provider: EmbeddingProvider | None = None,
) -> Document:
    if not raw_bytes:
        raise ValidationAppError("Uploaded file is empty")
    if len(raw_bytes) > settings.max_upload_bytes:
        raise PayloadTooLargeError(
            f"File exceeds max size of {settings.max_upload_bytes} bytes",
        )

    safe_name = _safe_filename(filename)
    _validate_extension(safe_name, settings)

    try:
        text = raw_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValidationAppError("File must be valid UTF-8 text") from exc

    cleaned = clean_text(text)
    if not cleaned:
        raise ValidationAppError("Document contains no readable text")

    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)

    doc_id = str(uuid.uuid4())
    storage_name = f"{doc_id}_{safe_name}"
    storage_path = upload_dir / storage_name
    storage_path.write_bytes(raw_bytes)

    now = utc_now_iso()
    document = Document(
        id=doc_id,
        filename=safe_name,
        content_text=cleaned,
        storage_path=str(storage_path),
        byte_size=len(raw_bytes),
        processing_status="processing",
        created_at=now,
        updated_at=now,
    )
    db.add(document)
    db.commit()
    record_activity(db, "document_uploaded", {"document_id": doc_id, "filename": safe_name})

    embedder = provider or get_embedding_provider(settings)
    try:
        _process_document(db, document, settings, embedder)
    except Exception as exc:
        document.processing_status = "failed"
        document.processing_error = str(exc)
        document.updated_at = utc_now_iso()
        db.commit()
        raise

    return document


def _process_document(
    db: Session,
    document: Document,
    settings: Settings,
    embedder: EmbeddingProvider,
) -> None:
    db.query(Chunk).filter(Chunk.document_id == document.id).delete()
    db.commit()

    drafts = chunk_text(
        document.content_text,
        settings.chunk_size_chars,
        settings.chunk_overlap_chars,
    )
    if not drafts:
        raise ValidationAppError("Chunking produced no chunks")

    chunk_rows: list[Chunk] = []
    for draft in drafts:
        chunk = Chunk(
            id=str(uuid.uuid4()),
            document_id=document.id,
            chunk_index=draft.chunk_index,
            text=draft.text,
            char_start=draft.char_start,
            char_end=draft.char_end,
            created_at=utc_now_iso(),
        )
        chunk_rows.append(chunk)
        db.add(chunk)
    db.commit()
    record_activity(
        db,
        "chunks_created",
        {"document_id": document.id, "chunk_count": len(chunk_rows)},
    )

    vectors = embedder.embed_texts([c.text for c in chunk_rows])
    if len(vectors) != len(chunk_rows):
        raise ValidationAppError("Embedding count mismatch")

    for chunk, vec in zip(chunk_rows, vectors, strict=True):
        db.add(
            ChunkEmbedding(
                chunk_id=chunk.id,
                model_name=embedder.model_name,
                dimension=embedder.dimension,
                vector=vector_to_bytes(vec),
                created_at=utc_now_iso(),
            ),
        )
    db.commit()
    record_activity(
        db,
        "embeddings_generated",
        {"document_id": document.id, "model": embedder.model_name},
    )

    document.processing_status = "completed"
    document.processing_error = None
    document.updated_at = utc_now_iso()
    db.commit()
    record_activity(db, "document_processing_completed", {"document_id": document.id})


def reprocess_document(
    db: Session,
    settings: Settings,
    document_id: str,
    provider: EmbeddingProvider | None = None,
) -> Document:
    document = db.get(Document, document_id)
    if document is None:
        raise NotFoundError(f"Document {document_id} not found")
    document.processing_status = "processing"
    document.updated_at = utc_now_iso()
    db.commit()
    embedder = provider or get_embedding_provider(settings)
    _process_document(db, document, settings, embedder)
    db.refresh(document)
    return document


def delete_document(db: Session, settings: Settings, document_id: str) -> None:
    if settings.demo_mode:
        raise DemoModeError("Delete disabled in demo mode")
    document = db.get(Document, document_id)
    if document is None:
        raise NotFoundError(f"Document {document_id} not found")
    path = Path(document.storage_path)
    db.delete(document)
    db.commit()
    if path.exists():
        path.unlink(missing_ok=True)
    record_activity(db, "document_deleted", {"document_id": document_id})


def get_chunk_count(db: Session, document_id: str) -> int:
    stmt = select(func.count()).select_from(Chunk).where(Chunk.document_id == document_id)
    return int(db.scalar(stmt) or 0)
