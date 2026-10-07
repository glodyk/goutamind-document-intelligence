import io
from pathlib import Path

from pypdf import PdfWriter

from app.extraction.pdf_reader import read_pdf
from app.ids import IdFactory
from app.vocabulary import (
    ExtractionMethod,
    IngestionStatus,
    Modality,
    PageKind,
    TextStatus,
)
from tests.fixtures.synthetic_pdf import build_pdf


def write(tmp_path: Path, name: str, data: bytes) -> Path:
    path = tmp_path / name
    path.write_bytes(data)
    return path


def test_source_file_identity_is_stable_and_content_based(tmp_path: Path):
    data = build_pdf([["SATU"], ["DUA"]])
    a = read_pdf(write(tmp_path, "a.pdf", data), IdFactory())
    b = read_pdf(write(tmp_path, "renamed.pdf", data), IdFactory())
    c = read_pdf(write(tmp_path, "c.pdf", build_pdf([["LAIN"]])), IdFactory())
    assert a.source_file_id == b.source_file_id
    assert a.content_digest == b.content_digest
    assert a.source_file_id != c.source_file_id
    assert a.page_count == 2
    assert a.media_type == "application/pdf"
    assert a.source_reference == "a.pdf"  # file name only, no local path


def test_pages_keep_numbers_even_without_text(tmp_path: Path):
    source = read_pdf(write(tmp_path, "x.pdf", build_pdf([["TEKS"], "BLANK", "IMAGE"])), IdFactory())
    assert [p.page_number for p in source.pages] == [1, 2, 3]
    text, blank, image = source.pages
    assert (text.page_kind, text.modality, text.extraction_method) == (
        PageKind.CONTENT,
        Modality.DIGITAL_TEXT,
        ExtractionMethod.NATIVE_TEXT,
    )
    assert (blank.page_kind, blank.text_status) == (PageKind.BLANK, TextStatus.NOT_AVAILABLE)
    # Image-only: content exists, but nothing says whether it is a scan or a photo.
    assert (image.page_kind, image.modality) == (PageKind.CONTENT, Modality.UNKNOWN)
    assert image.extraction_method is ExtractionMethod.UNKNOWN
    assert image.text_status is TextStatus.NOT_AVAILABLE
    assert image.image_count == 1


def test_unreadable_file_fails_gracefully(tmp_path: Path):
    source = read_pdf(write(tmp_path, "broken.pdf", b"this is not a pdf"), IdFactory())
    assert source.ingestion_status is IngestionStatus.FAILED
    assert source.page_count is None
    assert source.pages == []
    assert source.error


def test_password_protected_file_fails_gracefully(tmp_path: Path):
    writer = PdfWriter()
    writer.add_blank_page(100, 100)
    writer.encrypt("secret", algorithm="RC4-128")
    buffer = io.BytesIO()
    writer.write(buffer)
    source = read_pdf(write(tmp_path, "locked.pdf", buffer.getvalue()), IdFactory())
    assert source.ingestion_status is IngestionStatus.FAILED
    assert "password" in (source.error or "").lower()
