from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.eval_case import EvalCase
from app.models.eval_result import EvalResult
from app.services.answer_service import answer_question
from app.services.retrieval_service import retrieve_chunks
from app.utils.text import keyword_label, safe_json_dumps, safe_json_loads, split_sentences


def ensure_eval_cases_for_document(db: Session, document: Document) -> None:
    existing = db.query(EvalCase).filter(EvalCase.expected_document_id == document.id).count()
    if existing > 0 or not document.chunks:
        return

    candidate_chunks = _pick_eval_chunks(document)
    for chunk in candidate_chunks:
        first_sentences = split_sentences(chunk.chunk_text)
        reference_answer = " ".join(first_sentences[:2]) if first_sentences else chunk.chunk_text[:240]
        page_numbers = [chunk.page_number] if chunk.page_number else []
        question = (
            f'What does "{document.title}" say about {keyword_label(chunk.chunk_text, limit=3)}?'
        )
        eval_case = EvalCase(
            question=question,
            reference_answer=reference_answer,
            expected_document_id=document.id,
            expected_page_numbers=safe_json_dumps(page_numbers),
            notes="Auto-generated from indexed content for baseline retrieval and citation checks.",
        )
        db.add(eval_case)
    db.commit()


def run_all_evals(db: Session) -> list[dict[str, object]]:
    cases = db.query(EvalCase).order_by(EvalCase.created_at.asc()).all()
    results: list[dict[str, object]] = []

    for eval_case in cases:
        retrieved_chunks = retrieve_chunks(db, eval_case.question)
        answer = answer_question(eval_case.question, retrieved_chunks)
        expected_pages = _parse_pages(eval_case.expected_page_numbers)
        retrieved_ids = [int(chunk["chunk_id"]) for chunk in retrieved_chunks]

        retrieval_hit = _retrieval_hit(retrieved_chunks, eval_case.expected_document_id, expected_pages)
        citation_correct = _citation_correct(answer["citations"], eval_case.expected_document_id, expected_pages)
        answer_score = round(_answer_similarity(answer["answer"], eval_case.reference_answer), 3)

        result_model = EvalResult(
            eval_case_id=eval_case.id,
            retrieved_chunk_ids=safe_json_dumps(retrieved_ids),
            answer_text=answer["answer"],
            citation_json=safe_json_dumps(answer["citations"]),
            retrieval_hit=retrieval_hit,
            citation_correct=citation_correct,
            answer_score=answer_score,
        )
        db.add(result_model)
        db.commit()
        db.refresh(result_model)

        results.append(
            {
                "id": result_model.id,
                "eval_case_id": eval_case.id,
                "question": eval_case.question,
                "reference_answer": eval_case.reference_answer,
                "expected_document_id": eval_case.expected_document_id,
                "expected_page_numbers": expected_pages,
                "retrieved_chunk_ids": retrieved_ids,
                "answer_text": result_model.answer_text,
                "citation_json": answer["citations"],
                "retrieval_hit": retrieval_hit,
                "citation_correct": citation_correct,
                "answer_score": answer_score,
                "created_at": result_model.created_at,
            }
        )

    return results


def list_eval_cases(db: Session) -> list[dict[str, object]]:
    cases = db.query(EvalCase).order_by(EvalCase.created_at.asc()).all()
    return [
        {
            "id": case.id,
            "question": case.question,
            "reference_answer": case.reference_answer,
            "expected_document_id": case.expected_document_id,
            "expected_page_numbers": _parse_pages(case.expected_page_numbers),
            "notes": case.notes,
            "created_at": case.created_at,
        }
        for case in cases
    ]


def list_eval_results(db: Session) -> list[dict[str, object]]:
    cases_by_id = {case.id: case for case in db.query(EvalCase).all()}
    results = db.query(EvalResult).order_by(EvalResult.created_at.desc()).all()

    payload = []
    for result in results:
        eval_case = cases_by_id.get(result.eval_case_id)
        expected_pages = _parse_pages(eval_case.expected_page_numbers if eval_case else "[]")
        payload.append(
            {
                "id": result.id,
                "eval_case_id": result.eval_case_id,
                "question": eval_case.question if eval_case else "Unknown eval case",
                "reference_answer": eval_case.reference_answer if eval_case else "",
                "expected_document_id": eval_case.expected_document_id if eval_case else None,
                "expected_page_numbers": expected_pages,
                "retrieved_chunk_ids": safe_json_loads(result.retrieved_chunk_ids, []),
                "answer_text": result.answer_text,
                "citation_json": safe_json_loads(result.citation_json, []),
                "retrieval_hit": result.retrieval_hit,
                "citation_correct": result.citation_correct,
                "answer_score": result.answer_score,
                "created_at": result.created_at,
            }
        )
    return payload


def _pick_eval_chunks(document: Document) -> list:
    if len(document.chunks) <= 3:
        return document.chunks
    mid_index = len(document.chunks) // 2
    selected = [document.chunks[0], document.chunks[mid_index], document.chunks[-1]]
    deduped = []
    seen_ids = set()
    for chunk in selected:
        if chunk.id in seen_ids:
            continue
        seen_ids.add(chunk.id)
        deduped.append(chunk)
    return deduped


def _parse_pages(raw_value: str) -> list[int]:
    parsed = safe_json_loads(raw_value, [])
    return [int(value) for value in parsed if value is not None]


def _retrieval_hit(
    retrieved_chunks: list[dict[str, object]],
    expected_document_id: int | None,
    expected_pages: list[int],
) -> bool:
    if expected_document_id is None:
        return False
    for chunk in retrieved_chunks:
        if int(chunk["document_id"]) != expected_document_id:
            continue
        if not expected_pages:
            return True
        if chunk["page_number"] in expected_pages:
            return True
    return False


def _citation_correct(citations: list[dict[str, object]], expected_document_id: int | None, expected_pages: list[int]) -> bool:
    if expected_document_id is None:
        return False
    for citation in citations:
        if int(citation["document_id"]) != expected_document_id:
            continue
        if not expected_pages:
            return True
        if citation.get("page_number") in expected_pages:
            return True
    return False


def _answer_similarity(left: str, right: str) -> float:
    left_tokens = set(token.lower() for token in left.split() if token)
    right_tokens = set(token.lower() for token in right.split() if token)
    if not left_tokens or not right_tokens:
        return 0.0
    return len(left_tokens & right_tokens) / len(left_tokens | right_tokens)
