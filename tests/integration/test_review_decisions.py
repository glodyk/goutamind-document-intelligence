"""Regression tests for the four decisions taken in the PR #1 review.

ADR-REQ-001  every page membership has a basis and evidence
ADR-REQ-002  UNKNOWN (not classified) is distinct from OTHER (known, unlisted)
ADR-REQ-003  ADMISSION means inpatient admission; a printed "Tanggal Masuk"
             on an emergency/outpatient document does not create one
ADR-REQ-004  extraction_method and text_status are separate; an image-only
             page is not declared non-textual
"""

import json
from pathlib import Path

import pytest
from pypdf import PageObject

from app.bundle import ClaimDocumentBundle
from app.vocabulary import (
    AssignmentBasis,
    ContentKind,
    DateRole,
    DocumentType,
    EventType,
    ExtractionMethod,
    PageKind,
    TextStatus,
)
from pipeline.report import render_inspection, render_page_assignment
from pipeline.run import process_pdf
from pipeline.serialize import to_json_dict
from tests.conftest import FIXED_NOW
from tests.fixtures.synthetic_pdf import build_pdf

# --- ADR-REQ-001: page membership provenance ----------------------------------


def test_every_page_membership_has_basis_and_evidence(synthetic_bundle: ClaimDocumentBundle):
    evidence = {e.evidence_id: e for e in synthetic_bundle.evidence}
    pages = synthetic_bundle.pages
    seen: list[str] = []
    for document in synthetic_bundle.documents:
        for ref in document.page_refs:
            assert isinstance(ref.basis, AssignmentBasis)
            cited = evidence[ref.evidence_ref]
            assert cited.purpose == "page_membership"
            assert cited.page_id == ref.page_id  # the evidence is on the assigned page itself
            assert cited.document_id == document.document_id
            seen.append(ref.page_id)
    assert len(seen) == len(set(seen)), "a page belongs to at most one document"
    unassigned = [p for p in pages.values() if p.page_id not in seen]
    assert all(p.page_kind is PageKind.BLANK for p in unassigned)


def test_continuation_cites_what_the_page_starts_with(synthetic_bundle: ClaimDocumentBundle):
    evidence = {e.evidence_id: e for e in synthetic_bundle.evidence}
    assessment = next(d for d in synthetic_bundle.documents if d.document_type is DocumentType.ASSESSMENT)
    ref = assessment.page_refs[1]
    assert ref.basis is AssignmentBasis.CONTINUATION
    first_line = synthetic_bundle.pages[ref.page_id].text_lines[0]
    assert evidence[ref.evidence_ref].element_id == first_line.element_id


def test_membership_basis_is_serialized(synthetic_bundle: ClaimDocumentBundle):
    data = to_json_dict(synthetic_bundle)
    resume = data["documents"][2]["page_refs"]
    assert [(r["page_number"], r["basis"]) for r in resume] == [(3, "TITLE"), (4, "PAGE_COUNTER")]
    assert all(r["evidence_ref"].startswith("evidence-") for r in resume)
    assert json.dumps(data)  # plain JSON, no enum objects left


def test_page_assignment_diagnostic(synthetic_bundle: ClaimDocumentBundle):
    text = render_page_assignment(synthetic_bundle)
    assert text.startswith("Page assignment:")
    assert "  Page 5\n    Document: NONE\n    Reason: BLANK\n" in text
    assert "  Page 6\n    Document: doc-004\n    Type: UNKNOWN\n    Basis: IMAGE_PAGE\n" in text
    assert "  Page 12\n    Document: doc-007\n    Type: ASSESSMENT\n    Basis: CONTINUATION\n" in text
    assert text.count("  Page ") == 16
    assert "Cited:" not in render_page_assignment(synthetic_bundle, show_source_text=False)
    assert "Page assignment:" in render_inspection(synthetic_bundle)


