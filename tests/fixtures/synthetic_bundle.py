"""A fully synthetic claim bundle that exercises every rule in the slice.

No real person, facility, claim or record number appears here. The layout
is invented, but it reproduces the structural situations seen in real
bundles (DATA_MODEL 48): several logical documents in one PDF, an untitled
first page, printed page counters, blank separator pages, an image-only
page, two consecutive documents of the same type, an ambiguous numeric date,
a month-precision date, a "-" value, and a device on a prescription line.
"""

from tests.fixtures.synthetic_pdf import PageSpec, build_pdf

SYNTHETIC_BUNDLE_PAGES: list[PageSpec] = [
    # p1 INA-CBG output (claim anchor): title on line 2
    [
        "KEMENTERIAN KESEHATAN (CONTOH SINTETIS)",
        "Berkas Klaim Individual Pasien 06/02/2025",
        "Nama RS : RS SINTETIS",
        "Tanggal Masuk : 03/02/2025",
        "Tanggal Keluar : 05/02/2025",
        "Diagnosa Utama : K35.8 Acute appendicitis, other and unspecified",
        "Diagnosa Sekunder : -",
        "Prosedur : 47.09 Other appendectomy",
        "99.21 Injection of antibiotic",
        "Lembar 1 / 1",
    ],
    # p2 SEP without a title line: recognised by its labels
    [
        "No.SEP : 0000SINTETIS0001",
        "Tgl.SEP : 2025-02-03",
        "Nama Peserta : PASIEN SINTETIS",
        "Diagnosa Awal : R10.4 - Abdominal pain",
    ],
    # p3-p4 medical resume with printed counters; p4 starts with "RESEP"
    [
        "RS SINTETIS",
        "RESUME MEDIS",
        "Nama : PASIEN SINTETIS",
        "Tanggal Masuk : 3 Februari 2025 08:15 WIB",
        "Tanggal Keluar : 5 Februari 2025",
        "ANAMNESIS",
        "Nyeri perut kanan bawah sejak 1 hari",
        "DIAGNOSA",
        "K35.8 Acute appendicitis",
        "PROSEDUR",
        "47.09 Other appendectomy",
        "Halaman 1 of 2",
    ],
    [
        "RESEP",
        "R/ CEFTRIAXONE 1 g INJEKSI 2x1",
        "R/ DISPOSABLE SYRINGE 5 ml",
        "Kontrol : September 2025",
        "Halaman 2 of 2",
    ],
    "BLANK",  # p5
    "IMAGE",  # p6 photographed document, no text layer
    "BLANK",  # p7
    # p8-p9 laboratory report 1 (untitled; table header + counter)
    [
        "Pasien : PASIEN SINTETIS",
        "Tgl. Order : 03/02/2025 09:00",
        "Pemeriksaan Hasil Satuan Nilai Rujukan",
        "Hemoglobin 13.1 g/dL 12.0 - 16.0",
        "Halaman 1 of 2",
    ],
    [
        "Pemeriksaan Hasil Satuan Nilai Rujukan",
        "Leukosit 14.2 10^3/uL 4.0 - 10.0",
        "Halaman 2 of 2",
    ],
    # p10 laboratory report 2: same type right after report 1
    [
        "Pasien : PASIEN SINTETIS",
        "Pemeriksaan Hasil Satuan Nilai Rujukan",
        "CRP 48 mg/L < 5",
        "Halaman 1 of 1",
    ],
    # p11-p12 emergency assessment; p12 has no title
    [
        "ASESMEN AWAL GAWAT DARURAT",
        "Waktu Datang : 3 Februari 2025",
        "PEMERIKSAAN FISIK",
        "TD : 120/80 mmHg",
    ],
    [
        "Nyeri tekan McBurney (+)",
        "TINDAK LANJUT",
        "Rawat Inap",
    ],
    # p13 service recap (financial): "RADIOLOGI" here is a billing category
    [
        "NOTA REKAP PELAYANAN",
        "Tgl KRS : 5 Februari 2025",
        "LABORATORIUM",
        "Hemoglobin Rp 25,000.00",
        "RADIOLOGI",
        "USG Abdomen Rp 150,000.00",
        "GRAND TOTAL Rp 175,000.00",
    ],
    # p14 recognised title with no document_type in the data model
    ["TRIASE", "Waktu Datang : 3 Februari 2025, 07:55 WIB"],
    "BLANK",  # p15
    # p16 untitled text page with no current document -> UNKNOWN
    ["Catatan tambahan tanpa judul", "Isi sintetis"],
]


def synthetic_bundle_pdf() -> bytes:
    return build_pdf(SYNTHETIC_BUNDLE_PAGES)
