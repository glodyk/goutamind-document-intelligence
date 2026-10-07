"""Vertical slice: PDF -> SourceFile -> Pages -> Documents -> Sections -> Chunks
-> Evidence -> Facts / Events.

Usage::

    python -m pipeline.run path/to/bundle.pdf [--out outputs/] [--numeric-date-order DMY]

Writes ``<name>.bundle.json`` and ``<name>.inspection.txt`` to ``--out``
(default ``outputs/``, which is git-ignored).
"""

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

from app.bundle import ClaimDocumentBundle
from app.document.dates import collect_document_dates
from app.document.segmentation import Segmenter
from app.document.structure import build_structure
from app.evidence.models import EvidenceRegistry
from app.extraction.facts import FactExtractor
from app.extraction.pdf_reader import read_pdf
from app.ids import IdFactory
from app.temporal import NumericOrder
from app.vocabulary import IngestionStatus
from pipeline.report import render_inspection
from pipeline.serialize import to_json_dict

SCHEMA_VERSION = "0.1-r1-slice"
"""Not a JSON Schema version: identifies the in-code shape of this slice."""
EXTRACTION_VERSION = "slice-1"

logger = logging.getLogger(__name__)


def process_pdf(
    path: Path,
    numeric_order: NumericOrder | None = None,
    now: datetime | None = None,
) -> ClaimDocumentBundle:
    """Run the whole slice on one PDF. Never raises for a bad PDF."""
    ids = IdFactory()
    evidence = EvidenceRegistry(ids)
    bundle = ClaimDocumentBundle(
        bundle_id=ids.next("bundle"),
        schema_version=SCHEMA_VERSION,
        extraction_version=EXTRACTION_VERSION,
    )

    source_file = read_pdf(path, ids, now=now)
    bundle.source_files.append(source_file)
    if source_file.ingestion_status is IngestionStatus.FAILED:
        return bundle

    pages = bundle.pages
    documents = Segmenter(ids, evidence).segment(source_file)
    for document in documents:
        build_structure(document, pages, ids)
        collect_document_dates(document, pages, numeric_order)

    extracted = FactExtractor(ids, evidence, numeric_order).extract(documents, pages)
    bundle.documents = documents
    bundle.facts = extracted.facts
    bundle.events = extracted.events
    bundle.evidence = list(evidence.items.values())
    return bundle


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--out", type=Path, default=Path("outputs"))
    parser.add_argument(
        "--numeric-date-order",
        choices=["DMY", "MDY"],
        default=None,
        help="resolve ambiguous dd/mm vs mm/dd dates (default: leave UNKNOWN)",
    )
    parser.add_argument(
        "--no-source-text", action="store_true", help="omit source text from the inspection report"
    )
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")
    logging.getLogger("pypdf").setLevel(logging.ERROR)  # font warnings are noise here

    if not args.pdf.is_file():
        print(f"not a file: {args.pdf}", file=sys.stderr)
        return 2

    bundle = process_pdf(args.pdf, numeric_order=args.numeric_date_order)
    args.out.mkdir(parents=True, exist_ok=True)
    stem = args.pdf.stem
    json_path = args.out / f"{stem}.bundle.json"
    report_path = args.out / f"{stem}.inspection.txt"
    json_path.write_text(json.dumps(to_json_dict(bundle), indent=2, ensure_ascii=False), "utf-8")
    report_path.write_text(render_inspection(bundle, show_source_text=not args.no_source_text), "utf-8")
    print(f"wrote {json_path} and {report_path}")
    return 0 if bundle.source_files[0].ingestion_status is IngestionStatus.INGESTED else 1


if __name__ == "__main__":
    raise SystemExit(main())
