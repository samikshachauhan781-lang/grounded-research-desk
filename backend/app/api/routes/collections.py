"""Collections API."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.core.dependencies import get_db
from backend.app.models.schemas import (
    CollectionCreate,
    CollectionDocumentRequest,
    CollectionResponse,
    CollectionUpdate,
)
from backend.app.services import collections as collection_service

router = APIRouter(prefix="/collections", tags=["collections"])


@router.post("", response_model=CollectionResponse, status_code=201)
def create_collection(payload: CollectionCreate, db: Session = Depends(get_db)) -> CollectionResponse:
    collection = collection_service.create_collection(db, payload.name, payload.description)
    return CollectionResponse(
        collection_id=collection.id,
        name=collection.name,
        description=collection.description,
        document_count=0,
        created_at=collection.created_at,
    )


@router.get("", response_model=list[CollectionResponse])
def list_collections(db: Session = Depends(get_db)) -> list[CollectionResponse]:
    rows = collection_service.list_collections(db)
    return [
        CollectionResponse(
            collection_id=c.id,
            name=c.name,
            description=c.description,
            document_count=int(count),
            created_at=c.created_at,
        )
        for c, count in rows
    ]


@router.get("/{collection_id}", response_model=CollectionResponse)
def get_collection(collection_id: str, db: Session = Depends(get_db)) -> CollectionResponse:
    collection = collection_service.get_collection(db, collection_id)
    count = len(collection.documents)
    return CollectionResponse(
        collection_id=collection.id,
        name=collection.name,
        description=collection.description,
        document_count=count,
        created_at=collection.created_at,
    )


@router.patch("/{collection_id}", response_model=CollectionResponse)
def patch_collection(
    collection_id: str,
    payload: CollectionUpdate,
    db: Session = Depends(get_db),
) -> CollectionResponse:
    collection = collection_service.update_collection(
        db,
        collection_id,
        payload.name,
        payload.description,
    )
    return CollectionResponse(
        collection_id=collection.id,
        name=collection.name,
        description=collection.description,
        document_count=len(collection.documents),
        created_at=collection.created_at,
    )


@router.delete("/{collection_id}", status_code=204)
def delete_collection_route(collection_id: str, db: Session = Depends(get_db)) -> None:
    collection_service.delete_collection(db, collection_id)


@router.post("/{collection_id}/documents", status_code=204)
def add_document(
    collection_id: str,
    payload: CollectionDocumentRequest,
    db: Session = Depends(get_db),
) -> None:
    collection_service.add_document_to_collection(db, collection_id, payload.document_id)


@router.delete("/{collection_id}/documents/{document_id}", status_code=204)
def remove_document(
    collection_id: str,
    document_id: str,
    db: Session = Depends(get_db),
) -> None:
    collection_service.remove_document_from_collection(db, collection_id, document_id)
