from datetime import UTC, datetime
from pathlib import Path

import pytest

from app.bundle import ClaimDocumentBundle
from pipeline.run import process_pdf
from tests.fixtures.synthetic_bundle import synthetic_bundle_pdf

FIXED_NOW = datetime(2025, 1, 1, tzinfo=UTC)


@pytest.fixture
def synthetic_pdf_path(tmp_path: Path) -> Path:
    path = tmp_path / "synthetic_bundle.pdf"
    path.write_bytes(synthetic_bundle_pdf())
    return path


@pytest.fixture
def synthetic_bundle(synthetic_pdf_path: Path) -> ClaimDocumentBundle:
    return process_pdf(synthetic_pdf_path, now=FIXED_NOW)
