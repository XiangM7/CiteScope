from __future__ import annotations

from typing import Any

import httpx
import numpy as np
from sklearn.feature_extraction.text import HashingVectorizer

from app.core.config import settings


class EmbeddingService:
    def __init__(self) -> None:
        # 初始化一个本地 HashingVectorizer，用于不依赖外部 embedding API 的本地向量化
        # n_features 决定输出向量维度
        # alternate_sign=False 避免哈希后正负号抵消，便于后续稳定处理
        # norm=None 表示这里先不做 sklearn 内部归一化，后面自己手动做 L2 normalize
        # ngram_range=(1, 2) 表示使用 unigram + bigram，稍微增强局部语义表达
        # lowercase=True 表示统一转小写，减少大小写差异
        self.vectorizer = HashingVectorizer(
            n_features=settings.hashing_dimensions,
            alternate_sign=False,
            norm=None,
            ngram_range=(1, 2),
            lowercase=True,
        )

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        # 根据配置选择 embedding 提供方式：
        # 1. openai_compatible：调用兼容 OpenAI embeddings 接口的服务
        # 2. 其他：使用本地 HashingVectorizer 生成向量
        provider = settings.embedding_provider.lower()
        if provider == "openai_compatible":
            return self._embed_openai_compatible(texts)
        return self._embed_local(texts)

    def embed_query(self, text: str) -> list[float]:
        # 查询文本本质上也是一个文本 embedding，
        # 这里复用 embed_texts，只取返回结果的第一个向量
        return self.embed_texts([text])[0]

    def _embed_local(self, texts: list[str]) -> list[list[float]]:
        # 用 HashingVectorizer 把文本列表转成稀疏矩阵
        matrix = self.vectorizer.transform(texts)

        # 转成 dense numpy array，并统一为 float32
        dense = matrix.toarray().astype(np.float32)

        # 计算每一行向量的 L2 范数
        norms = np.linalg.norm(dense, axis=1, keepdims=True)

        # 避免零向量除以 0
        norms[norms == 0] = 1.0

        # 手动做 L2 normalization，
        # 这样后面用 cosine similarity / 向量相似度时更稳定
        normalized = dense / norms

        # 返回 Python list，方便后续 JSON 存储或传给向量库
        return normalized.tolist()

    def _embed_openai_compatible(self, texts: list[str]) -> list[list[float]]:
        # 如果使用 openai_compatible provider，必须指定 embedding model
        if not settings.embedding_model:
            raise ValueError("EMBEDDING_MODEL must be set when EMBEDDING_PROVIDER=openai_compatible.")

        # 组织请求体，input 可以直接是一组文本
        payload: dict[str, Any] = {"model": settings.embedding_model, "input": texts}

        # 默认请求头
        headers = {"Content-Type": "application/json"}

        # 如果配置了 API key，就加上 Authorization
        if settings.embedding_api_key:
            headers["Authorization"] = f"Bearer {settings.embedding_api_key}"

        # 向兼容 OpenAI embeddings 的服务发请求
        response = httpx.post(
            f"{settings.embedding_base_url.rstrip('/')}/embeddings",
            json=payload,
            headers=headers,
            timeout=settings.request_timeout_seconds,
        )

        # 如果请求失败，直接抛异常
        response.raise_for_status()

        # 按 OpenAI embeddings 响应格式取出 data 字段
        data = response.json()["data"]

        # 返回 embedding 列表
        return [item["embedding"] for item in data]


# 创建一个全局单例，方便其他模块直接 import 使用
embedding_service = EmbeddingService()