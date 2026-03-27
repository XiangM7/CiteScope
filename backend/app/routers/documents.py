from __future__ import annotations

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.models.document import Document
from app.schemas.document import DocumentDetailResponse, DocumentResponse, WebDocumentCreate
from app.services.document_service import (
    create_uploaded_document,
    create_web_document,
    get_document_or_404,
    index_document,
)


router = APIRouter(prefix="/documents", tags=["documents"])


def _document_payload(document: Document) -> dict[str, object]:
    return {
        "id": document.id,
        "title": document.title,
        "source_type": document.source_type,
        "source_path": document.source_path,
        "status": document.status,
        "created_at": document.created_at,
        "chunk_count": len(document.chunks),
    }


@router.post("/upload", response_model=DocumentResponse)
def upload_document(file: UploadFile = File(...), db: Session = Depends(get_db)) -> DocumentResponse:
    document = create_uploaded_document(db, file, settings.uploads_dir)
    return DocumentResponse.model_validate(_document_payload(document))


@router.post("/web", response_model=DocumentResponse)
def add_web_document(payload: WebDocumentCreate, db: Session = Depends(get_db)) -> DocumentResponse:
    document = create_web_document(db, payload.url)
    return DocumentResponse.model_validate(_document_payload(document))


@router.get("", response_model=list[DocumentResponse])
def list_documents(db: Session = Depends(get_db)) -> list[DocumentResponse]:
    documents = db.query(Document).order_by(Document.created_at.desc()).all()
    return [DocumentResponse.model_validate(_document_payload(document)) for document in documents]


@router.get("/{document_id}", response_model=DocumentDetailResponse)
def get_document(document_id: int, db: Session = Depends(get_db)) -> DocumentDetailResponse:
    document = get_document_or_404(db, document_id)
    payload = {**_document_payload(document), "chunks": document.chunks}
    return DocumentDetailResponse.model_validate(payload)


@router.post("/{document_id}/index", response_model=DocumentResponse)
def index_document_route(document_id: int, db: Session = Depends(get_db)) -> DocumentResponse:
    document = get_document_or_404(db, document_id)
    indexed_document = index_document(db, document)
    return DocumentResponse.model_validate(_document_payload(indexed_document))
