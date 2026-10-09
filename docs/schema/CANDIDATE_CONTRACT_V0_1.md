# Candidate Contract v0.1 — Physical Evidence Candidate & Document Structural Context

**Status:** PROPOSED — FOR REVIEW. Not approved. Documentation only.
**Date:** 2026-10-09
**Next step (not started):** `CONCEPT_TO_PERSISTENCE_MAPPING.md`

This contract is the first schema-design document. It turns the frozen architecture
into a conceptual contract. It adds no code, model, DDL, API, test, ground truth or
experiment result. Every JSON snippet is **illustrative only — not a production schema**.
All examples are synthetic.

Tags used below: **DECIDED** (already accepted in the repository), **PROPOSED** (this
contract proposes it, for review), **OPEN** (not decided; stays open).

---

## 1. Purpose and Scope

**Purpose.** Fix the conceptual contract for:

1. the Physical Evidence Candidate (Candidate);
2. Document Structural Context, held as a separate concept, `DocumentStructureNode`;
3. how a Candidate relates to the physical source and to document structure;
4. where the Candidate Layer stops and the Semantic Layer starts.

**Question the Candidate Layer answers:** *what information was found, in what form,
where in the document, and from which physical source.*

**In scope:** responsibilities, information groups, boundaries, ambiguity handling,
provenance principles, open questions.

**Out of scope:** see section 10.

## 2. Normative References and Terminology

### 2.1 References actually examined

| Document | Used for |
|---|---|
| `docs/DATA_MODEL.md` (11B to 11E, 2.8, 5A, 11, 14, 15, 41, 42, 51, Appendix C) | Candidate concept, provenance, immutability, Evidence terminology |
| `docs/architecture/EVIDENCE_CANDIDATE_PROPOSAL.md` | Candidate types, unresolved states, CONTINUES, headings as layout context, AD-C/D/E |
| `docs/architecture/ARCHITECTURAL_BOUNDARY_CLARIFICATIONS.md` | boundaries, NO_CANDIDATE_FOUND |
| `docs/architecture/DATA_MODEL_IMPACT_ANALYSIS.md` and `DATA_MODEL_MAPPING_PROPOSAL.md` | gaps between the model and the accepted concepts |
| `docs/architecture/ARCHITECTURE_FINAL_FREEZE_GATE.md` (R-1 to R-8) | binding architecture |
| `docs/architecture/PHASE_2_LAYOUT_INVESTIGATION.md` (E0 to E5, Q1 to Q9) | physical layout steps and open questions |
| `app/extraction/models.py` (read only) | actual terminology: `SourceFile`, `Page`, `DocumentElement` |

The "Phase 2 contract E0 to E5" is taken to be the E0 to E5 step list and the Q1 to Q9
open points in `PHASE_2_LAYOUT_INVESTIGATION.md`. No separate contract file was found.
Nothing in this contract changes it.

### 2.2 Terms

| Term | Definition | Status |
|---|---|---|
| **Physical Evidence** | The immutable source representation: SourceFile, Page, and what is printed on the page, down to a positioned run where one exists. A conceptual boundary, not one table or entity. | DECIDED (DM 42, 11B.10) |
| **Candidate** (Evidence Candidate) | A fragment of information formed from the physical representation, traceable to its source. Immutable. Carries no relevance, stance or verdict. | DECIDED (DM 11B) |
| **Candidate Type** | The *form* of the source information (for example label and value, table row). Not its clinical meaning and not its place in the document. | DECIDED for the notion; vocabulary OPEN |
| **DocumentStructureNode** (Structure Node) | A separate concept for the structure of a document: a heading, a section, a sub-section, and their hierarchy. | PROPOSED (owner instruction 2026-10-09) |
| **Structural Context** | The Structure Node (or nodes) a Candidate sits in, or an explicit "not classified". Reached by reference. | PROPOSED |
| **Provenance** | The traceable chain from a Candidate back to its physical source, with the method that produced it. | DECIDED (DM 11B.8) |
| **Semantic Layer** | The later layer that interprets: clinical concepts, administrative and billing meaning, relations between concepts, clinical and administrative representation. | DECIDED (DM 12, 2.8) |

