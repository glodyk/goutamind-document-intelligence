# Vertical slice 1: findings from execution

**Status:** report of what running the first vertical slice showed.

- **Iteration 1** (initial PR #1) raised ADR-REQ-001 to 004.
- **Iteration 2** (PR #1 review): the owner accepted all four. They are
  applied in code and as small additive notes in `DATA_MODEL.md`
  (`[S1]`, Appendix C). See "Decision status" and "Iteration 2 results"
  below. Earlier observations are kept unchanged as the evidence for the
  decisions.

Identifiers in this file (`OBS-`, `GAP-`, `IMPL-`, `ADR-REQ-`, `TECH-`) are
local to slice 1. Where a finding touches an existing open decision, the
`DATA_MODEL.md` Appendix B number (ADR-01 ... ADR-15) is given.

## How the findings were obtained

The pipeline was run on:

- the committed synthetic bundle (`examples/golden_claim/`, 16 pages);
- two real claim bundles kept outside Git: **Sample E**, an emergency visit
  (18 pages), and **Sample I**, an inpatient stay (38 pages). These are the
  same two bundles used for the conceptual stress test (taxonomy section 5).
  Only structural results are reported here; no content, identifiers, codes
  or dates from them are reproduced.

| | Sample E (emergency) | Sample I (inpatient) |
|---|---|---|
| Pages | 18, all with a text layer | 38: 31 text, 4 image-only, 3 blank |
| Logical documents | 9 | 14 (4 of them image-only `UNKNOWN`) |
| Page attachment basis | 9 title, 6 counter, 3 continuation | 7 title, 1 marker, 5 counter, 18 continuation, 4 image |
| Facts | 6 (4 diagnosis, 2 procedure) | 49 (4 diagnosis, 3 procedure, 42 medication lines) |
| Events | 4 | 0 |
| Evidence items | 19 | 63 |
| Dates found / with a known role | 27 / 11 | 52 / 16 |

Manual comparison with the PDFs: in Sample E every page landed in the right
logical document. In Sample I, by manual reading, 10 of 38 pages were most
likely attached to the wrong document (OBS-003, OBS-004); everything else
matched.

## Observations

**OBS-001: page counters are the strongest boundary signal.** Printed
"Halaman k of n" / "Halaman k" counters correctly split two consecutive
laboratory reports and kept a resume page that starts with "RESEP" inside
the resume. Titles alone would have got both wrong.

**OBS-002: many first pages have no title in the text layer.** An SEP page
and several laboratory pages start directly with labels; the form title is
part of an image or missing. Label markers ("No.SEP" + "Tgl.SEP", the lab
result table header) were needed.

**OBS-003: untitled pages after a document are attached to it, sometimes
wrongly.** In Sample I nine untitled pages after a CPPT were attached to the
CPPT by the continuation rule. Read by hand, they look like separate
single-clinician medication/order printouts, each with its own header block,
but nothing in their text layer names them.

**OBS-004: a wrong boundary moves facts to the wrong document type.** The
last page of Sample I (an inpatient plan letter, *surat rencana inap*) was
attached to the preceding service recap. Its title is printed at the bottom
of the page, outside the top lines the title rule reads, so no title was
recognised. A diagnosis field on it became a Fact whose document is a
`SERVICE_RECAP`. Provenance to the page is still correct; the document
attribution is not. The letter is `document_type = OTHER`: no listed type
fits it (GAP-002).

*Corrected after the Phase 2 logical-document review: iteration 1 described
this page as "an inpatient admission order without a title in the text
layer". The title is in the text layer, at the bottom of the page, and the
document is an inpatient plan letter.*

**OBS-005: blank separator pages alternate with photographed documents.**
Sample I has 4 image-only pages each followed by a blank page. They are kept
as pages; image pages became `UNKNOWN` documents with image evidence, blank
pages belong to no document.

**OBS-006: document order is not clinical order.** In Sample E the triage
form, the earliest clinical event, is the last page of the PDF.

**OBS-007: the same event appears in two documents with different
precision.** In Sample E the arrival is stated as a date in the assessment
and as a date-time in the triage form. The slice keeps two Events
(ADR-09).

**OBS-008: labels and values separated by table layout.** In Sample I's
discharge summary, the admission/discharge labels and their values come out
on different text lines, so no admission/discharge Event was produced and the
dates have role `UNKNOWN`. Native text order does not preserve table cells.

**OBS-009: two-column lines merge unrelated fields.** One extracted text
line often holds two label/value pairs from neighbouring columns (for
example a diagnosis next to a care class). The Fact keeps only the code, but
its Evidence `source_text` carries the whole line, including the other field
(ADR-08).

**OBS-010: prescription lines include devices and are wrapped.** At least 14
of 42 "R/" lines in Sample I are devices or consumables (syringes, gloves,
swabs, underpads). Some names wrap onto the next line, so the Fact value is
truncated. Two lines contain a literal `null` printed by the source system.
This confirms ADR-06 (`item_category`, `medication_context`).

**OBS-011: the claim's initial diagnosis differs from the coded main
diagnosis.** In both samples the SEP diagnosis ("Diagnosa Awal") differs from
the INA-CBG main diagnosis. Both are kept as separate Facts with their printed
labels (ADR-04).

**OBS-012: dates.** Both samples mix ISO dates, `dd/mm/yyyy`, `dd-mm-yyyy`,
Indonesian and English month names and abbreviations, with and without time
and "WIB". No ambiguous numeric date occurred in these two samples (the day
was always > 12 or the format was ISO), so the ambiguity rule is covered only
by the synthetic bundle. Print, entry and signature dates are frequent; one
signature date is weeks after the visit.

**OBS-013: almost every text page also contains images.** 34 of 49 text
pages embed images (logos, barcodes, signatures, stamps). `DIGITAL_TEXT` vs
`MIXED` cannot be decided from "has images" (ADR-11).

**OBS-014: a "recap" title over an itemised bill, printed twice.** Sample I
has two documents titled as a service recap with the same transaction; the
first is itemised line by line, the second is a summary. Title semantics do
not match the Billing / Service Recap / Detailed Billing split (taxonomy 32.3)
and the second may be a partial duplicate (ADR-07). Not detected by the slice.

**OBS-015: printed length of stay counts both ends.** In both samples the
printed LOS equals the number of calendar days including admission and
discharge day, matching the taxonomy example. No derived LOS is computed in
this slice; the counting rule is noted for the future `DERIVED_FACT`.

**OBS-016: chunks split at page breaks.** Because a Chunk has one
`page_number` (DATA_MODEL 10), a lab table or a CPPT note that continues on
the next page becomes two chunks. Provenance stays simple; semantic
coherence across the break is lost.

**OBS-017: an emergency visit prints "Tanggal Masuk" / "Tanggal Keluar".**
In Sample E (an emergency visit that the SEP and INA-CBG declare as
outpatient) the resume prints date-in and date-out labels. Iteration 1
turned them into ADMISSION and DISCHARGE events. This is the evidence for
ADR-REQ-003.

## Gaps

**GAP-001: `document_type` has no value for "not classified".** `OTHER`
means a known type outside the list. The slice needs both. See ADR-REQ-002.

**GAP-002: no `document_type` for forms seen in both samples:** triage,
inpatient admission request, inpatient plan letter, single-clinician
medication orders. They
are typed `OTHER` with the title kept.

**GAP-003: `completeness_status` uses the availability vocabulary.** Printed
counters ("1 of 3, 2 of 3, 3 of 3") can show that a document is complete or
missing pages, but `PRESENT | NOT_FOUND | ...` cannot express "complete" or
"partial". The slice records the counters (`page_counters`) and leaves
`completeness_status = UNKNOWN`.

**GAP-004: no vocabulary for "text not extracted".** For an image-only page
without OCR, `NO_TEXT` would wrongly claim the content is non-textual and
`modality` cannot say scan vs photo. See ADR-REQ-004.

## Decision status

**DECIDED** (PR #1 review, applied in iteration 2):

| Decision | Accepted option | Applied as |
|---|---|---|
| ADR-REQ-001 page membership provenance | B | `PageRef.basis` + `PageRef.evidence_ref` on every `page_refs` entry; page-assignment diagnostic |
| ADR-REQ-002 unclassified type | A | `DocumentType.UNKNOWN`, distinct from `OTHER` |
| ADR-REQ-003 ADMISSION semantics | B | ADMISSION = inpatient admission; "Masuk/Keluar" dates keep `date_role = UNKNOWN` plus the printed label; no ADMISSION/DISCHARGE events |
| ADR-REQ-004 extraction status | B | `text_status` beside `extraction_method`; `NO_TEXT` never assigned |

**STILL OPEN**

- ADR-01: a page in several documents; a document starting mid-page.
- ADR-05: a `date_role` / event for encounter start and end of any
  visit. ADR-REQ-003 only says what ADMISSION is *not*.
- ADR-03: how an inpatient stay is established (declared service type vs
  clinical evidence). Until then the slice emits no ADMISSION event at all.
- ADR-14 / GAP-002: types for triage, admission request, inpatient plan
  letter, single-clinician medication order (typed `OTHER` today).
- GAP-003: `completeness_status` vocabulary.
- ADR-11 remainder: per-component confidence; meaning of `MIXED`.
- ADR-04, 06, 07, 08, 09: unchanged; new evidence in OBS-007, 009, 010, 011, 014.

## Architecture decisions required (iteration 1, now decided)

The text below is the original request, kept as the record of why each
decision was made.

**ADR-REQ-001: page-to-document assignment has no provenance.**
(related: ADR-01)

- Problem: which Document a page belongs to is an inference made by the
  segmenter, often a weak one (OBS-003, OBS-004).
- Observed behaviour: 18 of 38 pages in Sample I were attached only because
  no new title appeared.
- Current model: `Document.page_refs[]` is a plain list of
  `{source_file_id, page_number}`. DATA_MODEL 14 says relationships carry
  provenance, but `page_refs` cannot.
- Options:
  A. keep plain `page_refs`; record the basis outside the model;
  B. add an optional `basis` (and evidence ref) to each `page_refs` entry;
  C. model page membership as a separate relationship object with
  provenance and confidence, allowing alternative segmentations.
- Recommended: **B**. It is additive, keeps `page_refs` as the authority,
  and is what the slice already does in code (`page_bases`, boundary
  evidence).
- Why: downstream layers (canonical claim, timeline) must be able to
  discount facts from weakly attached pages without re-running segmentation.

**ADR-REQ-002: "unclassified" document type.** (related: ADR-14)

- Problem: GAP-001.
- Observed behaviour: 6 documents across the three runs could not be
  classified (image-only, untitled).
- Current model: list ends with `OTHER`; no unknown value.
- Options: A. add `UNKNOWN` to `document_type`; B. keep the list and add
  `classification_status` (`CLASSIFIED | UNCLASSIFIED`); C. use `OTHER` for
  both.
- Recommended: **A** (implemented provisionally as `UNKNOWN`).
- Why: simplest, mirrors `UNKNOWN` in every other vocabulary; C would
  silently merge "unknown" with "known other".

**ADR-REQ-003: what "Tanggal Masuk" means outside an inpatient stay.**
(related: ADR-03, ADR-05)

- Problem: the label "Tanggal Masuk" (date in) maps to `date_role =
  ADMISSION`, and the slice emits an `ADMISSION` Event.
- Observed behaviour: in Sample E (an emergency visit the claim classifies
  as outpatient) the resume prints "Tanggal Masuk" and "Tanggal Keluar". The
  slice produced ADMISSION and DISCHARGE events although there was no
  inpatient admission.
- Current model: `ADMISSION` is used both as a date role and an event type;
  whether it means "start of this encounter" or "inpatient admission" is not
  defined.
- Options: A. `ADMISSION` means start of any encounter; inpatient admission
  is a separate event (`INPATIENT_ADMISSION`, already a taxonomy outcome);
  B. `ADMISSION` means inpatient admission only, and encounter start gets a
  new role (for example `ENCOUNTER_START`); C. keep the label-derived role
  and let the timeline layer reinterpret it with the care pathway.
- Recommended: **B**, so an `ADMISSION` event cannot appear on an emergency
  or outpatient visit by label alone.
- Why: a wrong ADMISSION event would flow straight into the timeline and
  into LOS-style derived facts.

**ADR-REQ-004: extraction method and modality for pages without OCR.**
(related: ADR-11)

- Problem: GAP-004 and OBS-013.
- Current model: `extraction_method` has no "not extracted" value;
  `modality` has no "image, kind unknown" value; `MIXED` is undefined.
- Options: A. add `NOT_EXTRACTED` to `extraction_method`; B. keep the
  vocabulary and add a separate text-extraction status (what the slice does
  with `text_status`); C. use `UNKNOWN` for both.
- Recommended: **B** for now (implemented). Revisit when OCR is introduced,
  because OCR adds a second representation of the same page (DATA_MODEL 42).

No decision is required for OBS-016 (chunk per page): the slice follows
DATA_MODEL 10 as written. It is listed so the trade-off is visible when
retrieval is designed.

## Implementation decisions

| ID | Decision | Why |
|---|---|---|
| IMPL-001 | `document_type = UNKNOWN` added (ADR-REQ-002). | Needed by the brief and by image-only pages. |
| IMPL-002 | `text_status` on Page and `ingestion_status` on SourceFile. | Failure must be explicit without misusing `extraction_method`. |
| IMPL-003 | `page_counters` on Document; in iteration 1 also `page_bases`, replaced in iteration 2 by `PageRef.basis` / `evidence_ref` (ADR-REQ-001). | Makes segmentation inspectable. |
| IMPL-004 | Evidence has `purpose` and `chunk_id`. | Shows that evidence exists without a fact; the brief asks for a chunk reference. |
| IMPL-005 | Fact has `source_label` (printed label, e.g. "Diagnosa Awal"). | `diagnosis_role` / `diagnosis_context` are open (ADR-04); the label must not be lost. |
| IMPL-006 | Temporal Value has `ambiguity`. | DATA_MODEL 17A allows "flagged"; this is the flag. |
| IMPL-007 | Ambiguous numeric dates stay `UNKNOWN` unless `--numeric-date-order` is given. | No guessing; the option is the "documented adapter configuration" of 17A. |
| IMPL-008 | Birth dates are skipped. | Personal data with no use in this slice (ADR-08). |
| IMPL-009 | `source_reference` is the file name only; `source_file_id` comes from the content digest. | Local paths can reveal names; identity must be stable. |
| IMPL-010 | `document_role` for types without a taxonomy-9 example is assumed and marked in `rules.py`; `OTHER`, `UNKNOWN`, `REFERRAL` get none. | No role is guessed where there is no basis. |
| IMPL-011 | A page counter k > 1 outranks a title. | OBS-001. |
| IMPL-012 | One Fact per mention; no merging across documents. | ADR-09 open. |
| IMPL-013 | Claim anchors never produce Events. | DATA_MODEL 31. |
| IMPL-014 | `sensitivity = UNKNOWN`, `redaction_state = ORIGINAL` on all evidence. | ADR-08 open; the slice cannot classify text. |
| IMPL-015 | `classification_confidence`, `bbox`, `confidence` left empty. | No calibrated score or coordinates exist (DATA_MODEL 34). |
| IMPL-016 | stdlib dataclasses; one runtime dependency (`pypdf`). | Small, pure Python; Pydantic not needed until schemas exist. |

Added in iteration 2:

| ID | Decision | Why |
|---|---|---|
| IMPL-017 | `AssignmentBasis` gains `EXTRACTION_FAILED` for pages whose text extraction raised an error. | Calling them `IMAGE_PAGE` would misstate what is known. |
| IMPL-018 | `CONTINUATION` and `UNTITLED_START` cite the page's first text line as evidence. | They have no positive signal; the first line shows what the page starts with, which matched no rule. |
| IMPL-019 | Temporal Value keeps `source_label` (the printed label before the date). | "Tanggal Masuk" is preserved without claiming a role (ADR-REQ-003). |
| IMPL-020 | The run also writes `<name>.page_assignment.txt`; the inspection report includes the same block. | Page assignment is the largest error source; reviewers need to see each page's basis and evidence. |

## Iteration 2 results

Same inputs, same code paths except for the four decisions.

| | Sample E iter 1 | Sample E iter 2 | Sample I iter 1 | Sample I iter 2 |
|---|---|---|---|---|
| Pages | 18 | 18 | 38 | 38 |
| Documents | 9 | 9 | 14 | 14 |
| UNKNOWN documents | 0 | 0 | 4 | 4 |
| Pages without document | 0 | 0 | 3 (blank) | 3 (blank) |
| Facts | 6 | 6 | 49 | 49 |
| Events | 4 | 2 | 0 | 0 |
| Evidence | 19 | 26 | 63 | 84 |

- **Page assignment did not change.** No page moved to another document or
  type in either sample. The decisions add provenance; they do not fix
  segmentation, and no improvement in assignment is claimed.
- **The suspected wrong assignments are now explicit.** In Sample I the nine
  pages after the CPPT and the last page are each shown as
  `Basis: CONTINUATION` with the cited first line as evidence. Before, the
  same pages were attached silently.
- **A basis alone does not separate right from wrong.** Of the 18
  `CONTINUATION` pages in Sample I, about 10 are the suspected wrong ones and
  about 8 look right (summary, CPPT and billing continuation pages). Telling
  them apart needs another signal (layout, header/footer), not a different
  basis value.
- **Events:** Sample E lost its ADMISSION and DISCHARGE events (OBS-017);
  the two arrival events remain. The dates stay on the resume with
  `date_role = UNKNOWN` and labels "Tanggal Masuk" / "Tanggal Pulang".
  Billing and INA-CBG date-out labels ("Tgl Keluar", "Tgl KRS") are now
  `UNKNOWN` too, as they were never events (claim anchors).
- **Evidence** now has one item per page membership instead of one per
  document: +9 in Sample E (minus 2 for the removed events) and +21 in
  Sample I.

No new architecture decision was exposed by iteration 2.

## Technical debt

- **TECH-001** Text comes from pypdf's native text order. No coordinates,
  no table cells, no column separation (OBS-008, OBS-009). bbox is empty.
- **TECH-002** No OCR: image-only pages are opaque.
- **TECH-003** Image count reads page resources; it does not check whether
  an image is drawn or how much of the page it covers.
- **TECH-004** Recognition rules are a Python module. They should move to
  versioned configuration (`rule_version`, DATA_MODEL 43).
- **TECH-005** Section headings are a short keyword list; many sections
  are tiny and long headings with inline content are missed.
- **TECH-006** "R/" lines are taken one text line at a time, so wrapped
  names are truncated (OBS-010).
- **TECH-007** No duplicate detection (OBS-014).
- **TECH-008** JSON output is not validated against a schema; ids are
  sequential per run, so they are stable only for identical input.
- **TECH-009** Logging is minimal (a few structured warnings).

## Next recommended step

*(Written after iteration 1. After iteration 2 the work stops here and
waits for architecture review; nothing below has been started.)*

The errors in this run came from two places: weak page-to-document
attachment (OBS-003/004) and loss of layout (OBS-008/009/010). Both are
upstream of canonical extraction, so building the canonical claim next would
build on unreliable input.

1. Decide ADR-REQ-001 to 004. They are small and additive, and 001 and 003
   change what the next layers can trust.
2. Add layout-aware element extraction: line positions and bbox, column
   separation, label/value pairing within a table row. This fills Evidence
   `bbox`, fixes OBS-008/009/010, and gives the segmenter a header/footer
   signal for untitled pages (OBS-003).
3. Re-run both samples plus at least one bundle from another hospital, and
   compare page attachment against a hand-labelled page map kept outside Git.
4. Only then start canonical extraction (diagnoses with role/context,
   procedures, medications with context).
