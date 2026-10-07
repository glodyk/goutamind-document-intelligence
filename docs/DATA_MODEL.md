# GOUTAMIND Data Model

**Version:** 0.1, revision r1 (proposed)
**Status:** Draft / Architecture Baseline, pending owner review
**Related Document:** `docs/DOCUMENT_TAXONOMY.md`

---

## 0. Revision Notes (baseline 0.1 → revision r1)

This revision (r1) keeps every concept, section number and field of baseline 0.1.
Changes are **additive**. Nothing was removed or renamed.

> **Slice-1 decisions `[S1]`.** Four decisions taken after running the first
> vertical slice (PR #1 review) are applied as small additive notes in
> sections 7, 11A, 13 and 17B, marked `[S1, ADR-REQ-00n]`. Appendix C
> lists what changed, why, the observed evidence and what stays open.

New material is marked with a tag:

- `[GAP-n]` points to the gap register in Appendix A (gaps found by
  mapping this model against two representative claim bundles, one
  emergency/IGD and one inpatient).
- `[ADR-nn]` marks an **Architecture Decision Required**. The text
  describes the problem and a *proposed, non-binding* shape. The
  decision belongs to the architecture owner and is **not locked**.
  Appendix B lists every open decision.

Gap types used throughout: `structural`, `data-model`, `provenance`,
`extraction`, `domain-decision`.

Fields introduced in this revision are **proposed**. They must not be
turned into JSON Schema until their governing ADR (if any) is resolved.

This revision was cross-checked against the full `DOCUMENT_TAXONOMY.md`
(sections 1-31). Section 25 of the taxonomy lists 14 stress-test
concerns; Appendix A maps them. Where the taxonomy already states a
principle (sections 6, 26, 27), it is cited, not redefined.

Editorial fixes (no semantic change): `input_format` was listed twice
in section 6; section 22 used "Clinical Claim" and is now titled
"Canonical Clinical Claim" to match the rest of the document.

---

## 1. Purpose

This document defines the conceptual data model for the GOUTAMIND
Document Intelligence pipeline.

`DOCUMENT_TAXONOMY.md` defines the vocabulary and semantic taxonomy.

This document defines how those concepts are represented as data and
how they relate to one another.

The data model is designed to support heterogeneous healthcare claim
document bundles from different hospitals while maintaining:

- semantic consistency;
- evidence traceability;
- provenance;
- temporal information;
- clinical workflow relationships;
- separation between source information and model output.

This document is not an official BPJS Kesehatan data standard.

---

# 2. Design Principles

### 2.1 Source Before Intelligence

Source documents remain the foundation of the system.

```text
Source Document
      ↓
Semantic Representation
      ↓
Canonical Claim
      ↓
Evidence
      ↓
Timeline
      ↓
Narrative / Intelligence
```

### 2.2 Preserve Lineage

Important information must be traceable back to its source.

```text
Intelligence
     ↓
Canonical Fact / Event
     ↓
Evidence
     ↓
Document
     ↓
Original Source
```

### 2.3 Separate Physical and Semantic Representation

The physical document representation must not be confused with the
canonical clinical claim.

```text
Physical Document
        ↓
Document Representation
        ↓
Semantic Document
        ↓
Canonical Claim
```

### 2.4 Preserve Uncertainty

The system must not manufacture precision that does not exist in the
source. This applies especially to dates, times, diagnoses,
procedures, clinical interpretations and inferred information.

### 2.5 Hospital-Agnostic Canonical Model

Hospital-specific layouts and terminology belong in document
understanding and extraction. They must not unnecessarily leak into
the canonical claim model.

### 2.6 Core Distinctions `[r1]`

These distinctions are the interpretive backbone of the model. Every
entity and field below must be read in their light.

| Distinction | Meaning |
|---|---|
| PDF ≠ logical Document | A physical file is a container; it may hold many logical documents, blank pages and photos of other documents. |
| Document ≠ clinical workflow | Document type and role never imply care pathway or care stage. |
| Document order ≠ clinical event order | Page order carries no clinical chronology. |
| Source Fact ≠ Derived Fact ≠ Inferred Fact ≠ Model Output | Provenance classes are never silently converted. |
| Evidence ≠ Fact | Evidence says *where* something is written. A Fact says *what* is asserted. Evidence is never itself a clinical assertion. |
| Narrative ≠ Intelligence | Narrative presents; Intelligence analyses. Narrative is never a source of analytical truth. |
| Confidence ≠ truth | Confidence qualifies extraction/inference, not clinical correctness. |

---

# 3. Top-Level Model

```text
Claim Document Bundle
│
├── Bundle Metadata
│
├── Source Files[]                       [r1, GAP-1]
│   └── Pages[]
│       └── Document Elements[]          (Raw Document Representation)
│
├── Documents[]
│   │
│   ├── Document Metadata
│   ├── Source Facility
│   ├── Page References[]                [r1, GAP-1]
│   ├── Sections[]
│   │   └── Chunks[]
│   │       ├── Facts[]
│   │       └── Events[]
│   │
│   └── Document Evidence References
│
├── Canonical Claim
│   │
│   ├── Claim Header
│   ├── Participant
│   ├── Encounter
│   ├── Care Pathways[]
│   ├── Diagnoses[]
│   ├── Procedures[]
│   ├── Medications[]
│   ├── Clinical Findings[]
│   ├── Investigations[]
│   ├── Events[]
│   ├── Claim Coding
│   └── Costs[]
│
├── Evidence[]
│
├── Source Discrepancies[]               [r1, GAP-3, ADR-02]
│
├── Timeline[]
│
├── Narrative
│
└── Intelligence[]
```

The semantic hierarchy `Claim Document Bundle → Document → Section →
Chunk → Fact / Event` is unchanged. `Source Files`, `Pages` and
`Document Elements` belong to the **Raw Document Representation**
layer and sit beside, not inside, that hierarchy. A Document points to
them through page references. This keeps the physical layer and the
semantic layer separate (principle 2.3).

The detailed JSON representation will be defined later.

---

# 4. Identity Model

Every major entity must have a stable identifier within the processing
context.

Initial identifiers:

```text
bundle_id
document_id
section_id
chunk_id
fact_id
event_id
claim_id
encounter_id
evidence_id
timeline_event_id
intelligence_id
```

Proposed additions `[r1]`:

```text
source_file_id          (GAP-1)
page_id                 (GAP-1)
element_id              (already used by Evidence; now owned by Document Element)
discrepancy_id          (GAP-3)
```

Identifiers should be opaque and must not encode business meaning
unless there is a documented reason to do so.

Example: `doc-001`, `section-001`, `chunk-001`, `fact-001`,
`event-001`, `evidence-001`.

The identifier itself should not be interpreted as clinical
information. A claim number, SEP number, medical record number or any
other source-printed identifier is a **Fact value**, never an entity
identifier.

---

# 5. Claim Document Bundle

A ClaimDocumentBundle represents the complete collection of documents
associated with one healthcare claim or service episode.

```text
ClaimDocumentBundle
│
├── bundle_id
├── claim_id
├── source_metadata
├── source_files[]            [r1]
├── documents[]
├── canonical_claim
├── evidence[]
├── source_discrepancies[]    [r1]
├── timeline[]
├── narrative
└── intelligence[]
```

A bundle may contain one document, multiple documents, multiple
document files, and supporting documents from other authorized
facilities.

A bundle is the primary processing boundary for a claim document
intelligence workflow.

## 5A. Source File and Page `[r1, GAP-1, structural]`

A **SourceFile** is the physical container of one or more pages. It is
the unit that was actually ingested (for example one PDF). A
SourceFile is **not** a Document.

Proposed SourceFile attributes:

```text
source_file_id
source_reference
media_type
page_count
content_digest        (optional; supports duplicate-file detection)
ingested_at
```

A **Page** is one physical page of a SourceFile.

Proposed Page attributes:

```text
page_id
source_file_id
page_number
page_kind
modality
extraction_method
```

`page_kind` initial values: `CONTENT`, `BLANK`, `SEPARATOR`,
`UNKNOWN`. Blank and separator pages are real pages and must be
representable. They simply belong to no Document.

`modality` initial values: `DIGITAL_TEXT`, `SCANNED_IMAGE`,
`PHOTO`, `MIXED`, `UNKNOWN`. See section 11A for `extraction_method`.

Observed in representative bundles (informational, not
hospital-specific rules):

- one PDF contained roughly 9 to 12 logical documents;
- the pages of one logical document were not always contiguous;
- documents from another facility were embedded as photographs;
- blank separator pages occurred between embedded photographs;
- a page could be a repeated copy of an earlier document.

Consequences for the model:

- `Document.page_refs[]` (section 7) lists pages and may be
  non-contiguous;
- a Page need not belong to any Document;
- duplicate content is representable (see `duplicate_of`, section 7).

`[ADR-01]` Page-to-document multiplicity: may one Page belong to more
than one Document (for example two forms printed on one page), and may
a Document start or end in the middle of a Page? The audit did not
establish either case. Until decided, the model **does not assume**
one-page-one-document, and Document-to-Page is many-to-many by
structure.

---

# 6. Bundle Metadata

Initial attributes:

```text
bundle_id
claim_id
created_at
source_reference
input_format
processing_status
schema_version
```

`input_format` examples: `PDF`, `TXT`, `CSV`, `EXCEL`, `API`,
`DATABASE`, `OTHER`.

The model should not permanently depend on PDF as the only input
format.

---

# 7. Document

A Document represents a logically identifiable document inside a
Claim Document Bundle.

Initial attributes (baseline 0.1, unchanged):

```text
document_id
document_type
document_role[]
source_facility
document_title
document_date
page_range
source_reference
classification_confidence
sections[]
```

Proposed additions `[r1]`:

```text
page_refs[]            (GAP-1)  list of {source_file_id, page_number}
                                [S1, ADR-REQ-001] each entry also carries
                                page_id, basis, evidence_ref (see below)
dates[]                (GAP-6)  list of Temporal Values with date_role
duplicate_of           (GAP-9)  optional document_id
completeness_status    (see section 41)
```

Page membership provenance `[S1, ADR-REQ-001, decided]`: assigning a
page to a Document is an inference by the segmenter, so each
`page_refs[]` entry records **why** the page is there:

```text
page_id        the Page (section 5A)
basis          the rule that placed it: TITLE | MARKER | PAGE_COUNTER |
               CONTINUATION | IMAGE_PAGE | EXTRACTION_FAILED | UNTITLED_START
evidence_ref   the Evidence that rule used (title line, marker line,
               counter line, image region, or for CONTINUATION /
               UNTITLED_START the line the page starts with)
```

`basis` is provenance, not confidence; no numeric score is attached
until there is a basis for calibrating one. `page_refs[]` stays the
authoritative list.

Compatibility: `page_range` is retained as a convenience for the
common contiguous case. When a Document is non-contiguous,
`page_refs[]` is authoritative and `page_range` is `UNKNOWN` or the
bounding range, which must be stated.

`document_date` is retained but is **ambiguous by itself** (GAP-6):
a document can carry a print date, service date, order date and
result date. `document_date` should hold only a date whose role is
documented. All other dates go in `dates[]` with an explicit
`date_role` (section 17).

`duplicate_of` `[structural]`: a Document whose content repeats
another Document. It is a derived relationship (provenance
`DERIVED_FACT` or `INFERRED_FACT`) and must reference the evidence
that justifies it. A duplicate is **not deleted**; downstream
aggregation (notably Costs) must respect it. `[ADR-07]`

Note: `DOCUMENT_TAXONOMY.md` section 8 also defines SEGMENT. It has no counterpart here and none is introduced `[ADR-15]`.

### document_type

Represents the semantic document category.

```text
SEP
INA_CBG_OUTPUT
MEDICAL_RESUME
DISCHARGE_SUMMARY
ASSESSMENT
CPPT
LABORATORY
RADIOLOGY
ECG
PRESCRIPTION
MEDICATION_ORDER
BILLING
SERVICE_RECAP
REFERRAL
SUPPORTING_DOCUMENT
OTHER
UNKNOWN                [S1, ADR-REQ-002]
```

`[S1, ADR-REQ-002, decided]` `UNKNOWN` = the type could not be
classified. `OTHER` = the document was recognised but its type is not
in this list. `OTHER` is never a fallback for "not classified".

This list is extensible. Candidate additions observed in the audit
are proposals for `DOCUMENT_TAXONOMY.md`, not decisions here.

### document_role

A document may have multiple roles.

```text
ADMINISTRATIVE
CLINICAL
DIAGNOSTIC
MEDICATION_TREATMENT
FINANCIAL
CLAIM_CODING
SUPPORTING
```

`document_role` is independent of `document_type`, care pathway and
care stage. Claim anchors (SEP, INA-CBG Output, Billing / Service
Recap) are identified through type and role. They provide
administrative, coding and financial context and are **not**
automatically clinical timeline sources.

---

# 8. Source Facility

A SourceFacility identifies the organization from which a document
originates.

Initial attributes (baseline):

```text
facility_id
facility_name
facility_type
facility_code
```

Proposed additions `[r1, GAP-11, data-model]`:

```text
facility_aliases[]     alternative names seen in different documents
facility_codes[]       list of {code_system, code}; supersedes single
                       facility_code when several systems occur
```

`facility_code` remains valid for the single-code case.

All attributes are optional except where required by the source. A
facility may be `NOT_DOCUMENTED` (for example a scanned tracing with
no letterhead). That must be stated, not guessed.

The same facility can appear under different names in different
documents of one bundle. Aliases are recorded as source facts; whether
two names denote one facility is an inference and must carry
provenance. `[ADR-12]` Facility identity resolution (when aliases may
be merged and with which evidence).

The source facility may differ from the primary claim facility. This
distinction must be preserved.

```text
Claim Facility
    RSUD Gambiran

Supporting Document
    RSIA Melinda
```

---

# 9. Section

Initial attributes:

```text
section_id
document_id
section_type
title
page_start
page_end
chunks[]
```

`page_start` / `page_end` refer to the physical pages of the Document's
`page_refs[]`. For non-contiguous Documents they identify positions in
that list `[r1]`.

Examples of `section_type`: `CHIEF_COMPLAINT`, `HISTORY`,
`PHYSICAL_EXAMINATION`, `DIAGNOSIS`, `TREATMENT`, `DISPOSITION`,
`VITAL_SIGNS`, `LABORATORY_RESULT`, `BILLING_DETAIL`.

Section types may vary according to document type.

---

# 10. Chunk

Initial attributes:

```text
chunk_id
section_id
chunk_type
text
page_number
element_refs[]
facts[]
events[]
```

The chunk is the primary unit for semantic processing and retrieval.
Chunk boundaries should be semantic rather than based only on fixed
token or character length.

`[r1, GAP-12]` `text` may contain personal identifiers because it is
copied from the source. Its handling is governed by the Evidence
sensitivity policy (section 15, `[ADR-08]`).

---

# 11. Document Element

A DocumentElement represents a physical element extracted from the
source. This belongs to the Raw Document Representation layer.

Element types: `TEXT`, `TABLE`, `TABLE_CELL`, `IMAGE`, `LINE`,
`HEADER`, `FOOTER`, `OTHER`.

Initial attributes:

```text
element_id
page_number
element_type
text
bbox
style
```

Proposed additions `[r1]`:

```text
page_id               (GAP-1)
extraction_method     (GAP-2)
extraction_confidence (GAP-2)
```

`bbox` is optional because not every extraction method provides
reliable coordinates. An `IMAGE` element may have **no text at all**
(for example a physiological tracing); that is a valid state, not an
extraction failure.

## 11A. Extraction Method `[r1, GAP-2, extraction]`

How a piece of text or content was obtained must be recorded
separately from how confident the system is.

Proposed `extraction_method` initial values:

```text
NATIVE_TEXT            text layer present in the source file
OCR                    machine character recognition of an image
HANDWRITING_RECOGNITION machine reading of handwriting
MANUAL_TRANSCRIPTION   transcribed by a person
NO_TEXT                content is non-textual (image/tracing only)
UNKNOWN
```

`extraction_method` applies to Page, DocumentElement and Evidence.

`[S1, ADR-REQ-004, decided]` `extraction_method` says **how** a
representation was obtained. A separate `text_status` on Page
(`EXTRACTED | NOT_AVAILABLE | FAILED`) says **whether** a text
representation exists. A page whose text was not extracted (for example
an image-only page without OCR) has `extraction_method = UNKNOWN` and
`text_status = NOT_AVAILABLE`; `NO_TEXT` is used only when the content is
known to be non-textual. `MIXED` modality is not assigned until it can be
shown from the page.

Rules:

- text from `OCR`, `HANDWRITING_RECOGNITION` or
  `MANUAL_TRANSCRIPTION` is a *representation* of the source, never
  the source itself, and must not be treated with the certainty of
  `NATIVE_TEXT`;
- a Fact supported only by lower-fidelity extraction keeps that
  limitation visible through its Evidence;
- non-textual content can still be Evidence (see section 15).

`[ADR-11]` Final `extraction_method` vocabulary, how confidence is
qualified per component (extraction vs classification vs inference),
and how non-textual content (for example an ECG tracing) may support a
Fact.

---

# 12. Fact

A Fact represents an explicit or derived piece of information at the
semantic layer.

Initial attributes (baseline):

```text
fact_id
fact_type
subject
attribute
value
unit
provenance
temporal_information
confidence
evidence_refs[]
```

Proposed additions `[r1]`:

```text
derived_from_refs[]       (GAP-14, provenance)
inference_basis_refs[]    (GAP-14, provenance)
availability_status       (section 41)
raw_value_text            (GAP-7, preserves source spelling)
```

Example:

```json
{
  "fact_id": "fact-001",
  "fact_type": "DIAGNOSIS",
  "subject": "patient",
  "attribute": "primary_diagnosis",
  "value": "R33",
  "provenance": "SOURCE_FACT",
  "evidence_refs": ["evidence-001"]
}
```

Provenance rules (GAP-14):

- `SOURCE_FACT` requires `evidence_refs[]` where evidence exists and
  must **not** carry `derived_from_refs[]`;
- `DERIVED_FACT` must carry `derived_from_refs[]` (the facts it was
  calculated from) and a statement of the deterministic rule;
- `INFERRED_FACT` must carry `inference_basis_refs[]`;
- a value printed in the source (for example a length of stay printed
  by an administrative output) is a `SOURCE_FACT` even if it *could*
  be recomputed. A value computed by the system from other facts is a
  `DERIVED_FACT`. When both exist and differ, that is a candidate
  Source Discrepancy (section 38A), not something to be silently
  corrected.

`raw_value_text` preserves how the value was written in the source
(for example the original spelling or format of a date), so that
normalization is always reversible and auditable.

The exact schema for clinical facts will be refined in later versions.

## 12A. Relationship between Facts, Events and canonical entities `[r1, GAP-13, data-model]`

baseline 0.1 describes the same information in three places: semantic-layer
Facts/Events (inside Chunks), canonical typed entities (Diagnosis,
Procedure, Medication, ... in the Canonical Claim), and Timeline
events. baseline 0.1 does not say how they relate. This section records the
problem and a proposed linkage, **without** locking ownership.

Proposed, additive linkage fields on canonical entities:

```text
source_fact_refs[]     fact_ids this entity was built from
source_event_refs[]    event_ids (semantic layer) this entity merges
```

Intended reading (proposal):

- Fact/Event (semantic layer) = what a Chunk asserts, per document;
- canonical entity = the normalized, deduplicated claim-level view,
  possibly supported by Facts from several documents;
- Timeline event = a chronologically placed view of an event.

Fields already defined stay unchanged (`event_id`, `fact_id`,
`timeline_event_id`).

`[ADR-09]` Open decisions: (a) whether typed canonical entities or
generic Facts are authoritative when they disagree; (b) whether a
canonical Event reuses the semantic-layer `event_id` or gets its own
identity; (c) the merge/reconciliation policy when several documents
describe the same event.

---

# 13. Event

An Event represents something that occurred during the healthcare
episode.

Initial attributes (baseline):

```text
event_id
event_type
description
event_time
temporal_precision
care_pathway
care_stage
provenance
evidence_refs[]
```

Proposed additions `[r1]`:

```text
temporal_value          (GAP-6/7) see section 17
derived_from_refs[]     (GAP-14)
inference_basis_refs[]  (GAP-14)
```

`event_time` and `temporal_precision` are retained. `temporal_value`
is the full structured form (section 17); the two baseline 0.1 fields are its
simplest projection.

Examples of `event_type`: `PATIENT_ARRIVAL`, `TRIAGE`, `ASSESSMENT`,
`INVESTIGATION`, `MEDICATION`, `PROCEDURE`, `ADMISSION`, `TRANSFER`,
`REFERRAL`, `DISCHARGE`.

`[S1, ADR-REQ-003, decided]` `ADMISSION` means **inpatient admission**.
A printed "Tanggal Masuk" / "Tanggal Keluar" (date in / out) does not by
itself establish an inpatient stay, so it never produces an `ADMISSION`
or `DISCHARGE` event, notably on emergency and outpatient documents.

An event may originate from multiple documents. An event is a
*clinical or service occurrence*, distinct from the *act of printing
or filing* a document (print dates are `date_role: PRINT`, not
events).

---

# 14. Provenance

Every important fact or event must identify its provenance.

```text
SOURCE_FACT
DERIVED_FACT
INFERRED_FACT
MODEL_OUTPUT
```

- `SOURCE_FACT`: explicitly present in source material.
- `DERIVED_FACT`: deterministically calculated from source information.
- `INFERRED_FACT`: obtained through reasoning from available
  information.
- `MODEL_OUTPUT`: produced by an AI, statistical or machine learning
  model.

Provenance must not be silently changed. `[r1]` Any change of
provenance class is a new object, not an edit; the new object
references what it was built from.

Provenance applies to **relationships and detections** as well as to
values. For example, "document B repeats document A", "facility X and
facility Y are the same", and "these two values disagree" are each
`DERIVED_FACT`, `INFERRED_FACT` or `MODEL_OUTPUT`, never
`SOURCE_FACT`.

---

# 15. Evidence

An Evidence object links a fact, event or intelligence output to its
source.

Initial attributes (baseline):

```text
evidence_id
document_id
document_type
page_number
section_id
element_id
source_text
bbox
confidence
```

Proposed additions `[r1]`:

```text
source_file_id          (GAP-1)
page_id                 (GAP-1)
extraction_method       (GAP-2)
content_kind            (GAP-2)   TEXT | IMAGE_REGION | OTHER
sensitivity             (GAP-12)
redaction_state         (GAP-12)
```

Not every field is mandatory for every source (`page_number`,
`bbox`, `element_id` may be unavailable). Absence must be represented
explicitly, never invented.

`source_text` is optional. For `content_kind = IMAGE_REGION`
(non-textual evidence) it is absent and the region is identified by
page and, where available, `bbox`.

**Evidence ≠ Fact.** An Evidence object only states *where* something
is written. It never asserts a clinical statement by itself.

## 15A. Evidence sensitivity `[r1, GAP-12, domain-decision]`

`source_text`, Chunk `text` and element text are copied verbatim from
source documents and can contain personal identifiers (names,
identity and card numbers, addresses, telephone numbers, dates of
birth) even when the Fact they support is not itself personal.

Proposed attributes:

```text
sensitivity        e.g. NONE_KNOWN | CONTAINS_PERSONAL_DATA | UNKNOWN
redaction_state    e.g. ORIGINAL | REDACTED | DE_IDENTIFIED | UNKNOWN
```

Both are proposals. Their effect (what may be stored, logged,
embedded, shown, or used in fixtures) is a policy question.

`[ADR-08]` Evidence sensitivity policy: classification vocabulary,
what may be persisted or embedded in each state, and how de-identified
fixtures preserve lineage without carrying real identifiers.

---

# 16. Evidence Reference

Entities should reference evidence using identifiers rather than
duplicating evidence objects.

```text
Fact
│
└── evidence_refs[]
       ├── evidence-001
       ├── evidence-004
       └── evidence-007
```

The evidence registry then contains `evidence-001`, `evidence-004`,
`evidence-007`. This avoids duplication and keeps lineage centralized.

---

# 17. Temporal Model

Time-related information is represented explicitly.

Initial attributes (baseline): `event_time`, `start_time`, `end_time`,
`temporal_precision`.

Temporal precision:

```text
EXACT_DATETIME
DATE
MONTH
YEAR
UNKNOWN
```

The model must preserve the precision provided by the source.

```text
Source:  September 2025
Representation:  value = 2025-09, precision = MONTH
```

The system must not invent a day or time.

## 17A. Temporal Value `[r1, GAP-6/7, data-model]`

Proposed structured form used wherever a point in time appears:

```text
value          partial ISO 8601 string matching the precision
precision      EXACT_DATETIME | DATE | MONTH | YEAR | UNKNOWN
raw_text       the date exactly as written in the source
date_role      what the date means (see 17B)
timezone       optional; only if stated or reliably documented
```

Rules:

- `value` is never more precise than `precision`;
- `raw_text` is always kept when a source string exists, so
  normalization is reversible;
- start and end times each carry **their own** precision (a start may
  be a DATETIME while an end is only a DATE);
- if the source format is ambiguous (for example numeric day/month
  order), the value is not guessed: precision is `UNKNOWN` or the
  ambiguity is flagged, unless a documented adapter configuration
  resolves it.

Observed (informational): source dates appeared in several numeric
orders and in both Indonesian and English month names within the same
bundle. Parsing therefore belongs to document-understanding adapters,
which emit the normalized `value` plus `raw_text`. The canonical model
stores only the result.

## 17B. Date roles `[r1, GAP-6, domain-decision]`

One `event_time` cannot express the several dates a bundle contains.
Proposed `date_role` initial values (extensible):

```text
SERVICE         date/time the care occurred
REGISTRATION
ADMISSION
DISCHARGE
ORDER           when something was ordered/requested
SPECIMEN        when a specimen was collected
RESULT          when a result was produced
VERIFICATION    when a result/document was verified or signed
ENTRY           when a record was entered into a system
PRINT           when the document was printed/generated
BILLING         date associated with a charge
BIRTH
UNKNOWN
```

A `PRINT` or `ENTRY` date must not be used as a clinical event time.

`[S1, ADR-REQ-003, decided]` `ADMISSION` (and its counterpart
`DISCHARGE`) refer to an inpatient stay. Dates printed under "Masuk" /
"Keluar" labels keep `date_role = UNKNOWN` and the printed label, until
the stay is shown to be inpatient. A role for "start / end of any
encounter" does not exist yet and is left unresolved (ADR-05).

`[ADR-05]` Date role vocabulary, and the policy for ambiguous numeric
dates (adapter configuration vs flagged-unknown).

---

# 18. Care Pathway

A CarePathway represents the clinical workflow context.

```text
EMERGENCY
OUTPATIENT
INPATIENT
```

A claim may contain multiple pathways (for example EMERGENCY then
INPATIENT, or OUTPATIENT then INPATIENT).

Care pathway is independent from document type.

## 18A. Claim-declared service type `[r1, GAP-4, domain-decision]`

Administrative and claim documents declare a service type of their
own (for example how the claim classifies the visit). That declaration
is a **SOURCE_FACT about the claim**. It is not the same thing as the
clinical care pathway, and the two can legitimately disagree (for
example an emergency visit that a claim output classifies as an
outpatient service).

Proposed field in Claim Header / Claim Coding:

```text
declared_service_type        value normalized from the source
declared_service_type_text   original wording (raw_text)
```

Rules:

- `declared_service_type` never overwrites or is overwritten by
  `care_pathways[]`;
- a mismatch is representable as a Source Discrepancy (38A) rather
  than being "fixed".

`[ADR-03]` Normalized vocabulary for `declared_service_type`, and
whether it is a separate field or a typed Fact.

---

# 19. Care Stage

A CareStage represents the stage of care associated with an event.
Care stage is attached primarily to events rather than documents. A
single document may contain information tied to several stages.

Stage sets are **per care pathway** (as defined in the project
baseline). A stage name is only meaningful together with its pathway.

```text
EMERGENCY (IGD)
  ARRIVAL → TRIAGE → INITIAL_ASSESSMENT → INITIAL_TREATMENT
  → SUPPORTING_INVESTIGATION → DISPOSITION
  Outcomes: DISCHARGE, INPATIENT_ADMISSION, ICU, SURGERY, REFERRAL

OUTPATIENT (RAWAT JALAN)
  REGISTRATION → ELIGIBILITY → INITIAL_ASSESSMENT
  → CLINICAL_ASSESSMENT → INVESTIGATION → TREATMENT → DISPOSITION
  Outcomes: FOLLOW_UP, PRESCRIPTION, PROCEDURE,
            INPATIENT_ADMISSION, REFERRAL

INPATIENT (RAWAT INAP)
  ADMISSION → INITIAL_ASSESSMENT → DAILY_CARE → INVESTIGATION
  → TREATMENT → MONITORING → DISPOSITION → DISCHARGE
```

The baseline 0.1 flat list (ARRIVAL, TRIAGE, INITIAL_ASSESSMENT,
INITIAL_TREATMENT, SUPPORTING_INVESTIGATION, ADMISSION, DAILY_CARE,
INVESTIGATION, TREATMENT, MONITORING, DISPOSITION, DISCHARGE,
REFERRAL) is the union of these sets and remains valid. `REFERRAL`,
`DISCHARGE` and the other **outcomes** are dispositions of a pathway,
not additional stages inside it.

`care_stage` is always interpreted together with `care_pathway`.
Stages are optional on an Event: an event whose stage cannot be
determined carries `UNKNOWN`/`NOT_DOCUMENTED`, not a guessed stage.

`[ADR-10]` (a) `INVESTIGATION` (outpatient/inpatient) and
`SUPPORTING_INVESTIGATION` (emergency) are kept distinct per the
baseline; is a cross-pathway equivalence mapping needed for timeline
and analytics? (b) whether an outcome is modelled as a stage value,
a separate `disposition_outcome` field, or both.

---

# 20. Encounter

Initial attributes:

```text
encounter_id
encounter_type
start_time
end_time
care_pathways[]
facility_id
disposition
```

Possible encounter types: `EMERGENCY`, `OUTPATIENT`, `INPATIENT`,
`OTHER`.

One claim may contain one or more encounter contexts depending on the
actual source data. `start_time` and `end_time` are Temporal Values
(17A) and may differ in precision `[r1]`.

---

# 21. Participant

Potential participant types: `PATIENT`, `DOCTOR`, `NURSE`,
`OTHER_PPA`, `FACILITY`, `REFERRING_FACILITY`.

The detailed identity model is intentionally deferred because the
system must support privacy-preserving and de-identified
environments. `[r1]` This deferral does not remove the sensitivity
concern for Evidence text (section 15A).

Roles of performers (who performed a procedure, who verified a
result) are expressed through Participant references on the relevant
entity (for example Procedure, Investigation) and are optional.

---

# 22. Canonical Clinical Claim

The Canonical Clinical Claim is the normalized semantic
representation of the claim.

```text
Canonical Clinical Claim
│
├── claim_header
├── participant
├── encounter
├── care_pathways[]
├── diagnoses[]
├── procedures[]
├── medications[]
├── clinical_findings[]
├── investigations[]
├── events[]
├── claim_coding
├── costs[]
└── evidence_refs[]
```

The canonical claim must remain independent of the hospital's
original document layout. `claim_header` carries `declared_service_type`
`[r1, 18A]`.

---

# 23. Diagnosis

Initial attributes (baseline):

```text
diagnosis_id
code
description
diagnosis_role
source
provenance
evidence_refs[]
```

Possible `diagnosis_role` values: `PRIMARY`, `SECONDARY`, `OTHER`.

Proposed additions `[r1, GAP-5, domain-decision]`:

```text
coding_system          e.g. ICD-10; explicit, never implied
coding_system_version  optional
diagnosis_context      when/where in the episode the diagnosis stands
source_fact_refs[]     (12A)
```

`diagnosis_role` (rank within a claim) and `diagnosis_context`
(point in the episode) are **different axes**. Observed: administrative
documents carry an initial/entry diagnosis that differs from the final
coded diagnoses. `diagnosis_context` therefore needs values beyond
the three roles, for example:

```text
INITIAL      entry/admission diagnosis (e.g. on SEP)
WORKING      during care
FINAL        at discharge / for the claim
UNKNOWN
```

`[ADR-04]` `diagnosis_context` vocabulary and its relation to
`diagnosis_role`; the registry of allowed `coding_system` values.
The exact coding-system representation remains configurable.

---

# 24. Procedure

Initial attributes (baseline):

```text
procedure_id
code
description
procedure_role
event_time
provenance
evidence_refs[]
```

Proposed additions `[r1]`:

```text
coding_system          explicit; procedure coding is a different
                       system from diagnosis coding
performer_ref          optional Participant reference
source_fact_refs[]
```

Procedure coding must remain distinguishable from diagnosis coding.
`event_time` is a Temporal Value (17A). A procedure listed in a coding
output but without a documented performance event stays so: its
`availability_status` is not upgraded to "performed" without evidence.

---

# 25. Medication

Initial attributes (baseline):

```text
medication_id
name
code
dose
unit
route
frequency
duration
status
provenance
evidence_refs[]
```

Proposed additions `[r1, GAP-8, domain-decision]`:

```text
medication_context
item_category
source_fact_refs[]
```

`medication_context` records **what kind of statement** the source
makes. Observed in one bundle: an order in the hospital, a
prescription at emergency visit, a take-home therapy list on
discharge, and billed pharmacy line items. These are not the same
fact. Proposed initial values:

```text
ORDERED
PRESCRIBED
DISPENSED
ADMINISTERED
DISCHARGE
BILLED
UNKNOWN
```

`status` (baseline) is retained; it must not be overloaded to carry
context.

`item_category` separates drugs from other items that appear in the
same lists (devices, consumables). Proposed values:

```text
MEDICATION
MEDICAL_DEVICE
CONSUMABLE
UNKNOWN
```

`[ADR-06]` `medication_context` vocabulary; and whether devices and
consumables stay in Medication with `item_category` or become a
separate entity.

Not all fields will be available from every document. An absent
field is `NOT_DOCUMENTED`, not empty-by-assumption.

---

# 26. Investigation

Initial attributes (baseline):

```text
investigation_id
investigation_type
name
result
unit
reference_range
flag
event_time
provenance
evidence_refs[]
```

Proposed additions `[r1, GAP-10, data-model]`:

```text
panel                  group the test belongs to (as printed)
specimen               specimen type, if stated
critical_flag          separate from `flag`; source-printed critical value
dates[]                Temporal Values with date_role ORDER, SPECIMEN,
                       RESULT, VERIFICATION
requester_ref          optional Participant reference
performer_ref          optional Participant reference
verifier_ref           optional Participant reference
source_fact_refs[]
```

`event_time` is retained as the single most relevant time; when order,
specimen, result and verification times exist, they live in `dates[]`.

Possible `investigation_type`: `LABORATORY`, `RADIOLOGY`, `ECG`,
`PATHOLOGY`, `OTHER`.

An investigation result may span several pages and may come from a
facility other than the claim facility. Its source facility is
recorded on the Document (section 8). A tracing with no extractable
text is an Investigation whose `result` is `NOT_DOCUMENTED` (not
"normal", not "absent").

`[ADR-13]` Vocabulary for `panel` and `specimen`, and whether panels
are first-class entities.

---

# 27. Clinical Finding

Initial attributes:

```text
finding_id
finding_type
name
value
unit
status
event_time
provenance
evidence_refs[]
```

Examples: vital signs, physical examination findings, symptoms,
clinical observations. `[r1]` `event_time` is a Temporal Value;
`source_fact_refs[]` applies (12A).

---

# 28. Claim Coding

Examples: primary diagnosis code, secondary diagnosis codes,
procedure codes, INA-CBG group, severity, claim tariff.

```text
Claim Coding
│
├── diagnosis_codes[]
├── procedure_codes[]
├── grouping
├── severity
└── tariff
```

The detailed INA-CBG representation will be defined separately from
the general clinical model.

`[r1]` Claim Coding values are SOURCE_FACTs about what the coding
output **states**. They are not clinical truth and not a verdict on
coding correctness. The claim tariff here is a `CLAIM_TARIFF`
amount (section 29) and is distinct from billed charges.

---

# 29. Cost

Initial attributes (baseline):

```text
cost_id
cost_type
description
amount
currency
service_date
provenance
evidence_refs[]
```

Proposed additions `[r1, GAP-9, domain-decision]`:

```text
amount_basis
cost_level
duplicate_of          optional cost_id (see below)
source_fact_refs[]
```

Possible `cost_type`: `SERVICE`, `MEDICATION`, `LABORATORY`,
`RADIOLOGY`, `PROCEDURE`, `ROOM`, `OTHER`, `TOTAL`.

`amount_basis` states **which monetary concept** the amount is.
Observed: hospital billing recaps and claim coding outputs both
report totals, and they differ. They must not be merged or compared
as if they were the same quantity. Proposed initial values:

```text
BILLED_CHARGE     charge in a hospital billing/service recap
CLAIM_TARIFF      tariff from the grouping / coding output
OTHER
UNKNOWN
```

`cost_level` distinguishes `LINE_ITEM`, `CATEGORY_SUBTOTAL` and
`TOTAL`, so subtotals and totals are not double counted. A TOTAL that
the source prints is a SOURCE_FACT; a sum computed by the system is a
DERIVED_FACT with `derived_from_refs[]`.

`duplicate_of` marks a repeated cost record (for example a repeated
billing recap page). Aggregations must exclude duplicates unless the
source states otherwise.

`DOCUMENT_TAXONOMY.md` section 27 already fixes the principle that hospital billing total and INA-CBG tariff are different concepts. Only the vocabulary below is open.

`[ADR-07]` `amount_basis` vocabulary; whether duplicate detection is
deterministic (identical content) or an inference; and how aggregates
treat duplicates.

Financial information must remain separate from clinical facts.

---

# 30. Timeline

A Timeline represents the reconstructed clinical journey. It is
derived from source documents and events.

```text
Timeline
├── event-001
├── event-002
├── event-003
└── event-004
```

Each timeline event should preserve:

```text
timeline_event_id
event_id
event_time
temporal_precision
care_pathway
care_stage
description
evidence_refs[]
```

`[r1]` Timeline order is determined by event time and, where time
is imprecise or missing, by explicitly stated ordering evidence. It is
**never** determined by document or page order. An event of unknown
time is placed as such and flagged, not given an invented time.

The timeline is a derived representation and must not replace the
original source events.

---

# 31. Timeline Reconstruction

Timeline reconstruction may combine evidence from multiple documents.

```text
Triage                → Triage Document
Initial Assessment    → IGD Assessment
Investigation         → Laboratory
Treatment             → Medication, Procedure
Disposition           → Discharge
```

The timeline engine must preserve evidence references for each event.

`[r1]` Claim anchors (SEP, INA-CBG Output, Billing / Service Recap)
supply claim, administrative, coding and financial context. They are
not automatic timeline sources: a registration date or a print date
on an anchor is not a clinical event unless a clinical document
supports it.

---

# 32. Narrative

Initial attributes:

```text
summary_id
summary_type
text
evidence_refs[]
generation_metadata
```

Narrative is generated from the canonical claim, evidence and
timeline. It is a presentation layer, never a replacement for
structured clinical data, and **never the source of analytical
truth**. Intelligence must not consume Narrative as input.
Narrative text is `MODEL_OUTPUT` unless produced by a documented
deterministic template.

---

# 33. Intelligence

Initial attributes:

```text
intelligence_id
intelligence_type
severity
description
score
provenance
evidence_refs[]
model_metadata
```

Possible `intelligence_type`: `RULE_FINDING`, `ANOMALY`,
`INCONSISTENCY`, `RISK_SCORE`, `RECOMMENDATION`, `MODEL_OUTPUT`.

Examples: potential diagnosis-procedure inconsistency; potential
missing supporting evidence; unusual service pattern; potential
documentation gap; claim risk score.

`[r1]` Intelligence = Canonical Claim + Evidence + Timeline +
Rules/Models. Its inputs never include Narrative. A Source
Discrepancy (38A) is an *input observation*, an Intelligence
`INCONSISTENCY` is an *analytical judgement*; they are different
objects. `[ADR-02]`

---

# 34. Confidence

Confidence represents the reliability associated with an extraction,
classification, inference, or model output.

Confidence must not be confused with evidence. `confidence = 0.97`
means the system is highly confident in its extraction or inference.
It does not mean that the underlying clinical fact is true with 97%
probability.

Where necessary, confidence should be qualified by the component
that produced it. `[r1]` Component kinds at minimum: extraction,
classification, linking, inference, model output. A missing
confidence is represented as absent, never as `1.0` or `0`.
`[ADR-11]`

---

# 35. Model Metadata

AI or machine learning outputs should preserve model context where
appropriate.

```text
model_name
model_version
prompt_version
rule_version
generated_at
```

This supports reproducibility and auditability.

---

# 36. Source Reference

A source reference identifies the original input or repository
location. Examples: `source_reference`, `document_uri`,
`file_identifier`, `repository_identifier`, `external_document_id`.

The model must not assume that the original source is stored inside
the GOUTAMIND application. The original may remain in OneDrive, a
hospital document repository, JKN Drive, hospital storage, or another
authorized repository. GOUTAMIND may store only an authorized
reference. `[r1]` A SourceFile (5A) carries this reference.

---

# 37. Relationship Model

```text
ClaimDocumentBundle
        │
        ├── contains → SourceFile → Page → DocumentElement   [r1]
        │
        ├── contains → Document
        │                  │
        │                  ├── located_on → Page (page_refs[])  [r1]
        │                  └── contains → Section
        │                                   └── contains → Chunk
        │                                                     ├── Fact
        │                                                     └── Event
        │
        ├── represents → CanonicalClaim
        │
        ├── references → Evidence
        │
        ├── records → SourceDiscrepancy                       [r1]
        │
        ├── produces → Timeline
        │
        ├── produces → Narrative
        │
        └── produces → Intelligence
```

Evidence connects semantic information back to source documents:

```text
Fact / Event / Intelligence
        │
        └── evidence_refs[]
                ↓
             Evidence
                ↓
             Document ──► Page ──► SourceFile
                ↓
          Original Source
```

---

# 38. Source vs Derived Relationships

The model must make derivation explicit.

```text
SOURCE_FACT  Admission Date = 2025-09-22 ─┐
SOURCE_FACT  Discharge Date = 2025-09-25 ─┤
                                          ▼
                              DERIVED_FACT  LOS = 4 days
                              derived_from_refs[] = both dates above
```

The derived fact must retain references to the source facts that
support its calculation (`derived_from_refs[]`, section 12).

## 38A. Source Discrepancy `[r1, GAP-3, provenance + domain-decision]`

Documents in one bundle can disagree (for example a referring
facility named differently by an administrative document and a
clinical document; a service type declared one way and clinically
observed another; a printed total that differs from a recomputed
sum). baseline 0.1 has no way to represent this without silently choosing
one value.

A **SourceDiscrepancy** records that two or more source-derived
assertions are in tension. It does **not** decide which is right.

Proposed attributes:

```text
discrepancy_id
discrepancy_type        e.g. VALUE_MISMATCH | FACILITY_MISMATCH |
                        SERVICE_TYPE_MISMATCH | TOTAL_MISMATCH | OTHER
subject_refs[]          the facts/entities in tension
evidence_refs[]
provenance              DERIVED_FACT | INFERRED_FACT | MODEL_OUTPUT
detected_by             rule/model metadata (section 35)
resolution_status       UNRESOLVED | (see ADR-02)
```

Rules:

- all conflicting values remain in the model, each with its own
  evidence;
- detection is never `SOURCE_FACT` (no source states "these differ");
- a discrepancy is not an Intelligence finding and not a verdict on
  correctness.

`DOCUMENT_TAXONOMY.md` section 26 states the principle (preserve both source facts; the conflict itself may become an intelligence signal; do not destroy contradictory source information). It does not say where the discrepancy *record* lives.

`[ADR-02]` Open decisions: (a) whether SourceDiscrepancy belongs to
the Canonical Claim layer or the Intelligence layer; (b) whether and
how a canonical value is chosen when sources disagree (precedence
policy), or whether the canonical claim carries multiple candidate
values; (c) `discrepancy_type` vocabulary.

---

# 39. Inferred Information

Inference must remain distinguishable.

```text
SOURCE_FACT  Urine retention documented
SOURCE_FACT  Foley catheter inserted
SOURCE_FACT  1000 mL urine output
        ↓
INFERRED_FACT  Clinical episode consistent with urinary retention
               management
               inference_basis_refs[] = the three facts above
```

The inferred statement must not be represented as if it were directly
documented.

---

# 40. Model Output

Model output must remain separate from clinical facts.

```text
Canonical Claim + Evidence
      ↓
Risk Model
      ↓
MODEL_OUTPUT  risk_score = 0.82
```

A model output does not automatically become a clinical fact.

---

# 41. Missing Information Model

The data model explicitly represents missingness.

```text
NOT_FOUND
NOT_DOCUMENTED
NOT_APPLICABLE
EXPLICITLY_NEGATED
UNKNOWN
```

`procedure_status = NOT_DOCUMENTED` must not be converted into
`NOT_PERFORMED` unless supported by explicit evidence.

`[r1, data-model]` Proposed attribute carrying these states:

```text
availability_status     PRESENT | NOT_FOUND | NOT_DOCUMENTED |
                        NOT_APPLICABLE | EXPLICITLY_NEGATED | UNKNOWN
```

`PRESENT` is the default when a value exists. It applies on Fact and
on canonical entities and optional fields (for example Procedure,
Medication, Investigation result, SourceFacility), and on Document
(`completeness_status` is its Document-level use). It is distinct
from `status` fields such as Medication `status`, which describe the
clinical item, not the availability of information.

`NOT_FOUND` means "looked for and not located by the system". It is
not evidence that the thing did not happen.

---

# 42. Immutability of Source Representation

The original document representation should be treated as immutable
after ingestion. Transformations produce new representations.

```text
Original Document → Raw Representation → Semantic Representation
                                      → Canonical Claim
```

Do not overwrite the original extracted source representation with
normalized or inferred information. `[r1]` Normalized values keep
their `raw_text`; reprocessing with a different extraction method
creates a new representation and does not replace the earlier one.

---

# 43. Versioning

The following should be versionable:

```text
schema_version
document_taxonomy_version
extraction_version
rule_version
model_version
prompt_version
```

This is important for reproducibility and auditability.

---

# 44. Validation Principles

The data model should eventually validate:

- **Identity:** required identifiers are present.
- **Relationships:** references point to valid entities.
- **Provenance:** facts and events identify their provenance;
  `DERIVED_FACT` has `derived_from_refs[]`; `INFERRED_FACT` has
  `inference_basis_refs[]`; `SOURCE_FACT` has no derivation refs.
- **Evidence:** important source-derived information has valid
  evidence references where available.
- **Temporal consistency:** `value` is never more precise than
  `precision`; `raw_text` kept; roles present.
- **Type consistency:** diagnosis, procedure, medication,
  investigation and financial information remain distinguishable;
  `amount_basis` values are not mixed in aggregates.
- **Canonical consistency:** hospital-specific fields do not leak
  into the canonical domain model.
- **Physical consistency `[r1]`:** every page belongs to exactly
  one SourceFile; every `page_refs[]` entry resolves; blank pages are
  allowed to belong to no Document.
- **Sensitivity `[r1]`:** Evidence/Chunk text has a
  `sensitivity` classification before it leaves the processing
  boundary (policy per ADR-08).

---

# 45. Initial JSON Representation

A simplified conceptual representation:

```json
{
  "bundle_id": "bundle-001",
  "claim_id": "claim-001",

  "source_files": [],
  "documents": [],

  "canonical_claim": {
    "claim_id": "claim-001",
    "claim_header": {},
    "encounter": {},
    "diagnoses": [],
    "procedures": [],
    "medications": [],
    "investigations": [],
    "clinical_findings": [],
    "events": [],
    "claim_coding": {},
    "costs": []
  },

  "evidence": [],
  "source_discrepancies": [],
  "timeline": [],
  "narrative": null,
  "intelligence": []
}
```

This is intentionally conceptual. It is not yet the final JSON Schema.

---

# 46. Example Evidence Relationship

```json
{
  "fact_id": "fact-001",
  "fact_type": "DIAGNOSIS",
  "value": "R33",
  "provenance": "SOURCE_FACT",
  "evidence_refs": ["evidence-001", "evidence-002"]
}
```

Evidence registry (synthetic):

```json
{
  "evidence_id": "evidence-001",
  "document_id": "doc-002",
  "document_type": "INA_CBG_OUTPUT",
  "source_file_id": "file-001",
  "page_number": 2,
  "extraction_method": "NATIVE_TEXT",
  "content_kind": "TEXT",
  "source_text": "R33",
  "sensitivity": "NONE_KNOWN"
}
```

```json
{
  "evidence_id": "evidence-002",
  "document_id": "doc-003",
  "document_type": "MEDICAL_RESUME",
  "source_file_id": "file-001",
  "page_number": 4,
  "extraction_method": "NATIVE_TEXT",
  "content_kind": "TEXT",
  "source_text": "Urinary retention",
  "sensitivity": "NONE_KNOWN"
}
```

One canonical fact may be supported by multiple sources.

Example of non-textual evidence (synthetic):

```json
{
  "evidence_id": "evidence-020",
  "document_id": "doc-009",
  "document_type": "ECG",
  "source_file_id": "file-001",
  "page_number": 13,
  "extraction_method": "NO_TEXT",
  "content_kind": "IMAGE_REGION"
}
```

---

# 47. Example Clinical Timeline

```json
{
  "timeline_event_id": "timeline-001",
  "event_id": "event-001",
  "event_time": "2025-09-22T14:30:00",
  "temporal_precision": "EXACT_DATETIME",
  "care_pathway": "EMERGENCY",
  "care_stage": "TRIAGE",
  "description": "Patient arrived at emergency department",
  "evidence_refs": ["evidence-010"]
}
```

The timeline is a structured interpretation of events, not a copy of
PDF page order.

Example Temporal Value (synthetic), partial precision preserved:

```json
{
  "value": "2025-09",
  "precision": "MONTH",
  "raw_text": "September 2025",
  "date_role": "SERVICE"
}
```

---

# 48. Golden Claim Requirement

The project should eventually maintain a representative golden claim
dataset demonstrating:

```text
Document Bundle → Documents → Sections → Chunks → Facts / Events
→ Canonical Claim → Evidence → Timeline → Narrative → Intelligence
```

The fixture must use synthetic or properly de-identified data.
`[r1]` To be representative, the golden claim should include at
least: a multi-document PDF with non-contiguous pages, a blank
separator page, a scanned/photographed document from another
facility, a duplicated page, mixed date formats, and one deliberate
Source Discrepancy. These are coverage requirements for the model,
not facility-specific content.

---

# 49. Relationship to Implementation

This document defines the conceptual data model. Implementation
should be derived from this model.

```text
docs/
    DATA_MODEL.md

schemas/
    canonical_claim.schema.json
    document.schema.json
    evidence.schema.json
    timeline.schema.json
    intelligence.schema.json

app/
    document/
    extraction/
    evidence/
    timeline/
    intelligence/
```

The exact implementation structure may evolve without changing the
underlying domain concepts. `[r1]` Source files/pages and
discrepancies will need schema homes; their placement is deferred
until the related ADRs are resolved.

---

# 50. Design Invariants

The following invariants should remain stable unless explicitly
revised.

1. A Claim Document Bundle may contain multiple Documents.
2. A PDF is not necessarily equivalent to a logical Document.
3. A Document may contain multiple Sections.
4. A Section may contain multiple Chunks.
5. Facts and Events may originate from multiple source Documents.
6. Evidence must remain traceable to source Documents.
7. Source Facts, Derived Facts, Inferred Facts and Model Outputs must
   remain distinguishable.
8. Document order must not be treated as clinical event order.
9. Care Pathway and Care Stage are workflow concepts, not document
   types.
10. Financial and claim/coding information must remain
    distinguishable from clinical information.
11. Temporal precision must not be artificially increased.
12. The canonical claim must remain independent from
    hospital-specific document layouts.
13. The original source representation must remain immutable.

Proposed additional invariants `[r1]`, supported by the audit and
pending owner confirmation:

14. The pages of one Document need not be contiguous, and a Page need
    not belong to any Document.
15. Evidence is not a Fact; it never asserts clinical content itself.
16. Extraction method is recorded and never inferred to be better
    than it is.
17. Disagreement between sources is recorded, never silently
    resolved.
18. Different monetary concepts (billed charge, claim tariff) are
    never merged or compared as one quantity.
19. Narrative is never an input to Intelligence.

---

# 51. Status

Version: 0.1, revision r1 (proposed)
Status: Draft / Architecture Baseline, pending owner review

This document is intended to be reviewed against representative claim
document bundles from multiple hospitals and care pathways. The next
step after approval is to translate the conceptual model into
machine-readable schemas under `schemas/`.

The schema implementation should not introduce concepts that are not
supported by this data model without an explicit architecture review.
**No schema should be derived from a field whose governing ADR is
still open.**

---

# Appendix A. Gap Register `[r1]`

Gaps were found by mapping baseline 0.1 against two representative bundles
(one IGD/outpatient-classified, one inpatient). Types: S structural,
D data-model, P provenance, E extraction, X domain-decision.

| # | Gap | Type | Where addressed | ADR |
|---|---|---|---|---|
| 1 | No physical container (file/page); non-contiguous documents; blank pages | S | 3, 4, 5A, 7, 9, 37 | ADR-01 |
| 2 | No extraction modality; scans/photos/tracings | E | 11, 11A, 15 | ADR-11 |
| 3 | No representation of disagreement between sources | P, X | 38A, 3, 5, 37 | ADR-02 |
| 4 | Claim-declared service type vs care pathway | X | 18A, 22 | ADR-03 |
| 5 | Diagnosis role too narrow; coding system implicit | D, X | 23, 24 | ADR-04 |
| 6 | One time field for many date meanings | D, X | 7, 17A, 17B | ADR-05 |
| 7 | Mixed date formats; raw text not kept | D, E | 12, 17A | ADR-05 |
| 8 | Medication context and non-drug items | D, X | 25 | ADR-06 |
| 9 | Billed charge vs claim tariff; duplicates | D, X | 29, 7 | ADR-07 |
| 10 | Investigation panel/specimen/date roles | D | 26 | ADR-13 |
| 11 | Facility aliases and multiple code systems | D, X | 8 | ADR-12 |
| 12 | Evidence text carries personal identifiers | X | 15A, 10, 44 | ADR-08 |
| 13 | Fact vs typed entity vs Event ownership | S, D | 12A | ADR-09 |
| 14 | `derived_from` / inference basis missing | P | 12, 13, 38, 39, 44 | none |
| 15 | Care stages mixed across pathways | D, X | 19 | ADR-10 |

Taxonomy section 25 items 1-14 correspond to gaps 1-3, 5-9 and 12 above (taxonomy items 2-3 merge into gap 2; items 5-7 into gap 1). Gaps 4, 10, 11, 13, 14, 15 were found by the PDF mapping and are not in taxonomy section 25.

Gap 14 is a consistency fix: baseline 0.1 sections 38 and 39 already required
the references but the Fact/Event attributes did not carry them.

# Appendix B. Architecture Decisions Required

Each is **open**. Text in this document gives a proposed shape only.

| ADR | Question |
|---|---|
| ADR-01 | May a Page belong to several Documents; may a Document start/end mid-Page? |
| ADR-02 | Where does SourceDiscrepancy live (Canonical Claim vs Intelligence); is there a value-precedence policy or do candidates coexist; type vocabulary? |
| ADR-03 | Vocabulary and field form for `declared_service_type`. |
| ADR-04 | `diagnosis_context` values and relation to `diagnosis_role`; `coding_system` registry. |
| ADR-05 | `date_role` vocabulary; policy for ambiguous numeric dates. |
| ADR-06 | `medication_context` values; devices/consumables inside Medication or separate entity. |
| ADR-07 | `amount_basis` values; duplicate detection rule and aggregate treatment. |
| ADR-08 | Evidence sensitivity classes; what may be stored/embedded/logged per class; de-identified fixture lineage. |
| ADR-09 | Authority between Facts and typed entities; event identity across layers; merge policy. |
| ADR-10 | Cross-pathway stage equivalence; outcomes as stages vs separate field. |
| ADR-11 | `extraction_method` vocabulary; per-component confidence; non-textual evidence supporting Facts. |
| ADR-12 | Facility alias resolution and code-system handling. |
| ADR-13 | `panel`/`specimen` vocabulary; panels as entities. |
| ADR-14 | Naming conventions: singular/plural field names (for example `document_role[]`), `document_type` vs `doc_type` usage, capitalization of enum values, field naming across Evidence and Document. No rename is made in this revision. |
| ADR-15 | `DOCUMENT_TAXONOMY.md` section 8 defines SEGMENT (major semantic part / document identity) as distinct from CHUNK. This document has no Segment. Is a Segment the same as a Document, a Section, or a separate level? Not resolved here; no Segment entity is introduced. |

# Appendix C. Decisions from vertical slice 1 `[S1]`

Decided in the PR #1 review on the basis of running the slice on one
synthetic and two real bundles. Evidence: `docs/findings/SLICE_01_FINDINGS.md`.

| Decision | What changed | Why | Observed evidence | Still unresolved |
|---|---|---|---|---|
| ADR-REQ-001 (Option B) | `page_refs[]` entries carry `page_id`, `basis`, `evidence_ref` (section 7). | Page-to-document assignment is an inference and had no provenance. | OBS-003, OBS-004: untitled pages attached by continuation, some wrongly; 18 of 38 pages of one bundle rest on continuation alone. | ADR-01 (page in several documents, document starting mid-page). A basis does not tell a right continuation from a wrong one. |
| ADR-REQ-002 (Option A) | `document_type` gains `UNKNOWN` (section 7). | "Not classified" and "known but unlisted" are different. | Six documents across the runs could not be classified (image-only, untitled). | Types for forms seen but unlisted (triage, admission order, single-clinician medication order); ownership of the list (ADR-14). |
| ADR-REQ-003 (Option B) | `ADMISSION` = inpatient admission (sections 13, 17B). | An emergency visit produced ADMISSION/DISCHARGE events from its resume labels. | OBS-017: emergency visit declared as outpatient, resume prints "Tanggal Masuk/Keluar". | Vocabulary for encounter start/end (ADR-05); how an inpatient stay is established (ADR-03). |
| ADR-REQ-004 (Option B) | `text_status` beside `extraction_method` (section 11A). | `NO_TEXT` would declare an un-OCR'd page non-textual. | OBS-005, OBS-013: image-only pages; 34 of 49 text pages also embed images. | Rest of ADR-11 (per-component confidence, non-textual evidence supporting Facts); meaning of `MIXED`. |
