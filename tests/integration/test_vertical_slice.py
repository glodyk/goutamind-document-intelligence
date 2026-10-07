"""End-to-end checks on the synthetic bundle (tests/fixtures/synthetic_bundle.py)."""

import json
from pathlib import Path

from app.bundle import ClaimDocumentBundle
from app.evidence.models import Evidence, Fact
from app.vocabulary import (
    AssignmentBasis,
    ContentKind,
    DocumentType,
    EventType,
    ExtractionMethod,
    IngestionStatus,
    PageKind,
    Provenance,
    TemporalPrecision,
)
from pipeline.report import render_inspection
from pipeline.run import main, process_pdf
from pipeline.serialize import to_json_dict
from tests.conftest import FIXED_NOW


def doc_types(bundle: ClaimDocumentBundle) -> list[tuple[str, list[int]]]:
    return [(d.document_type.value, d.page_numbers) for d in bundle.documents]


# --- SourceFile / Page ---------------------------------------------------


def test_pdf_is_ingested_with_all_pages(synthetic_bundle: ClaimDocumentBundle):
    source = synthetic_bundle.source_files[0]
    assert source.ingestion_status is IngestionStatus.INGESTED
    assert source.page_count == 16
    assert [p.page_number for p in source.pages] == list(range(1, 17))


def test_same_input_gives_same_identities(synthetic_pdf_path: Path):
    first = to_json_dict(process_pdf(synthetic_pdf_path, now=FIXED_NOW))
    second = to_json_dict(process_pdf(synthetic_pdf_path, now=FIXED_NOW))
    assert first == second


def test_blank_and_image_pages_are_kept(synthetic_bundle: ClaimDocumentBundle):
    pages = {p.page_number: p for p in synthetic_bundle.source_files[0].pages}
    assert [n for n, p in pages.items() if p.page_kind is PageKind.BLANK] == [5, 7, 15]
    assert pages[6].page_kind is PageKind.CONTENT and pages[6].text_lines == []
    # Blank pages exist but belong to no Document.
    assert [p.page_number for p in synthetic_bundle.unassigned_pages()] == [5, 7, 15]


# --- Document --------------------------------------------------------------


def test_logical_documents_are_independent_of_the_pdf(synthetic_bundle: ClaimDocumentBundle):
    assert doc_types(synthetic_bundle) == [
        ("INA_CBG_OUTPUT", [1]),
        ("SEP", [2]),
        ("MEDICAL_RESUME", [3, 4]),
        ("UNKNOWN", [6]),
        ("LABORATORY", [8, 9]),
        ("LABORATORY", [10]),
        ("ASSESSMENT", [11, 12]),
        ("SERVICE_RECAP", [13]),
        ("OTHER", [14]),
        ("UNKNOWN", [16]),
    ]


def test_documents_reference_pages_not_contain_them(synthetic_bundle: ClaimDocumentBundle):
    pages = synthetic_bundle.pages
    for document in synthetic_bundle.documents:
        assert document.page_refs
        for ref in document.page_refs:
            page = pages[ref.page_id]
            assert (page.source_file_id, page.page_number) == (ref.source_file_id, ref.page_number)


def test_boundary_rules(synthetic_bundle: ClaimDocumentBundle):
    by_first_page = {d.page_numbers[0]: d for d in synthetic_bundle.documents}
    assert by_first_page[2].boundary_basis is AssignmentBasis.MARKER  # untitled SEP
    # p4 starts with "RESEP" but its printed counter says "2 of 2".
    assert [r.basis for r in by_first_page[3].page_refs] == [
        AssignmentBasis.TITLE,
        AssignmentBasis.PAGE_COUNTER,
    ]
    # Two lab reports in a row are split by the "1 of 1" counter.
    assert by_first_page[10].boundary_basis is AssignmentBasis.PAGE_COUNTER
    assert by_first_page[11].page_refs[1].basis is AssignmentBasis.CONTINUATION


def test_uncertain_classification_stays_unknown(synthetic_bundle: ClaimDocumentBundle):
    unknown = [d for d in synthetic_bundle.documents if d.document_type is DocumentType.UNKNOWN]
    assert [d.boundary_basis for d in unknown] == [AssignmentBasis.IMAGE_PAGE, AssignmentBasis.UNTITLED_START]
    assert all(d.document_role == [] for d in unknown)
    triage = next(d for d in synthetic_bundle.documents if d.document_type is DocumentType.OTHER)
    assert triage.document_title == "TRIASE"


def test_unknown_metadata_is_not_invented(synthetic_bundle: ClaimDocumentBundle):
    for document in synthetic_bundle.documents:
        assert document.classification_confidence is None
        assert document.document_date is None
        assert document.completeness_status == "UNKNOWN"


