"""Raw Document Representation (DATA_MODEL 5A, 11).

SourceFile, Page and DocumentElement describe the *physical* input. They do
not know about logical Documents; Documents point to Pages, never the
other way round (DOCUMENT_TAXONOMY 3A).
"""

from dataclasses import dataclass, field

from app.vocabulary import (
    ElementType,
    ExtractionMethod,
    IngestionStatus,
    Modality,
    PageKind,
    TextStatus,
)


@dataclass(slots=True)
class DocumentElement:
    element_id: str
    page_id: str
    page_number: int
    element_type: ElementType
    extraction_method: ExtractionMethod
    text: str | None = None
    bbox: tuple[float, float, float, float] | None = None  # not provided by the current reader
    extraction_confidence: float | None = None  # absent, never invented (DATA_MODEL 34)
    line_index: int | None = None  # IMPLEMENTATION: order of the line on its page


@dataclass(slots=True)
class Page:
    page_id: str
    source_file_id: str
    page_number: int
    page_kind: PageKind
    modality: Modality
    extraction_method: ExtractionMethod
    text_status: TextStatus
    text: str = ""
    image_count: int = 0
    elements: list[DocumentElement] = field(default_factory=list)
    error: str | None = None

    @property
    def text_lines(self) -> list[DocumentElement]:
        return [e for e in self.elements if e.element_type is ElementType.TEXT]


@dataclass(slots=True)
class SourceFile:
    source_file_id: str
    source_reference: str
    media_type: str
    content_digest: str
    ingested_at: str
    ingestion_status: IngestionStatus
    page_count: int | None  # None = UNKNOWN (file could not be opened)
    error: str | None = None
    pages: list[Page] = field(default_factory=list)
