# GOUTAMIND DOCUMENT TAXONOMY — ARCHITECTURE CONTEXT

**Version:** 0.1, revision r1 (proposed)
**Status:** Draft / Architecture Baseline, pending owner review
**Related Document:** `docs/DATA_MODEL.md`

> **Catatan revisi r1.** Revisi ini bersifat aditif. Tidak ada konsep,
> prinsip, atau nama yang dihapus atau diubah. Tambahan ditandai
> `[r1]`. Bagian baru: 3A (lapisan wadah fisik), catatan pada bagian 8,
> 26 dan 27, 25A (status resolusi hasil stress test), dan 32 (catatan
> konsistensi). Keputusan domain yang belum diambil ditandai
> **Architecture Decision Required (ADR)** dan dirinci di
> `docs/DATA_MODEL.md` Appendix B.

## 1. Latar Belakang

GOUTAMIND Document Intelligence adalah engine yang dirancang untuk
memahami dokumen klaim pelayanan kesehatan yang berasal dari berbagai
rumah sakit.

Tujuan awalnya bukan langsung melakukan fraud detection atau membuat
model machine learning.

Tujuan pertama adalah:

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

Dengan kata lain, kita ingin membangun fondasi Document Intelligence
yang nantinya dapat digunakan oleh DESKON dan kemudian CLAIRE.

---

# 2. Masalah Utama yang Ingin Diselesaikan

Rumah sakit tidak menggunakan format dokumen yang sama.

Perbedaan dapat terjadi pada:

- nama dokumen;
- layout;
- urutan halaman;
- urutan dokumen;
- section;
- istilah;
- format tabel;
- dokumen yang digabung;
- dokumen yang dipisah;
- PDF digital;
- PDF hasil scan;
- foto dokumen;
- tulisan tangan;
- dokumen dari fasilitas kesehatan lain.

Karena itu kita tidak ingin membuat:

Hospital A Schema
Hospital B Schema
Hospital C Schema

atau:

PDF Template A
PDF Template B
PDF Template C

Prinsip utama yang kita sepakati adalah:

"Do not normalize the hospital layout.
 Normalize the meaning of the information."

Dalam Bahasa Indonesia:

"Kita tidak menormalisasi rumah sakitnya.
Kita menormalisasi makna informasinya."

---

# 3. Insight Penting: PDF Bukan Dokumen

Salah satu insight paling penting dari percakapan kita:

PDF adalah physical container.

PDF tidak selalu sama dengan satu logical document.

Satu PDF dapat berisi:

- SEP;
- INA-CBG;
- resume medis;
- assessment;
- CPPT;
- laboratorium;
- radiologi;
- resep;
- billing;
- dokumen rujukan;
- dokumen supporting.

Sebaliknya, satu logical document dapat:

- terdiri dari banyak halaman;
- terpisah;
- muncul tidak berurutan;
- bercampur dengan dokumen lain.

Karena itu kita memperkenalkan konsep:

CLAIM DOCUMENT BUNDLE

sebagai unit konseptual utama.

---

# 3A. Lapisan Wadah Fisik `[r1]`

Bagian 3 menyatakan bahwa PDF adalah physical container. Agar
pernyataan itu dapat dipakai, wadah fisik perlu istilah sendiri yang
terpisah dari hierarki semantik (bagian 7).

Istilah konseptual:

SOURCE FILE
= wadah fisik yang di-ingest (misalnya satu PDF).

PAGE
= satu halaman fisik dari source file.

DOCUMENT ELEMENT
= elemen fisik hasil ekstraksi (teks, tabel, gambar, dst.).

Ketiganya berada di lapisan Raw Document Representation. Mereka
BUKAN bagian dari hierarki semantik
Claim Document Bundle → Document → Section → Chunk → Fact / Event.
Sebuah Document merujuk ke Page; Document tidak "berisi" Page.

Hal yang sudah teramati pada dua PDF contoh (bagian 5, 25):

- satu PDF memuat banyak logical document;
- halaman suatu document bisa tidak berurutan;
- ada halaman kosong atau halaman pemisah yang bukan bagian dari
  document mana pun;
