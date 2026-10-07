"""Minimal deterministic Fact / Event extraction.

Only patterns that can be read without interpretation are extracted:

- DIAGNOSIS: a coded diagnosis after a "Diagnosa ... :" label, or a coded
  line inside a DIAGNOSIS section. The label is kept verbatim in
  ``source_label``; it is *not* mapped to diagnosis_role or
  diagnosis_context (ADR-04 is open). A printed "-" becomes a Fact with
  ``availability_status = NOT_DOCUMENTED``, never "no diagnosis".
- PROCEDURE: same approach with "Prosedur/Tindakan ... :" labels and coded
  lines inside a PROCEDURE section.
- MEDICATION: prescription lines starting with "R/". The line text is kept
  whole; dose, route and medication_context are not parsed (ADR-06).
- Events: admission, discharge and arrival dates on *clinical* documents
  only. Claim anchors (SEP, INA-CBG, billing) never produce Events
  (DATA_MODEL 31).

Every Fact and Event is a SOURCE_FACT with at least one Evidence item.
``coding_system`` is set only when the source names it next to the label.
"""

import re
from collections.abc import Iterator
from dataclasses import dataclass, field

from app.document.dates import labelled_dates
from app.document.models import Chunk, Document, Section
from app.document.rules import CLAIM_ANCHOR_TYPES
from app.evidence.models import Event, EvidenceRegistry, Fact, SemanticRefs
from app.extraction.models import DocumentElement, Page
from app.ids import IdFactory
from app.temporal import NumericOrder
from app.vocabulary import Availability, DateRole, EventType, FactType, Provenance

ICD10_CODE = r"[A-Z]\d{2}(?:\.[0-9A-Z]{1,4})?"
ICD9CM_CODE = r"\d{2}\.\d{1,2}"

DIAGNOSIS_LABEL = re.compile(
    r"^(?P<label>(?:DIAGNOSA|DIAGNOSIS)(?:\s+(?:UTAMA|SEKUNDER|AWAL|PRIMER|MASUK|KELUAR|AKHIR|KERJA))?)"
    r"(?P<system>\s*\(?ICD[\s.-]?10\)?)?\s*:\s*(?P<rest>.*)$",
    re.IGNORECASE,
)
PROCEDURE_LABEL = re.compile(
    r"^(?P<label>(?:PROSEDUR|PROCEDURE|TINDAKAN)(?:\s+(?:UTAMA|SEKUNDER))?)"
    r"(?P<system>\s*\(?ICD[\s.-]?9(?:[\s.-]?CM)?\)?)?\s*:\s*(?P<rest>.*)$",
    re.IGNORECASE,
)
DIAGNOSIS_LINE = re.compile(r"^(?P<code>" + ICD10_CODE + r")\s+\S")
PROCEDURE_LINE = re.compile(r"^(?P<code>" + ICD9CM_CODE + r")\s+\S")
LEADING_DIAGNOSIS_CODE = re.compile(r"^(?P<code>" + ICD10_CODE + r")\b")
LEADING_PROCEDURE_CODE = re.compile(r"^(?P<code>" + ICD9CM_CODE + r")\b")
PRESCRIPTION_LINE = re.compile(r"^R/\s*(?P<text>\S.*)$")
NOT_DOCUMENTED_MARK = "-"

EVENT_FOR_ROLE: dict[DateRole, EventType] = {
    DateRole.ADMISSION: EventType.ADMISSION,
    DateRole.DISCHARGE: EventType.DISCHARGE,
    # SERVICE is only produced by arrival labels ("Waktu Datang", "Jam Datang").
    DateRole.SERVICE: EventType.PATIENT_ARRIVAL,
}


@dataclass(slots=True)
class ExtractionResult:
    facts: list[Fact] = field(default_factory=list)
    events: list[Event] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class _Candidate:
    fact_type: FactType
    attribute: str
    value: str | None
    raw_value_text: str
    source_label: str | None
    coding_system: str | None
    availability: Availability


def _labelled_code(
    match: re.Match[str], fact_type: FactType, code_pattern: re.Pattern[str]
) -> _Candidate | None:
    rest = match["rest"].strip()
    system = match["system"].strip(" ()") if match["system"] else None
    attribute = "diagnosis_code" if fact_type is FactType.DIAGNOSIS else "procedure_code"
    if rest == NOT_DOCUMENTED_MARK:
        return _Candidate(
            fact_type, attribute, None, rest, match["label"], system, Availability.NOT_DOCUMENTED
        )
    code = code_pattern.match(rest)
    if code:
        return _Candidate(
            fact_type, attribute, code["code"], code["code"], match["label"], system, Availability.PRESENT
        )
    return None  # free text or a value on the next line: not extracted