def test_failed_page_is_kept_with_its_own_basis(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    def broken(*args: object, **kwargs: object) -> str:
        raise RuntimeError("damaged content stream")

    monkeypatch.setattr(PageObject, "extract_text", broken)
    pdf = tmp_path / "damaged.pdf"
    pdf.write_bytes(build_pdf([["RESUME MEDIS"]]))
    bundle = process_pdf(pdf, now=FIXED_NOW)
    page = bundle.source_files[0].pages[0]
    assert (page.page_kind, page.text_status) == (PageKind.UNKNOWN, TextStatus.FAILED)
    (document,) = bundle.documents
    assert document.document_type is DocumentType.UNKNOWN
    assert document.page_refs[0].basis is AssignmentBasis.EXTRACTION_FAILED
    assert bundle.evidence[0].content_kind is ContentKind.OTHER


# --- ADR-REQ-002: UNKNOWN is not OTHER -------------------------------------------


def test_unknown_and_other_are_different_values():
    assert DocumentType.UNKNOWN != DocumentType.OTHER
    assert DocumentType.UNKNOWN.value == "UNKNOWN" and DocumentType.OTHER.value == "OTHER"


def test_other_only_for_recognised_titles(synthetic_bundle: ClaimDocumentBundle):
    for document in synthetic_bundle.documents:
        if document.document_type is DocumentType.OTHER:
            assert document.boundary_basis is AssignmentBasis.TITLE and document.document_title
        if document.boundary_basis in {AssignmentBasis.IMAGE_PAGE, AssignmentBasis.UNTITLED_START}:
            assert document.document_type is DocumentType.UNKNOWN


def test_unknown_and_other_survive_serialization_and_report(synthetic_bundle: ClaimDocumentBundle):
    types = [d["document_type"] for d in to_json_dict(synthetic_bundle)["documents"]]
    assert types.count("UNKNOWN") == 2 and types.count("OTHER") == 1
    report = render_inspection(synthetic_bundle)
    assert "4. UNKNOWN" in report and "9. OTHER" in report


# --- ADR-REQ-003: ADMISSION means inpatient admission -------------------------------

# Invented emergency visit that the claim declares as outpatient, shaped like
# the case seen in a real emergency bundle (findings OBS-017).
EMERGENCY_VISIT = [
    ["No.SEP : 0000SINTETIS0002", "Tgl.SEP : 2024-07-11", "Jns Rawat : Rawat Jalan"],
    [
        "RESUME MEDIS IGD",
        "Tanggal Masuk : 11 Juli 2024 21:40",
        "Tanggal Keluar : 11 Juli 2024 23:05",
        "Waktu Datang : 11 Juli 2024 21:35",
        "TINDAK LANJUT",
        "Pulang",
    ],
]


def test_emergency_tanggal_masuk_is_not_an_admission(tmp_path: Path):
    pdf = tmp_path / "emergency.pdf"
    pdf.write_bytes(build_pdf(EMERGENCY_VISIT))
    bundle = process_pdf(pdf, now=FIXED_NOW)

    event_types = [e.event_type for e in bundle.events]
    assert EventType.ADMISSION not in event_types
    assert EventType.DISCHARGE not in event_types
    assert event_types == [EventType.PATIENT_ARRIVAL]  # the arrival is still recorded

    resume = bundle.documents[1]
    assert resume.document_type is DocumentType.MEDICAL_RESUME
    by_label = {d.source_label: d for d in resume.dates}
    for label in ("Tanggal Masuk", "Tanggal Keluar"):
        assert by_label[label].date_role is DateRole.UNKNOWN
        assert by_label[label].precision.value == "EXACT_DATETIME"  # the date itself is kept
    assert not any(d.date_role is DateRole.ADMISSION for doc in bundle.documents for d in doc.dates)


# --- ADR-REQ-004: extraction method vs text status -----------------------------------


def test_image_only_page_is_not_declared_non_textual(synthetic_bundle: ClaimDocumentBundle):
    image_page = synthetic_bundle.source_files[0].pages[5]
    assert image_page.page_kind is PageKind.CONTENT
    assert image_page.extraction_method is ExtractionMethod.UNKNOWN
    assert image_page.text_status is TextStatus.NOT_AVAILABLE
    image_evidence = [e for e in synthetic_bundle.evidence if e.page_id == image_page.page_id]
    assert [(e.content_kind, e.extraction_method) for e in image_evidence] == [
        (ContentKind.IMAGE_REGION, ExtractionMethod.UNKNOWN)
    ]


def test_no_text_is_never_assigned(synthetic_bundle: ClaimDocumentBundle):
    methods = {p.extraction_method for p in synthetic_bundle.pages.values()}
    methods |= {e.extraction_method for p in synthetic_bundle.pages.values() for e in p.elements}
    methods |= {e.extraction_method for e in synthetic_bundle.evidence}
    assert ExtractionMethod.NO_TEXT not in methods
