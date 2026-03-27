from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.chunk import Chunk
from app.models.document import Document
from app.services.vector_store import vector_store


def retrieve_chunks(db: Session, question: str, top_k: int | None = None) -> list[dict[str, object]]:
    target_k = top_k or settings.retrieval_top_k
    raw_results = vector_store.query(question, target_k)

    ids = [int(chunk_id) for chunk_id in raw_results.get("ids", [[]])[0] if chunk_id is not None]
    distances = raw_results.get("distances", [[]])[0]
    if not ids:
        return []

    chunk_records = db.query(Chunk).join(Document).filter(Chunk.id.in_(ids)).all()
    chunk_map = {chunk.id: chunk for chunk in chunk_records}

    retrieved: list[dict[str, object]] = []
    for index, chunk_id in enumerate(ids):
        chunk = chunk_map.get(chunk_id)
        if not chunk:
            continue
        distance = float(distances[index]) if index < len(distances) else 1.0
        score = max(0.0, 1.0 - distance)
        retrieved.append(
            {
                "chunk_id": chunk.id,
                "document_id": chunk.document_id,
                "document_title": chunk.document.title,
                "chunk_text": chunk.chunk_text,
                "chunk_index": chunk.chunk_index,
                "page_number": chunk.page_number,
                "section_title": chunk.section_title,
                "score": round(score, 4),
                "source_type": chunk.document.source_type,
                "source_path": chunk.document.source_path,
            }
        )
    return retrieved
