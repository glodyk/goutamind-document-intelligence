"""Deterministic recognition rules for logical documents and sections.

These are *vocabulary hints*: generic Indonesian / English form titles and
labels used in JKN claim bundles. They are deliberately not a description of
any one hospital's layout. Adding a rule is the intended way to evolve
classification before a model-based classifier exists.

Every rule is data, so it can later move to ``config/`` without code changes.
"""

import re
from dataclasses import dataclass
from typing import Literal

from app.vocabulary import DateRole, DocumentRole, DocumentType

TitleScope = Literal["FIRST_LINE", "TOP_LINES"]

TOP_LINES = 12
"""How many leading text lines of a page are searched for a document title."""


@dataclass(frozen=True, slots=True)
class TitleRule:
    document_type: DocumentType
    pattern: re.Pattern[str]
    # FIRST_LINE for short generic words (e.g. "RADIOLOGI") that also occur
    # as sub-headings inside other documents; TOP_LINES for specific phrases.
    scope: TitleScope


@dataclass(frozen=True, slots=True)
class MarkerRule:
    """Recognise an untitled first page by labels that must all be present."""

    document_type: DocumentType
    patterns: tuple[re.Pattern[str], ...]
    name: str


def _title(document_type: DocumentType, phrase: str, scope: TitleScope = "TOP_LINES") -> TitleRule:
    return TitleRule(document_type, re.compile(r"^" + phrase + r"\b", re.IGNORECASE), scope)


T = DocumentType
TITLE_RULES: tuple[TitleRule, ...] = (
    _title(T.SEP, r"SURAT EL[IE]GIBILITAS PESERTA"),
    _title(T.INA_CBG_OUTPUT, r"BERKAS KLAIM INDIVIDUAL PASIEN"),
    _title(T.DISCHARGE_SUMMARY, r"RINGKASAN PULANG"),
    _title(T.DISCHARGE_SUMMARY, r"(MEDICAL )?DISCHARGE SUMMARY"),
    _title(T.MEDICAL_RESUME, r"RESUME MEDIS"),
    _title(T.MEDICAL_RESUME, r"MEDICAL RESUME"),
    _title(T.ASSESSMENT, r"AS{1,2}ES{1,2}MENT? AWAL"),
    _title(T.ASSESSMENT, r"PENGKAJIAN AWAL"),
    _title(T.CPPT, r"CATATAN PERKEMBANGAN PASIEN TERINTEGRASI"),
    _title(T.CPPT, r"DETAIL CPPT"),
    _title(T.CPPT, r"CPPT", "FIRST_LINE"),
    _title(T.LABORATORY, r"HASIL (PEMERIKSAAN )?LABORATORIUM"),
    _title(T.LABORATORY, r"LABORATORY RESULT"),
    _title(T.RADIOLOGY, r"HASIL (PEMERIKSAAN )?RADIOLOGI"),
    _title(T.RADIOLOGY, r"RADIOLOGI", "FIRST_LINE"),
    _title(T.ECG, r"(EKG|ECG|ELEKTROKARDIOGRA(M|FI))", "FIRST_LINE"),
    _title(T.PRESCRIPTION, r"RESEP PASIEN"),
    _title(T.PRESCRIPTION, r"RESEP", "FIRST_LINE"),
    _title(T.BILLING, r"RINCIAN (BIAYA|TAGIHAN)"),
    _title(T.SERVICE_RECAP, r"REKAP BIAYA"),
    _title(T.SERVICE_RECAP, r"NOTA REKAP PELAYANAN"),
    _title(T.REFERRAL, r"SURAT RUJUKAN"),
    # Recognised titles with no matching document_type in DATA_MODEL 7.
    # They are typed OTHER (not UNKNOWN) and the title is kept verbatim.
    _title(T.OTHER, r"TRIA(S|G)E", "FIRST_LINE"),
    _title(T.OTHER, r"PERMINTAAN RAWAT INAP"),
    _title(T.OTHER, r"SURAT PERINTAH RAWAT INAP"),
)

MARKER_RULES: tuple[MarkerRule, ...] = (
    MarkerRule(
        T.SEP,
        (re.compile(r"^NO\.?\s*SEP\s*:", re.I), re.compile(r"^TGL\.?\s*SEP\s*:", re.I)),
        "SEP number and SEP date labels",
    ),
    MarkerRule(
        T.LABORATORY,
        (re.compile(r"^PEMERIKSAAN\s+HASIL\s+SATUAN\s+NILAI\s+RUJUKAN", re.I),),
        "laboratory result table header",
    ),
)

PAGE_COUNTER = re.compile(
    r"\b(?:HALAMAN|PAGE|LEMBAR)\s+(?P<k>\d{1,3})(?:\s*(?:OF|DARI|/)\s*(?P<n>\d{1,3}))?",
    re.IGNORECASE,
)
COUNTER_LINES = 3
"""Page counters are searched in the first and last few lines of a page."""

