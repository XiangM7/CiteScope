from __future__ import annotations

from app.core.config import settings
from app.utils.text import split_paragraphs, tail_overlap, safe_json_dumps


def _chunk_paragraphs(paragraphs: list[str], chunk_size_chars: int, overlap_chars: int) -> list[str]:
    chunks: list[str] = []
    current = ""

    for paragraph in paragraphs:
        candidate = f"{current}\n\n{paragraph}".strip() if current else paragraph
        if len(candidate) <= chunk_size_chars:
            current = candidate
            continue

        if current:
            chunks.append(current.strip())
            overlap = tail_overlap(current, overlap_chars)
            current = f"{overlap}\n\n{paragraph}".strip()
            if len(current) > chunk_size_chars and paragraph:
                chunks.append(paragraph[:chunk_size_chars].strip())
                current = paragraph[max(0, chunk_size_chars - overlap_chars) :].strip()
        else:
            chunks.append(paragraph[:chunk_size_chars].strip())
            current = paragraph[max(0, chunk_size_chars - overlap_chars) :].strip()

    if current.strip():
        chunks.append(current.strip())

    return [chunk for chunk in chunks if chunk]


def build_chunks(
    *,
    document_id: int,
    title: str,
    source_type: str,
    source_path: str,
    sections: list[dict[str, object]],
    chunk_size_chars: int | None = None,
    overlap_chars: int | None = None,
) -> list[dict[str, object]]:
    chunk_size_chars = chunk_size_chars or settings.chunk_size_chars
    overlap_chars = overlap_chars or settings.chunk_overlap_chars

    chunks: list[dict[str, object]] = []
    chunk_index = 0

    for section in sections:
        text = str(section.get("text", "")).strip()
        if not text:
            continue

        page_number = section.get("page_number")
        section_title = section.get("section_title")
        paragraphs = split_paragraphs(text)
        text_chunks = _chunk_paragraphs(paragraphs, chunk_size_chars=chunk_size_chars, overlap_chars=overlap_chars)

        for chunk_text in text_chunks:
            metadata = {
                "document_id": document_id,
                "chunk_index": chunk_index,
                "page_number": page_number,
                "source_type": source_type,
                "title": title,
                "source_path": source_path,
                "section_title": section_title,
            }
            chunks.append(
                {
                    "chunk_text": chunk_text,
                    "chunk_index": chunk_index,
                    "page_number": page_number,
                    "section_title": section_title,
                    "metadata_json": safe_json_dumps(metadata),
                }
            )
            chunk_index += 1

    return chunks
