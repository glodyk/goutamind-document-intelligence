# Project Identity — GOUTAMIND Document Intelligence

**Status:** Active architecture baseline  
**Repository:** `goutamind-document-intelligence`  
**Brand:** GOUTAMIND Healthcare Data × AI × Automation  
**Maintainer:** Dody Goutama

## 1. Short description

> Evidence-driven document intelligence for heterogeneous healthcare claim documents, turning PDF bundles into structured, traceable clinical information.

## 2. Tagline

> From healthcare documents to evidence-linked claim intelligence.

## 3. Purpose

GOUTAMIND Document Intelligence exists to provide a reliable semantic and evidence layer between heterogeneous healthcare claim documents and downstream claim-review or claim-intelligence systems.

The project does not assume that a PDF is a single document, that document order represents clinical order, or that hospital layouts can be standardized safely. Instead, it preserves the physical source while progressively normalizing the meaning of the information.

## 4. Primary objective

Build a reliable, evidence-driven foundation for understanding healthcare claim-document bundles while preserving source provenance, temporal fidelity, uncertainty, and semantic distinctions.

## 5. Target users

- Healthcare claim-review and verification teams
- Healthcare data and analytics teams
- Hospital financing and claim-management teams
- Developers building healthcare document-processing systems
- Researchers working on evidence-driven clinical/claim intelligence

## 6. Primary input

Heterogeneous healthcare claim-document bundles, especially PDFs containing combinations of:

- administrative documents;
- clinical records;
- diagnostic reports;
- medication and treatment records;
- billing and financial records;
- claim/coding documents;
- supporting documents from other facilities.

## 7. Primary output

A structured representation that preserves:

- logical document identity;
- sections and semantic chunks;
- source facts and events;
- evidence and physical provenance;
- temporal precision;
- explicit missingness;
- source disagreement;
- extraction status.

## 8. Core semantic contract

```text
Claim Document Bundle
        ↓
Document
        ↓
Section
        ↓
Chunk
        ↓
Fact / Event
        ↓
Evidence
```

The downstream target is:

```text
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

## 9. Relationship to other GOUTAMIND systems

The intended ecosystem is:

```text
GOUTAMIND
│
├── Document Intelligence
│       └── this repository
│
├── DESKON
│       └── claim review / verification
│
└── CLAIRE
        └── claim intelligence / risk-based assessment
```

This is an architectural target. Integration with DESKON and CLAIRE is not yet implemented here.

## 10. Design principles

1. **Evidence first.** Structured information must remain traceable to its source.
2. **Meaning over layout.** Hospital layouts are inputs to document understanding, not the canonical semantic model.
3. **Source is not interpretation.** Source, derived, inferred, and model-generated information remain distinct.
4. **Physical order is not clinical order.** Timeline reconstruction must use evidence and temporal semantics.
5. **Never invent precision.** Temporal precision may be preserved, not silently increased.
6. **Missingness is explicit.** Absence of extracted evidence is not automatically absence of the clinical fact.
7. **Disagreement is preserved.** Conflicting source values remain available for later resolution.
8. **Human-in-the-loop.** The system supports reviewers; it does not replace their judgment.
9. **Privacy by design.** Real claim documents remain outside the public repository and should be handled within an appropriate processing boundary.

## 11. Non-goals

At the current stage, the project is not:

- an autonomous clinical decision system;
- a fraud verdict engine;
- a generic OCR product;
- an LLM-first extraction pipeline;
- a vector database or RAG product;
- a hospital-specific PDF template collection;
- a replacement for claim reviewers;
- a production deployment platform.

## 12. Current maturity

**Early Architecture / First Vertical Slice**

The repository currently proves the physical-to-semantic document understanding foundation. Architecture decisions are intentionally driven by representative PDF stress tests and regression evidence before downstream canonicalization is expanded.

## 13. Discovery keywords / GitHub topics

Recommended repository topics:

```text
healthcare
healthcare-data
document-intelligence
clinical-data
medical-documents
healthcare-claims
claims-processing
pdf-extraction
evidence-provenance
python
```

These are discovery labels only; they do not imply capabilities that are not implemented.

## 14. One-sentence positioning

> **GOUTAMIND Document Intelligence is an evidence-driven foundation that turns heterogeneous healthcare claim-document bundles into structured, traceable information for downstream review and claim intelligence.**
