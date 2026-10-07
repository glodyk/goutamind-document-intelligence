# GOUTAMIND Document Intelligence

> **Evidence-driven document intelligence for heterogeneous healthcare claim documents.**
>
> **From healthcare documents to evidence-linked claim intelligence.**

## What is this project?

**GOUTAMIND Document Intelligence** is a document intelligence foundation for understanding heterogeneous healthcare claim-document bundles.

It is designed for claim packages in which a single PDF may contain multiple logical documents—such as SEP, INA-CBG output, medical resume, assessment, CPPT, laboratory, radiology, prescription, billing, and supporting documents—and where document layouts vary across hospitals.

The project transforms the **physical document representation** into a structured, traceable representation of:

`Document Bundle → Document → Section → Chunk → Fact / Event → Evidence`

The central design principle is:

> **Do not normalize the hospital layout. Normalize the meaning of the information.**

The system preserves the relationship between extracted information and its source so that downstream users can understand **what was found, where it came from, and how certain or precise the representation is**.

## Why does it exist?

Healthcare claim documents are heterogeneous in both structure and meaning. A PDF is not necessarily one logical document, page order is not clinical event order, and the same clinical or administrative information may appear in several sources with different precision or even conflicting values.

A useful intelligence layer therefore needs to:
- understand logical documents inside physical PDF bundles;
- preserve source and page context;
- distinguish facts from evidence;
- preserve temporal precision instead of inventing precision;
- represent missingness explicitly;
- keep source-derived information distinguishable from derived, inferred, and model-generated information;
- provide a stable semantic foundation that is independent of hospital-specific layouts.

## Primary goal

Build a **reliable, evidence-driven foundation for healthcare claim document understanding** without losing the relationship between structured information and its original source.

## Secondary goals

1. Identify logical documents within heterogeneous PDF bundles.
2. Represent sections and semantically coherent chunks.
3. Extract structured facts and clinical events.
4. Preserve evidence and provenance down to the physical source.
5. Reconstruct information without confusing document order with clinical event order.
6. Preserve temporal precision and ambiguity.
7. Represent missing or unavailable information explicitly.
8. Preserve conflicting source information rather than silently choosing a winner.
9. Prepare structured information for downstream claim review and intelligence.
10. Support human review and auditability rather than replace human judgment.

## Architecture

```text
PDF / Document Bundle
        ↓
Document Understanding
        ↓
Canonical Clinical Claim
        ↓
Evidence
        ↓
Clinical Timeline
        ↓
Narrative
        ↓
Claim Intelligence
```

The current repository implements only the **document-understanding foundation**. Canonical claim, clinical timeline, narrative, and claim intelligence are planned downstream layers.

### Relationship to GOUTAMIND, DESKON, and CLAIRE

```text
                         GOUTAMIND
                             │
             ┌───────────────┴───────────────┐
             │                               │
     Document Intelligence            Claim Intelligence
             │                               │
             ▼                               ▼
   This repository                      CLAIRE
             │
             ▼
          DESKON
 Claim Review / Verification
```

This diagram describes the **target architectural relationship**, not the current implementation. DESKON and CLAIRE integrations are not implemented in this repository yet.

## What is implemented now?

The current project is an **early architecture / first vertical slice**, not a production-ready claim intelligence system.

Implemented:
- PDF ingestion and physical source representation;
- `SourceFile`, `Page`, and `DocumentElement`;
- logical `Document`, `Section`, and `Chunk`;
- evidence as a first-class representation;
- deterministic source facts and events;
- page-to-document assignment provenance;
- explicit `UNKNOWN` document classification;
- temporal precision preservation;
- explicit extraction status;
- human-readable page-assignment diagnostics;
- synthetic golden-claim fixture and regression tests.

The current slice intentionally does **not** implement OCR, LLM extraction, embeddings, RAG, database/API/UI, canonical claim generation, timeline generation, narrative generation, fraud/risk scoring, or autonomous claim decisions.

## Core design principles

### 1. Evidence is first-class

A fact is not enough. The system should be able to trace it back to its source document, page, and extracted element.

### 2. Source is not the same as interpretation

The architecture distinguishes:
- `SOURCE_FACT`
- `DERIVED_FACT`
- `INFERRED_FACT`
- `MODEL_OUTPUT`

