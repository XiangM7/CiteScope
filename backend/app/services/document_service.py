from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.models.chunk import Chunk
from app.models.document import Document
from app.models.eval_case import EvalCase
from app.models.eval_result import EvalResult
from app.services.chunking import build_chunks
from app.services.eval_service import ensure_eval_cases_for_document
from app.services.pdf_parser import parse_pdf
from app.services.vector_store import vector_store
from app.services.web_parser import parse_web_page
from app.utils.text import safe_json_loads


def create_uploaded_document(db: Session, file: UploadFile, uploads_dir: Path) -> Document:
    filename = file.filename or "document.pdf"
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF uploads are supported.")

    safe_name = f"{uuid4().hex}_{Path(filename).name}"
    destination = uploads_dir / safe_name
    contents = file.file.read()
    destination.write_bytes(contents)

    document = Document(
        title=Path(filename).stem,
        source_type="pdf",
        source_path=str(destination),
        status="uploaded",
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    return document


def create_web_document(db: Session, url: str) -> Document:
    document = Document(title=url, source_type="web", source_path=url, status="uploaded")
    db.add(document)
    db.commit()
    db.refresh(document)
    return document


def get_document_or_404(db: Session, document_id: int) -> Document:
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found.")
    return document


def index_document(db: Session, document: Document) -> Document:
    try:
        _clear_existing_document_chunks(db, document.id)

        if document.source_type == "pdf":
            parsed = parse_pdf(document.source_path)
        elif document.source_type == "web":
            parsed = parse_web_page(document.source_path)
        else:
            raise ValueError(f"Unsupported source type: {document.source_type}")

        document.title = _resolve_document_title(document, str(parsed["title"]))
        document.status = "parsed"
        db.add(document)
        db.flush()

        chunk_payloads = build_chunks(
            document_id=document.id,
            title=document.title,
            source_type=document.source_type,
            source_path=document.source_path,
            sections=list(parsed["sections"]),
        )
        if not chunk_payloads:
            raise ValueError("No chunks could be created from the parsed document.")

        chunk_models: list[Chunk] = []
        for payload in chunk_payloads:
            chunk = Chunk(document_id=document.id, **payload)
            db.add(chunk)
            chunk_models.append(chunk)

        db.flush()

        vector_rows = []
        for chunk in chunk_models:
            metadata = safe_json_loads(chunk.metadata_json, {}) or {}
            vector_rows.append({"id": chunk.id, "chunk_text": chunk.chunk_text, "metadata": metadata})
        vector_store.upsert_chunks(vector_rows)

        document.status = "indexed"
        db.add(document)
        db.commit()
        db.refresh(document)

        ensure_eval_cases_for_document(db, document)
        db.refresh(document)
        return document
    except Exception as exc:
        document.status = "failed"
        db.add(document)
        db.commit()
        raise HTTPException(status_code=500, detail=f"Indexing failed: {exc}") from exc


def _clear_existing_document_chunks(db: Session, document_id: int) -> None:
    eval_case_ids = [
        eval_case_id
        for (eval_case_id,) in db.query(EvalCase.id).filter(EvalCase.expected_document_id == document_id).all()
    ]
    if eval_case_ids:
        db.query(EvalResult).filter(EvalResult.eval_case_id.in_(eval_case_ids)).delete(synchronize_session=False)
    vector_store.delete_document_chunks(document_id)
    db.query(EvalCase).filter(EvalCase.expected_document_id == document_id).delete(synchronize_session=False)
    db.query(Chunk).filter(Chunk.document_id == document_id).delete(synchronize_session=False)
    db.commit()


def _resolve_document_title(document: Document, parsed_title: str) -> str:
    cleaned_title = parsed_title.strip()
    if document.source_type == "web":
        return cleaned_title or document.title

    storage_stem = Path(document.source_path).stem
    if not cleaned_title or cleaned_title == storage_stem:
        return document.title
    return cleaned_title