def candidates_for_line(text: str, section: Section, carry: _Candidate | None = None) -> Iterator[_Candidate]:
    """Yield the facts a single line states. Pure function, used by tests.

    ``carry`` is the labelled fact on the previous line, if any. A coded line
    directly after it (no label of its own) continues the same list, as in
    "Prosedur : 47.09 ..." followed by "99.21 ...".
    """
    text = " ".join(text.split())
    continuing_dx = carry if _continues(carry, FactType.DIAGNOSIS) else None
    continuing_px = carry if _continues(carry, FactType.PROCEDURE) else None
    if match := DIAGNOSIS_LABEL.match(text):
        if candidate := _labelled_code(match, FactType.DIAGNOSIS, LEADING_DIAGNOSIS_CODE):
            yield candidate
    elif match := PROCEDURE_LABEL.match(text):
        if candidate := _labelled_code(match, FactType.PROCEDURE, LEADING_PROCEDURE_CODE):
            yield candidate
    elif (section.section_type == "DIAGNOSIS" or continuing_dx) and (match := DIAGNOSIS_LINE.match(text)):
        label = continuing_dx.source_label if continuing_dx else section.title
        yield _Candidate(
            FactType.DIAGNOSIS,
            "diagnosis_code",
            match["code"],
            match["code"],
            label,
            None,
            Availability.PRESENT,
        )
    elif (section.section_type == "PROCEDURE" or continuing_px) and (match := PROCEDURE_LINE.match(text)):
        label = continuing_px.source_label if continuing_px else section.title
        yield _Candidate(
            FactType.PROCEDURE,
            "procedure_code",
            match["code"],
            match["code"],
            label,
            None,
            Availability.PRESENT,
        )
    elif match := PRESCRIPTION_LINE.match(text):
        yield _Candidate(
            FactType.MEDICATION,
            "medication_text",
            match["text"],
            match["text"],
            "R/",
            None,
            Availability.PRESENT,
        )


def _continues(carry: _Candidate | None, fact_type: FactType) -> bool:
    return (
        carry is not None
        and carry.fact_type is fact_type
        and carry.availability is Availability.PRESENT
        and carry.source_label is not None
    )


class FactExtractor:
    def __init__(
        self,
        ids: IdFactory,
        evidence: EvidenceRegistry,
        numeric_order: NumericOrder | None = None,
    ) -> None:
        self._ids = ids
        self._evidence = evidence
        self._numeric_order = numeric_order

    def extract(self, documents: list[Document], pages: dict[str, Page]) -> ExtractionResult:
        result = ExtractionResult()
        elements = {e.element_id: e for p in pages.values() for e in p.elements}
        for document in documents:
            for section in document.sections:
                carry: _Candidate | None = None
                for chunk in section.chunks:
                    for element_id in chunk.element_refs:
                        line = _Line(elements[element_id], pages[chunk.page_id], document, section, chunk)
                        found = list(candidates_for_line(line.text, section, carry))
                        # Only a coded diagnosis/procedure can be continued on the next line.
                        last = found[-1] if found else None
                        carry = last if last and last.fact_type is not FactType.MEDICATION else None
                        result.facts.extend(self._fact(line, c) for c in found)
                        if document.document_type not in CLAIM_ANCHOR_TYPES:
                            result.events.extend(self._events(line))
        return result

    def _evidence_for(self, line: "_Line") -> str:
        refs = SemanticRefs(
            line.document.document_id,
            line.document.document_type,
            line.section.section_id,
            line.chunk.chunk_id,
        )
        ev = self._evidence.from_text_element(line.element, line.page.source_file_id, "fact", refs)
        return ev.evidence_id

    def _fact(self, line: "_Line", candidate: _Candidate) -> Fact:
        fact = Fact(
            fact_id=self._ids.next("fact"),
            fact_type=candidate.fact_type,
            subject="patient",
            attribute=candidate.attribute,
            value=candidate.value,
            provenance=Provenance.SOURCE_FACT,
            evidence_refs=[self._evidence_for(line)],
            availability_status=candidate.availability,
            raw_value_text=candidate.raw_value_text,
            source_label=candidate.source_label,
            coding_system=candidate.coding_system,
            document_id=line.document.document_id,
            chunk_id=line.chunk.chunk_id,
        )
        line.chunk.fact_refs.append(fact.fact_id)
        return fact

    def _events(self, line: "_Line") -> Iterator[Event]:
        for temporal in labelled_dates(line.text, self._numeric_order):
            event_type = EVENT_FOR_ROLE.get(temporal.date_role)
            if event_type is None:
                continue
            event = Event(
                event_id=self._ids.next("event"),
                event_type=event_type,
                description=f"{event_type} date stated in {line.document.document_type}",
                temporal_value=temporal,
                provenance=Provenance.SOURCE_FACT,
                evidence_refs=[self._evidence_for(line)],
                document_id=line.document.document_id,
                chunk_id=line.chunk.chunk_id,
            )
            line.chunk.event_refs.append(event.event_id)
            yield event


@dataclass(frozen=True, slots=True)
class _Line:
    """One text line together with everything it belongs to."""

    element: DocumentElement
    page: Page
    document: Document
    section: Section
    chunk: Chunk

    @property
    def text(self) -> str:
        return self.element.text or ""
