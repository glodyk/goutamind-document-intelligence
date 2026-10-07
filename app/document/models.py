"""Semantic Document Representation (DATA_MODEL 7, 9, 10).

A Document *references* Pages through ``page_refs``; it does not contain
them. Sections and Chunks are built from the Document's text lines and keep
references back to the physical elements they came from.
"""

from dataclasses import dataclass, field

from app.temporal import TemporalValue
from app.vocabulary import Availability, BoundaryBasis, DocumentRole, DocumentType


@dataclass(slots=True, frozen=True)
class PageRef:
    """DATA_MODEL 7 ``page_refs[]`` entry."""

    source_file_id: str
    page_number: int
    page_id: str  # IMPLEMENTATION: direct link to the Page object


@dataclass(slots=True)
class Chunk:
    chunk_id: str
    section_id: str
    document_id: str
    chunk_type: str
    text: str
    page_number: int  # a chunk never crosses a page break (DATA_MODEL 10 has one page_number)
    page_id: str
    element_refs: list[str] = field(default_factory=list)
    fact_refs: list[str] = field(default_factory=list)
    event_refs: list[str] = field(default_factory=list)


@dataclass(slots=True)
class Section:
    section_id: str
    document_id: str
    section_type: str
    title: str | None
    page_start: int  # physical page numbers (documents here are always contiguous runs)
    page_end: int
    chunks: list[Chunk] = field(default_factory=list)


@dataclass(slots=True)
class Document:
    document_id: str
    document_type: DocumentType
    document_role: list[DocumentRole]
    document_title: str | None
    page_refs: list[PageRef]
    boundary_basis: BoundaryBasis  # IMPLEMENTATION: how the first page was recognised
    page_bases: dict[int, BoundaryBasis] = field(default_factory=dict)  # page_number -> basis
    source_facility: Availability = Availability.UNKNOWN  # not extracted in this slice
    document_date: TemporalValue | None = None  # left empty: no date role is documented as "the" date
    dates: list[TemporalValue] = field(default_factory=list)
    completeness_status: Availability = Availability.UNKNOWN
    page_counters: list[str] = field(default_factory=list)  # e.g. "1/3" as printed on pages
    classification_confidence: float | None = None  # rule-based: no calibrated score exists
    duplicate_of: str | None = None  # not detected in this slice (ADR-07)
    sections: list[Section] = field(default_factory=list)
    evidence_refs: list[str] = field(default_factory=list)

    @property
    def page_numbers(self) -> list[int]:
        return [ref.page_number for ref in self.page_refs]

    @property
    def page_range(self) -> str:
        """Bounding range, marked when the pages are not contiguous (DATA_MODEL 7)."""
        numbers = self.page_numbers
        if not numbers:
            return "UNKNOWN"
        first, last = min(numbers), max(numbers)
        contiguous = numbers == list(range(first, last + 1))
        text = str(first) if first == last else f"{first}-{last}"
        return text if contiguous else f"{text} (non-contiguous)"