# --- Section / Chunk ---------------------------------------------------------


def test_sections_and_chunks_keep_parent_references(synthetic_bundle: ClaimDocumentBundle):
    elements = {e.element_id: e for p in synthetic_bundle.pages.values() for e in p.elements}
    resume = synthetic_bundle.documents[2]
    assert [s.section_type for s in resume.sections] == [
        "GENERIC",
        "HISTORY",
        "DIAGNOSIS",
        "PROCEDURE",
        "MEDICATION",
    ]
    for document in synthetic_bundle.documents:
        for section in document.sections:
            assert section.document_id == document.document_id
            for chunk in section.chunks:
                assert (chunk.section_id, chunk.document_id) == (section.section_id, document.document_id)
                # Chunk text is exactly the text of its elements, all on its one page.
                lines = [elements[ref] for ref in chunk.element_refs]
                assert chunk.text == "\n".join(e.text or "" for e in lines)
                assert {e.page_id for e in lines} == {chunk.page_id}


def test_financial_category_is_not_a_clinical_section(synthetic_bundle: ClaimDocumentBundle):
    recap = next(d for d in synthetic_bundle.documents if d.document_type is DocumentType.SERVICE_RECAP)
    assert [s.section_type for s in recap.sections] == ["BILLING_DETAIL"]


def test_image_only_document_has_no_sections(synthetic_bundle: ClaimDocumentBundle):
    assert synthetic_bundle.documents[3].sections == []


# --- Evidence ----------------------------------------------------------------


def test_evidence_references_the_physical_source(synthetic_bundle: ClaimDocumentBundle):
    pages = synthetic_bundle.pages
    elements = {e.element_id: e for p in pages.values() for e in p.elements}
    for ev in synthetic_bundle.evidence:
        page = pages[ev.page_id]
        assert ev.source_file_id == page.source_file_id
        assert ev.page_number == page.page_number
        assert ev.extraction_method in {ExtractionMethod.NATIVE_TEXT, ExtractionMethod.UNKNOWN}
        if ev.content_kind is ContentKind.TEXT:
            assert ev.source_text == elements[ev.element_id or ""].text
        assert ev.bbox is None and ev.confidence is None  # not available, not invented


def test_non_textual_evidence_has_no_text(synthetic_bundle: ClaimDocumentBundle):
    image_evidence = [e for e in synthetic_bundle.evidence if e.content_kind is ContentKind.IMAGE_REGION]
    assert len(image_evidence) == 1
    assert image_evidence[0].page_number == 6
    assert image_evidence[0].source_text is None


def test_evidence_does_not_become_a_fact(synthetic_bundle: ClaimDocumentBundle):
    cited = {ref for f in synthetic_bundle.facts for ref in f.evidence_refs}
    cited |= {ref for e in synthetic_bundle.events for ref in e.evidence_refs}
    uncited = [e for e in synthetic_bundle.evidence if e.evidence_id not in cited]
    # Boundary and image evidence exist without any Fact built on them.
    assert uncited and {e.purpose for e in uncited} == {"page_membership"}
    assert not any(isinstance(e, Fact) for e in synthetic_bundle.evidence)
    assert not any(isinstance(f, Evidence) for f in synthetic_bundle.facts)


# --- Facts / Events ------------------------------------------------------------


def test_fact_to_evidence_to_page_to_source_file(synthetic_bundle: ClaimDocumentBundle):
    """The provenance chain required by the PR brief."""
    evidence = {e.evidence_id: e for e in synthetic_bundle.evidence}
    pages = synthetic_bundle.pages
    source_files = {s.source_file_id: s for s in synthetic_bundle.source_files}

    fact = next(f for f in synthetic_bundle.facts if f.value == "R10.4")
    assert fact.provenance is Provenance.SOURCE_FACT
    ev = evidence[fact.evidence_refs[0]]
    page = pages[ev.page_id]
    source = source_files[page.source_file_id]
    assert (ev.document_type, page.page_number, source.source_reference) == (
        "SEP",
        2,
        "synthetic_bundle.pdf",
    )
    assert ev.source_text == "Diagnosa Awal : R10.4 - Abdominal pain"

    for every in synthetic_bundle.facts:
        assert every.evidence_refs and all(r in evidence for r in every.evidence_refs)
        assert every.derived_from_refs == [] and every.inference_basis_refs == []


def test_same_diagnosis_in_two_documents_stays_two_facts(synthetic_bundle: ClaimDocumentBundle):
    k358 = [f for f in synthetic_bundle.facts if f.value == "K35.8"]
    assert {f.document_id for f in k358} == {"doc-001", "doc-003"}
    assert {f.source_label for f in k358} == {"Diagnosa Utama", "DIAGNOSA"}