- ada halaman berupa gambar/foto tanpa lapisan teks;
- ada isi yang berulang (duplikat).

Rincian representasi data ada di `DATA_MODEL.md` bagian 5A.

ARCHITECTURE DECISION REQUIRED (ADR-01): apakah satu Page boleh
menjadi bagian dari lebih dari satu Document, dan apakah Document boleh
berawal/berakhir di tengah Page. Belum diputuskan.

---

# 4. Claim Document Bundle

Claim Document Bundle adalah kumpulan dokumen yang berkaitan dengan
satu claim atau service episode.

Contoh:

Claim Document Bundle
│
├── SEP
├── INA-CBG Output
├── Medical Resume
├── Assessment
├── CPPT
├── Laboratory
├── Radiology
├── Prescription
├── Billing
└── Supporting Documents

Bundle tidak harus memiliki komposisi yang sama untuk setiap rumah
sakit atau setiap claim.

Bundle juga dapat mengandung dokumen dari fasilitas kesehatan lain.

Contoh:

Primary Claim Facility
    RSUD Gambiran

Supporting Document
    RSIA Melinda

Karena itu source facility harus dipertahankan.

---

# 5. Dua PDF yang Digunakan sebagai Stress Test

Kita sengaja menggunakan dua PDF nyata sebagai conceptual test.

CASE A:
PDF IGD sekitar 18 halaman.

Strukturnya antara lain:

- SEP
- INA-CBG
- Medical Resume
- Assessment
- Prescription
- Billing
- CPPT
- Triage
- supporting clinical information

CASE B:
PDF Rawat Inap RSUD Gambiran sekitar 38 halaman.

Berisi antara lain:

- INA-CBG
- SEP
- discharge summary
- inpatient admission
- laboratory
- radiology
- ECG
- CPPT
- prescription
- billing
- detailed billing
- supporting documents
- dokumen dari fasilitas kesehatan lain

Hasil conceptual test:

Kedua PDF dapat dipetakan ke:

Claim Document Bundle
    ↓
Document
    ↓
Section
    ↓
Chunk

tanpa membuat schema khusus untuk masing-masing rumah sakit.

Namun stress test juga menemukan beberapa gap yang harus diperhatikan.

---

# 6. Document vs Clinical Workflow

Kita secara eksplisit memisahkan:

DOCUMENT STRUCTURE

dengan:

CLINICAL WORKFLOW.

Ini sangat penting.

Contoh urutan halaman PDF:

1. SEP
2. INA-CBG
3. Resume
4. Diagnosis
5. Prescription
6. Assessment
7. CPPT

Tidak berarti pasien mengalami kejadian tersebut dalam urutan itu.

Clinical workflow harus direkonstruksi dari:

- tanggal;
- waktu;
- timestamp;
- event;
- hubungan antar dokumen;
- evidence.

Jadi:

Document Order ≠ Clinical Event Order

---

# 7. Semantic Hierarchy

Struktur semantic utama yang kita sepakati:

Claim Document Bundle
    ↓
Document
    ↓
Section
    ↓
Chunk
    ↓
Fact / Event

Definisi konseptual:

Document
= logical document.

Section
= semantic section dalam document.

Chunk
= semantic unit yang cukup koheren untuk diproses/retrieve.

Fact
= informasi faktual.

Event
= sesuatu yang terjadi dalam perjalanan pelayanan.

---

# 8. Segment vs Chunk

Kita membedakan:

SEGMENT
dan
CHUNK.

Segment adalah major semantic part/document identity.

Contoh:

- SEP
- Medical Resume
- Laboratory
- Radiology
- CPPT
- Billing
- INA-CBG

Chunk adalah unit yang lebih kecil.

Contoh:

Medical Resume
    ├── Chief Complaint
    ├── History
    ├── Physical Examination
    ├── Diagnosis
    └── Treatment

Chunk bukan sekadar potongan teks berdasarkan jumlah token.

Chunk harus mempertahankan semantic coherence.

