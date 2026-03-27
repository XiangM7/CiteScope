from __future__ import annotations

from typing import Any

import chromadb
from chromadb.config import Settings as ChromaClientSettings

from app.core.config import settings
from app.services.embedding_service import embedding_service


class VectorStore:
    def __init__(self) -> None:
        self.client = chromadb.PersistentClient(
            path=str(settings.chroma_dir),
            settings=ChromaClientSettings(
                anonymized_telemetry=False,
                chroma_product_telemetry_impl="app.services.chroma_noop_telemetry.NoOpProductTelemetry",
                chroma_telemetry_impl="app.services.chroma_noop_telemetry.NoOpProductTelemetry",
            ),
        )
        self.collection = self.client.get_or_create_collection(
            name="citescope_chunks",
            metadata={"hnsw:space": "cosine"},
        )

    def upsert_chunks(self, chunk_rows: list[dict[str, Any]]) -> None:
        if not chunk_rows:
            return

        ids = [str(row["id"]) for row in chunk_rows]
        documents = [row["chunk_text"] for row in chunk_rows]
        metadatas = [self._sanitize_metadata(row["metadata"]) for row in chunk_rows]
        embeddings = embedding_service.embed_texts(documents)

        self.collection.upsert(ids=ids, documents=documents, metadatas=metadatas, embeddings=embeddings)

    def query(self, question: str, top_k: int) -> dict[str, list[list[Any]]]:
        collection_count = self.collection.count()
        if collection_count == 0:
            return {"ids": [[]], "distances": [[]], "documents": [[]], "metadatas": [[]]}

        query_embedding = embedding_service.embed_query(question)
        return self.collection.query(
            query_embeddings=[query_embedding],
            n_results=min(top_k, collection_count),
            include=["documents", "metadatas", "distances"],
        )

    def delete_document_chunks(self, document_id: int) -> None:
        self.collection.delete(where={"document_id": document_id})

    def _sanitize_metadata(self, metadata: dict[str, Any]) -> dict[str, Any]:
        sanitized: dict[str, Any] = {}
        for key, value in metadata.items():
            if value is None:
                continue
            if isinstance(value, (str, int, float, bool)):
                sanitized[key] = value
            else:
                sanitized[key] = str(value)
        return sanitized


vector_store = VectorStore()
