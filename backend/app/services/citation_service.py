from __future__ import annotations


def build_citations(
    retrieved_chunks: list[dict[str, object]],
    cited_chunk_ids: list[int] | None = None,
) -> list[dict[str, object]]:
    cited_chunk_ids = cited_chunk_ids or []
    if cited_chunk_ids:
        selected = [chunk for chunk in retrieved_chunks if int(chunk["chunk_id"]) in set(cited_chunk_ids)]
    else:
        selected = []

    deduped: list[dict[str, object]] = []
    seen: set[int] = set()

    for chunk in selected:
        chunk_id = int(chunk["chunk_id"])
        if chunk_id in seen:
            continue
        seen.add(chunk_id)
        deduped.append(
            {
                "chunk_id": chunk_id,
                "document_id": int(chunk["document_id"]),
                "document_title": str(chunk["document_title"]),
                "page_number": chunk["page_number"],
                "source_type": str(chunk["source_type"]),
                "source_path": str(chunk["source_path"]),
            }
        )

    return deduped