ARCHITECTURE DECISION REQUIRED (ADR-15) `[r1]`:
SEGMENT didefinisikan di sini sebagai "major semantic part/document
identity", tetapi `DATA_MODEL.md` tidak memiliki entity Segment. Belum
jelas apakah Segment sama dengan Document, Section, atau tingkat
tersendiri. Tidak ada entity baru diperkenalkan sebelum diputuskan.

---

# 9. Document Role

Kita ingin memisahkan semantic role dokumen.

Initial roles:

ADMINISTRATIVE
CLINICAL
DIAGNOSTIC
MEDICATION_TREATMENT
FINANCIAL
CLAIM_CODING
SUPPORTING

Contoh:

SEP
→ ADMINISTRATIVE

Medical Resume
→ CLINICAL

Laboratory
→ DIAGNOSTIC

Prescription
→ MEDICATION_TREATMENT

Billing
→ FINANCIAL

INA-CBG
→ CLAIM_CODING

Supporting document dari rumah sakit lain
→ SUPPORTING

Satu document dapat memiliki lebih dari satu role jika diperlukan.

---

# 10. Claim Anchor Documents

Kita juga memperkenalkan konsep Claim Anchor.

Initial claim anchors:

- SEP
- INA-CBG Output
- Billing / Service Recap

Alasannya:

SEP memberikan administrative/service context.

INA-CBG memberikan claim/coding/payment context.

Billing memberikan service utilization/financial context.

Tetapi ketiganya TIDAK boleh otomatis dianggap sebagai clinical
timeline.

Mereka berfungsi sebagai anchor yang dapat dibandingkan dengan
clinical evidence.

Contoh:

Clinical Evidence
    ↓
Diagnosis / Procedure / Investigation / Treatment
    ↓
Claim / Coding
    ↓
INA-CBG
    ↓
Billing

Dengan demikian clinical information, claim/coding information, dan
financial information tetap berbeda tetapi saling berhubungan.

---

# 11. Care Pathway

Clinical workflow kita modelkan sebagai dimensi terpisah.

Initial pathways:

EMERGENCY / IGD
OUTPATIENT / RAWAT JALAN
INPATIENT / RAWAT INAP

Satu claim dapat melibatkan lebih dari satu pathway.

Contoh:

IGD
 ↓
INPATIENT
 ↓
DISCHARGE

atau:

OUTPATIENT
 ↓
REFERRAL
 ↓
INPATIENT

Care pathway bukan document type.

---

# 12. IGD Workflow

Initial conceptual workflow:

ARRIVAL
 ↓
TRIAGE
 ↓
INITIAL_ASSESSMENT
 ↓
INITIAL_TREATMENT
 ↓
SUPPORTING_INVESTIGATION
 ↓
DISPOSITION

Possible outcomes:

DISCHARGE
INPATIENT_ADMISSION
ICU
SURGERY
REFERRAL

---

# 13. Outpatient Workflow

Initial conceptual workflow:

REGISTRATION
 ↓
ELIGIBILITY
 ↓
INITIAL_ASSESSMENT
 ↓
CLINICAL_ASSESSMENT
 ↓
INVESTIGATION
 ↓
TREATMENT
 ↓
DISPOSITION

Possible outcomes:

FOLLOW_UP
PRESCRIPTION
PROCEDURE
INPATIENT_ADMISSION
REFERRAL

---

# 14. Inpatient Workflow

Initial conceptual workflow:

ADMISSION
 ↓
INITIAL_ASSESSMENT
 ↓
DAILY_CARE
 ↓
INVESTIGATION
 ↓
TREATMENT
 ↓
MONITORING
 ↓
DISPOSITION
 ↓
DISCHARGE

Daily care may involve:

- doctor;
- nursing;
- other PPA.

Investigation may include:

- laboratory;
- radiology;
- pathology;
- other.

Treatment may include:

- medication;
- procedure;
- nursing;
- other.

---

# 15. Provenance

One of the most important architectural decisions:

Do not mix different origins of information.

We distinguish:

SOURCE_FACT
DERIVED_FACT
INFERRED_FACT
MODEL_OUTPUT

SOURCE_FACT:
explicitly present in source.

DERIVED_FACT:
deterministically calculated from source facts.

