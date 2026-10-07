# Pipeline: vertical slice 1

`python -m pipeline.run <pdf> [--out DIR] [--numeric-date-order DMY|MDY] [--no-source-text]`

`pipeline.run.process_pdf()` runs these steps. Each step only adds a layer;
nothing overwrites an earlier one (DATA_MODEL 42).

| Step | Module | Produces |
|---|---|---|
| 1. Read PDF | `app/extraction/pdf_reader.py` | `SourceFile`, `Page`, `DocumentElement` |
| 2. Segment | `app/document/segmentation.py` | `Document` with `page_refs[]` |
| 3. Structure | `app/document/structure.py` | `Section`, `Chunk` |
| 4. Dates | `app/document/dates.py` | `Document.dates[]` (Temporal Values with `date_role`) |
| 5. Facts / Events | `app/extraction/facts.py` | `Fact`, `Event`, plus their `Evidence` |

## 1. Physical layer

- Native text only (pypdf). No OCR, so an image-only page keeps
  `text_status = NOT_AVAILABLE` and is still a Page.
- `page_kind`: `CONTENT` (text or images), `BLANK` (neither), `UNKNOWN`
  (extraction failed). `SEPARATOR` is never assigned: a blank page and a
  separator page look the same to the reader.
- `modality`: `DIGITAL_TEXT` when a text layer exists, otherwise `UNKNOWN`
  (a scan and a photo cannot be told apart without image analysis).
- `extraction_method`: `NATIVE_TEXT` when text was read, otherwise `UNKNOWN`.
  `NO_TEXT` is not used because it asserts the content *is* non-textual,
  which the reader cannot know.
- Each non-empty text line becomes a `TEXT` element; each image XObject an
  `IMAGE` element. `bbox` is not provided.
- `source_file_id` is derived from the SHA-256 of the bytes, so the same file
  always gets the same id. Only the file name is stored as `source_reference`.
- An unreadable or password-protected file gives `ingestion_status = FAILED`
  with an error message; the run still writes its output.

## 2. Segmentation (pages -> logical documents)

A Document *references* pages; it does not contain them. For each page, in
order (first rule that applies wins):

1. `BLANK` page: belongs to no document and ends the current one.
2. Image-only or failed page: its own `UNKNOWN` document.
3. Printed counter "Halaman k of n" / "Halaman k" with k > 1: continues the
   current document. This outranks a title, because a counter belongs to the
   page's own document (a resume's last page can start with "RESEP").
4. Title in the page's top lines: starts a new document of that type.
5. Counter with k = 1: starts a new document (splits two lab reports in a row).
6. Marker labels (for example both "No.SEP" and "Tgl.SEP"): starts a new
   document unless the current one already has that type.
7. Otherwise: continues the current document, or starts an `UNKNOWN` one.

Rules are data in `app/document/rules.py`: generic Indonesian/English form
titles and labels, not a hospital layout. Short generic words such as
"RADIOLOGI" count as a title only on a page's first line, because they also
appear as headings inside bills. Each document records why each page was
attached (`page_bases`) and keeps the title or marker line as evidence.

`document_type` gets `UNKNOWN` when nothing matched and `OTHER` when a
title was recognised but has no type in DATA_MODEL 7 (for example triage).
`document_role` follows the examples in DOCUMENT_TAXONOMY 9; types without
an example there are marked "assumed" in the rules file, and `OTHER`,
`UNKNOWN` and `REFERRAL` get no role. `classification_confidence`,
`document_date`, `source_facility`, `completeness_status` and
`duplicate_of` are left empty/`UNKNOWN`: nothing in this slice can state
them reliably.

## 3. Sections and chunks

- Short heading lines (DIAGNOSA, PROSEDUR, TERAPI, PEMERIKSAAN FISIK,
  S/ O/ A/ P/, TINDAK LANJUT, ...) start a section. Text before the first
  heading is a `GENERIC` section.
- Financial documents get one `BILLING_DETAIL` section, because their
  headings are billing categories.
- A chunk is a section's lines on one page (split after 12 lines). Chunks
  never cross a page break, so each has one `page_number`, as in
  DATA_MODEL 10, and lists its `element_refs`.

## 4. Dates

Every date on a document's lines is parsed into a Temporal Value
(`app/temporal.py`): the raw text is kept, precision is never increased
("September 2025" stays `MONTH`), and numeric dates where both parts are
<= 12 stay `UNKNOWN` unless `--numeric-date-order` is given. The `date_role`
comes only from a label just before the date on the same line; otherwise it is
`UNKNOWN`. Birth dates are recognised and skipped (personal data, ADR-08).

## 5. Facts and events

Deterministic and deliberately narrow (`app/extraction/facts.py`):

- DIAGNOSIS / PROCEDURE: a code after a "Diagnosa ... :" / "Prosedur ... :"
  label, coded lines that directly follow such a label, and coded lines inside
  a DIAGNOSIS / PROCEDURE section. The printed label goes to `source_label`
  and is not mapped to `diagnosis_role` or `diagnosis_context` (ADR-04).
  `coding_system` is set only when the source prints it. A printed "-" gives
  `availability_status = NOT_DOCUMENTED`.
- MEDICATION: whole "R/ ..." lines, unparsed (`medication_context` and
  `item_category` are ADR-06).
- Events: admission, discharge and arrival dates on clinical documents only.
  Claim anchors (SEP, INA-CBG, billing, service recap) never produce events.
  `care_pathway` and `care_stage` stay `UNKNOWN`.

Every Fact and Event is a `SOURCE_FACT` with one Evidence item pointing at the
exact line (`element_id`), page and source file. The same value found in two
documents gives two Facts; merging is ADR-09. Evidence also exists without any
Fact (document boundaries, image pages), so Evidence never implies a Fact.

## Output

- `<name>.bundle.json`: every layer, plus empty placeholders for the layers
  not built yet (`canonical_claim`, `timeline`, ...). Not a JSON Schema.
- `<name>.inspection.txt`: pages, documents, evidence, facts and events, with
  the chain Fact -> Evidence -> page -> source file.
