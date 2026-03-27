from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.document import Document
from app.models.query_log import QueryLog
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.answer_service import answer_question
from app.services.retrieval_service import retrieve_chunks
from app.utils.text import safe_json_dumps


router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/ask", response_model=ChatResponse)
def ask_question(payload: ChatRequest, db: Session = Depends(get_db)) -> ChatResponse:
    indexed_count = db.query(Document).filter(Document.status == "indexed").count()
    if indexed_count == 0:
        raise HTTPException(status_code=400, detail="Index at least one source before asking questions.")

    retrieved_chunks = retrieve_chunks(db, payload.question, payload.top_k)
    answer_payload = answer_question(payload.question, retrieved_chunks)

    query_log = QueryLog(
        question=payload.question,
        retrieved_chunk_ids=safe_json_dumps([chunk["chunk_id"] for chunk in retrieved_chunks]),
        answer_text=answer_payload["answer"],
        citation_json=safe_json_dumps(answer_payload["citations"]),
    )
    db.add(query_log)
    db.commit()
    db.refresh(query_log)

    return ChatResponse(
        answer=answer_payload["answer"],
        citations=answer_payload["citations"],
        retrieved_chunks=retrieved_chunks,
        query_log_id=query_log.id,
        created_at=query_log.created_at or datetime.utcnow(),
    )
