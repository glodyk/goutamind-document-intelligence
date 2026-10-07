from app.document.models import Section
from app.extraction.facts import candidates_for_line
from app.vocabulary import Availability, FactType

GENERIC = Section("section-001", "doc-001", "GENERIC", None, 1, 1)
DIAGNOSIS = Section("section-002", "doc-001", "DIAGNOSIS", "DIAGNOSA", 1, 1)


def one(text: str, section: Section = GENERIC, carry=None):
    found = list(candidates_for_line(text, section, carry))
    assert len(found) == 1, found
    return found[0]


def test_labelled_diagnosis_keeps_label_and_code_only():
    c = one("Diagnosa Awal : J18.9 - Pneumonia Kelas Rawat : Kelas 1")
    assert (c.fact_type, c.value, c.source_label) == (FactType.DIAGNOSIS, "J18.9", "Diagnosa Awal")
    assert c.coding_system is None  # not printed, so not assumed


def test_coding_system_only_when_printed():
    assert one("Diagnosa ICD 10 : K35.8 Appendicitis").coding_system == "ICD 10"


def test_dash_is_not_documented_not_absent():
    c = one("Diagnosa Sekunder : -")
    assert c.value is None
    assert c.availability is Availability.NOT_DOCUMENTED


def test_free_text_or_empty_values_are_not_extracted():
    assert list(candidates_for_line("Diagnosa : P2002 kontrol", GENERIC)) == []
    assert list(candidates_for_line("Diagnosa ICD 10 :", GENERIC)) == []


def test_coded_line_in_diagnosis_section():
    c = one("K35.8 Acute appendicitis", DIAGNOSIS)
    assert (c.value, c.source_label) == ("K35.8", "DIAGNOSA")
    assert list(candidates_for_line("K35.8 Acute appendicitis", GENERIC)) == []


def test_unlabelled_code_continues_a_labelled_list():
    first = one("Prosedur : 88.72 Diagnostic ultrasound of heart")
    second = one("93.96 Other oxygen enrichment", carry=first)
    assert (second.fact_type, second.value, second.source_label) == (
        FactType.PROCEDURE,
        "93.96",
        "Prosedur",
    )
    assert list(candidates_for_line("93.96 Other oxygen enrichment", GENERIC)) == []


def test_prescription_line_kept_whole():
    c = one("R/ DISPOSABLE SYRINGE 5 ml")
    assert (c.fact_type, c.value) == (FactType.MEDICATION, "DISPOSABLE SYRINGE 5 ml")
