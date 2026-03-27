from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class WebDocumentCreate(BaseModel):
    url: str = Field(min_length=4)


class ChunkResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    document_id: int
    chunk_text: str
    chunk_index: int
    page_number: int | None = None
    section_title: str | None = None
    metadata_json: str
    created_at: datetime


class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    source_type: str
    source_path: str
    status: str
    created_at: datetime
    chunk_count: int = 0


class DocumentDetailResponse(DocumentResponse):
    chunks: list[ChunkResponse] = Field(default_factory=list)
