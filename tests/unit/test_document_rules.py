from app.document.segmentation import find_marker, find_page_counter, find_title
from app.document.structure import heading_type
from app.extraction.models import DocumentElement
from app.vocabulary import DocumentType, ElementType, ExtractionMethod


def lines(*texts: str) -> list[DocumentElement]:
    return [
        DocumentElement(f"el-{i}", "page-001", 1, ElementType.TEXT, ExtractionMethod.NATIVE_TEXT, t)
        for i, t in enumerate(texts)
    ]


def test_title_found_below_a_letterhead():
    match = find_title(lines("PEMERINTAH KABUPATEN", "RSUD CONTOH", "RESUME MEDIS IGD", "Nama : X"))
    assert match is not None
    assert match.document_type is DocumentType.MEDICAL_RESUME
    assert match.element.text == "RESUME MEDIS IGD"


def test_generic_word_is_only_a_title_on_the_first_line():
    assert find_title(lines("RADIOLOGI", "Nama : X")).document_type is DocumentType.RADIOLOGY
    # Inside a bill, "RADIOLOGI" is a category heading, not a new document.
    assert find_title(lines("OPERASI", "SUBTOTAL Rp 0", "RADIOLOGI", "SUBTOTAL Rp 0")) is None


def test_untitled_sep_is_recognised_by_its_labels():
    match = find_marker(lines("No.SEP :0000X", "Tgl.SEP :2025-01-01", "Nama : X"))
    assert match is not None and match.document_type is DocumentType.SEP
    assert find_marker(lines("No BPJS : 000", "No SEP : 000")) is None  # one label is not enough


def test_page_counter_formats():
    assert find_page_counter(lines("a", "b", "Halaman 2 of 3 Dicetak pada x")).label == "2/3"
    assert find_page_counter(lines("a", "Resume Medis Rumah Sakit Halaman 4")).label == "4"
    assert find_page_counter(lines("Lembar 1 / 1")).label == "1/1"
    assert find_page_counter(lines("tanpa nomor halaman")) is None


def test_section_headings():
    assert heading_type("DIAGNOSA") == "DIAGNOSIS"
    assert heading_type("Assessment :") == "ASSESSMENT"
    assert heading_type("A/") == "ASSESSMENT"
    assert heading_type("PEMERIKSAAN FISIK") == "PHYSICAL_EXAMINATION"
    assert heading_type("Diagnosa : -") is None  # a label with a value is not a heading
    assert heading_type("TERAPI/PENGOBATAN DI RUMAH AMOKSISILIN 500 mg 3x1") is None
    assert heading_type("Catatan bebas") is None
