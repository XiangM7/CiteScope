from __future__ import annotations

from app.core.config import settings
from app.utils.text import split_paragraphs, tail_overlap, safe_json_dumps


def _chunk_paragraphs(paragraphs: list[str], chunk_size_chars: int, overlap_chars: int) -> list[str]:
    # 存最终切好的文本块
    chunks: list[str] = []

    # current 表示当前正在累积的 chunk
    current = ""

    # 逐段处理文本，而不是直接按整篇硬切
    for paragraph in paragraphs:
        # 尝试把当前段落拼接到 current 后面；
        # 如果 current 为空，就直接用 paragraph 作为候选
        candidate = f"{current}\n\n{paragraph}".strip() if current else paragraph

        # 如果拼接后长度还没超过 chunk 大小上限，就继续累积
        if len(candidate) <= chunk_size_chars:
            current = candidate
            continue

        # 如果超出上限，并且 current 里已经有内容，
        # 先把 current 作为一个完整 chunk 存起来
        if current:
            chunks.append(current.strip())

            # 从 current 末尾截取一部分重叠内容，
            # 让下一个 chunk 保留一些上下文连续性
            overlap = tail_overlap(current, overlap_chars)

            # 下一个 current = 上一个 chunk 的尾部 overlap + 当前 paragraph
            current = f"{overlap}\n\n{paragraph}".strip()

            # 如果这样拼完还是太长，说明 paragraph 本身就很长
            if len(current) > chunk_size_chars and paragraph:
                # 先直接切出 paragraph 的前半部分作为一个 chunk
                chunks.append(paragraph[:chunk_size_chars].strip())

                # 剩余没装进去的部分继续留到 current，
                # 同时保留 overlap 的空间
                current = paragraph[max(0, chunk_size_chars - overlap_chars) :].strip()

        else:
            # 如果 current 本来就是空，说明单独一个 paragraph 就已经过长
            # 直接把 paragraph 前 chunk_size_chars 个字符切成一个 chunk
            chunks.append(paragraph[:chunk_size_chars].strip())

            # 剩余部分继续保留到 current，准备后续继续处理
            current = paragraph[max(0, chunk_size_chars - overlap_chars) :].strip()

    # 循环结束后，如果 current 还有内容，补成最后一个 chunk
    if current.strip():
        chunks.append(current.strip())

    # 返回非空 chunk 列表
    return [chunk for chunk in chunks if chunk]


def build_chunks(
    *,
    document_id: int,
    title: str,
    source_type: str,
    source_path: str,
    sections: list[dict[str, object]],
    chunk_size_chars: int | None = None,
    overlap_chars: int | None = None,
) -> list[dict[str, object]]:
    # 如果调用时没传 chunk_size_chars / overlap_chars，
    # 就使用全局配置中的默认值
    chunk_size_chars = chunk_size_chars or settings.chunk_size_chars
    overlap_chars = overlap_chars or settings.chunk_overlap_chars

    # 存最终生成的所有 chunk 对象
    chunks: list[dict[str, object]] = []

    # 全文档范围内的 chunk 编号
    chunk_index = 0

    # sections 来自前面的 parser（PDF 或网页）
    # 每个 section 通常包含 text、page_number、section_title
    for section in sections:
        # 取出当前 section 的正文文本
        text = str(section.get("text", "")).strip()

        # 如果没有正文，直接跳过
        if not text:
            continue

        # 保留页码信息（网页一般是 None，PDF 通常有值）
        page_number = section.get("page_number")

        # 保留 section 标题，方便后续展示和引用
        section_title = section.get("section_title")

        # 先按段落切开，而不是直接对整块文本硬切
        paragraphs = split_paragraphs(text)

        # 再把段落列表进一步组装成带 overlap 的 chunk
        text_chunks = _chunk_paragraphs(paragraphs, chunk_size_chars=chunk_size_chars, overlap_chars=overlap_chars)

        # 对每个切出来的 chunk，构造结构化对象
        for chunk_text in text_chunks:
            # metadata 用来保存后续检索、引用、调试所需的信息
            metadata = {
                "document_id": document_id,
                "chunk_index": chunk_index,
                "page_number": page_number,
                "source_type": source_type,
                "title": title,
                "source_path": source_path,
                "section_title": section_title,
            }

            # 把 chunk 和 metadata 一起存成统一格式
            chunks.append(
                {
                    "chunk_text": chunk_text,
                    "chunk_index": chunk_index,
                    "page_number": page_number,
                    "section_title": section_title,
                    "metadata_json": safe_json_dumps(metadata),
                }
            )

            # chunk 编号递增
            chunk_index += 1

    # 返回当前文档最终生成的所有 chunk
    return chunks