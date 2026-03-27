from __future__ import annotations

from typing import Any

import httpx
import numpy as np
from sklearn.feature_extraction.text import HashingVectorizer

from app.core.config import settings


class EmbeddingService:
    def __init__(self) -> None:
        self.vectorizer = HashingVectorizer(
            n_features=settings.hashing_dimensions,
            alternate_sign=False,
            norm=None,
            ngram_range=(1, 2),
            lowercase=True,
        )

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        provider = settings.embedding_provider.lower()
        if provider == "openai_compatible":
            return self._embed_openai_compatible(texts)
        return self._embed_local(texts)

    def embed_query(self, text: str) -> list[float]:
        return self.embed_texts([text])[0]

    def _embed_local(self, texts: list[str]) -> list[list[float]]:
        matrix = self.vectorizer.transform(texts)
        dense = matrix.toarray().astype(np.float32)
        norms = np.linalg.norm(dense, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        normalized = dense / norms
        return normalized.tolist()

    def _embed_openai_compatible(self, texts: list[str]) -> list[list[float]]:
        if not settings.embedding_model:
            raise ValueError("EMBEDDING_MODEL must be set when EMBEDDING_PROVIDER=openai_compatible.")

        payload: dict[str, Any] = {"model": settings.embedding_model, "input": texts}
        headers = {"Content-Type": "application/json"}
        if settings.embedding_api_key:
            headers["Authorization"] = f"Bearer {settings.embedding_api_key}"

        response = httpx.post(
            f"{settings.embedding_base_url.rstrip('/')}/embeddings",
            json=payload,
            headers=headers,
            timeout=settings.request_timeout_seconds,
        )
        response.raise_for_status()
        data = response.json()["data"]
        return [item["embedding"] for item in data]


embedding_service = EmbeddingService()
