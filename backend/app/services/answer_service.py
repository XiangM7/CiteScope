from __future__ import annotations

import json
from typing import Any

import httpx

from app.core.config import settings
from app.services.citation_service import build_citations
from app.utils.text import content_tokens, cosine_like_overlap, split_sentences, truncate_text


GROUNDING_SYSTEM_PROMPT = """
You are CiteScope, a grounded research assistant.
Answer only from the provided context.
If the context does not support the answer, say that the evidence is insufficient.
Do not invent facts.
Be concise and factual.
Return valid JSON with this shape:
{"answer":"string","citation_labels":["C1","C2"]}
Only cite labels that are supported by the context.
""".strip()


def answer_question(question: str, retrieved_chunks: list[dict[str, object]]) -> dict[str, object]:
    provider = settings.llm_provider.lower()
    if provider == "openai_compatible":
        try:
            return _answer_with_openai_compatible(question, retrieved_chunks)
        except Exception:
            return _answer_locally(question, retrieved_chunks)
    return _answer_locally(question, retrieved_chunks)


def _answer_locally(question: str, retrieved_chunks: list[dict[str, object]]) -> dict[str, object]:
    if not retrieved_chunks:
        return {
            "answer": "Evidence is insufficient because no indexed source content was retrieved for this question.",
            "citations": [],
        }

    question_terms = set(content_tokens(question))
    ranked_sentences: list[tuple[float, str, int]] = []

    for chunk in retrieved_chunks:
        chunk_boost = float(chunk["score"]) + 0.05
        for sentence in split_sentences(str(chunk["chunk_text"])):
            sentence_terms = set(content_tokens(sentence))
            lexical_overlap = len(question_terms & sentence_terms) / max(len(question_terms), 1)
            semantic_overlap = cosine_like_overlap(question, sentence)
            score = lexical_overlap * 0.6 + semantic_overlap * 0.4 + chunk_boost * 0.2
            if score > 0:
                ranked_sentences.append((score, sentence, int(chunk["chunk_id"])))

    ranked_sentences.sort(key=lambda item: item[0], reverse=True)

    selected_sentences: list[str] = []
    cited_ids: list[int] = []
    seen_sentences: set[str] = set()

    for score, sentence, chunk_id in ranked_sentences:
        cleaned_sentence = truncate_text(sentence.strip(), limit=260)
        if cleaned_sentence in seen_sentences:
            continue
        if score < 0.18 and selected_sentences:
            continue
        selected_sentences.append(cleaned_sentence)
        cited_ids.append(chunk_id)
        seen_sentences.add(cleaned_sentence)
        if len(selected_sentences) >= 3:
            break

    if not selected_sentences:
        return {
            "answer": "Evidence is insufficient in the retrieved context to answer this question confidently.",
            "citations": [],
        }

    answer = " ".join(selected_sentences)
    citations = build_citations(retrieved_chunks, cited_chunk_ids=cited_ids)
    return {"answer": answer, "citations": citations}


def _answer_with_openai_compatible(question: str, retrieved_chunks: list[dict[str, object]]) -> dict[str, object]:
    if not settings.llm_model:
        raise ValueError("LLM_MODEL must be set when LLM_PROVIDER=openai_compatible.")

    labeled_context = []
    label_to_chunk_id: dict[str, int] = {}
    for index, chunk in enumerate(retrieved_chunks, start=1):
        label = f"C{index}"
        label_to_chunk_id[label] = int(chunk["chunk_id"])
        location = f"page {chunk['page_number']}" if chunk["page_number"] else chunk["source_path"]
        labeled_context.append(
            f"[{label}] {chunk['document_title']} ({location})\n{truncate_text(str(chunk['chunk_text']), limit=1800)}"
        )

    user_prompt = (
        f"Question: {question}\n\n"
        f"Context:\n\n{'\n\n'.join(labeled_context)}\n\n"
        "Return JSON only."
    )

    headers = {"Content-Type": "application/json"}
    if settings.llm_api_key:
        headers["Authorization"] = f"Bearer {settings.llm_api_key}"

    response = httpx.post(
        f"{settings.llm_base_url.rstrip('/')}/chat/completions",
        json={
            "model": settings.llm_model,
            "temperature": 0,
            "messages": [
                {"role": "system", "content": GROUNDING_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
        },
        headers=headers,
        timeout=settings.request_timeout_seconds,
    )
    response.raise_for_status()
    message = response.json()["choices"][0]["message"]["content"]
    payload = _extract_json_object(message)
    cited_ids = [label_to_chunk_id[label] for label in payload.get("citation_labels", []) if label in label_to_chunk_id]
    citations = build_citations(retrieved_chunks, cited_chunk_ids=cited_ids)
    return {"answer": payload.get("answer", "").strip(), "citations": citations}


def _extract_json_object(content: str) -> dict[str, Any]:
    content = content.strip()
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        start = content.find("{")
        end = content.rfind("}")
        if start != -1 and end != -1 and end > start:
            return json.loads(content[start : end + 1])
        raise
