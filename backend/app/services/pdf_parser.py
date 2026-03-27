from __future__ import annotations

from pathlib import Path

import fitz

from app.utils.text import normalize_whitespace, split_sentences


def parse_pdf(pdf_path: str) -> dict[str, object]:
    document = fitz.open(pdf_path)
    metadata = document.metadata or {}
    title = metadata.get("title") or Path(pdf_path).stem
    sections: list[dict[str, object]] = []

    for page_number, page in enumerate(document, start=1):
        text = page.get_text("text")
        cleaned_text = text.strip()
        if not cleaned_text:
            continue
        sentences = split_sentences(cleaned_text)
        section_title = normalize_whitespace(sentences[0])[:120] if sentences else f"Page {page_number}"
        sections.append(
            {
                "text": cleaned_text,
                "page_number": page_number,
                "section_title": section_title,
            }
        )

    document.close()
    return {"title": title, "sections": sections}
