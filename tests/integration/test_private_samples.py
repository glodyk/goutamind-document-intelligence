"""Optional run against real claim bundles kept on the developer's machine.

Put PDFs in ``samples_private/`` (git-ignored) or point
``GOUTAMIND_PRIVATE_SAMPLES`` at a folder. The test is skipped when no PDF
is found, so CI never needs private data. It checks structural invariants
only and never prints or asserts document content.
"""

import os
from pathlib import Path

import pytest

from app.vocabulary import IngestionStatus, PageKind
from pipeline.run import process_pdf

ROOT = Path(__file__).resolve().parents[2]
SAMPLES = Path(os.environ.get("GOUTAMIND_PRIVATE_SAMPLES", ROOT / "samples_private"))
PDFS = sorted(SAMPLES.glob("*.pdf")) if SAMPLES.is_dir() else []


@pytest.mark.skipif(not PDFS, reason="no private sample PDFs available")
@pytest.mark.parametrize("pdf", PDFS, ids=lambda p: f"sample-{PDFS.index(p) + 1}")
def test_private_bundle_invariants(pdf: Path):
    bundle = process_pdf(pdf)
    source = bundle.source_files[0]
    assert source.ingestion_status is IngestionStatus.INGESTED
    assert [p.page_number for p in source.pages] == list(range(1, (source.page_count or 0) + 1))

    pages = bundle.pages
    assigned = {ref.page_id for d in bundle.documents for ref in d.page_refs}
    for page in source.pages:
        # Every page is either in a document or is blank: nothing is dropped silently.
        assert page.page_id in assigned or page.page_kind is PageKind.BLANK

    evidence = {e.evidence_id: e for e in bundle.evidence}
    for item in [*bundle.facts, *bundle.events]:
        assert item.evidence_refs
        for ref in item.evidence_refs:
            assert evidence[ref].page_id in pages
            assert pages[evidence[ref].page_id].source_file_id == source.source_file_id
