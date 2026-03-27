from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.chat import CitationSchema


class EvalCaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    question: str
    reference_answer: str
    expected_document_id: int | None = None
    expected_page_numbers: list[int]
    notes: str | None = None
    created_at: datetime


class EvalResultSchema(BaseModel):
    id: int
    eval_case_id: int
    question: str
    reference_answer: str
    expected_document_id: int | None = None
    expected_page_numbers: list[int]
    retrieved_chunk_ids: list[int]
    answer_text: str
    citation_json: list[CitationSchema]
    retrieval_hit: bool
    citation_correct: bool
    answer_score: float
    created_at: datetime


class EvalRunResponse(BaseModel):
    total_cases: int
    results: list[EvalResultSchema]
