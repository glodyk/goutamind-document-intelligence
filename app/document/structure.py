"""Split a Document into Sections and Chunks.

Sections start at short heading lines recognised by ``CLINICAL_SECTION_RULES``.
Text before the first heading forms a ``GENERIC`` section. Financial documents
get one ``BILLING_DETAIL`` section, because their sub-headings are billing
categories, not clinical sections.

A Chunk is the run of a section's lines on one page, split further only when
it gets long. Chunks never cross a page break, so each keeps a single
``page_number`` and the ids of the text elements it was built from.
"""

import re
from collections.abc import Iterable
from itertools import groupby

from app.document.models import Chunk, Document, Section
from app.document.rules import (
    CLINICAL_SECTION_RULES,
    DEFAULT_SECTION_TYPE,
    FINANCIAL_SECTION_TYPE,
    FINANCIAL_TYPES,
    MAX_CHUNK_LINES,
    SECTION_HEADING_MAX_LEN,
)
from app.extraction.models import DocumentElement, Page
from app.ids import IdFactory

_LABEL_WITH_VALUE = re.compile(r":\s*\S")


def heading_type(text: str) -> str | None:
    """Return the section type if ``text`` is a section heading line."""
    text = " ".join(text.split())
    if len(text) > SECTION_HEADING_MAX_LEN or _LABEL_WITH_VALUE.search(text):
        return None
    for rule in CLINICAL_SECTION_RULES:
        if rule.pattern.search(text):
            return rule.section_type
    return None


def _document_lines(document: Document, pages: dict[str, Page]) -> list[DocumentElement]:
    lines: list[DocumentElement] = []
    for ref in document.page_refs:
        lines.extend(pages[ref.page_id].text_lines)
    return lines


def _chunks(section: Section, lines: Iterable[DocumentElement], ids: IdFactory) -> list[Chunk]:
    chunks: list[Chunk] = []
    for (page_number, page_id), group in groupby(lines, key=lambda e: (e.page_number, e.page_id)):
        page_lines = list(group)
        for start in range(0, len(page_lines), MAX_CHUNK_LINES):
            part = page_lines[start : start + MAX_CHUNK_LINES]
            chunks.append(
                Chunk(
                    chunk_id=ids.next("chunk"),
                    section_id=section.section_id,
                    document_id=section.document_id,
                    chunk_type=section.section_type,
                    text="\n".join(e.text or "" for e in part),
                    page_number=page_number,
                    page_id=page_id,
                    element_refs=[e.element_id for e in part],
                )
            )
    return chunks


def build_structure(document: Document, pages: dict[str, Page], ids: IdFactory) -> None:
    """Fill ``document.sections`` (with chunks) in place."""
    lines = _document_lines(document, pages)
    if not lines:
        return  # image-only document: no text, so no sections or chunks

    financial = document.document_type in FINANCIAL_TYPES
    groups: list[tuple[str, str | None, list[DocumentElement]]] = []
    for element in lines:
        kind = None if financial else heading_type(element.text or "")
        if kind is not None:
            groups.append((kind, element.text, [element]))
        elif not groups:
            section_type = FINANCIAL_SECTION_TYPE if financial else DEFAULT_SECTION_TYPE
            groups.append((section_type, None, [element]))
        else:
            groups[-1][2].append(element)

    for section_type, title, members in groups:
        section = Section(
            section_id=ids.next("section"),
            document_id=document.document_id,
            section_type=section_type,
            title=title,
            page_start=members[0].page_number,
            page_end=members[-1].page_number,
        )
        section.chunks = _chunks(section, members, ids)
        document.sections.append(section)
