"""Group physical pages into logical Documents.

Decision order for a page with text (first match wins):

1. a printed page counter "k of n" with k > 1  -> continues the current document
2. a document title in the page's top lines   -> starts a new document
3. a page counter with k = 1                   -> starts a new document
4. a marker rule (labels typical of a type)    -> starts a new document,
   unless the current document already has that type
5. otherwise                                   -> continues the current document,
   or starts an UNKNOWN document if there is none

Pages without text are handled before these rules: a BLANK page belongs to
no document and ends the current one; an image-only or failed page becomes
its own UNKNOWN document, because nothing on it can be classified.

Every page membership records its rule (``PageRef.basis``) and the Evidence
the rule used (``PageRef.evidence_ref``), so a weak assignment such as
CONTINUATION stays visible downstream instead of looking like a fact.

The result is deliberately conservative: when the evidence is weak the
document type is UNKNOWN rather than a guess.
"""

from dataclasses import dataclass

from app.document.models import Document, PageRef
from app.document.rules import (
    COUNTER_LINES,
    DOCUMENT_ROLES,
    MARKER_RULES,
    PAGE_COUNTER,
    TITLE_RULES,
    TOP_LINES,
)
from app.evidence.models import EvidenceRegistry, SemanticRefs
from app.extraction.models import DocumentElement, Page, SourceFile
from app.ids import IdFactory
from app.vocabulary import AssignmentBasis, ContentKind, DocumentType, PageKind, TextStatus


@dataclass(frozen=True, slots=True)
class PageCounter:
    k: int
    n: int | None
    element: DocumentElement

    @property
    def label(self) -> str:
        return f"{self.k}/{self.n}" if self.n else str(self.k)


@dataclass(frozen=True, slots=True)
class TitleMatch:
    document_type: DocumentType
    element: DocumentElement


def find_page_counter(lines: list[DocumentElement]) -> PageCounter | None:
    candidates = lines[-COUNTER_LINES:] + lines[:COUNTER_LINES]
    for element in candidates:
        match = PAGE_COUNTER.search(element.text or "")
        if match:
            n = int(match["n"]) if match["n"] else None
            return PageCounter(int(match["k"]), n, element)
    return None


def find_title(lines: list[DocumentElement]) -> TitleMatch | None:
    for index, element in enumerate(lines[:TOP_LINES]):
        text = " ".join((element.text or "").split())
        for rule in TITLE_RULES:
            if rule.scope == "FIRST_LINE" and index != 0:
                continue
            if rule.pattern.search(text):
                return TitleMatch(rule.document_type, element)
    return None


def find_marker(lines: list[DocumentElement]) -> TitleMatch | None:
    top = lines[:TOP_LINES]
    for rule in MARKER_RULES:
        hits = [next((e for e in top if p.search(e.text or "")), None) for p in rule.patterns]
        if all(hits):
            first = hits[0]
            assert first is not None
            return TitleMatch(rule.document_type, first)
    return None


class Segmenter:
    def __init__(self, ids: IdFactory, evidence: EvidenceRegistry) -> None:
        self._ids = ids
        self._evidence = evidence

    def _new_document(
        self,
        page: Page,
        document_type: DocumentType,
        basis: AssignmentBasis,
        basis_element: DocumentElement | None,
    ) -> Document:
        document = Document(
            document_id=self._ids.next("doc"),
            document_type=document_type,
            document_role=list(DOCUMENT_ROLES.get(document_type, ())),
            document_title=basis_element.text if basis is AssignmentBasis.TITLE and basis_element else None,
            page_refs=[],
        )
        ref = self._attach(document, page, basis, basis_element)
        document.evidence_refs.append(ref.evidence_ref)
        return document

    def _attach(
        self,
        document: Document,
        page: Page,
        basis: AssignmentBasis,
        element: DocumentElement | None,
    ) -> PageRef:
        """Add a page membership together with the Evidence its rule used.

        TITLE / MARKER / PAGE_COUNTER cite the matching line. IMAGE_PAGE cites
        the page region. CONTINUATION and UNTITLED_START have no positive
        signal, so they cite the page's first line: what the page starts with,
        which matched no rule.
        """
        refs = SemanticRefs(document.document_id, document.document_type)
        purpose = "page_membership"
        if basis is AssignmentBasis.IMAGE_PAGE:
            evidence = self._evidence.from_page_region(page, purpose, refs, ContentKind.IMAGE_REGION)
        elif basis is AssignmentBasis.EXTRACTION_FAILED:
            evidence = self._evidence.from_page_region(page, purpose, refs, ContentKind.OTHER)
        else:
            cited = element or page.text_lines[0]
            evidence = self._evidence.from_text_element(cited, page.source_file_id, purpose, refs)
        ref = PageRef(page.source_file_id, page.page_number, page.page_id, basis, evidence.evidence_id)
        document.page_refs.append(ref)
        return ref

    def segment(self, source_file: SourceFile) -> list[Document]:
        documents: list[Document] = []
        current: Document | None = None

        for page in source_file.pages:
            if page.page_kind is PageKind.BLANK:
                current = None
                continue
            if page.text_status is not TextStatus.EXTRACTED:
                basis = (
                    AssignmentBasis.EXTRACTION_FAILED
                    if page.text_status is TextStatus.FAILED
                    else AssignmentBasis.IMAGE_PAGE
                )
                documents.append(self._new_document(page, DocumentType.UNKNOWN, basis, None))
                current = None
                continue

            lines = page.text_lines
            counter = find_page_counter(lines)
            title = find_title(lines)
            marker = find_marker(lines)

            if counter and counter.k > 1 and current is not None:
                self._attach(current, page, AssignmentBasis.PAGE_COUNTER, counter.element)
            elif title:
                current = self._new_document(page, title.document_type, AssignmentBasis.TITLE, title.element)
                documents.append(current)
            elif counter and counter.k == 1:
                # The counter decides the boundary; a marker, if present, decides the type.
                doc_type = marker.document_type if marker else DocumentType.UNKNOWN
                current = self._new_document(page, doc_type, AssignmentBasis.PAGE_COUNTER, counter.element)
                documents.append(current)
            elif marker and (current is None or current.document_type is not marker.document_type):
                current = self._new_document(
                    page, marker.document_type, AssignmentBasis.MARKER, marker.element
                )
                documents.append(current)
            elif current is not None:
                self._attach(current, page, AssignmentBasis.CONTINUATION, None)
            else:
                current = self._new_document(page, DocumentType.UNKNOWN, AssignmentBasis.UNTITLED_START, None)
                documents.append(current)

            if counter is not None and current is not None:
                current.page_counters.append(counter.label)

        return documents
