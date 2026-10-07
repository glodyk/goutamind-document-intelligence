# Phase 2 investigation: physical layout and document boundaries

**Status:** investigation for architecture review. Nothing here is
implemented, and nothing here changes the PR #1 architecture or
`DATA_MODEL.md`. No dependency, OCR, LLM, ML, scoring model or canonical
extraction is proposed for implementation.

**Inputs:** `docs/findings/SLICE_01_FINDINGS.md` (PR #1, iterations 1 and 2),
the PR #1 architecture review, `DATA_MODEL.md` sections 5A, 7, 9, 10, 11,
11A, 15, 42 and Appendix B/C, and the structural outputs of the slice on
Sample E (18 pages) and Sample I (38 pages). As in the findings, no content,
identifier, code or date from the real samples is reproduced.

Every statement carries one of these tags:

| Tag | Meaning |
|---|---|
| **OBSERVED** | Seen in a slice run, in the code, or by running the library on the committed synthetic PDF. |
| **INFERRED** | Reasoned from observations; not yet measured. |
| **PROPOSED** | A suggestion for review. Not decided, not implemented. |
| **DECIDED** | Already decided by the owner (PR #1 review). |
| **OPEN** | A question this investigation cannot answer yet. |

---

## 1. Objective

Find out whether the next largest problem is in the physical/layout
representation and in document boundary detection, before canonical
extraction is built. Concretely:

1. Which layout information is lost today, and which observed errors it causes.
2. Which deterministic signals a PDF offers for boundaries and for
   label/value structure, without OCR, ML or new dependencies.
3. Which representation option (A–D) should be tested next, and how to
   measure whether it helps.
4. Whether any of this needs an architecture decision now.

---

## 2. Evidence from Phase 1

| Finding | What was seen (OBSERVED) | Layout information that would be needed (INFERRED) |
|---|---|---|
| OBS-003 untitled continuation pages | Sample I: 9 untitled pages after a CPPT attached to it by `CONTINUATION`. By manual reading they look like separate medication/order printouts, each with its own header block. | Something that tells "same form, next page" from "different form, no title": a header/footer or layout signature. |
| OBS-004 wrong document attribution | Sample I, last page (an inpatient plan letter whose title is printed at the bottom of the page, outside the lines the title rule reads) attached to the preceding service recap; a diagnosis on it became a Fact of a `SERVICE_RECAP`. | Same as OBS-003. A layout change between a tabular recap page and a form page. |
| OBS-008 label/value split by table layout | Discharge summary: admission/discharge labels and their values come out on different text lines. | Positions: label and value drawn in the same visual row or cell. |
| OBS-009 two-column lines | One extracted line holds two label/value pairs from neighbouring columns; Evidence `source_text` carries both. | Horizontal positions and gaps to split a visual line into column segments. |
| OBS-010 wrapped prescription lines | Some "R/" item names wrap onto the next line; the Fact value is truncated. | Indentation and vertical spacing to tell a wrapped continuation from a new item. |
| OBS-013 text pages with images | 34 of 49 text pages embed image resources (logos, barcodes, signatures, stamps). | Where an image is drawn and how large it is, not only that it exists. |
| OBS-016 chunks split at page breaks | A lab table or a CPPT note continuing on the next page becomes two chunks. | A signal that a table or note continues across the break. Not a layout gap in itself (see 10.5). |

Additional structural observations from the iteration 2 outputs (OBSERVED,
counts only):

- Sample E: 18 pages, 9 documents; bases 9 `TITLE`, 6 `PAGE_COUNTER`,
  3 `CONTINUATION`. Manual reading found every page in the right document.
- Sample I: 38 pages, 14 documents; 18 pages rest on `CONTINUATION`. About
  10 of them are the suspected wrong ones (pages 23–31 and 38); about 8 look
  right (discharge summary, CPPT and service-recap continuation pages).
- The page-level image count that the slice reads from page resources does
  **not** separate suspected-wrong from correct continuation pages: in Sample I
  the nine suspected pages after the CPPT have no image resource, but neither
  do four correct continuation pages (one CPPT page, three service-recap
  pages), while the suspected last page has image resources. Line counts per
  page do not separate them either.
- In Sample E no assignment error was found, so Sample E is the regression
  guard: any new signal must not split its correct continuation pages.

What Phase 1 does **not** show (OPEN): whether pages 23–31 of Sample I are
nine documents or one multi-page printout. "Each with its own header block"
comes from a manual reading, not from a labelled page map.

---

## 3. Problem statement

Two problems sit upstream of canonical extraction (INFERRED from section 2):

1. **Weak page-to-document assignment.** When a page has no title, marker or
   counter, the only rule left is "attach to the current document". Since
   ADR-REQ-001 (DECIDED) this is visible (`basis = CONTINUATION` plus the
   first line as evidence), but the basis explains the mechanism, not the
   correctness (PR #1 review note 3). About 10 of 18 continuation pages in
   Sample I are suspect, and no text-only signal used so far separates them
   from the 8 correct ones.
2. **Loss of layout inside a page.** Native text order merges columns,
   separates labels from values in tables, and breaks wrapped item names.
   This lowers the quality of Facts and puts unrelated (possibly personal)
   fields into Evidence `source_text`.

Both problems come from the same gap: the physical layer stores lines of
text **without positions**. Building canonical extraction on top would carry
wrong document attribution (OBS-004) and wrong values (OBS-008/009/010)
into the canonical claim.

What is *not* the problem (OBSERVED): pages with a title, marker or page
counter. Those were assigned correctly in all three runs. Image-only and
blank pages are also handled as decided (ADR-REQ-004).

---

## 4. Current physical representation

OBSERVED, from `app/extraction/pdf_reader.py`, `app/extraction/models.py`
and the slice outputs:

| Layer item | What is stored today | What is missing |
|---|---|---|
| SourceFile | id from content digest, file name, page count, ingestion status | – |
| Page | `page_kind`, `modality`, `extraction_method`, `text_status`, `image_count`, elements | page size, rotation, page box |
| Text element | one `TEXT` element per non-empty line of pypdf `extract_text()` (plain mode), in content-stream order | `bbox`, font, size, column, any grouping |
| Image element | one `IMAGE` element per image XObject in the page resources | whether it is drawn, where, how large (TECH-003) |
| Layout elements | none | `HEADER`, `FOOTER`, `TABLE`, `TABLE_CELL`, `LINE` (all already listed in DATA_MODEL 11) |
| Chunk | a section's lines on one page | – (one `page_number`, as DATA_MODEL 10 requires) |
| Evidence | `element_id`, page, source file, `source_text` (the whole line); `bbox = null` | position; a sub-line part when a line holds two fields |

Two facts about the existing model matter for the options (OBSERVED, from
`DATA_MODEL.md`):

- `DocumentElement` already has `bbox` and `style`, and its `element_type`
  vocabulary already has `HEADER`, `FOOTER`, `TABLE`, `TABLE_CELL` and
  `LINE`. Evidence already has an optional `bbox`. Filling them is **not** a
  model change.
- DATA_MODEL 42 already says that reprocessing with a different extraction
  method creates a new representation and does not replace the earlier one.

What the current library already offers without a new dependency (OBSERVED,
pypdf 6.17.0, checked on the committed synthetic PDF only):

- `extract_text(visitor_text=...)` calls back per text run with the text,
  the current transformation matrix, the text matrix, the font dictionary
  and the font size. On the synthetic PDF this gave the start point (x, y)
  and size of every run.
- `extract_text(visitor_operand_before=...)` exposes each content-stream
  operator with the current matrix, which is where an image draw (`Do`) and
  marked content (`BDC`/`BMC`) would be seen.
- `page.mediabox` and `page.rotation` are available.
- `extract_text(extraction_mode="layout")` returns text spaced to mimic the
  page, but as a string without coordinates.

Not offered directly (INFERRED from the API): a run's end point or width
(it needs the font's glyph widths), and any notion of line, column, table
or header. Whether the real samples have tagged structure (`/StructTreeRoot`,
`/Artifact` pagination marks), an outline, or differing page sizes is not
known (OPEN, step E0 of the experiment). The synthetic PDF has none of them.

---

## 5. Candidate approaches

### Option A: current line-based representation

Keep one `TEXT` element per extracted line, no coordinates.

- **Data model change:** none.
- **Benefit:** stable; every Evidence id and the golden output stay as they are.
- **Risk:** the errors in section 2 stay. Any fix has to be a text heuristic
  (for example "a page whose first line looks like a header block starts a
  document"), which is a hospital-layout rule in disguise and conflicts with
  the project principle "do not normalize the hospital layout".
- **Evidence lineage:** unchanged; `bbox` stays empty.
- **Segmenter:** unchanged; continuation remains the default.
- **OBS-003/004:** not solved (OBSERVED: no text-only signal used so far
  separates the suspect pages). **OBS-008/009/010:** not solved.
- **Complexity:** none. **New dependency:** no.

### Option B: add coordinates to text

Build text elements from positioned runs (via the pypdf visitor) and store a
`bbox` and font size on each; group runs into visual lines by vertical
position.

- **Data model change:** none for `bbox`/`style` (already defined). Page
  needs its size and rotation so a `bbox` can be interpreted (PROPOSED,
  additive). A coordinate convention is needed (OPEN, Q1).
- **Benefit:** Evidence gets a position; a header/footer band and
  indentation become measurable; a label and a value drawn on the same row
  can be found even if pypdf emits them on different lines.
- **Risk:** visual lines built from runs differ from pypdf's own lines, so
  element ids and line texts change. Run width must be estimated, so the
  right edge of a `bbox` is approximate (INFERRED). Rotated or
  matrix-transformed text needs care.
- **Evidence lineage:** improves (position); element ids change unless the
  old representation is kept (see D).
- **Segmenter:** gains position-based inputs (top/bottom band text), but B
  alone has no notion of a header or a column.
- **OBS-003/004:** partly; a header band can be compared between pages, but
  B does not define what a header is. **OBS-008:** likely solved for
  same-row label/value. **OBS-009:** not solved unless lines are also split
  at large horizontal gaps. **OBS-010:** likely solved by indentation.
- **Complexity:** moderate. **New dependency:** no (INFERRED; confirmed only
  on the synthetic PDF).

### Option C: layout-aware elements and regions

On top of coordinates, derive regions: header band, footer band, column
segments, table rows and cells, and image placements, as elements with
`element_type` `HEADER`, `FOOTER`, `TABLE`, `TABLE_CELL`, `IMAGE`.

- **Data model change:** element types already exist. A region has to point
  to the elements it contains; DATA_MODEL 11 has no parent/child reference
  (PROPOSED, additive, OPEN Q2).
- **Benefit:** a page signature (header, footer, columns, image placement)
  can be compared across pages for boundaries; label/value pairing by row or
  cell; Evidence can cite one cell instead of a merged line.
- **Risk:** region detection without ML is heuristic. Tables without ruling
  lines, forms with free placement, and stamps over text vary by hospital, so
  a region detector can be wrong while looking precise. Wrong regions would
  be worse than no regions, because they would produce confident-looking
  evidence. C also implies B.
- **Evidence lineage:** strongest (cell-level evidence with `bbox`), but only
  as reliable as the region detection.
- **Segmenter:** can use header/footer/layout similarity directly.
- **OBS-003/004:** likely, if the suspect pages have a header/layout that
  differs from the preceding document (INFERRED, unmeasured). **OBS-008/009:**
  likely. **OBS-010:** likely.
- **Complexity:** high. **New dependency:** not necessarily; a library with
  table detection would be a new dependency.

### Option D: hybrid

Keep the current line elements as they are (representation 1). Add a
positioned representation next to it (representation 2): runs grouped into
visual lines with `bbox`, split into segments at large horizontal gaps.
Derive only a few regions, and only where a deterministic rule supports
them: a header band and a footer band defined by **text repeated across
pages**, column segments defined by gaps, and image placements. Where no rule
applies, no region is created; nothing is forced.

- **Data model change:** the B and C additions (page size/rotation, a
  coordinate convention, a region-to-element reference), plus a way to tell
  representations of the same page apart (OPEN Q2). DATA_MODEL 42 already
  allows several representations.
- **Benefit:** existing Evidence and golden output stay valid; new signals
  can be compared side by side with the current ones on the same pages,
  which is what an evidence-driven decision needs.
- **Risk:** two representations of one page must not both produce Facts
  for the same text (double counting); a rule is needed for which one feeds
  Facts (OPEN Q2). More data per page.
- **Evidence lineage:** existing Evidence keeps pointing at representation 1;
  new Evidence can point at a segment or region with a `bbox`. A segment
  holding one field also reduces unrelated personal data in `source_text`
  (OBS-009, ADR-08).
- **Segmenter:** same as C for the regions that exist; falls back to today's
  rules otherwise.
- **OBS-003/004/008/009/010:** as C where the deterministic regions exist,
  as B elsewhere.
- **Complexity:** moderate; less than C because regions are limited to the
  ones that can be justified. **New dependency:** no (INFERRED).

---

## 6. Trade-off matrix

Ratings are INFERRED. None of them is measured; section 11 says how to
measure them.

| | A: lines | B: coordinates | C: regions | D: hybrid |
|---|---|---|---|---|
| Data model change | none | small, additive | additive (region references) | additive (B + C + representation identity) |
| OBS-003 continuation pages | no | partial | likely | likely where header/footer repeat |
| OBS-004 wrong attribution | no | partial | likely | likely |
| OBS-008 label/value in tables | no | likely (same row) | likely | likely |
| OBS-009 two-column lines | no | only with gap split | likely | likely |
| OBS-010 wrapped "R/" lines | no | likely (indent) | likely | likely |
| Evidence `bbox` | none | yes | yes | yes |
| Existing Evidence ids | unchanged | change | change | unchanged (new ones added) |
| Risk of confident-looking errors | low | low | high | medium |
| Effect on current segmenter | none | new inputs | new signals | new signals, old rules kept |
| Implementation complexity | none | moderate | high | moderate |
| New dependency | no | no* | no*, unless a table library | no* |

\* Assuming the pypdf visitor gives usable positions on the real samples
(experiment step E1). If it does not, a library such as pdfminer.six or
pdfplumber would be the alternative; that would be a dependency decision for
the owner (OPEN Q7).

---

## 7. Recommended approach

**PROPOSED: Option D, tested by an experiment before any implementation.**

Why, from the evidence:

- The text-only signals tried in Phase 1 do not separate the suspect
  continuation pages from the correct ones (OBSERVED, section 2). A position
  or layout signal is the next candidate, and only B, C and D provide one.
- Four of the five targeted findings (OBS-008/009/010 and Evidence `bbox`)
  need positions inside a page, which A cannot give.
- D keeps the PR #1 representation and its Evidence intact (DATA_MODEL 42),
  so the experiment can report "before vs after" on the same pages, and the
  decision can be reversed by dropping representation 2.
- D limits regions to those with a deterministic basis (text repeated
  across pages, horizontal gaps, image draws), which keeps the honesty rule
  from PR #1: an uncertain structure stays absent instead of being forced.
- The library already in use appears to expose positions (OBSERVED on the
  synthetic PDF), so no dependency is needed to test it.

What D will probably **not** fix (INFERRED):

- If the nine pages after the CPPT share one header layout with each other,
  a layout signature can separate them from the CPPT, but not from each
  other. Whether they should be separated from each other is a ground-truth
  question (OPEN Q4).
- Fixing a boundary does not classify the page. The last page of Sample I
  would move to an `UNKNOWN` document, which is correct but not typed
  (DECIDED: `UNKNOWN` is not `OTHER`).
- OBS-016 (chunks at page breaks) is a chunking rule, not a layout gap.

---

## 8. Impact on existing data model

PROPOSED, all additive, none applied. Each would be written down as
DATA_MODEL additions only after the experiment shows it is needed.

| Item | Status in DATA_MODEL today | Change under D |
|---|---|---|
| `DocumentElement.bbox`, `style` | defined, optional | filled for representation 2 |
| `element_type` `HEADER`, `FOOTER`, `TABLE`, `TABLE_CELL`, `LINE` | defined | used for derived regions |
| Page width, height, rotation | not defined | added, so a `bbox` can be read (Q1) |
| Coordinate convention (unit, origin, page box, rotation) | not defined | needed before a `bbox` is persisted (Q1) |
| Region → contained elements | not defined | a reference from a region to its elements, or from an element to its region (Q2) |
| Representation identity | principle in section 42, no field | a way to tell representation 1 and 2 of a page apart and to say which feeds Facts (Q2) |
| `PageRef.basis` vocabulary | slice vocabulary (ADR-REQ-001 B, DECIDED) | possibly new basis values for a layout signal (implementation vocabulary, not a new contract) |
| `PageRef` with several signals | one `basis`, one `evidence_ref` | possibly several, including conflicting ones (Q3) |
| `Section.page_start/page_end` | positions in `page_refs` for non-contiguous documents | unchanged; layout work must not make contiguity an invariant (PR #1 review note 2) |
| Chunk single `page_number` | DATA_MODEL 10 | unchanged (Q6) |

Nothing in DOCUMENT_TAXONOMY.md changes. No `document_type` is added.

---

## 9. Impact on Evidence

INFERRED unless marked.

- **Position:** Evidence `bbox` can be filled for text from representation 2.
  Image evidence can carry the drawn area instead of only "this page"
  (OBS-013).
- **Granularity:** Evidence can point at a segment (one side of a
  two-column line) or a cell instead of a merged line. This makes a Fact's
  `source_text` match the Fact and reduces unrelated personal data in
  evidence (OBS-009, ADR-08).
- **Lineage:** existing Evidence keeps pointing at representation 1, so PR #1
  outputs stay valid. New Evidence must say which representation it cites
  (Q2). An element id must be unique across representations of a page.
- **Page membership:** the evidence for a page assignment can cite a header
  or footer region instead of the first line, and could cite more than one
  signal (Q3). DECIDED: no numeric confidence is added (ADR-REQ-001 B).
- **Sensitivity:** header and footer bands often hold the patient name and
  record number (INFERRED from the form types). A page signature used for
  comparison should be computed from normalised text (digits masked) and
  kept as a digest, not as copied text (PROPOSED, relates to ADR-08).
- **Not changed:** Evidence ≠ Fact; Evidence without a Fact remains valid.

---

## 10. Impact on segmentation

### 10.1 Deterministic boundary signals

Which signals a PDF can give without OCR, ML or scoring:

| Signal | Status | Needs | What it can say | Known limits |
|---|---|---|---|---|
| Title | in use | text | "a document of type T starts here" | missing on many first pages (OBS-002); generic words need first-line scope |
| Marker | in use | text | "an SEP / lab report starts here" | only for types with distinctive labels |
| Page counter | in use | text | k = 1 starts, k > 1 continues | strongest signal (OBS-001); absent on many forms |
| Header/footer | not used | coordinates + repetition across pages | "same form as the previous page" or "a different form starts" | a continuation page may have no header; text in the band varies (dates, numbers) and must be normalised |
| Layout similarity | not used | coordinates | column positions, font set, line density alike or not | correct continuation pages can look different (a short last page) |
| Continuation signal | partly (counter) | coordinates | a table continuing with the same column positions; an item list continuing | must not override a positive start signal |
| Image/scan boundary | in use (image-only page) | image draws with position | logo or stamp placement as part of a page signature; scan vs text page change | page-level image counts do not separate the suspect pages (OBSERVED) |
| Page size / rotation | not used | page box | a change of paper size or orientation between pages | unknown whether it varies in the samples (E0) |
| Tagged structure / outline | not used | PDF catalogue | pagination artefacts, bookmarks | unknown whether present (E0); likely absent in merged claim PDFs (INFERRED) |

### 10.2 How signals would combine (PROPOSED, no scoring)

Keep the current ordered rules, which are correct for every page that has a
positive signal, and change only the default at the end:

1. Blank, image-only and failed pages: as today.
2. Counter k > 1, title, counter k = 1, marker: as today.
3. **New:** no positive signal, and the page's header/footer/layout signature
   **differs** from the current document's: start a new `UNKNOWN` document
   with a layout basis and the region as evidence.
4. **New:** no positive signal, and the signature **matches**: continuation,
   with the matching region as evidence instead of the first line.
5. No signature available (no header band found, no coordinates): today's
   `CONTINUATION`, unchanged and still marked as weak.

When signals disagree (for example a matching footer but a different column
layout), the conflict is recorded on the page assignment rather than
resolved by a weight (Q3). No score, no threshold learned from data.

### 10.3 Effect on the observed cases (INFERRED, to be measured)

- Sample I pages 23–31: split from the CPPT if their header band differs
  from the CPPT pages. Splitting them from each other needs a per-printout
  difference (for example a header that changes per printout) and a ground
  truth that says they are separate (Q4).
- Sample I page 38: split from the service recap if a form page and a
  tabular recap page have different signatures; the result is an `UNKNOWN`
  document.
- Correct continuation pages (Sample E: 3; Sample I: about 8): at risk of a
  false split when a continuation page has no header or is a short last
  page. This is the main risk and is measured as false boundaries.

### 10.4 Order of work inside the segmenter (PROPOSED)

Header/footer detection is needed before layout similarity, because the
header band is the cheapest and most specific signature. Column and table
structure is needed for label/value pairing but not for boundaries.

### 10.5 OBS-016

Layout can tell that a table continues on the next page (same column
positions), but DATA_MODEL 10 gives a chunk one `page_number`. Joining chunks
across a page break would change that contract. This investigation does not
propose it; a continuation relation between two chunks would be the
additive alternative (OPEN Q6, for when retrieval is designed).

---

## 11. Minimal next experiment

PROPOSED. A throwaway measurement, not an implementation: no change to
`app/` or `pipeline/`, no dependency, outputs and labels kept outside Git
(`samples_private/`, `outputs/`). Only aggregate numbers are reported.
**Not to be run until the owner confirms the ground truth.**

### Framing: logical document first (DECIDED, owner review)

> Identify the document first. Record its pages second.
> Physical page location is evidence provenance, not document identity.

The experiment does **not** ask "where do page boundaries fall?" and then
group pages into documents. It asks whether the evidence available in the
PDF identifies the same logical documents a person identifies, and only then
records which pages hold each document's evidence.

```text
Primary:    physical document evidence
                    ↓
            logical document identity
                    ↓
            member_page_refs (provenance; may be non-contiguous)

Secondary:  page-boundary precision / recall (operational check only)
```

Page-boundary metrics stay useful for diagnosing the segmenter, but they do
not define a logical document. A page sequence that happens to split
correctly can still assign the wrong identity, and a document can be
identified correctly from pages that are not adjacent.

### Steps

```text
E0  PDF inventory: page box, rotation, fonts used, image draws (Do +
    matrix), marked content, tagged structure, outline
        ↓
E1  Extract text runs + coordinates (pypdf visitor_text)
    → coverage check against today's extracted text
        ↓
E2  Group runs into visual lines; split lines at large horizontal gaps
        ↓
E3  Detect header/footer bands (text repeated in the top / bottom of pages,
    digits masked) and column segments
        ↓
E4  Collect document identity signals as evidence: title, marker, printed
    counter, header/form identity (for example an order or transaction
    number in a header block), footer/form code, closing signature block,
    internal section sequence, layout signature, image placement
        ↓
E5  Form logical document hypotheses from those signals; record each
    hypothesis's member_page_refs and identification basis; compare with
    the logical document ground truth. Evaluate label/value and "R/" line
    reconstruction on their own labelled sets
```

E0–E3 produce physical evidence. E4–E5 are where identity is decided, and
they work from that evidence, not from page order. Rules stay deterministic
and ordered as in section 10.2; there is no score.

### Ground truth needed first

A **logical document ground truth** per sample, made by a person and kept
outside Git. One record per logical document:

```text
logical_document_id
document_type
document_role
identification_basis      the documentary evidence for its identity
member_page_refs          provenance, recorded after identification
status                    DRAFT | OPEN / NEEDS HUMAN GROUND TRUTH | CONFIRMED
notes                     relationships to other documents, ambiguity
```

Documents whose identity is still OPEN are reported separately and are not
counted as right or wrong. Relationships between documents (for example a
referral letter and its consent/refusal form, linked by one referral event)
are recorded as relationships, not merged into one document.

Separate small labelled sets are needed for label/value pairs (OBS-008
discharge-summary fields, OBS-009 two-column lines) and for the "R/" items of
Sample I.

### Metrics

Primary (logical document identity):

| Metric | Definition |
|---|---|
| Documents recovered | ground-truth documents (not OPEN) for which one hypothesis has the same `member_page_refs` |
| Merged documents | ground-truth documents whose evidence ended up inside another document's hypothesis |
| Split documents | ground-truth documents spread over more than one hypothesis |
| Spurious documents | hypotheses that match no ground-truth document |
| Type agreement | recovered documents with the same `document_type` |
| Identity basis agreement | recovered documents whose basis cites the same kind of evidence as the ground truth (for example a form identity rather than "continuation") |
| OPEN documents | reported separately: what the hypotheses say about them, without scoring |

Secondary (operational):

| Metric | Definition |
|---|---|
| Page-boundary precision / recall | over page transitions, derived from `member_page_refs` |
| Page assignment accuracy | pages whose document matches the ground truth / pages with physical evidence |
| Weak-basis pages | pages assigned only by `CONTINUATION` |

Physical layout:

| Metric | Definition |
|---|---|
| Label/value pairing correctness | correctly paired / labelled pairs |
| Mixed-field lines | lines or segments holding fields from two columns |
| "R/" line reconstruction | items whose full name is reconstructed / items; plus wrong joins |
| Run coverage (E1) | characters in positioned runs / characters in today's text |

### Phase 1 baseline against the draft ground truth (OBSERVED)

The PR #1 pipeline, compared with the draft logical document ground truth
(DRAFT, not yet confirmed):

| | Sample E | Sample I |
|---|---|---|
| Ground-truth documents (excluding OPEN) | 9 | 14 |
| Documents recovered | 9 | 12 |
| Not recovered | 0 | 2: the CPPT (its hypothesis also holds the pages of the OPEN medication/order printouts) and the inpatient plan letter (OBS-004) |
| Merged documents | 0 | 1: the inpatient plan letter, absorbed by the hypothesis that holds the second service recap |
| Type agreement among recovered | 9 of 9 | 8 of 12 (the four image-only documents are `UNKNOWN`) |
| OPEN documents | 0 | 8: seven medication/order printout candidates and the second service recap |
| Weak-basis pages (secondary) | 3 | 18 |

### What would count as a useful result (PROPOSED)

- Sample E: all 9 documents still recovered; none merged, split or spurious.
- Sample I: the two documents not recovered today are recovered, with an identity basis that
  cites document evidence rather than continuation, and no new split of the
  documents recovered today.
- OPEN documents: the hypotheses and their evidence are reported for the
  owner's reading, not scored.
- OBS-008 pairs and OBS-009 lines separated correctly on the labelled set.
- Wrapped "R/" items joined with no wrong joins.
- E1 coverage close to complete. If coverage is poor, the result is "pypdf
  is not enough", and the next question is a dependency decision (Q7), not
  more heuristics.

A negative result is also a result: if the identity signals do not recover
those two documents, the recommendation in section 7 changes and is
reported as such.

Two bundles from one hospital are not enough to judge hospital-agnostic
rules. The Phase 1 recommendation to add at least one bundle from another
hospital stands (INFERRED, OPEN on availability).

---

## 12. Open architecture questions

These are questions, not ADRs. Each names what would answer it.

| ID | Question | Answered by |
|---|---|---|
| Q1 | Coordinate convention for `bbox`: unit, origin, which page box, how rotation is applied, normalised or absolute. | E0/E1 results; must be settled before any `bbox` is persisted. |
| Q2 | How regions reference elements, and how two representations of one page coexist (identity, which one feeds Facts, no double counting). | E2/E3 results. DATA_MODEL 42 already sets the principle. |
| Q3 | Should a page assignment carry several signals, including conflicting ones, instead of one `basis`? | E5: how often signals conflict. Extends ADR-REQ-001 B; does not reopen it. |
| Q4 | Which logical documents do the medication/order printouts in Sample I represent? (Working hypothesis: seven, each with its own order number; OPEN.) | The logical document ground truth (owner / domain reading). |
| Q5 | Does a page ever hold two forms, or a document start mid-page? (ADR-01) | E3/E4 on the samples; still not observed. |
| Q6 | Should content continuing across a page break be linked (chunk relation) or stay split? (OBS-016) | Retrieval design; not a layout question. |
| Q7 | If pypdf positions are insufficient, which library, under which licence? | E1 coverage. |
| Q8 | Evidence for part of a line: a sub-element (segment) or character offsets into a line? | E2: whether segments are stable. |
| Q9 | Is a header/footer digest acceptable for comparison under the sensitivity policy? | ADR-08 (open). |

---

## 13. Whether a new ADR is actually required

**No, not now.**

Nothing in this investigation forces a choice between architectural
contracts today:

- Options B, C and D fill fields DATA_MODEL already defines (`bbox`,
  `style`, `HEADER`, `FOOTER`, `TABLE`, `TABLE_CELL`) and follow a principle
  it already states (section 42, new representations do not replace old ones).
- The boundary signals in section 10 extend the decided ADR-REQ-001 B
  (basis and evidence per page) without changing it, and add no score.
- The open points (Q1–Q9) need data from the experiment before a contract
  can be chosen; choosing now would be guessing.

**Expected later:** if the experiment supports D, one decision will be needed
**before production implementation**: the physical layout contract, covering
the coordinate convention (Q1) and region/representation identity (Q2),
possibly Q3 and Q8. That would be raised then as a single ARCHITECTURE
DECISION REQUIRED with the experiment's numbers as evidence. ADR-01 (Q5)
stays open as it is.

Work stops here and waits for architecture review.
