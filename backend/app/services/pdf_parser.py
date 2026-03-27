from __future__ import annotations

from pathlib import Path

import fitz

from app.utils.text import normalize_whitespace, split_sentences


def parse_pdf(pdf_path: str) -> dict[str, object]:
    # 打开 PDF 文件
    document = fitz.open(pdf_path)

    # 读取 PDF 元数据；如果没有元数据就用空字典
    metadata = document.metadata or {}

    # 优先使用 PDF 自带标题；如果没有就用文件名作为标题
    title = metadata.get("title") or Path(pdf_path).stem

    # sections 用来存每一页提取出来的内容
    sections: list[dict[str, object]] = []

    # 逐页遍历 PDF，页码从 1 开始
    for page_number, page in enumerate(document, start=1):
        # 提取当前页纯文本
        text = page.get_text("text")

        # 去掉首尾空白字符
        cleaned_text = text.strip()

        # 如果这一页没有有效文字，直接跳过
        if not cleaned_text:
            continue

        # 把当前页文本拆成句子，方便后面取第一句做 section_title
        sentences = split_sentences(cleaned_text)

        # 用第一页/当前页第一句生成一个简短标题；如果没有句子就退化成 Page X
        section_title = normalize_whitespace(sentences[0])[:120] if sentences else f"Page {page_number}"

        # 把当前页保存成一个 section，保留 text、页码、标题
        sections.append(
            {
                "text": cleaned_text,
                "page_number": page_number,
                "section_title": section_title,
            }
        )

    # 关闭 PDF 文件，释放资源
    document.close()

    # 返回统一结构，供后续 chunking / embedding / retrieval 使用
    return {"title": title, "sections": sections}