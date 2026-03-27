from __future__ import annotations

from bs4 import BeautifulSoup
import httpx

from app.core.config import settings
from app.utils.text import normalize_whitespace


MAIN_CANDIDATE_SELECTORS = ["article", "main", "[role='main']", ".content", ".post-content", ".entry-content"]


def _extract_main_text(soup: BeautifulSoup) -> str:
    for tag_name in ["script", "style", "noscript", "header", "footer", "nav", "aside"]:
        for tag in soup.select(tag_name):
            tag.decompose()

    candidates = []
    for selector in MAIN_CANDIDATE_SELECTORS:
        for node in soup.select(selector):
            text = normalize_whitespace(node.get_text(" ", strip=True))
            if len(text) > 300:
                candidates.append(text)

    if candidates:
        return max(candidates, key=len)

    paragraphs = [
        normalize_whitespace(node.get_text(" ", strip=True))
        for node in soup.find_all(["p", "li"])
        if normalize_whitespace(node.get_text(" ", strip=True))
    ]
    return "\n\n".join(paragraphs)


def parse_web_page(url: str) -> dict[str, object]:
    response = httpx.get(
        url,
        follow_redirects=True,
        timeout=settings.request_timeout_seconds,
        headers={"User-Agent": "CiteScope/0.1 (+local research assistant)"},
    )
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    title_node = soup.find("title")
    page_title = normalize_whitespace(title_node.get_text(" ", strip=True)) if title_node else url
    body_text = _extract_main_text(soup)
    if not body_text:
        raise ValueError("No readable web page text could be extracted.")

    heading = soup.find(["h1", "h2"])
    section_title = normalize_whitespace(heading.get_text(" ", strip=True)) if heading else None

    return {
        "title": page_title or url,
        "sections": [
            {
                "text": body_text,
                "page_number": None,
                "section_title": section_title,
            }
        ],
    }
