"""Controlled vocabularies used by the vertical slice.

Every enum here mirrors a vocabulary in ``docs/DATA_MODEL.md``. The section
number is given next to each enum so the code and the contract can be checked
against each other. Values marked ``IMPLEMENTATION`` are not in the data model
and are reported in the PR as implementation decisions.
"""

from enum import StrEnum


class PageKind(StrEnum):
    """DATA_MODEL 5A ``page_kind``."""

    CONTENT = "CONTENT"
    BLANK = "BLANK"
    SEPARATOR = "SEPARATOR"
    UNKNOWN = "UNKNOWN"


class Modality(StrEnum):
    """DATA_MODEL 5A ``modality``."""

    DIGITAL_TEXT = "DIGITAL_TEXT"
    SCANNED_IMAGE = "SCANNED_IMAGE"
    PHOTO = "PHOTO"
    MIXED = "MIXED"
    UNKNOWN = "UNKNOWN"


class ExtractionMethod(StrEnum):
    """DATA_MODEL 11A ``extraction_method``."""

    NATIVE_TEXT = "NATIVE_TEXT"
    OCR = "OCR"
    HANDWRITING_RECOGNITION = "HANDWRITING_RECOGNITION"
    MANUAL_TRANSCRIPTION = "MANUAL_TRANSCRIPTION"
    NO_TEXT = "NO_TEXT"
    UNKNOWN = "UNKNOWN"


class TextStatus(StrEnum):
    """IMPLEMENTATION: outcome of the text-extraction attempt on a page.

    Kept separate from ``extraction_method`` so that "no text was obtained"
    is never confused with "the content is non-textual" (``NO_TEXT``).
    """

    EXTRACTED = "EXTRACTED"
    NOT_AVAILABLE = "NOT_AVAILABLE"
    FAILED = "FAILED"


class IngestionStatus(StrEnum):
    """IMPLEMENTATION: outcome of opening a source file."""

    INGESTED = "INGESTED"
    FAILED = "FAILED"


class ElementType(StrEnum):
    """DATA_MODEL 11 element types."""

    TEXT = "TEXT"
    TABLE = "TABLE"
    TABLE_CELL = "TABLE_CELL"
    IMAGE = "IMAGE"
    LINE = "LINE"
    HEADER = "HEADER"
    FOOTER = "FOOTER"
    OTHER = "OTHER"


class DocumentType(StrEnum):
    """DATA_MODEL 7 ``document_type``.

    ``UNKNOWN`` is an IMPLEMENTATION addition: ``OTHER`` means "recognised,
    but not one of the listed types", whereas ``UNKNOWN`` means "not
    classified". The data model list has no value for the second case.
    """

    SEP = "SEP"
    INA_CBG_OUTPUT = "INA_CBG_OUTPUT"
    MEDICAL_RESUME = "MEDICAL_RESUME"
    DISCHARGE_SUMMARY = "DISCHARGE_SUMMARY"
    ASSESSMENT = "ASSESSMENT"
    CPPT = "CPPT"
    LABORATORY = "LABORATORY"
    RADIOLOGY = "RADIOLOGY"
    ECG = "ECG"
    PRESCRIPTION = "PRESCRIPTION"
    MEDICATION_ORDER = "MEDICATION_ORDER"
    BILLING = "BILLING"
    SERVICE_RECAP = "SERVICE_RECAP"
    REFERRAL = "REFERRAL"
    SUPPORTING_DOCUMENT = "SUPPORTING_DOCUMENT"
    OTHER = "OTHER"
    UNKNOWN = "UNKNOWN"


class DocumentRole(StrEnum):
    """DATA_MODEL 7 ``document_role``."""

    ADMINISTRATIVE = "ADMINISTRATIVE"
    CLINICAL = "CLINICAL"
    DIAGNOSTIC = "DIAGNOSTIC"
    MEDICATION_TREATMENT = "MEDICATION_TREATMENT"
    FINANCIAL = "FINANCIAL"
    CLAIM_CODING = "CLAIM_CODING"
    SUPPORTING = "SUPPORTING"


class BoundaryBasis(StrEnum):
    """IMPLEMENTATION: why a page was attached to a Document."""

    TITLE = "TITLE"
    MARKER = "MARKER"
    PAGE_COUNTER = "PAGE_COUNTER"
    CONTINUATION = "CONTINUATION"
    IMAGE_PAGE = "IMAGE_PAGE"
    UNTITLED_START = "UNTITLED_START"


class Availability(StrEnum):
    """DATA_MODEL 41 ``availability_status``."""

    PRESENT = "PRESENT"
    NOT_FOUND = "NOT_FOUND"
    NOT_DOCUMENTED = "NOT_DOCUMENTED"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    EXPLICITLY_NEGATED = "EXPLICITLY_NEGATED"
    UNKNOWN = "UNKNOWN"


class Provenance(StrEnum):
    """DATA_MODEL 14."""

    SOURCE_FACT = "SOURCE_FACT"
    DERIVED_FACT = "DERIVED_FACT"
    INFERRED_FACT = "INFERRED_FACT"
    MODEL_OUTPUT = "MODEL_OUTPUT"


class ContentKind(StrEnum):
    """DATA_MODEL 15 ``content_kind``."""

    TEXT = "TEXT"
    IMAGE_REGION = "IMAGE_REGION"
    OTHER = "OTHER"


class Sensitivity(StrEnum):
    """DATA_MODEL 15A (proposed; ADR-08 open)."""

    NONE_KNOWN = "NONE_KNOWN"
    CONTAINS_PERSONAL_DATA = "CONTAINS_PERSONAL_DATA"
    UNKNOWN = "UNKNOWN"


class RedactionState(StrEnum):
    """DATA_MODEL 15A (proposed; ADR-08 open)."""

    ORIGINAL = "ORIGINAL"
    REDACTED = "REDACTED"
    DE_IDENTIFIED = "DE_IDENTIFIED"
    UNKNOWN = "UNKNOWN"


class TemporalPrecision(StrEnum):
    """DATA_MODEL 17."""

    EXACT_DATETIME = "EXACT_DATETIME"
    DATE = "DATE"
    MONTH = "MONTH"
    YEAR = "YEAR"
    UNKNOWN = "UNKNOWN"


class DateRole(StrEnum):
    """DATA_MODEL 17B (proposed; ADR-05 open)."""

    SERVICE = "SERVICE"
    REGISTRATION = "REGISTRATION"
    ADMISSION = "ADMISSION"
    DISCHARGE = "DISCHARGE"
    ORDER = "ORDER"
    SPECIMEN = "SPECIMEN"
    RESULT = "RESULT"
    VERIFICATION = "VERIFICATION"
    ENTRY = "ENTRY"
    PRINT = "PRINT"
    BILLING = "BILLING"
    BIRTH = "BIRTH"
    UNKNOWN = "UNKNOWN"


class FactType(StrEnum):
    """Fact types demonstrated in this slice (DATA_MODEL 12 example uses DIAGNOSIS)."""

    DIAGNOSIS = "DIAGNOSIS"
    PROCEDURE = "PROCEDURE"
    MEDICATION = "MEDICATION"


class EventType(StrEnum):
    """Subset of DATA_MODEL 13 ``event_type`` examples used in this slice."""

    PATIENT_ARRIVAL = "PATIENT_ARRIVAL"
    ADMISSION = "ADMISSION"
    DISCHARGE = "DISCHARGE"


UNKNOWN = "UNKNOWN"
"""Placeholder for care_pathway / care_stage, which this slice never infers."""
