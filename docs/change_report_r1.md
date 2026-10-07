# Change Report: revisi r1 DOCUMENT_TAXONOMY dan DATA_MODEL (baseline v0.1)

Tidak ada commit, push, atau branch. Repo lokal Anda tidak tersentuh. Revisi ada di folder bersama project, bukan di `D:\MSSQL\...`, jadi perlu Anda bandingkan (diff) dan salin sendiri. Label versi tetap **0.1, revision r1 (proposed)**, tidak dinaikkan ke 0.2.

## 1. Files changed

| File | Status |
|---|---|
| `/mnt/project-files/docs/DOCUMENT_TAXONOMY.md` | Revisi r1. Seluruh 31 bagian asli dipertahankan kata per kata (diperiksa dengan diff). Hanya penambahan. |
| `/mnt/project-files/docs/DATA_MODEL.md` | Revisi r1. Seluruh 51 bagian baseline dipertahankan, nomor tidak berubah. Hanya penambahan dan dua perbaikan editorial. |

## 2. Changes made

Taxonomy (semua ditandai `[r1]`):
- Header versi dan status, catatan revisi.
- Bagian 3A baru: lapisan wadah fisik (Source File, Page, Document Element), terpisah dari hierarki semantik.
- Bagian 8: catatan ADR-15 tentang Segment.
- Bagian 25A baru: tabel klasifikasi 14 temuan stress test (taxonomy / data model / extraction / implementation / security / ADR), sesuai instruksi bagian 25 asli.
- Catatan status di akhir bagian 26 dan 27 (prinsip tetap, bagian yang terbuka dirujuk ke ADR).
- Bagian 32 baru: selisih konsistensi dengan data model.

Data model (semua ditandai `[r1]`, field baru berstatus usulan):
- Bagian 0 (catatan revisi), 2.6 (pembeda inti), 5A, 11A, 12A, 15A, 17A/17B, 18A, 38A, Appendix A dan B.
- Field tambahan pada Document, Facility, Evidence, Fact, Event, Diagnosis, Procedure, Medication, Investigation, Cost.
- Bagian 19 diselaraskan ke stage per pathway; sekarang terverifikasi terhadap taxonomy bagian 12-14, bukan hanya Project Instructions.
- Perbaikan editorial: `input_format` ganda (bagian 6), "Clinical Claim" menjadi "Canonical Clinical Claim" (bagian 22).
- Setelah membaca taxonomy lengkap: ADR-15 (Segment), kutipan prinsip taxonomy bagian 26 dan 27 pada ADR-02 dan ADR-07.

## 3. Gap → resolution

Phase 1 (T taxonomy, D data model, E extraction, I implementation, S security/privacy):

| # | Gap | T | D | Lainnya | ADR | Resolusi |
|---|---|---|---|---|---|---|
| 1 | File/halaman fisik, kosong, tidak kontigu | 3A | 5A, 7, 9 | I (segmentasi) | ADR-01 (sebagian) | `page_refs[]`, SourceFile, Page |
| 2 | Metadata ekstraksi scan/foto | 3A | 11, 11A, 15 | E, I | ADR-11 | `extraction_method`, `content_kind` |
| 3 | Sumber bertentangan | 26 (status) | 38A | I (deteksi) | ADR-02 | SourceDiscrepancy |
| 4 | Jenis layanan klaim vs pathway | - | 18A | - | ADR-03 | `declared_service_type` |
| 5 | Peran diagnosis, coding system | - | 23 | - | ADR-04 | `coding_system`, `diagnosis_context` |
| 6 | Banyak makna tanggal | - | 17A, 17B | - | ADR-05 | `date_role`, `dates[]` |
| 7 | Format tanggal campuran | - | 17A (`raw_text`) | **I (adapter)** | ADR-05 (tanggal ambigu) | `raw_text` |
| 8 | Konteks obat, alkes | - | 25 | - | ADR-06 | `medication_context`, `item_category` |
| 9 | Total tagihan vs tarif INA-CBG | 27 (status) | 29 | - | ADR-07 | `amount_basis`, `cost_level`, `duplicate_of` |
| 10 | Panel/spesimen lab | - | 26 | E | ADR-13 | field opsional |
| 11 | Alias/kode fasilitas | - | 8 | I | ADR-12 | `facility_aliases[]`, `facility_codes[]` |
| 12 | Evidence membuka data sensitif | - | 15A | S, I (redaksi) | ADR-08 | `sensitivity`, `redaction_state` |
| 13 | Fact vs entitas vs Event | - | 12A | - | ADR-09 | `source_fact_refs[]`, `source_event_refs[]` |
| 14 | `derived_from` hilang | - | 12, 13, 38, 39, 44 | - | **tidak ada** | `derived_from_refs[]`, `inference_basis_refs[]` |
| 15 | Stage lintas pathway | - | 19 | - | ADR-10 (sebagian) | stage per pathway |

