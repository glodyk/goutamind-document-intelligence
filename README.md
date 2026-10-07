# GOUTAMIND Document Intelligence

Turns heterogeneous healthcare claim document bundles (one PDF holding SEP,
INA-CBG output, resume, CPPT, lab, billing, ...) into a canonical,
evidence-linked representation.

> "Do not normalize the hospital layout. Normalize the meaning of the information."

The architecture baseline lives in [`docs/`](docs/):
[`DOCUMENT_TAXONOMY.md`](docs/DOCUMENT_TAXONOMY.md),
[`DATA_MODEL.md`](docs/DATA_MODEL.md) and
[`change_report_r1.md`](docs/change_report_r1.md).

## Status: first vertical slice

The code currently implements the first runnable slice of the pipeline:

```text
PDF -> SourceFile -> Pages -> DocumentElements      (raw / physical layer)
          Documents -> Sections -> Chunks           (semantic layer, references pages)
          Evidence (first-class, points at page + element)
          Facts / Events (minimal, deterministic, SOURCE_FACT only)
```

Canonical claim, timeline, narrative and intelligence are not built yet.
What the slice does, and the rules it follows, is described in
[`pipeline/README.md`](pipeline/README.md). What running it on real bundles
taught us is in [`docs/findings/SLICE_01_FINDINGS.md`](docs/findings/SLICE_01_FINDINGS.md).

## Quick start

Requires Python 3.12+.

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"

# run the tests
python -m pytest

# process a PDF (outputs go to outputs/, which is git-ignored)
python -m pipeline.run examples/golden_claim/synthetic_claim_bundle.pdf
```

The run writes `<name>.bundle.json` (all layers) and `<name>.inspection.txt`
(human-readable check of documents, evidence and facts). See
[`examples/golden_claim/`](examples/golden_claim/) for the committed synthetic
example.

## Private claim PDFs

Real claim bundles contain patient data and must never be committed.

- Put them in `samples_private/` (git-ignored), or anywhere outside the repo.
- `*.pdf` is git-ignored everywhere except the synthetic golden example.
- `python -m pipeline.run samples_private/<file>.pdf` keeps all output in `outputs/`.
- `python -m pytest tests/integration/test_private_samples.py` runs structural
  checks on every PDF in `samples_private/` (or in `$GOUTAMIND_PRIVATE_SAMPLES`)
  and is skipped when none are present.
- Use `--no-source-text` when an inspection report has to be shown to
  someone else; it drops copied source text and document titles.

## Layout

```text
app/
  vocabulary.py        enums mirroring DATA_MODEL vocabularies
  temporal.py          Temporal Value parsing (precision never increased)
  ids.py               opaque ids, content-based SourceFile id
  bundle.py            ClaimDocumentBundle (processing boundary)
  extraction/          PDF reader (raw layer) and minimal fact/event extraction
  document/            Document / Section / Chunk, segmentation and rules
  evidence/            Evidence, Fact, Event and the evidence registry
  timeline/, intelligence/   not implemented yet
pipeline/              orchestration, CLI, JSON and inspection output
tests/                 unit, integration, synthetic PDF fixtures
examples/golden_claim/ synthetic bundle + its expected output
scripts/               regenerate the golden example
```