INFERRED_FACT:
conclusion inferred from multiple pieces of information.

MODEL_OUTPUT:
generated by AI/statistical/ML model.

Example:

SOURCE_FACT:
Admission date = 22 September

SOURCE_FACT:
Discharge date = 25 September

DERIVED_FACT:
LOS = 4 days

These must remain distinguishable.

---

# 16. Evidence

Evidence is a first-class concept.

The system should be able to answer:

"What is the claim/fact?"

"Why does the system believe this?"

"Which document supports it?"

"Where in the document?"

Evidence may contain:

- document_id;
- document_type;
- page_number;
- section_id;
- element_id;
- source_text;
- bbox;
- confidence.

However, not all source formats provide all fields.

For example:

bbox may not exist for:

- structured API data;
- some OCR outputs;
- external systems.

Therefore fields must be optional where appropriate.

---

# 17. Evidence Is Not the Same as Fact

This distinction is important.

Fact:

Diagnosis = R33

Evidence:

INA-CBG page 2 says R33.

Another Evidence:

Medical Resume page 4 says urinary retention.

Therefore:

Fact
    ↓
evidence_refs[]
    ↓
Evidence[]
    ↓
Source Document

One fact may have multiple supporting evidence items.

---

# 18. Clinical Timeline

Timeline is reconstructed from Events.

Timeline is NOT copied from PDF page order.

Example:

Triage
 ↓
Initial Assessment
 ↓
Investigation
 ↓
Treatment
 ↓
Disposition

Each timeline event should preserve evidence references.

Timeline is a derived representation.

Original document/event evidence remains the source.

---

# 19. Temporal Precision

The system must never invent time precision.

Initial levels:

EXACT_DATETIME
DATE
MONTH
YEAR
UNKNOWN

Example:

"September 2025"

must remain:

value = 2025-09
precision = MONTH

It must not become:

2025-09-15

unless the source actually says that date.

---

# 20. Missing Information

We recognized that:

NOT_FOUND
is not the same as:

NOT_PERFORMED.

Initial missingness states:

NOT_FOUND
NOT_DOCUMENTED
NOT_APPLICABLE
EXPLICITLY_NEGATED
UNKNOWN

This is important for claim verification.

Absence of evidence must not automatically become evidence of absence.

---

# 21. Narrative vs Intelligence

Narrative and intelligence are deliberately separated.

Narrative:

Canonical Claim
+
Evidence
+
Timeline
↓
Patient Journey Summary

Intelligence:

Canonical Claim
+
Evidence
+
Timeline
+
Rules / Models
↓
Risk / Anomaly / Inconsistency / Recommendation

The LLM should not become the source of truth.

It should consume structured information.

---

# 22. Embeddings

Embeddings are supporting infrastructure.

They may later support:

- semantic evidence retrieval;
- RAG;
- similar claim retrieval;
- historical comparison;
- reviewer search.

But embeddings are NOT the primary extraction mechanism.

The desired sequence is:

PDF
 ↓
Document Understanding
 ↓
Canonical Claim
 ↓
Evidence
 ↓
Timeline

not:

PDF
 ↓
Embedding
 ↓
LLM
 ↓
Claim

---

# 23. Why This Taxonomy Exists

The taxonomy is not merely a list of document names.

It exists to create a stable semantic contract between:

Document Intelligence
        ↓
Canonical Claim
        ↓
Evidence
        ↓
Timeline
        ↓
Narrative
        ↓
Intelligence
        ↓
DESKON / CLAIRE

This means that if Hospital A changes its PDF layout, the downstream
systems should not need to change.

Only the document understanding / extraction layer should need to adapt.

---

# 24. Important Architecture Rule

Hospital-specific logic belongs in:

Document Classification
Extraction
Hospital Adapter (if necessary)

Hospital-specific logic should NOT leak into:

Canonical Claim
Evidence model
Timeline model
Intelligence model

unless there is a genuine domain reason.

---

# 25. New Insights From Stress Testing

When the two real-world PDFs were tested, several additional concerns
were discovered.

These should be treated as architectural questions rather than
automatically solved.

Examples:

1. A physical PDF contains multiple logical documents.

2. Some pages are image/scan only.

3. Some pages contain handwriting.

4. Physical file and physical page are not yet explicit entities.

5. Empty pages may exist.

6. A logical document may not occupy contiguous pages.

7. Duplicate pages may exist.

8. Different source documents may contain conflicting information.

9. A diagnosis can have different semantic roles.

10. Dates may have different meanings:
   service date, admission date, discharge date, order date,
   result date, document date, etc.

11. Date formats may vary between Indonesian and English.

12. Medication information may have different contexts:
   order, administration, prescription, discharge medication, billing.

13. Hospital billing total and INA-CBG tariff are not necessarily the
   same financial concept.

14. Evidence may expose sensitive patient information.

These issues should NOT automatically result in arbitrary schema changes.

For each one, determine whether it is:

- taxonomy concern;
- data model concern;
- extraction concern;
- implementation concern;
- security/privacy concern;
- architecture decision.

---

# 25A. Status Resolusi Hasil Stress Test `[r1]`

Sesuai instruksi bagian 25, setiap temuan diklasifikasikan. Kolom:
T = taxonomy, D = data model, E = extraction, I = implementation,
S = security/privacy, ADR = architecture decision masih diperlukan.

| # | Temuan (bagian 25) | T | D | E | I | S | ADR |
|---|---|---|---|---|---|---|---|
| 1 | PDF memuat banyak logical document | sudah (3, 3A) | 5A | | | | |
| 2 | Halaman gambar/scan saja | 3A | 11A | ya | | | ADR-11 |
| 3 | Tulisan tangan | 3A | 11A | ya | | | ADR-11 |
| 4 | File dan halaman fisik belum eksplisit | 3A | 5A | | | | ADR-01 |
| 5 | Halaman kosong | 3A | 5A | | | | |
| 6 | Document tidak kontigu | 3A | 5A, 7 | | | | ADR-01 |
| 7 | Halaman duplikat | 3A | 7, 29 | | ya (deteksi) | | ADR-07 |
| 8 | Informasi saling bertentangan | 26 | 38A | | deteksi | | ADR-02 |
| 9 | Peran diagnosis berbeda | | 23 | | | | ADR-04 |
| 10 | Banyak makna tanggal | | 17A, 17B | | | | ADR-05 |
| 11 | Format tanggal Indonesia/Inggris | | 17A | | ya (adapter) | | ADR-05 |
| 12 | Konteks obat | | 25 | | | | ADR-06 |
| 13 | Total tagihan RS vs tarif INA-CBG | 27 | 29 | | | | ADR-07 |
| 14 | Evidence membuka data sensitif | | 15A | | ya (redaksi) | ya | ADR-08 |

Temuan tambahan dari pemetaan terhadap dua PDF, di luar daftar di
atas: jenis layanan menurut klaim vs care pathway (ADR-03), panel dan
spesimen laboratorium (ADR-13), alias dan kode fasilitas (ADR-12),
hubungan Fact / entity kanonik / Event (ADR-09), referensi
`derived_from` (tanpa ADR), dan stage per pathway (ADR-10). Lihat
`DATA_MODEL.md` Appendix A.

---

# 26. Conflict Handling

An important principle emerging from the PDF analysis:

If two documents disagree, do not silently choose one.

Example:

SEP:
referring facility = Facility A

Medical Resume:
referring facility = Facility B

The system should preserve both source facts.

Potentially:

SOURCE_FACT A
+
SOURCE_FACT B
↓
CONFLICT / INCONSISTENCY
↓
INTELLIGENCE

The conflict itself may become an intelligence signal.

Therefore the canonical model should not destroy contradictory source
information merely to create one clean value.

Status `[r1]`: prinsip di atas dipertahankan. Yang belum diputuskan
(ADR-02) adalah di lapisan mana catatan konflik disimpan (Canonical
Claim atau Intelligence), apakah ada aturan memilih nilai, dan
kosakata jenis konflik. Lihat `DATA_MODEL.md` bagian 38A.

---

# 27. Financial Semantics

Similarly, different financial figures should not automatically be
treated as the same field.