Hanya gap 14, perbaikan editorial, dan penyelarasan stage (gap 15, sebagian) yang bebas keputusan domain. Gap lain hanya diberi **bentuk usulan**, bukan keputusan.

## 4. Konsep baru

SourceFile, Page, `page_refs[]`, `extraction_method`, `content_kind`, Temporal Value (`raw_text`, `date_role`), SourceDiscrepancy, `declared_service_type`, `diagnosis_context`, `coding_system`, `medication_context`, `item_category`, `amount_basis`, `cost_level`, `duplicate_of`, `availability_status`, `derived_from_refs[]`, `inference_basis_refs[]`, `sensitivity`, `redaction_state`, `facility_aliases[]`, `facility_codes[]`. Di taxonomy hanya istilah Source File / Page / Document Element (3A).

## 5. Sengaja TIDAK diperkenalkan

- JSON Schema, kode Python, nama kelas, OCR, vector DB, pilihan LLM.
- Aturan hospital-specific atau format lembar rumah sakit tertentu.
- Aturan memilih nilai saat sumber bertentangan.
- Kebijakan redaksi/retensi data pribadi, model identitas Participant.
- Entity Segment, entity panel lab, entity alkes terpisah.
- Algoritma deteksi duplikat dan parsing tanggal.
- Perpindahan kepemilikan daftar `document_type` dari data model ke taxonomy (hanya dicatat, bagian 32 taxonomy).
- Penyeragaman bahasa taxonomy (Indonesia) dan data model (Inggris).
- Perubahan hierarki semantik, layer, atau nama field baseline.

## 6. Architecture decisions masih diperlukan

ADR-01 sampai ADR-15 (rinci di `DATA_MODEL.md` Appendix B). Yang paling menentukan bentuk schema: **ADR-01, 02, 08, 09, 11, 15**. Sisanya aditif dan bisa menyusul. Taxonomy bagian 26 menyiratkan konflik "menjadi sinyal Intelligence", tetapi tidak menyebut di mana catatan konfliknya disimpan, sehingga ADR-02 tetap terbuka.

## 7. Potensi risiko

1. **Scope.** Walau label tetap 0.1, jumlah tambahan di data model besar (file bertambah dari sekitar 1.100 menjadi sekitar 2.000 baris). Usulan bisa terbaca sebagai keputusan. Opsi: saya pangkas menjadi catatan gap, daftar ADR, dan perbaikan gap 14 saja.
2. Nilai enum usulan (date_role, medication_context, amount_basis, dll.) berasal dari dua bundle saja, bukan sampel representatif.
3. Invariant 14-19 di data model adalah usulan. Jika disetujui tanpa dibahas, menjadi kontrak.
4. Taxonomy sekarang punya tiga bagian baru, tetapi belum mendefinisikan daftar `document_type` yang dirujuk data model (ADR-14/bagian 32).
5. Dua PDF contoh memuat data pasien asli. Isinya tidak saya salin ke dokumen, tetapi file asli masih ada di unggahan project.
6. Dokumen ini belum ada di repo lokal Anda. Selisih dengan versi lokal Anda yang mungkin sudah berubah tidak bisa saya lihat.
7. Pemetaan gap 1-14 ke temuan taxonomy bagian 25 (25A) adalah penilaian saya. Mohon dicek.

## 8. Rekomendasi langkah berikutnya

1. Review kedua file dan putuskan: pertahankan r1 penuh atau pangkas.
2. Putuskan enam ADR yang menentukan bentuk schema (01, 02, 08, 09, 11, 15).
3. Putuskan kepemilikan daftar `document_type` dan perbedaan Billing / Service Recap / Detailed Billing (taxonomy bagian 32).
4. Jalankan ulang uji pemetaan pada 1-2 bundle tambahan dari rumah sakit lain sebelum nilai enum dikunci.
5. Setelah itu baru JSON Schema.
