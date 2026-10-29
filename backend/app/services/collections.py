"""Collection management."""

import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from sqlalchemy import select

from backend.app.core.exceptions import NotFoundError
from backend.app.database.models import Collection, CollectionDocument, Document, utc_now_iso


def create_collection(db: Session, name: str, description: str = "") -> Collection:
    now = utc_now_iso()
    collection = Collection(
        id=str(uuid.uuid4()),
        name=name,
        description=description,
        created_at=now,
        updated_at=now,
    )
    db.add(collection)
    db.commit()
    db.refresh(collection)
    return collection


def list_collections(db: Session) -> list[tuple[Collection, int]]:
    stmt = (
        select(Collection, func.count(CollectionDocument.document_id))
        .outerjoin(CollectionDocument, CollectionDocument.collection_id == Collection.id)
        .group_by(Collection.id)
        .order_by(Collection.created_at.desc())
    )
    return list(db.execute(stmt).all())


def get_collection(db: Session, collection_id: str) -> Collection:
    collection = db.get(Collection, collection_id)
    if collection is None:
        raise NotFoundError(f"Collection {collection_id} not found")
    return collection


def update_collection(
    db: Session,
    collection_id: str,
    name: str | None,
    description: str | None,
) -> Collection:
    collection = get_collection(db, collection_id)
    if name is not None:
        collection.name = name
    if description is not None:
        collection.description = description
    collection.updated_at = utc_now_iso()
    db.commit()
    db.refresh(collection)
    return collection


def delete_collection(db: Session, collection_id: str) -> None:
    collection = get_collection(db, collection_id)
    db.delete(collection)
    db.commit()


def add_document_to_collection(db: Session, collection_id: str, document_id: str) -> None:
    get_collection(db, collection_id)
    document = db.get(Document, document_id)
    if document is None:
        raise NotFoundError(f"Document {document_id} not found")
    existing = db.execute(
        select(CollectionDocument).where(
            CollectionDocument.collection_id == collection_id,
            CollectionDocument.document_id == document_id,
        ),
    ).scalar_one_or_none()
    if existing:
        return
    db.add(
        CollectionDocument(
            collection_id=collection_id,
            document_id=document_id,
            added_at=utc_now_iso(),
        ),
    )
    db.commit()


def remove_document_from_collection(db: Session, collection_id: str, document_id: str) -> None:
    row = db.execute(
        select(CollectionDocument).where(
            CollectionDocument.collection_id == collection_id,
            CollectionDocument.document_id == document_id,
        ),
    ).scalar_one_or_none()
    if row is None:
        raise NotFoundError("Document not in collection")
    db.delete(row)
    db.commit()