For example:

Hospital Billing Total
≠
INA-CBG Tariff

They represent different concepts.

The model should preserve semantic distinction.

This may later support:

- claim verification;
- payment analysis;
- anomaly detection;
- reconciliation.

Status `[r1]`: prinsip di atas dipertahankan. Kosakata konsep
keuangan (misalnya billed charge vs claim tariff) dan perlakuan
duplikat masih terbuka (ADR-07). Lihat `DATA_MODEL.md` bagian 29.

---

# 28. Desired End State

The architecture should ultimately support:

Different Hospital
Different PDF
Different Layout
Different Terminology
Different Document Composition

        ↓

Document Intelligence

        ↓

Common Semantic Representation

        ↓

Canonical Claim

        ↓

Evidence

        ↓

Clinical Timeline

        ↓

Narrative + Intelligence

without losing traceability to the original source.

---

# 29. Role of Claude

Claude is being used as an implementation and architecture-consistency
assistant.

Claude may:

- inspect the repository;
- test the model against sample PDFs;
- identify gaps;
- refactor code;
- improve documentation;
- add tests;
- identify inconsistencies.

However:

Claude must NOT silently redefine the domain architecture.

If a finding requires a domain decision, Claude should report:

ARCHITECTURE DECISION REQUIRED

and explain:

- current design;
- problem;
- options;
- implications;
- recommendation.

The human architecture owner will then decide.

---

# 30. Current Objective

The current objective is NOT yet:

- JSON Schema;
- Python implementation;
- OCR engine;
- vector database;
- LLM provider;
- production deployment.

The immediate objective is:

1. finalize DOCUMENT_TAXONOMY.md;
2. finalize DATA_MODEL.md;
3. validate both against representative claim bundles;
4. identify unresolved architecture decisions;
5. only then create machine-readable schemas.

---

# 31. Guiding Principle

The final system should be able to answer:

"What happened to the patient?"

"What documents support that?"

"What information came directly from the source?"

"What was calculated?"

"What was inferred?"

"What did the model conclude?"

"Where did the model get its evidence?"

without depending on the original hospital's PDF layout.

That is the purpose of the GOUTAMIND Document Taxonomy.

---

# 32. Catatan Konsistensi dengan DATA_MODEL `[r1]`

Bagian ini mencatat selisih terminologi dan kepemilikan antara
dokumen ini dan `DATA_MODEL.md`. Tidak ada yang diubah; setiap butir
menunggu keputusan pemilik arsitektur.

1. **Bahasa.** Dokumen ini berbahasa Indonesia, `DATA_MODEL.md`
   berbahasa Inggris. Istilah baku (nama field, enum, nama entity)
   tetap dalam bahasa Inggris.
2. **Kepemilikan daftar `document_type`.** `DATA_MODEL.md` bagian 1
   menyebut taxonomy sebagai pemilik kosakata, tetapi daftar
   `document_type` (SEP, INA_CBG_OUTPUT, MEDICAL_RESUME, ...) saat ini
   hanya ada di `DATA_MODEL.md` bagian 7. Taxonomy belum mendefinisikan
   daftar tersebut. Siapa pemiliknya perlu diputuskan.
3. **Penamaan dokumen.** Taxonomy memakai "Billing", "Service Recap",
   "Detailed Billing", "Medical Resume", "Discharge Summary", "INA-CBG";
   data model memakai `BILLING`, `SERVICE_RECAP`, `MEDICAL_RESUME`,
   `DISCHARGE_SUMMARY`, `INA_CBG_OUTPUT`. Belum ada definisi yang
   membedakan Billing, Service Recap, dan Detailed Billing, serta
   Medical Resume dan Discharge Summary.
4. **Segment.** Lihat ADR-15 pada bagian 8.
5. **Penamaan umum.** Lihat ADR-14 (singular/plural field,
   `document_role[]`, huruf kapital enum).
6. **Versi taxonomy.** `DATA_MODEL.md` bagian 43 menyebut
   `document_taxonomy_version`, sedangkan dokumen ini sebelumnya tidak
   punya nomor versi. Header di atas menambahkannya.