# Taxonomy section 9 gives these examples. Types without an example there
# (marked "assumed") follow the closest example and are listed in the PR.
DOCUMENT_ROLES: dict[DocumentType, tuple[DocumentRole, ...]] = {
    T.SEP: (DocumentRole.ADMINISTRATIVE,),
    T.INA_CBG_OUTPUT: (DocumentRole.CLAIM_CODING,),
    T.MEDICAL_RESUME: (DocumentRole.CLINICAL,),
    T.DISCHARGE_SUMMARY: (DocumentRole.CLINICAL,),  # assumed
    T.ASSESSMENT: (DocumentRole.CLINICAL,),  # assumed
    T.CPPT: (DocumentRole.CLINICAL,),  # assumed
    T.LABORATORY: (DocumentRole.DIAGNOSTIC,),
    T.RADIOLOGY: (DocumentRole.DIAGNOSTIC,),  # assumed
    T.ECG: (DocumentRole.DIAGNOSTIC,),  # assumed
    T.PRESCRIPTION: (DocumentRole.MEDICATION_TREATMENT,),
    T.MEDICATION_ORDER: (DocumentRole.MEDICATION_TREATMENT,),  # assumed
    T.BILLING: (DocumentRole.FINANCIAL,),
    T.SERVICE_RECAP: (DocumentRole.FINANCIAL,),  # assumed
    T.SUPPORTING_DOCUMENT: (DocumentRole.SUPPORTING,),
    # REFERRAL, OTHER, UNKNOWN: no role is assigned rather than guessed.
}

CLAIM_ANCHOR_TYPES: frozenset[DocumentType] = frozenset({T.SEP, T.INA_CBG_OUTPUT, T.BILLING, T.SERVICE_RECAP})
"""Taxonomy section 10. Dates on anchors never become clinical Events here."""

FINANCIAL_TYPES: frozenset[DocumentType] = frozenset({T.BILLING, T.SERVICE_RECAP})


@dataclass(frozen=True, slots=True)
class SectionRule:
    section_type: str
    pattern: re.Pattern[str]


def _section(section_type: str, phrase: str) -> SectionRule:
    # The lookahead (not \b) lets headings such as "O/" or "A/" match.
    return SectionRule(section_type, re.compile(r"^(?:" + phrase + r")(?![A-Za-z])", re.I))


SECTION_HEADING_MAX_LEN = 40
"""A heading is a short line; long lines are body text even if they start with a keyword."""

# Applied to non-financial documents only: inside a bill "RADIOLOGI" is a
# billing category, not a radiology result.
CLINICAL_SECTION_RULES: tuple[SectionRule, ...] = (
    _section("DIAGNOSIS", r"DIAGNOSA|DIAGNOSIS"),
    _section("PROCEDURE", r"PROSEDUR|PROCEDURE|TINDAKAN"),
    _section("MEDICATION", r"RESEP|TERAPI|OBAT|MEDICATION"),
    _section("PHYSICAL_EXAMINATION", r"PEMERIKSAAN FISIK|PHYSICAL EXAMINATION|OBJECTIVE|O/"),
    _section("HISTORY", r"ANAMNES[AI]S?|SUBJECTIVE|RIWAYAT|S/"),
    _section("ASSESSMENT", r"ASSESSMENT|ASESMEN|A/"),
    _section("PLAN", r"PLAN|PLANNING|P/"),
    _section("LABORATORY_RESULT", r"LABORATORIUM|PEMERIKSAAN HASIL SATUAN"),
    _section("RADIOLOGY", r"RADIOLOGI|RADIOLOGY"),
    _section("DISPOSITION", r"TINDAK LANJUT|KONDISI WAKTU PULANG|DISPOSITION"),
)
FINANCIAL_SECTION_TYPE = "BILLING_DETAIL"
DEFAULT_SECTION_TYPE = "GENERIC"

MAX_CHUNK_LINES = 12

# Date labels -> DATA_MODEL 17B date_role. Matched against the text just
# before a date on the same line. Labels that are not listed give UNKNOWN.
DATE_LABELS: tuple[tuple[re.Pattern[str], DateRole], ...] = (
    (re.compile(r"(TGL\.?|TANGGAL|TTL)\s*LAHIR|UMUR\s*/\s*TTL|LAHIR\s*/\s*UMUR", re.I), DateRole.BIRTH),
    (re.compile(r"(TGL\.?|TANGGAL)\s*(MASUK|ADMISI)", re.I), DateRole.ADMISSION),
    (re.compile(r"(TGL\.?|TANGGAL)\s*(KELUAR|PULANG|KRS)", re.I), DateRole.DISCHARGE),
    (re.compile(r"(TGL\.?|TANGGAL)\s*(REG(R)?ISTRASI|DAFTAR)", re.I), DateRole.REGISTRATION),
    (re.compile(r"(TGL\.?|TANGGAL)\s*ORDER", re.I), DateRole.ORDER),
    (re.compile(r"(TGL\.?|TANGGAL)\s*ENTRI", re.I), DateRole.ENTRY),
    (re.compile(r"DICETAK|(TGL\.?|TANGGAL)\s*CETAK|GENERATED", re.I), DateRole.PRINT),
    (re.compile(r"WAKTU\s*DATANG|JAM\s*DATANG", re.I), DateRole.SERVICE),
)
DATE_LABEL_WINDOW = 40
"""Characters before a date that are searched for its label."""
