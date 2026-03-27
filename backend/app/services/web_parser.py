from __future__ import annotations

from bs4 import BeautifulSoup
import httpx

from app.core.config import settings
from app.utils.text import normalize_whitespace


# 常见正文候选区域选择器，用来优先定位网页主内容
MAIN_CANDIDATE_SELECTORS = ["article", "main", "[role='main']", ".content", ".post-content", ".entry-content"]


def _extract_main_text(soup: BeautifulSoup) -> str:
    # 先删除通常不属于正文的标签，减少噪声
    for tag_name in ["script", "style", "noscript", "header", "footer", "nav", "aside"]:
        for tag in soup.select(tag_name):
            tag.decompose()

    # candidates 用来收集可能的正文区域
    candidates = []

    # 按常见正文选择器去找页面主内容
    for selector in MAIN_CANDIDATE_SELECTORS:
        for node in soup.select(selector):
            text = normalize_whitespace(node.get_text(" ", strip=True))

            # 只保留长度足够的文本块，避免把很短的导航/标题误判成正文
            if len(text) > 300:
                candidates.append(text)

    # 如果找到了候选正文，优先返回最长的那一块
    if candidates:
        return max(candidates, key=len)

    # 如果没有明显正文区域，就退化为拼接所有段落和列表项
    paragraphs = [
        normalize_whitespace(node.get_text(" ", strip=True))
        for node in soup.find_all(["p", "li"])
        if normalize_whitespace(node.get_text(" ", strip=True))
    ]

    return "\n\n".join(paragraphs)


def parse_web_page(url: str) -> dict[str, object]:
    # 请求网页内容
    response = httpx.get(
        url,
        follow_redirects=True,
        timeout=settings.request_timeout_seconds,
        headers={"User-Agent": "CiteScope/0.1 (+local research assistant)"},
    )

    # 如果请求失败，直接抛出异常
    response.raise_for_status()

    # 用 BeautifulSoup 解析 HTML
    soup = BeautifulSoup(response.text, "html.parser")

    # 提取网页标题；如果没有 <title>，就直接用 URL
    title_node = soup.find("title")
    page_title = normalize_whitespace(title_node.get_text(" ", strip=True)) if title_node else url

    # 提取网页正文
    body_text = _extract_main_text(soup)

    # 如果没有提取到可读正文，抛出异常
    if not body_text:
        raise ValueError("No readable web page text could be extracted.")

    # 尝试提取页面中的主标题作为 section_title
    heading = soup.find(["h1", "h2"])
    section_title = normalize_whitespace(heading.get_text(" ", strip=True)) if heading else None

    # 返回统一结构；网页没有页码，所以 page_number 为 None
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