Three things that must never be equated:

```text
heading text actually found   ≠   structural classification proposed by the system
                              ≠   semantic interpretation of the content
```

## 3. Candidate Conceptual Contract

A Candidate is a fragment of source information, formed from the physical
representation, and always traceable to it.

**Responsibilities of a Candidate (PROPOSED wording of DECIDED 11B):**

1. Preserve the fragment as read: its source text, and the parts that could be separated.
2. Say what *form* it has, and how far its internal structure could be read.
3. Keep a reference to every physical source that supports it.
4. Refer to its place in document structure by reference, without copying the context.
5. Carry the method that produced it (basis, tool and version), as provenance.

**A Candidate is not:** a confirmed clinical fact; a semantic interpretation;
Claim-Relevant Evidence (a conceptual projection, R-1); a Selection; a Verification
Verdict; a fraud or truth decision.

**Immutable.** No attribute such as `selected`, `relevant`, `stance` or
`verification_status` exists on a Candidate. A new extraction representation or
version yields new Candidates; it does not overwrite earlier ones (DM 11B.9).
Whether unselected Candidates are retained in production is OPEN (AD-C).

**Candidates are not exhaustive.** Not every run becomes a Candidate (DM 11B.2).
Uncertainty does not cause removal: a Candidate with unclear structure or context is
kept and the uncertainty is stated (section 8).

## 4. Candidate Information Groups

Conceptual groups only. They are not tables, not final attributes, and not all of them
are mandatory.

### 4.1 Identity

| Item | Content |
|---|---|
| Purpose | Name one Candidate unambiguously within an extraction. |
| Obligation | Required in some form. |
| Meaning boundary | An identifier names the Candidate; it carries no meaning, ordering or relevance. |
| OPEN | How the identifier is derived and its stability across re-extraction (the proposal derives it from source digest, extractor version and run refs; not decided). |

### 4.2 Representation

