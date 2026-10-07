"""Read a PDF into the Raw Document Representation.

Only native text extraction is done (pypdf). No OCR: a page whose content
is an image keeps ``text_status = NOT_AVAILABLE`` and is still a Page.
Nothing here raises for a bad file; failures are recorded on the
SourceFile / Page so the pipeline can continue and report them.
"""

import io
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pypdf import PdfReader
from pypdf.errors import PdfReadError

from app.extraction.models import DocumentElement, Page, SourceFile
from app.ids import IdFactory, content_digest, source_file_id_for
from app.vocabulary import (
    ElementType,
    ExtractionMethod,
    IngestionStatus,
    Modality,
    PageKind,
    TextStatus,
)

logger = logging.getLogger(__name__)

PDF_MEDIA_TYPE = "application/pdf"


def _count_images(xobjects: Any, depth: int = 0) -> int:
    """Count image XObjects declared in a page's resources (one level of nested forms)."""
    if not xobjects or depth > 1:
        return 0
    count = 0
    for ref in xobjects.values():
        obj = ref.get_object()
        subtype = obj.get("/Subtype")
        if subtype == "/Image":
            count += 1
        elif subtype == "/Form":
            nested = (obj.get("/Resources") or {}).get("/XObject")
            count += _count_images(nested, depth + 1)
    return count


def _page_from_pdf(pdf_page: Any, page_number: int, source_file_id: str, ids: IdFactory) -> Page:
    page_id = ids.next("page")
    text = ""
    error: str | None = None
    text_status = TextStatus.NOT_AVAILABLE
    try:
        text = pdf_page.extract_text() or ""
        if text.strip():
            text_status = TextStatus.EXTRACTED
    except Exception as exc:  # pypdf raises many types on damaged content streams
        text_status = TextStatus.FAILED
        error = f"text extraction failed: {type(exc).__name__}: {exc}"
        logger.warning("page_text_failed", extra={"page_number": page_number, "error": error})

    try:
        resources = pdf_page.get("/Resources") or {}
        image_count = _count_images(resources.get("/XObject"))
    except Exception as exc:
        image_count = 0
        error = (error + "; " if error else "") + f"image scan failed: {type(exc).__name__}"

    has_text = text_status is TextStatus.EXTRACTED
    if text_status is TextStatus.FAILED:
        page_kind = PageKind.UNKNOWN
    elif has_text or image_count:
        page_kind = PageKind.CONTENT
    else:
        # BLANK vs SEPARATOR cannot be told apart without layout analysis.
        page_kind = PageKind.BLANK

    page = Page(
        page_id=page_id,
        source_file_id=source_file_id,
        page_number=page_number,
        page_kind=page_kind,
        # An image-only page may be a scan or a photo; the reader cannot tell.
        modality=Modality.DIGITAL_TEXT if has_text else Modality.UNKNOWN,
        extraction_method=ExtractionMethod.NATIVE_TEXT if has_text else ExtractionMethod.UNKNOWN,
        text_status=text_status,
        text=text,
        image_count=image_count,
        error=error,
    )

    if has_text:
        lines = [line.strip() for line in text.splitlines()]
        for index, line in enumerate(line for line in lines if line):
            page.elements.append(
                DocumentElement(
                    element_id=ids.next("el"),
                    page_id=page_id,
                    page_number=page_number,
                    element_type=ElementType.TEXT,
                    extraction_method=ExtractionMethod.NATIVE_TEXT,
                    text=line,
                    line_index=index,
                )
            )
    for _ in range(image_count):
        page.elements.append(
            DocumentElement(
                element_id=ids.next("el"),
                page_id=page_id,
                page_number=page_number,
                element_type=ElementType.IMAGE,
                extraction_method=ExtractionMethod.UNKNOWN,
            )
        )
    return page


def read_pdf(path: Path, ids: IdFactory, now: datetime | None = None) -> SourceFile:
    """Ingest one PDF. Never raises for unreadable, encrypted or damaged files."""
    ingested_at = (now or datetime.now(UTC)).isoformat(timespec="seconds")
    data = path.read_bytes()
    digest = content_digest(data)
    source_file = SourceFile(
        source_file_id=source_file_id_for(digest),
        # Only the file name is kept; the full local path is not part of the record.
        source_reference=path.name,
        media_type=PDF_MEDIA_TYPE,
        content_digest=digest,
        ingested_at=ingested_at,
        ingestion_status=IngestionStatus.INGESTED,
        page_count=None,
    )

    try:
        reader = PdfReader(io.BytesIO(data))
        if reader.is_encrypted and not reader.decrypt(""):
            raise PdfReadError("password-protected PDF")
        pdf_pages = list(reader.pages)
    except Exception as exc:
        source_file.ingestion_status = IngestionStatus.FAILED
        source_file.error = f"{type(exc).__name__}: {exc}"
        logger.warning("source_file_failed", extra={"source_file_id": source_file.source_file_id})
        return source_file

    source_file.page_count = len(pdf_pages)
    for number, pdf_page in enumerate(pdf_pages, start=1):
        source_file.pages.append(_page_from_pdf(pdf_page, number, source_file.source_file_id, ids))
    return source_file