A model-generated conclusion must never silently become a source fact.

### 3. Document order is not clinical order

The order of pages in a PDF is a physical property. Clinical events must be reconstructed from their temporal and semantic evidence.

### 4. Never invent precision

If a source provides only a month, the representation remains month-level. If a date is ambiguous, it remains ambiguous.

### 5. Missingness is meaningful

`NOT_FOUND`, `NOT_DOCUMENTED`, `NOT_APPLICABLE`, `EXPLICITLY_NEGATED`, and `UNKNOWN` are not interchangeable.

### 6. Preserve disagreement

When sources disagree, the system should preserve the competing source facts and evidence rather than silently overwrite one with another.

### 7. Hospital-specific layouts stay upstream

Hospital-specific extraction rules may be necessary at the document-understanding boundary. They should not leak into the canonical semantic model unless there is a genuine domain reason.

### 8. Human-in-the-loop

The project is intended to strengthen claim review and verification. It is not designed to replace clinical, coding, or claim-review judgment.

## Non-goals

This repository is not intended to:
- make autonomous clinical decisions;
- replace claim verifiers or clinical reviewers;
- determine fraud by itself;
- silently infer undocumented clinical facts;
- force every hospital into one PDF template;
- use an LLM as the source of truth;
- treat embeddings or retrieval as the primary extraction mechanism;
- become a hospital-specific document template collection.

## Current status

**Status: Early Architecture / First Vertical Slice**

The architecture is being developed through evidence-driven stress testing against representative healthcare claim-document bundles.

The project follows a deliberate loop:

```text
Observed problem
      ↓
Explicit architecture decision
      ↓
Minimal implementation
      ↓
Regression test
      ↓
Real-PDF re-run
      ↓
New evidence
      ↓
Next architecture decision
```

Current architecture decisions and unresolved questions are documented in [`docs/DATA_MODEL.md`](docs/DATA_MODEL.md) and [`docs/findings/SLICE_01_FINDINGS.md`](docs/findings/SLICE_01_FINDINGS.md).

## Quick start

Requires Python 3.12+.

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"

python -m pytest

python -m pipeline.run examples/golden_claim/synthetic_claim_bundle.pdf
```

The run writes a JSON bundle, a human-readable inspection report, and a page-assignment diagnostic to `outputs/` (git-ignored).

## Private healthcare claim documents

Real claim bundles can contain sensitive patient information and must never be committed to the repository.

Private samples should remain outside Git tracking, for example in `samples_private/`. Use `--no-source-text` when an inspection report must be shared for review.

The committed golden example uses synthetic data.

## Documentation

- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — architecture overview.
- [`docs/DOCUMENT_TAXONOMY.md`](docs/DOCUMENT_TAXONOMY.md) — document and semantic taxonomy.
- [`docs/DATA_MODEL.md`](docs/DATA_MODEL.md) — conceptual data model and architecture decisions.
- [`docs/EVIDENCE_LINEAGE.md`](docs/EVIDENCE_LINEAGE.md) — evidence lineage.
- [`docs/ROADMAP.md`](docs/ROADMAP.md) — project roadmap.
- [`docs/findings/SLICE_01_FINDINGS.md`](docs/findings/SLICE_01_FINDINGS.md) — findings from the first vertical slice and real-PDF stress testing.

## Project identity

The formal project identity specification is documented in [`docs/PROJECT_IDENTITY.md`](docs/PROJECT_IDENTITY.md).

| Attribute | Definition |
|---|---|
| Project | GOUTAMIND Document Intelligence |
| Domain | Healthcare document intelligence |
| Primary input | Heterogeneous healthcare claim-document bundles |
| Primary output | Structured, evidence-linked document information |
| Core concern | Traceability, provenance, temporal fidelity, and semantic consistency |
| Primary users | Claim-review, verification, analytics, and healthcare data teams |
| Current stage | Early Architecture / First Vertical Slice |
| Brand | GOUTAMIND Healthcare Data × AI × Automation |
| Future downstream systems | DESKON and CLAIRE |
| Primary language | Python |

## License

See [`LICENSE`](LICENSE).

## Maintainer

Maintained by **Dody Goutama / GOUTAMIND**.