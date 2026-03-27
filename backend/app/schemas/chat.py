from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ChatRequest(BaseModel):
    question: str = Field(min_length=3)
    top_k: int | None = Field(default=None, ge=1, le=10)


class CitationSchema(BaseModel):
    chunk_id: int
    document_id: int
    document_title: str
    page_number: int | None = None
    source_type: str
    source_path: str


class RetrievedChunkSchema(BaseModel):
    chunk_id: int
    document_id: int
    document_title: str
    chunk_text: str
    chunk_index: int
    page_number: int | None = None
    section_title: str | None = None
    score: float
    source_type: str
    source_path: str


class ChatResponse(BaseModel):
    answer: str
    citations: list[CitationSchema]
    retrieved_chunks: list[RetrievedChunkSchema]
    query_log_id: int
    created_at: datetime


class QueryLogSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    question: str
    answer_text: str
    created_at: datetime