def test_minimal_facts(synthetic_bundle: ClaimDocumentBundle):
    summary = [(f.fact_type.value, f.value, f.availability_status.value) for f in synthetic_bundle.facts]
    assert summary == [
        ("DIAGNOSIS", "K35.8", "PRESENT"),
        ("DIAGNOSIS", None, "NOT_DOCUMENTED"),
        ("PROCEDURE", "47.09", "PRESENT"),
        ("PROCEDURE", "99.21", "PRESENT"),
        ("DIAGNOSIS", "R10.4", "PRESENT"),
        ("DIAGNOSIS", "K35.8", "PRESENT"),
        ("PROCEDURE", "47.09", "PRESENT"),
        ("MEDICATION", "CEFTRIAXONE 1 g INJEKSI 2x1", "PRESENT"),
        ("MEDICATION", "DISPOSABLE SYRINGE 5 ml", "PRESENT"),
    ]


def test_events_only_from_clinical_documents(synthetic_bundle: ClaimDocumentBundle):
    by_id = {d.document_id: d for d in synthetic_bundle.documents}
    events = [
        (e.event_type, by_id[e.document_id or ""].document_type, e.temporal_value.precision)
        for e in synthetic_bundle.events
    ]
    assert events == [
        (EventType.PATIENT_ARRIVAL, DocumentType.ASSESSMENT, TemporalPrecision.DATE),
        (EventType.PATIENT_ARRIVAL, DocumentType.OTHER, TemporalPrecision.EXACT_DATETIME),
    ]
    assert all(e.care_pathway == "UNKNOWN" and e.care_stage == "UNKNOWN" for e in synthetic_bundle.events)


def test_claim_anchor_dates_stay_document_metadata(synthetic_bundle: ClaimDocumentBundle):
    inacbg = synthetic_bundle.documents[0]
    labelled = {d.source_label: d for d in inacbg.dates}
    masuk = labelled["Tanggal Masuk"]
    assert masuk.precision is TemporalPrecision.UNKNOWN  # "03/02/2025" is ambiguous
    assert masuk.raw_text == "03/02/2025"
    assert masuk.date_role.value == "UNKNOWN"  # not ADMISSION (ADR-REQ-003)
    assert not any(e.document_id == inacbg.document_id for e in synthetic_bundle.events)


# --- Output ----------------------------------------------------------------------


def test_inspection_report(synthetic_bundle: ClaimDocumentBundle):
    report = render_inspection(synthetic_bundle)
    assert "SourceFile: synthetic_bundle.pdf" in report
    assert "3. MEDICAL_RESUME" in report and "pages: 3-4" in report
    assert "fact-005 DIAGNOSIS diagnosis_code='R10.4'" in report
    hidden = render_inspection(synthetic_bundle, show_source_text=False)
    assert "Abdominal pain" not in hidden and 'title: "' not in hidden


def test_cli_writes_json_and_report(synthetic_pdf_path: Path, tmp_path: Path):
    out = tmp_path / "out"
    assert main([str(synthetic_pdf_path), "--out", str(out)]) == 0
    data = json.loads((out / "synthetic_bundle.bundle.json").read_text("utf-8"))
    assert len(data["documents"]) == 10
    assert data["canonical_claim"] is None and data["timeline"] == []
    assert (out / "synthetic_bundle.inspection.txt").read_text("utf-8").startswith("SourceFile:")
    assert (out / "synthetic_bundle.page_assignment.txt").read_text("utf-8").startswith("Page assignment:")


def test_cli_reports_failure_for_bad_pdf(tmp_path: Path):
    bad = tmp_path / "bad.pdf"
    bad.write_bytes(b"%PDF-1.4 broken")
    assert main([str(bad), "--out", str(tmp_path / "out")]) == 1
    data = json.loads((tmp_path / "out" / "bad.bundle.json").read_text("utf-8"))
    assert data["source_files"][0]["ingestion_status"] == "FAILED"
    assert data["documents"] == []


def test_golden_example_is_up_to_date(tmp_path: Path):
    """examples/golden_claim is the regression reference; regenerate it with
    ``python -m scripts.make_synthetic_bundle`` when behaviour changes on purpose."""
    golden = Path(__file__).resolve().parents[2] / "examples" / "golden_claim"
    pdf = tmp_path / "synthetic_claim_bundle.pdf"
    pdf.write_bytes((golden / "synthetic_claim_bundle.pdf").read_bytes())
    report = render_inspection(process_pdf(pdf, now=FIXED_NOW))
    assert report == (golden / "synthetic_claim_bundle.inspection.txt").read_text("utf-8")
