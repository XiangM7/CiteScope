from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class EvalResult(Base):
    __tablename__ = "eval_results"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    eval_case_id: Mapped[int] = mapped_column(ForeignKey("eval_cases.id"), nullable=False, index=True)
    retrieved_chunk_ids: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    answer_text: Mapped[str] = mapped_column(Text, nullable=False)
    citation_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    retrieval_hit: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    citation_correct: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    answer_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