| Item | Content |
|---|---|
| Purpose | Record the form, the source text and the separated components. |
| Obligation | Candidate type and source text: required. Separated components: conditional, only when the structure was read. |
| Content | candidate type; source text exactly as extracted (SOURCE); components such as label and value, or cells; structural state (`RESOLVED` or `UNRESOLVED`, with reason and limitation). |
| Meaning boundary | Components are parts of the *source form*. A "label" is a printed label, not a canonical field. Any joined or normalised text is DERIVED and marked as such, and never replaces the source text. |
| OPEN | Final candidate-type vocabulary (5.3); final state and reason vocabulary (the repository's UNRESOLVED reasons are examples, DM 11B.6); representation of parts when a run holds several fields. |

### 4.3 Provenance

| Item | Content |
|---|---|
| Purpose | Make the Candidate traceable to every physical source behind it. |
| Obligation | Required to the deepest level available: page always; positioned run only where available. |
| Content | references to SourceFile, Page, and Physical Representation / Positioned Run (see 7); extraction basis and tool version. |
| Meaning boundary | Provenance says where and how a Candidate came from. It is not probability or confidence (none is defined). Provenance belongs to the Candidate and its physical sources. It does not belong to Claim-Relevant Evidence (R-1). |
| OPEN | Final relation of `PositionedRun` to `DocumentElement` (Phase 2 Q1/Q2); how a reference is written. |

### 4.4 Structural Context

| Item | Content |
|---|---|
| Purpose | Say which part of the document structure the Candidate sits in. |
| Obligation | Conditional. A reference to a Structure Node, or an explicit "not classified". |
| Meaning boundary | A reference, not copied text. A Structure Node name is context, never a clinical fact and never a Candidate type. |
| OPEN | Reference cardinality (one node or several); whether the reference may be empty or must say "not classified" explicitly (PROPOSED: explicit). |

### 4.5 Spatial Information

| Item | Content |
|---|---|
| Purpose | Record position where the source provides it. |
| Obligation | Conditional. Absent when the method gives no reliable coordinates. Never invented (DM 34). |
| Content | page; coordinates of the supporting run(s) or parts, when available. |
| Meaning boundary | Position is evidence of layout. Page order and page number are provenance only, never an identity or ordering rule. |
| OPEN | Coordinate convention: unit, origin, page box, rotation (Phase 2 Q1); sub-element or character-offset evidence for part of a line (Q8). |

### 4.6 Relationships

| Item | Content |
|---|---|
| Purpose | Express links to other Candidates or fragments. |
| Obligation | Conditional. |
| Content | continuation (`CONTINUES`, parent and child) as a relation, with its own basis and state ("proposed, not asserted"); other relations only if later accepted. |
| Meaning boundary | Continuation is a relation, not a Candidate type. A relation never rewrites either Candidate. |
| OPEN | Whether other relation kinds exist; relation state vocabulary; behaviour across pages. |

## 5. Candidate Types and Representation Boundaries

### 5.1 Three separate questions

| Question | Where it is answered | Example |
|---|---|---|
| What is the *physical or structural form* of this information? | Candidate type | label and value; table row; narrative |
| Where does it sit in the *document structure*? | Structure Node reference | under a heading printed as "ANAMNESIS" |
| What does it *mean*? | Semantic Layer (not here) | a chief complaint |

`ANAMNESIS`, `PEMERIKSAAN_FISIK`, `ASSESSMENT`, `TATALAKSANA`, `IDENTITAS` and
`BILLING` are **examples of structural context**. They are not candidate types and not
facts.

### 5.2 Types with a basis

| Type | Basis | Meaning | Not claimed |
|---|---|---|---|
| `LABEL_VALUE` | DECIDED initial type (DM 11B.4, proposal 3) | a label and a value that appear to belong together by shape | that the label has a meaning or the value is correct |
| `TABLE_ROW` | DECIDED initial type | one row of cells at distinct positions | that there is a table, or what the columns are |

Continuation is a **relation**, not a type (DM 11B.7).

### 5.3 Forms that still need a decision

| Form | Status | Note |
|---|---|---|
| Narrative or free text fragment | OPEN | The owner asks that the contract discuss narrative where it needs representing. The repository says free paragraphs are Physical Evidence until a claim need asks for them (proposal 3) and that DM 11B.4 holds two types. Whether narrative becomes a Candidate type, and its boundaries, is not decided here (Q-05). |
| Other source forms | OPEN | The list is an initial description, not a closed vocabulary (DM 11B.4). |

**Rule.** A Candidate is never forced into label and value when the source is narrative.
If a narrative fragment is represented, it is represented as what it is, not as a
label-value pair with an invented label. Until Q-05 is decided, narrative text remains
Physical Evidence.

## 6. Document Structural Context Contract

### 6.1 Concept

`DocumentStructureNode` is a concept separate from Candidate. A node describes a
piece of document structure: a heading, a section, a sub-section, and where it sits in
a hierarchy. Candidates reference nodes; a node does not contain Candidate content.

```text
DocumentStructureNode  1 ──── parent / child ──── 0..n  DocumentStructureNode
Candidate              n ──── references ───────── 0..n  DocumentStructureNode
```

(Cardinality is a proposal for discussion, not a decision; Q-04.)

### 6.2 What a node can describe

- a section title as printed;
- a section or sub-section;
- the parent and child hierarchy;
- which Candidates fall inside it, via the Candidate's reference.

### 6.3 Three kinds of information, kept apart (PROPOSED)

| Kind | Meaning | Example (synthetic) |
|---|---|---|
| Observed heading text | the heading text actually found in the source, with its source reference | `Anamnesis` |
| Proposed structural classification | the system's proposed reading of the section role | `ANAMNESIS` (a context label) |
| Semantic interpretation | what the content means | belongs to the Semantic Layer, never stored on a node |

The classification is a proposal with its own basis. It can be absent, wrong or
unvalidated, and it does not alter the observed text. Its vocabulary is OPEN (Q-03).

### 6.4 What a node is not

- not a Fact, not a clinical concept, not a Semantic Layer object;
- not a Candidate: headings and letterhead are not Candidates (DECIDED, proposal 3 and 8);
- not a requirement that every document has headings or follows one clinical template;
- not a logical Document: logical document identity is decided in Phase 2 E4/E5 from
  identity signals, and the relation between a node and a logical Document is OPEN (Q-06).

### 6.5 Unknown context

If no structure can be determined, the Candidate is kept and its context is explicitly
"not classified". A missing heading is not an error and not a reason to drop the
Candidate. "Not classified" is a statement about structure. It says nothing about the
document's content.

## 7. Provenance, Derived Representation, and Immutability

### 7.1 Chain (DECIDED principle, terminology to be confirmed)

```text
SourceFile → Page → Physical Representation / Positioned Run → Candidate
```

Actual terminology in the repository: `SourceFile`, `Page` and `DocumentElement`
(`app/extraction/models.py`). `DocumentElement.bbox` is `None` today, and positioned
runs exist only in throwaway E1 output. Whether a positioned run **is** a
`DocumentElement`, a separate representation, or something else is **OPEN** (Phase 2
Q1/Q2, DM 11B.8). This contract uses "Physical Representation / Positioned Run" and
does not decide that mapping. Where a positioned run is not available, the reference
stops at the Page.

### 7.2 Candidates built from several fragments

When a Candidate is made from several physical fragments (a wrapped value, a joined
continuation):

- the **form of the result** must be explainable (what the Candidate is);
- the **relation to every contributing source** must be explainable;
- no source reference may be dropped when fragments are combined;
- provenance is stored once, at the Candidate, not duplicated without a reason;
- a joined text is DERIVED and marked so; it never replaces the source text of any
  contributing fragment.

Whether a joined result is its own Candidate or a *view* over a parent and child is
OPEN (Q-07). The repository's current reading is the second: a logical view, not a
rewrite (proposal 6).

### 7.3 Immutability

- The original representation is never overwritten by a transformation (DM 42).
- A re-extraction or a change of representation is distinguishable from the earlier
  one. A different representation or version yields new Candidates (DM 11B.9).
- **OPEN:** persistence and versioning mechanism (identity across representations,
  which representation feeds later layers, no double counting; Phase 2 Q2).

## 8. Incomplete, Ambiguous, and Fragmented Cases

Rule: a Candidate is not discarded because interpretation or context is uncertain.
Uncertainty is stated, not closed by assumption.

| Case | Contract behaviour | Open |
|---|---|---|
| Structural context unknown | Candidate kept; context "not classified". | Representation of "not classified". |
| No heading available | Candidate kept; no node reference, or the nearest structure if one is observed. No heading is invented. | Whether any node may exist without printed heading text (Q-03). |
| Label and value cannot be separated with certainty | Candidate kept as `UNRESOLVED` with source text and source references; components absent. | Reason vocabulary. |
| One fragment holds several pieces of information | Kept as one Candidate (for example a single run with several `label : value` pairs), `UNRESOLVED`; no guessed split. | Whether later resolution produces new Candidates (DM 11B.6 says resolution creates a new state, not a rewrite). |
| Information continues across fragments or pages | Expressed as a `CONTINUES` relation, proposed, not asserted. | Behaviour across a page break. |
| Candidate composed of several sources | All sources referenced; joined text DERIVED. | Q-07. |
| Position or provenance incomplete | The reference stops at the deepest available level; coordinates absent, never invented. | Q1/Q2. |

## 9. Worked Examples

All examples are synthetic. They show what a Candidate holds and what it does not.
JSON is **illustrative only — not a production schema**; field names are placeholders.
No example contains a clinical fact, relevance, stance or status.

### 9.1 Medical summary with an anamnesis section

Printed page (synthetic):

```text
ANAMNESIS
Keluhan Utama : nyeri dada sejak 2 hari
Riwayat       : tidak ada
```

Structure and Candidates:

```json
// illustrative only — not a production schema
{
  "structure_node": { "node_id": "N1", "observed_heading_text": "ANAMNESIS",
    "proposed_classification": "ANAMNESIS", "parent": null, "source_ref": "p1:run0" },
  "candidates": [
    { "candidate_id": "C1", "type": "LABEL_VALUE", "structural_state": "RESOLVED",
      "source_text": "Keluhan Utama : nyeri dada sejak 2 hari",
      "parts": { "label": "Keluhan Utama", "value": "nyeri dada sejak 2 hari" },
      "provenance": ["p1:run1", "p1:run2"], "structure_ref": ["N1"] },
    { "candidate_id": "C2", "type": "LABEL_VALUE", "structural_state": "RESOLVED",
      "source_text": "Riwayat : tidak ada",
      "parts": { "label": "Riwayat", "value": "tidak ada" },
      "provenance": ["p1:run3", "p1:run4"], "structure_ref": ["N1"] }
  ]
}
```

`C1` sits under an anamnesis section, but it is **not** a chief complaint fact. That
conclusion belongs to the Semantic Layer. The heading line is a node, not a Candidate.

### 9.2 Laboratory result as a table

```text
Pemeriksaan   Hasil   Nilai Rujukan
Zat-X         9.9     5 - 10
Zat-Y         1.1     1 - 2
```

Each data row is a `TABLE_ROW` Candidate with its cells and source references. The
column names are not assumed unless a header is associated; without it the state is
`UNRESOLVED` (reason: no header association), consistent with DM 11B.6. The Candidate
holds no "normal" or "abnormal" reading.

### 9.3 Billing or administrative document

```text
RINCIAN BIAYA
Tindakan A    1    100.000
Tindakan B    2     50.000
```

The heading is a node with proposed classification `BILLING`. Rows are `TABLE_ROW`
Candidates under that node. The numbers are source text. Which number is a unit price
or a total is Semantic Layer interpretation, and is not stated in the Candidate.

### 9.4 Fragment with no recognisable heading

```text
Pasien dalam keadaan baik, kontrol 1 minggu lagi.
```

No heading is found. The fragment, if it is represented at all (Q-05), has
`structure_ref` empty with context "not classified". It is kept; it is not forced into
label and value and it gets no invented section.

### 9.5 Candidate composed of several source fragments

```text
Diagnosa : Penyakit-X dengan komplikasi
           yang cukup lama
```

```json
// illustrative only — not a production schema
{ "candidate_id": "C9", "type": "LABEL_VALUE", "structural_state": "RESOLVED",
  "source_text": "Diagnosa : Penyakit-X dengan komplikasi",
  "relations": [{ "kind": "CONTINUES", "child": "C10", "relation_state": "CANDIDATE" }],
  "provenance": ["p3:run5", "p3:run6"] }
{ "candidate_id": "C10", "source_text": "yang cukup lama",
  "relations": [{ "kind": "CONTINUES_FROM", "parent": "C9" }], "provenance": ["p3:run7"] }
```

A logical view joins the two texts. That joined text is DERIVED, both contributing
source references remain reachable, and neither source text is changed.

## 10. Explicit Non-Goals

This contract does **not** define: DDL or final database tables; production JSON
schema; API implementation; extraction models or algorithms; OCR, LLM, embedding or ML
models; the Semantic Layer; Evidence Need, Need Assessment, Selection or Verification
Verdict; Claim-Relevant Evidence as an entity (it stays a conceptual projection, R-1).
It does not create a logical Document identification method (Phase 2 E4/E5). It does
not rename `Evidence` (DM 15).

## 11. Decisions and Open Questions

| ID | Question or decision | Status | Basis | Impact on persistence design |
|---|---|---|---|---|
| Q-01 | A Candidate is immutable and has no relevance, stance, selection or verdict attribute. | DECIDED | R-6; DM 11B.9 | Candidate store is append-only; no later-layer flags on it. |
| Q-02 | Structural context is a separate concept (`DocumentStructureNode`) referenced by Candidates, not copied onto them. | PROPOSED | owner instruction 2026-10-09; supersedes the optional `layout_context` pointer in proposal 8 if accepted | Needs a separate structure concept and a reference. |
| Q-03 | Vocabulary and validation of proposed structural classification (`ANAMNESIS`, `BILLING`, ...); whether a node may exist without printed heading text. | OPEN | proposal 8 (heading detection gave false positives) | Classification stored as a labelled proposal with basis, not as a closed enum. |
| Q-04 | Cardinality of Candidate to node reference; whether "not classified" is explicit. | OPEN (PROPOSED: explicit) | this contract 4.4 | Nullable versus explicit-state reference. |
| Q-05 | Is narrative / free text a Candidate type? | OPEN | proposal 3 says free paragraphs are Physical Evidence; owner asks narrative be discussed | Whether the type set is closed; conflicts with "not exhaustive". |
| Q-06 | Relation between Structure Node hierarchy and logical Document identity (E4/E5). | OPEN | Phase 2 E4/E5 | Whether a node belongs to a Document, a Page range or neither. |
| Q-07 | A joined (multi-fragment) result: own Candidate, or view over parent and child. | OPEN | proposal 6; DM 11B.7 | One-versus-two persisted shapes for a wrapped value. |
| Q-08 | Final relation of `PositionedRun` to `DocumentElement`. | OPEN | Phase 2 Q2; DM 11B.8 | Foreign target of the provenance reference. |
| Q-09 | Coordinate convention (unit, origin, page box, rotation). | OPEN | Phase 2 Q1 | Whether `bbox` can be persisted. |
| Q-10 | Candidate identifier derivation and stability across re-extraction. | OPEN | proposal 4 | Key design. |
| Q-11 | Persistence and versioning of representations; retention of unselected Candidates. | OPEN | DM 11B.9; AD-C; Phase 2 Q2 | Retention and data-sensitivity policy. |
| Q-12 | Final candidate-type, structural-state and unresolved-reason vocabularies. | OPEN | DM 11B.4 to 11B.6 | Enum versus open vocabulary. |
| Q-13 | Candidate must not require every group of attributes: spatial and component data are conditional. | PROPOSED | this contract section 4 | Nullable / absent attributes allowed. |
| Q-14 | Provenance belongs to the Candidate and its sources, not to Claim-Relevant Evidence. | DECIDED | R-1; DM 11B.8, 2.8 | No provenance copy on any projection. |

**Inconsistencies noted, not resolved:**

- `EVIDENCE_CANDIDATE_PROPOSAL.md` 8 stores heading context as an optional `layout_context` pointer to a run (page-scoped, "does not extend across pages"). The owner now asks for a hierarchical, separate node concept. These differ in scope; Q-02 and Q-06.
- The same proposal says free paragraphs are not Candidates; the owner asks narrative to be discussed. Q-05.

## 12. Acceptance Criteria

The contract is fit for review if each holds:

- [ ] Candidate and Structure Node have separate, clear responsibilities (sections 3 and 6).
- [ ] Candidate type is not mixed with structural context or semantic meaning (5.1).
- [ ] Source provenance is preserved, including for multi-fragment Candidates (7).
- [ ] Unknown context does not cause a Candidate to be lost (6.5, 8).
- [ ] JSON examples are marked illustrative and are not treated as a final schema (9).
- [ ] The boundary with the Semantic Layer is explicit (2.2, 5.1, 9).
- [ ] No conflict with R-1 to R-8 or the Phase 2 E0 to E5 steps (see consistency check below).

### Consistency check (this contract against the frozen architecture)

| Check | Result |
|---|---|
| Candidate immutable; no `selected`, `relevant`, `stance`, `verification_status` attribute | Holds (3, Q-01) |
| Structure Node does not take over Semantic Layer responsibility | Holds (6.3, 6.4) |
| `ANAMNESIS` and `BILLING` are context examples, not types or facts | Holds (5.1, 9) |
| Narrative is not forced into label-value | Holds (5.3) |
| Provenance not claimed by Claim-Relevant Evidence | Holds (4.3, Q-14) |
| R-1 to R-8 unchanged | Holds; none re-opened |
| No conflict with Phase 2 E0 to E5 | Holds; E4/E5 logical-document identification is not touched (Q-06 open) |
| Mapping document not created | Holds |
