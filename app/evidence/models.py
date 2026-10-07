"""Evidence, Fact and Event (DATA_MODEL 12, 13, 15, 16).

Evidence and Fact are separate classes on purpose: Evidence only says
*where* something is written; a Fact says *what* is asserted and points to
its Evidence through ``evidence_refs``. Creating Evidence never creates a
Fact.
"""

from dataclasses import dataclass, field

from app.extraction.models import DocumentElement, Page
from app.ids import IdFactory
from app.temporal import TemporalValue
from app.vocabulary import (
    UNKNOWN,
    Availability,
    ContentKind,
    EventType,
    ExtractionMethod,
    FactType,
    Provenance,
    RedactionState,
    Sensitivity,
    TemporalPrecision,
)


@dataclass(slots=True)
class Evidence:
    evidence_id: str
    source_file_id: str
    page_id: str
    page_number: int
    extraction_method: ExtractionMethod
    content_kind: ContentKind
    purpose: str  # IMPLEMENTATION: what the evidence was created for (fact, boundary, image)
    document_id: str | None = None
    document_type: str | None = None
    section_id: str | None = None
    chunk_id: str | None = None  # IMPLEMENTATION: brief asks for a chunk reference
    element_id: str | None = None
    source_text: str | None = None  # absent for IMAGE_REGION
    bbox: tuple[float, float, float, float] | None = None  # not available from the reader
    confidence: float | None = None
    # Text copied from a claim document may contain personal data. This slice
    # does not classify it, so the honest value is UNKNOWN (ADR-08).
    sensitivity: Sensitivity = Sensitivity.UNKNOWN
    redaction_state: RedactionState = RedactionState.ORIGINAL


@dataclass(slots=True)
class Fact:
    fact_id: str
    fact_type: FactType
    subject: str
    attribute: str
    value: str | None
    provenance: Provenance
    evidence_refs: list[str]
    availability_status: Availability = Availability.PRESENT
    raw_value_text: str | None = None
    source_label: str | None = None  # IMPLEMENTATION: label as printed, e.g. "Diagnosa Awal"
    coding_system: str | None = None  # only when the source names it
    unit: str | None = None
    temporal_information: TemporalValue | None = None
    confidence: float | None = None
    document_id: str | None = None
    chunk_id: str | None = None
    derived_from_refs: list[str] = field(default_factory=list)
    inference_basis_refs: list[str] = field(default_factory=list)


@dataclass(slots=True)
class Event:
    event_id: str
    event_type: EventType
    description: str
    temporal_value: TemporalValue
    provenance: Provenance
    evidence_refs: list[str]
    care_pathway: str = UNKNOWN  # never inferred in this slice
    care_stage: str = UNKNOWN
    document_id: str | None = None
    chunk_id: str | None = None
    derived_from_refs: list[str] = field(default_factory=list)
    inference_basis_refs: list[str] = field(default_factory=list)

    @property
    def event_time(self) -> str | None:
        """Baseline projection of ``temporal_value`` (DATA_MODEL 13)."""
        return self.temporal_value.value

    @property
    def temporal_precision(self) -> TemporalPrecision:
        return self.temporal_value.precision


@dataclass(slots=True, frozen=True)
class SemanticRefs:
    """Where in the semantic layer a piece of evidence sits (all optional)."""

    document_id: str | None = None
    document_type: str | None = None
    section_id: str | None = None
    chunk_id: str | None = None


class EvidenceRegistry:
    """Central evidence list; everything else refers to evidence by id (DATA_MODEL 16)."""

    def __init__(self, ids: IdFactory) -> None:
        self._ids = ids
        self.items: dict[str, Evidence] = {}

    def _add(self, evidence: Evidence) -> Evidence:
        self.items[evidence.evidence_id] = evidence
        return evidence

    def from_text_element(
        self, element: DocumentElement, source_file_id: str, purpose: str, refs: SemanticRefs
    ) -> Evidence:
        return self._add(
            Evidence(
                evidence_id=self._ids.next("evidence"),
                source_file_id=source_file_id,
                page_id=element.page_id,
                page_number=element.page_number,
                extraction_method=element.extraction_method,
                content_kind=ContentKind.TEXT,
                purpose=purpose,
                element_id=element.element_id,
                source_text=element.text,
                document_id=refs.document_id,
                document_type=refs.document_type,
                section_id=refs.section_id,
                chunk_id=refs.chunk_id,
            )
        )

    def from_image_page(self, page: Page, purpose: str, refs: SemanticRefs) -> Evidence:
        """Non-textual evidence: the page region itself, with no source_text."""
        images = [e for e in page.elements if e.text is None]
        return self._add(
            Evidence(
                evidence_id=self._ids.next("evidence"),
                source_file_id=page.source_file_id,
                page_id=page.page_id,
                page_number=page.page_number,
                extraction_method=page.extraction_method,
                content_kind=ContentKind.IMAGE_REGION,
                purpose=purpose,
                element_id=images[0].element_id if images else None,
                document_id=refs.document_id,
                document_type=refs.document_type,
                section_id=refs.section_id,
                chunk_id=refs.chunk_id,
            )
        )
